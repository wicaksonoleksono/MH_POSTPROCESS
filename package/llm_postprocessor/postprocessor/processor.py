"""Main post-processor class."""

import json
from pathlib import Path
from typing import Optional

from llm_postprocessor.config import Settings, get_settings
from llm_postprocessor.llm.client import LLMClient, OpenAIClient, TogetherAIClient
from llm_postprocessor.schemas.input_schemas import SessionData
from llm_postprocessor.schemas.output_schemas import ProcessedResult
from llm_postprocessor.io.json_reader import JsonReader
from llm_postprocessor.io.conversation_loader import ChatHistoryFormatter


class PostProcessor:
    """Main post-processor for LLM analysis."""
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize post-processor.
        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self.llm_client = self._init_llm_client()

        # Initialize LLM analyzer
        from llm_postprocessor.postprocessor.llm_analyzer import LLMAnalyzer
        self.llm_analyzer = LLMAnalyzer(self.llm_client)

    def _init_llm_client(self) -> LLMClient:
        """Initialize LLM client based on settings."""
        if self.settings.llm.provider == "openai":
            return OpenAIClient(
                model_name=self.settings.llm.model_name,
                temperature=self.settings.llm.temperature,
                max_tokens=self.settings.llm.max_tokens,
            )
        elif self.settings.llm.provider == "togetherai":
            return TogetherAIClient(
                model_name=self.settings.llm.model_name,
                temperature=self.settings.llm.temperature,
                max_tokens=self.settings.llm.max_tokens,
            )
        else:
            raise ValueError(f"Unknown provider: {self.settings.llm.provider}")

    def process_session(self, session_data: SessionData) -> ProcessedResult:
        """Process a single session.

        Args:
            session_data: Input session data

        Returns:
            ProcessedResult: Processed results
        """
        return ProcessedResult(**{
            "user_id": session_data.user.user_id,
            "session_id": session_data.user.session_id,
            "llm_extraction": self._extract_llm_insights(session_data.llm_conversation),
            "metadata": session_data.metadata,
        })

    def _extract_llm_insights(self, llm_conversation) -> dict:
        """Extract insights from LLM conversation."""
        from llm_postprocessor.schemas.output_schemas import LLMExtraction
        from llm_postprocessor.schemas.llm_analysis_schemas import LLMAnalysisInput

        if not llm_conversation or len(llm_conversation) == 0:
            return LLMExtraction(**{
                "key_themes": [],
                "overall_sentiment": "neutral",
                "insights": "No LLM conversation available",
            })

        try:
            # Use LLMAnalyzer for clean interface
            analysis_output = self.llm_analyzer.analyze(
                LLMAnalysisInput(chat_history=llm_conversation)
            )

            # Extract key themes from indicators with score >= 2
            key_themes = [
                item.indicator
                for item in analysis_output.analysis
                if item.score.phq >= 2 or item.score.operational >= 2
            ]

            return LLMExtraction(**{
                "key_themes": key_themes,
                "overall_sentiment": "analyzed",
                "risk_factors": [],
                "insights": analysis_output.notes,
            })

        except Exception as e:
            # Fallback on error
            return LLMExtraction(**{
                "key_themes": ["error"],
                "overall_sentiment": "error",
                "insights": f"LLM extraction failed: {str(e)}",
            })

    def process_batch(self, sessions: list[SessionData]) -> list[ProcessedResult]:
        """Process multiple sessions.

        Args:
            sessions: List of session data

        Returns:
            List of processed results
        """
        results = []
        for session in sessions:
            result = self.process_session(session)
            results.append(result)
        return results


class BatchFileProcessor:
    """Process multiple session files from data folder."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize batch processor.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self.processor = PostProcessor(self.settings)

    def process_data_folder(
        self,
        data_folder: str | Path = "data",
        output_folder: str | Path = "post_processed",
        session_number: int = 1,
    ) -> dict:
        """Process all session files from data folder.

        Args:
            data_folder: Path to data folder containing user session folders
            output_folder: Path to save processed results
            session_number: Which session to process (default: 1)

        Returns:
            Dictionary with stats: {"processed": count, "failed": count, "results": [...]}
        """
        data_path = Path(data_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find all session folders matching pattern
        session_pattern = f"*_session{session_number}"
        session_folders = sorted(data_path.glob(session_pattern))

        results = []
        processed_count = 0
        failed_count = 0

        for folder in session_folders:
            conv_file = folder / "llm_conversation.json"

            if not conv_file.exists():
                print(f"⊘ Skipped {folder.name} - no llm_conversation.json")
                continue

            try:
                # Load and format conversation
                formatted_conv = ChatHistoryFormatter.format_from_file(conv_file)

                # Load raw messages for processing
                messages = JsonReader.read_conversation(conv_file)

                # Extract user_id and session_id from folder name
                # Format: user_11_miko_session1 -> user_id=user_11, session_id=session1
                folder_name = folder.name
                parts = folder_name.rsplit("_", 1)
                session_id = parts[-1] if len(parts) > 1 else "session1"
                user_id = parts[0] if len(parts) > 1 else folder_name

                # Create session data
                session_data = SessionData(**{
                    "user": {"user_id": user_id, "session_id": session_id},
                    "llm_conversation": messages,
                    "metadata": {
                        "folder_name": folder.name,
                        "data_path": str(conv_file),
                        "formatted_conversation": formatted_conv,
                    },
                })

                # Process session
                result = self.processor.process_session(session_data)

                # Save result to output folder
                output_subfolder = output_path / folder.name
                output_subfolder.mkdir(parents=True, exist_ok=True)

                output_file = output_subfolder / "analysis_result.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    # Use model_dump_json for proper serialization
                    f.write(result.model_dump_json(indent=2))

                results.append({
                    "folder": folder.name,
                    "status": "success",
                    "output_path": str(output_file),
                })
                processed_count += 1
                print(f"✓ Processed {folder.name}")

            except Exception as e:
                results.append({
                    "folder": folder.name,
                    "status": "failed",
                    "error": str(e),
                })
                failed_count += 1
                print(f"✗ Failed {folder.name}: {str(e)}")

        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(session_folders),
            "results": results,
        }


def _model_to_dict(model):
    """Return a serialisable representation compatible with Pydantic v1 & v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Unsupported model type: {type(model)!r}")

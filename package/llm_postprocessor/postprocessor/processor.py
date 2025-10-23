"""Main post-processor class."""

import json
import shutil
from pathlib import Path
from typing import Optional

from ..config import Settings, get_settings
from ..schemas.input_schemas import SessionData
from ..schemas.output_schemas import AssessmentSummary, ProcessedResult
from ..io.json_reader import JsonReader
from ..io.conversation_loader import ChatHistoryFormatter, ConversationLoader


class PostProcessor:
    """Main post-processor responsible for conversation formatting."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize post-processor.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()

    def process_session(self, session_data: SessionData) -> ProcessedResult:
        """Process a single session.

        Args:
            session_data: Input session data

        Returns:
            ProcessedResult containing formatted conversation and assessment summaries.
        """
        metadata = dict(session_data.metadata or {})
        data_path = metadata.get("data_path")
        session_folder = Path(data_path).parent if data_path else None

        phq_summary = self._load_assessment_summary(
            session_folder / "phq_analysis.jsonl" if session_folder else None
        )
        llm_summary = self._load_assessment_summary(
            session_folder / "llm_analysis.jsonl" if session_folder else None
        )

        phq_responses = self._load_json(session_folder / "phq_responses.json" if session_folder else None)
        session_metadata = self._load_json(session_folder / "metadata.json" if session_folder else None)

        if session_metadata:
            metadata["session_metadata"] = session_metadata

        if phq_summary:
            extra = phq_summary.extra.copy() if phq_summary.extra else {}
            if phq_responses:
                extra.update({
                    "total_score": phq_responses.get("total_score"),
                    "max_possible_score": phq_responses.get("max_possible_score"),
                    "responses": phq_responses.get("responses"),
                })
            if session_metadata and session_metadata.get("phq_analysis"):
                extra["analysis_stats"] = session_metadata["phq_analysis"]
            if extra:
                phq_summary = phq_summary.model_copy(update={"extra": extra})

        if llm_summary and session_metadata and session_metadata.get("llm_analysis"):
            extra = llm_summary.extra.copy() if llm_summary.extra else {}
            extra["analysis_stats"] = session_metadata["llm_analysis"]
            llm_summary = llm_summary.model_copy(update={"extra": extra})

        return ProcessedResult(
            user_id=session_data.user.user_id,
            session_id=session_data.user.session_id,
            metadata=metadata,
            phq_summary=phq_summary,
            llm_summary=llm_summary,
        )

    @staticmethod
    def _load_assessment_summary(file_path: Optional[Path]) -> Optional[AssessmentSummary]:
        """Read a JSONL assessment file and return a lightweight summary."""
        if not file_path or not file_path.exists():
            return None

        metadata_entry = None
        total_rows = 0
        with open(file_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total_rows += 1
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if metadata_entry is None and payload.get("type") == "metadata":
                    metadata_entry = payload

        data_rows = total_rows - (1 if metadata_entry else 0)
        if data_rows < 0:
            data_rows = 0

        return AssessmentSummary(
            metadata=metadata_entry,
            total_rows=total_rows,
            data_rows=data_rows,
        )

    @staticmethod
    def _load_json(file_path: Optional[Path]) -> Optional[dict]:
        """Safely load a JSON file if it exists."""
        if not file_path or not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return None

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
                raw_turns = ConversationLoader.load_turns_without_created_at(conv_file)

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
                        "raw_conversation": raw_turns,
                    },
                })

                # Process session
                result = self.processor.process_session(session_data)

                # Save result and copy supporting analysis files
                output_subfolder = output_path / folder.name
                output_subfolder.mkdir(parents=True, exist_ok=True)

                phq_src = folder / "phq_analysis.jsonl"
                llm_src = folder / "llm_analysis.jsonl"
                phq_responses_src = folder / "phq_responses.json"
                metadata_src = folder / "metadata.json"

                metadata = dict(result.metadata or {})
                phq_summary = result.phq_summary
                llm_summary = result.llm_summary

                if phq_src.exists():
                    phq_dest = output_subfolder / phq_src.name
                    shutil.copyfile(phq_src, phq_dest)
                    rel_path = str(phq_dest.relative_to(output_path))
                    metadata["phq_analysis_file"] = rel_path
                    if phq_summary is not None:
                        phq_summary = phq_summary.model_copy(update={"file_path": rel_path})
                    else:
                        phq_summary = AssessmentSummary(file_path=rel_path)

                if llm_src.exists():
                    llm_dest = output_subfolder / llm_src.name
                    shutil.copyfile(llm_src, llm_dest)
                    rel_path = str(llm_dest.relative_to(output_path))
                    metadata["llm_analysis_file"] = rel_path
                    if llm_summary is not None:
                        llm_summary = llm_summary.model_copy(update={"file_path": rel_path})
                    else:
                        llm_summary = AssessmentSummary(file_path=rel_path)

                if phq_responses_src.exists():
                    phq_responses_dest = output_subfolder / phq_responses_src.name
                    shutil.copyfile(phq_responses_src, phq_responses_dest)
                    rel_path = str(phq_responses_dest.relative_to(output_path))
                    metadata["phq_responses_file"] = rel_path

                if metadata_src.exists():
                    metadata_dest = output_subfolder / metadata_src.name
                    shutil.copyfile(metadata_src, metadata_dest)
                    rel_path = str(metadata_dest.relative_to(output_path))
                    metadata["session_metadata_file"] = rel_path

                result_to_store = result.model_copy(
                    update={
                        "metadata": metadata,
                        "phq_summary": phq_summary,
                        "llm_summary": llm_summary,
                    }
                )

                output_file = output_subfolder / "analysis_result.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    # Use model_dump_json for proper serialization
                    f.write(result_to_store.model_dump_json(indent=2))

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

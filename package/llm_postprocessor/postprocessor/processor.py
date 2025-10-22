"""Main post-processor class."""

from typing import Optional

from llm_postprocessor.config import Settings, get_settings
from llm_postprocessor.llm.client import LLMClient, OpenAIClient, TogetherAIClient
from llm_postprocessor.schemas.input_schemas import SessionData
from llm_postprocessor.schemas.output_schemas import ProcessedResult


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

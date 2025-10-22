"""Main post-processor class."""

from typing import Optional

from llm_postprocessor.config import Settings, get_settings
from llm_postprocessor.llm.client import LLMClient, OpenAIClient, TogetherAIClient
from llm_postprocessor.schemas.input_schemas import SessionData
from llm_postprocessor.schemas.output_schemas import ProcessedResult
from llm_postprocessor.io.json_reader import JsonReader
from llm_postprocessor.io.json_writer import JsonWriter


class PostProcessor:
    """Main post-processor for LLM analysis."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize post-processor.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self.llm_client = self._init_llm_client()
        self.json_reader = JsonReader()
        self.json_writer = JsonWriter()

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
        from llm_postprocessor.schemas.output_schemas import (
            ProcessedResult,
            PHQSummary,
            LLMExtraction,
            FacialAnalysisSummary,
        )
        from llm_postprocessor.utils.helpers import (
            get_phq_severity,
            calculate_emotion_stats,
        )

        # Process PHQ data
        phq_summary = self._process_phq(session_data.phq_data)

        # Process LLM extraction
        llm_extraction = self._extract_llm_insights(session_data.llm_conversation)

        # Process facial analysis
        facial_analysis = self._process_facial_analysis(
            session_data.facial_analysis_frames
        )

        result = ProcessedResult(
            user_id=session_data.user.user_id,
            session_id=session_data.user.session_id,
            phq_summary=phq_summary,
            llm_extraction=llm_extraction,
            facial_analysis=facial_analysis,
            metadata=session_data.metadata,
        )

        return result

    def _process_phq(self, phq_data) -> dict:
        """Process PHQ data."""
        from llm_postprocessor.schemas.output_schemas import PHQSummary
        from llm_postprocessor.utils.helpers import get_phq_severity

        if not phq_data:
            return PHQSummary(
                total_score=0, max_possible_score=27, severity="minimal"
            )

        severity = get_phq_severity(phq_data.total_score)
        return PHQSummary(
            total_score=phq_data.total_score,
            max_possible_score=phq_data.max_possible_score,
            severity=severity,
        )

    def _extract_llm_insights(self, llm_conversation) -> dict:
        """Extract insights from LLM conversation."""
        from llm_postprocessor.schemas.output_schemas import LLMExtraction
        from llm_postprocessor.llm.prompt_builder import PromptBuilder
        import json

        if not llm_conversation or len(llm_conversation) == 0:
            return LLMExtraction(
                key_themes=[],
                overall_sentiment="neutral",
                insights="No LLM conversation available",
            )

        # Build prompt using PromptBuilder
        builder = PromptBuilder()
        messages = builder.build_analysis_messages(llm_conversation)

        # Get LLM client and invoke
        llm = self.llm_client.get_client()

        try:
            # Invoke LLM with the constructed messages
            response = llm.invoke(messages)

            # Parse JSON response
            result = json.loads(response.content)

            # Extract analysis data
            analysis = result.get("analysis", [])
            notes = result.get("notes", "")

            # Extract key themes from indicators
            key_themes = [
                item.get("indicator", "")
                for item in analysis
                if item.get("score", {}).get("phq", 0) >= 2
                or item.get("score", {}).get("operational", 0) >= 2
            ]

            return LLMExtraction(
                key_themes=key_themes,
                overall_sentiment="analyzed",
                risk_factors=[],
                insights=notes or "Analysis completed successfully",
            )

        except Exception as e:
            # Fallback on error
            return LLMExtraction(
                key_themes=["error"],
                overall_sentiment="error",
                insights=f"LLM extraction failed: {str(e)}",
            )

    def _process_facial_analysis(self, facial_frames) -> dict:
        """Process facial analysis frames."""
        from llm_postprocessor.schemas.output_schemas import FacialAnalysisSummary
        from llm_postprocessor.utils.helpers import calculate_emotion_stats

        if not facial_frames or len(facial_frames) == 0:
            return FacialAnalysisSummary(
                emotion_frequency={},
                emotion_intensity_mean={},
                dominant_emotion="unknown",
                total_frames=0,
            )

        # Convert Pydantic models to dicts for processing
        frames_dict = [
            frame.model_dump() if hasattr(frame, "model_dump") else frame
            for frame in facial_frames
        ]

        emotion_freq, emotion_intensity = calculate_emotion_stats(frames_dict)

        dominant_emotion = (
            max(emotion_freq, key=emotion_freq.get)
            if emotion_freq
            else "unknown"
        )

        return FacialAnalysisSummary(
            emotion_frequency=emotion_freq,
            emotion_intensity_mean=emotion_intensity,
            dominant_emotion=dominant_emotion,
            total_frames=len(facial_frames),
        )

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

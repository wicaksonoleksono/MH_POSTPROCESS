"""Main post-processor class."""

from pathlib import Path
from typing import Optional

from ..config import Settings, get_settings
from ..io.assessment_loader import AssessmentLoader
from ..schemas.input_schemas import SessionData
from ..schemas.output_schemas import AssessmentSummary, ProcessedResult


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

        phq_summary = AssessmentLoader.load_assessment_summary(
            session_folder / "phq_analysis.jsonl" if session_folder else None
        )
        llm_summary = AssessmentLoader.load_assessment_summary(
            session_folder / "llm_analysis.jsonl" if session_folder else None
        )

        phq_responses = AssessmentLoader.load_json(
            session_folder / "phq_responses.json" if session_folder else None
        )
        session_metadata = AssessmentLoader.load_json(
            session_folder / "metadata.json" if session_folder else None
        )

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


def _model_to_dict(model):
    """Return a serialisable representation compatible with Pydantic v1 & v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Unsupported model type: {type(model)!r}")

"""Output data schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AssessmentSummary(BaseModel):
    """Lightweight overview of an assessment JSONL file."""

    metadata: Optional[dict[str, Any]] = Field(
        None, description="Metadata entry extracted from the analysis file"
    )
    total_rows: int = Field(
        0, ge=0, description="Total number of rows contained in the analysis file"
    )
    data_rows: int = Field(
        0, ge=0, description="Number of data rows excluding metadata entries"
    )
    file_path: Optional[str] = Field(
        None, description="Relative path to the copied analysis file"
    )
    extra: Optional[dict[str, Any]] = Field(
        None, description="Additional summary details derived from related files"
    )


class ProcessedResult(BaseModel):
    """Output schema for processed results."""

    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    processed_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = None
    phq_summary: Optional[AssessmentSummary] = Field(
        None, description="Summary information for PHQ analysis"
    )
    llm_summary: Optional[AssessmentSummary] = Field(
        None, description="Summary information for LLM analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "session_456",
                "processed_at": "2024-01-01T00:00:00",
                "metadata": {
                    "folder_name": "user_123_session1",
                    "data_path": "data/user_123_session1/llm_conversation.json",
                    "formatted_conversation": "mahasiswa: halo\nsindi: hai!"
                },
                "phq_summary": {
                    "metadata": {"assessment_type": "PHQ", "total_images": 53},
                    "total_rows": 54,
                    "data_rows": 53,
                    "file_path": "user_123_session1/phq_analysis.jsonl",
                    "extra": {
                        "total_score": 6,
                        "max_possible_score": 27,
                        "analysis_stats": {"dominant_emotion": "Neutral"}
                    }
                },
                "llm_summary": None
            }
        }

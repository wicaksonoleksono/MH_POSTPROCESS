"""Input data schemas."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserMetadata(BaseModel):
    """User metadata schema."""

    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Session identifier")


class FacialAnalysisFrame(BaseModel):
    """Single facial analysis frame from JSONL."""

    filename: str
    timestamp: str
    facial_expression: str = Field(..., description="Detected emotion/expression")
    au_intensities: dict[str, float] = Field(
        default_factory=dict, description="Action unit intensity values"
    )
    analysis: Optional[dict[str, Any]] = None


class PHQData(BaseModel):
    """PHQ-9 response data."""

    total_score: int
    max_possible_score: int = 27
    responses: dict[str, Any]


class SessionData(BaseModel):
    """Input schema for session data."""

    user: UserMetadata
    phq_data: Optional[PHQData] = None
    llm_conversation: Optional[list[dict[str, str]]] = None
    facial_analysis_frames: Optional[list[FacialAnalysisFrame]] = None
    metadata: Optional[dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user": {"user_id": "user_123", "session_id": "session_456"},
                "phq_data": {"total_score": 8, "responses": {}},
                "llm_conversation": [],
                "facial_analysis_frames": [],
                "metadata": {},
            }
        }

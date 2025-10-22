"""Output data schemas."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LLMExtraction(BaseModel):
    """Extracted insights from LLM conversation."""

    key_themes: list[str] = Field(..., description="Key themes identified")
    overall_sentiment: str = Field(..., description="Overall sentiment")
    risk_factors: list[str] = Field(default_factory=list, description="Identified risk factors")
    insights: str = Field(..., description="Summary of insights from LLM analysis")


class ProcessedResult(BaseModel):
    """Output schema for processed results."""

    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    llm_extraction: LLMExtraction
    processed_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "session_456",
                "llm_extraction": {
                    "key_themes": ["work stress", "sleep issues"],
                    "overall_sentiment": "concerned",
                    "insights": "Patient shows signs of...",
                },
                "processed_at": "2024-01-01T00:00:00",
            }
        }

"""Output data schemas."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PHQSummary(BaseModel):
    """PHQ-9 summary."""

    total_score: int = Field(..., description="Total PHQ-9 score")
    max_possible_score: int = 27
    severity: str = Field(
        ..., description="Severity level: minimal, mild, moderate, moderately_severe, severe"
    )


class LLMExtraction(BaseModel):
    """Extracted insights from LLM conversation."""

    key_themes: list[str] = Field(..., description="Key themes identified")
    overall_sentiment: str = Field(..., description="Overall sentiment")
    risk_factors: list[str] = Field(default_factory=list, description="Identified risk factors")
    insights: str = Field(..., description="Summary of insights from LLM analysis")


class FacialAnalysisSummary(BaseModel):
    """Facial analysis statistics."""

    emotion_frequency: dict[str, int] = Field(
        ..., description="Count of each emotion detected"
    )
    emotion_intensity_mean: dict[str, float] = Field(
        ..., description="Mean intensity for each emotion"
    )
    dominant_emotion: str = Field(..., description="Most frequently detected emotion")
    total_frames: int = Field(..., description="Total frames analyzed")


class ProcessedResult(BaseModel):
    """Output schema for processed results."""

    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    phq_summary: PHQSummary
    llm_extraction: LLMExtraction
    facial_analysis: FacialAnalysisSummary
    processed_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "session_456",
                "phq_summary": {
                    "total_score": 12,
                    "severity": "moderate",
                },
                "llm_extraction": {
                    "key_themes": ["work stress", "sleep issues"],
                    "overall_sentiment": "concerned",
                    "insights": "Patient shows signs of...",
                },
                "facial_analysis": {
                    "emotion_frequency": {"neutral": 25, "sad": 5, "anxious": 10},
                    "emotion_intensity_mean": {
                        "neutral": 0.6,
                        "sad": 0.45,
                    },
                    "dominant_emotion": "neutral",
                    "total_frames": 40,
                },
                "processed_at": "2024-01-01T00:00:00",
            }
        }

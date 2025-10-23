"""Schemas for LLM analysis input and output."""

from typing import Optional
from pydantic import BaseModel, Field


class IndicatorScore(BaseModel):
    """Score for a single indicator."""

    phq: int = Field(..., ge=0, le=3, description="PHQ-9 scale score (0-3)")


class IndicatorAnalysis(BaseModel):
    """Analysis for a single PHQ indicator."""

    indicator: str = Field(..., description="Name of the indicator")
    score: IndicatorScore = Field(..., description="Scores for this indicator")
    evidence: str = Field(..., description="Evidence from conversation supporting the score")
    reasoning: Optional[str] = Field(None, description="Reasoning for the score")


class LLMAnalysisOutput(BaseModel):
    """Expected output from LLM analysis."""

    analysis: list[IndicatorAnalysis] = Field(
        ...,
        description="List of analyzed indicators with scores"
    )
    notes: str = Field(
        ...,
        description="Overall notes and observations from the conversation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": [
                    {
                        "indicator": "Anhedonia atau Kehilangan Minat atau Kesenangan",
                        "score": {"phq": 2},
                        "evidence": "User mentioned losing interest in hobbies",
                        "reasoning": "Clear indication of anhedonia based on conversation"
                    }
                ],
                "notes": "Patient shows moderate symptoms of depression with primary concerns around..."
            }
        }


class LLMAnalysisInput(BaseModel):
    """Input for LLM analysis."""

    chat_history: list[dict[str, str]] = Field(
        ...,
        description="Conversation history to analyze"
    )
    aspects: Optional[str] = Field(
        None,
        description="PHQ aspects to analyze (auto-loaded if not provided)"
    )
    phq_scale: Optional[str] = Field(
        None,
        description="PHQ scale definitions (auto-loaded if not provided)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chat_history": [
                    {"role": "Sindi", "content": "How are you feeling?"},
                    {"role": "User", "content": "I've been feeling down lately"}
                ]
            }
        }

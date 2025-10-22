"""Multi-client analysis schemas."""

from pydantic import BaseModel, Field

class MultiClientAnalysisResult(BaseModel):
    """Schema for multi-client analysis results."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    openai_response: str | None = Field(None, description="OpenAI model response")
    together_response: str | None = Field(None, description="TogetherAI model response")
    errors: dict[str, str] = Field(default_factory=dict, description="Errors by client")

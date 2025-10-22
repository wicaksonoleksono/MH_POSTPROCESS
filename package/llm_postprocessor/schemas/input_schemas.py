"""Input data schemas."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class UserMetadata(BaseModel):
    """User metadata schema."""

    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Session identifier")


class SessionData(BaseModel):
    """Input schema for session data."""

    user: UserMetadata
    llm_conversation: Optional[list[dict[str, str]]] = None
    metadata: Optional[dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user": {"user_id": "user_123", "session_id": "session_456"},
                "llm_conversation": [],
                "metadata": {},
            }
        }

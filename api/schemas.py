"""
api/schemas.py
Pydantic schemas for API request/response handling.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


class ChatRequest(BaseModel):
    """
    API request for /chat endpoint.

    User sends their message and session ID.
    Empty message retrieves current state's response.
    """
    session_id: str = Field(..., description="Unique session identifier (UUID string)")
    message: str = Field(default="", description="User's message (empty to get current state response)", max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "f598f3ab-958b-4f82-9ee6-7a4f4c329ad3",
                "message": "I'm ready to begin"
            }
        }


class StateInfo(BaseModel):
    """Current state information."""
    state_id: UUID
    state_code: str
    state_name: str


class LibraryContent(BaseModel):
    """A piece of content from the library."""
    kind: str
    title: str
    body: str
    metadata: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """
    Successful API response from /chat endpoint.

    Contains the current state, LLM-generated response, and session info.
    """
    success: bool = Field(default=True, description="Whether the request succeeded")
    session_id: UUID = Field(..., description="Session identifier")
    current_state: StateInfo = Field(..., description="Current state info")
    emotion: Optional[str] = Field(default=None, description="Detected emotion from classifier")
    ### RItesh Oraon ###
    process_text: str = Field(..., description="Process being followed")
    ####################
    content: list[LibraryContent] = Field(..., description="Library content for context")
    llm_response: str = Field(..., description="Personalized response from Claude LLM")
    message_count: int = Field(..., description="Total messages in session")
    started_at: datetime = Field(..., description="When session started")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "f598f3ab-958b-4f82-9ee6-7a4f4c329ad3",
                "current_state": {
                    "state_id": "4b25bfed-6f04-4d20-8f0f-7497b623e19d",
                    "state_code": "calm_breath_observation",
                    "state_name": "Observe Your Breath"
                },
                "content": [
                    {
                        "kind": "script",
                        "title": "Observe Your Breath Script",
                        "body": "Take a comfortable position...",
                        "metadata": {"intent": "calm"}
                    }
                ],
                "message_count": 1,
                "started_at": "2026-05-12T20:37:39.342968+00:00"
            }
        }


class ErrorResponse(BaseModel):
    """
    API error response.

    Returned when something goes wrong.
    """
    success: bool = Field(default=False, description="Request failed")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Session not found",
                "detail": "Session ID f598f3ab-958b-4f82-9ee6-7a4f4c329ad3 does not exist"
            }
        }

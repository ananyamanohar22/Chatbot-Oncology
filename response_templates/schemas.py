"""
response_templates/schemas.py
Pydantic schemas for response template API.
"""

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ResponseTemplateCreate(BaseModel):
    """Request to create a new response template."""
    query_pattern: str = Field(..., description="Patient query pattern (e.g., 'not ready')")
    intent_category: str = Field(..., description="Intent category (e.g., 'hesitation', 'fear')")
    responses: list[str] = Field(..., description="List of response options")
    keywords: list[str] = Field(default=[], description="Keywords for pattern matching")
    description: str = Field(default="", description="Description for admin reference")
    relevance_score: float = Field(default=0.8, description="Base relevance score (0.0-1.0)")


class ResponseTemplateUpdate(BaseModel):
    """Request to update a response template."""
    query_pattern: str | None = None
    intent_category: str | None = None
    responses: list[str] | None = None
    keywords: list[str] | None = None
    description: str | None = None
    relevance_score: float | None = None
    is_active: bool | None = None


class ResponseTemplateResponse(BaseModel):
    """Response with response template data."""
    id: UUID
    query_pattern: str
    intent_category: str
    description: str | None
    responses: list[str]
    keywords: list[str]
    relevance_score: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RAGRetrievalResult(BaseModel):
    """Result from RAG retrieval."""
    template: ResponseTemplateResponse | None
    matched_query_pattern: str | None
    retrieval_method: str | None  # "pattern_match" or "semantic_search"
    confidence_score: float

"""Response Template model for RAG system."""

from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Float, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base

logger = logging.getLogger(__name__)


class ResponseTemplate(Base):
    """Response template for patient queries."""

    __tablename__ = "response_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    query_pattern: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, unique=True,
    )

    intent_category: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    responses: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list,
    )

    keywords: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list,
    )

    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    relevance_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.8,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False, index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_intent_category_active", "intent_category", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ResponseTemplate pattern={self.query_pattern!r} category={self.intent_category!r}>"

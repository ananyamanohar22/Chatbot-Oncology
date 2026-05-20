"""
rag/retriever.py
RAG retriever - fetches relevant context from database and library.

Retrieves:
- Current state content (scripts, prompts)
- Patient context (session history, emotional state)
- Therapy guidelines for current state
"""

from __future__ import annotations

import uuid
import logging
from typing import List, Dict, Any

from db import get_session
from library.models import LibraryItem
from sessions.models import Session
from states.models import State

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves context for RAG."""

    @staticmethod
    def retrieve_context(
            session_id: uuid.UUID,
            current_state_id: uuid.UUID,
            message: str,
            emotion: str
    ) -> Dict[str, Any]:
        """
        Retrieve all relevant context for LLM generation.

        Args:
            session_id: Current session ID
            current_state_id: Current state UUID
            message: User's latest message
            emotion: Classified emotion (calm, anxious, overwhelmed)

        Returns:
            Dict with retrieved context including:
            - state_info: Current state details
            - library_context: Relevant scripts/prompts from library
            - session_history: Recent message history
            - emotional_context: Patient's emotional state info
            - guidelines: Therapeutic guidelines for current state
        """
        with get_session() as db:
            # Retrieve current state info
            state = db.query(State).filter(State.id == current_state_id).first()
            state_info = {
                "state_code": state.code if state else None,
                "state_name": state.name if state else None,
                "state_description": state.description if state else None,
            }

            # Retrieve library items for context (all items for this intent)
            library_items = db.query(LibraryItem).all()
            library_context = [
                {
                    "kind": item.kind,
                    "title": item.title,
                    "body": item.body,
                    "metadata": item.item_metadata,
                }
                for item in library_items
            ]

            # Retrieve session history
            session = db.query(Session).filter(Session.id == session_id).first()
            session_history = []
            if session:
                messages = session.session_metadata.get("messages", [])
                # Get last 5 messages for context
                session_history = messages[-5:] if messages else []

            # Build emotional context
            emotional_context = {
                "emotion": emotion,
                "recommendations": RAGRetriever._get_emotional_guidelines(emotion),
            }

            context = {
                "state_info": state_info,
                "library_context": library_context,
                "session_history": session_history,
                "emotional_context": emotional_context,
                "user_message": message,
            }

            logger.info(f"[RAG] Retrieved context for session {session_id}")
            return context

    @staticmethod
    def _get_emotional_guidelines(emotion_state: str) -> List[str]:
        """Get therapeutic guidelines based on emotional state."""
        guidelines = {
            "calm": [
                "Maintain peaceful tone",
                "Encourage continued relaxation",
                "Deepen the experience",
                "Use gentle pacing",
                "Build on current calm state",
            ],
            "anxious": [
                "Acknowledge anxiety without judgment",
                "Offer grounding techniques",
                "Use reassuring language",
                "Provide control/choice",
                "Slow down the pace",
            ],
            "overwhelmed": [
                "Validate the feeling",
                "Break into smaller steps",
                "Offer immediate relief techniques",
                "Reduce complexity",
                "Emphasize safety and support",
            ],
        }
        return guidelines.get(emotion_state, guidelines["calm"])
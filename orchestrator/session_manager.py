"""
orchestrator/session_manager.py
Session Manager - coordinates between user input, classifier, orchestrator, and LLM.

Responsibilities:
1. Load and manage sessions from database
2. Apply classifier to determine emotion/intent
3. Coordinate with OrchestratorEngine
4. Retrieve context with RAG
5. Generate personalized responses with LLM
6. Assemble response for user
"""

from __future__ import annotations

import logging
from uuid import UUID
from datetime import datetime, timezone

from db import get_session
from sessions.models import Session
from library.models import LibraryItem

from .engine import OrchestratorEngine
from .schemas import OrchestratorRequest, ClassifierOutput
from .session_manager_schemas import (
    SessionManagerRequest,
    SessionManagerResponse,
    StateInfo,
    LibraryItemResponse,
)
from rag.retriever import RAGRetriever
from rag.llm_generator import get_llm_generator

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Coordinates between user, classifier, and orchestrator.

    Flow:
    1. User sends message + session_id
    2. Load session from database
    3. (Optional) Apply classifier to message
    4. Pass to Orchestrator with classifier output
    5. Assemble response from orchestrator data
    6. Return to user
    """

    def __init__(self, classifier_fn=None):
        """
        Initialize Session Manager.

        Args:
            classifier_fn: Optional callable that takes a message string
                          and returns ClassifierOutput (intent, emotion, etc.)
        """
        self.orchestrator = OrchestratorEngine()
        self.classifier_fn = classifier_fn

    def process(self, request: SessionManagerRequest) -> SessionManagerResponse:
        """
        Process a user message and return orchestrator response.

        Steps:
        1. Load session from database
        2. Apply classifier if available
        3. Call orchestrator
        4. Assemble response
        5. Return to user

        Args:
            request: SessionManagerRequest with session_id and message

        Returns:
            SessionManagerResponse ready for user

        Raises:
            ValueError: If session not found
        """
        logger.info(f"[SessionManager] Processing message for session {request.session_id}")

        # Step 1: Load session from database
        db_session = self._load_session(request.session_id)
        if not db_session:
            raise ValueError(f"Session {request.session_id} not found")

        # Step 2: Apply classifier (optional)
        classifier_output = None
        if self.classifier_fn:
            logger.info(f"[SessionManager] Running classifier on message")
            classifier_output = self.classifier_fn(request.message)
            logger.info(f"[SessionManager] Classifier output: {classifier_output}")

        # Step 3: Call orchestrator
        logger.info(f"[SessionManager] Calling orchestrator")
        orchestrator_request = OrchestratorRequest(
            session_id=request.session_id,
            message=request.message,
            classifier_output=classifier_output
        )

        orchestrator_response = self.orchestrator.process(orchestrator_request)
        logger.info(f"[SessionManager] Orchestrator returned response")

        # Step 4: Generate personalized response with RAG + LLM
        emotion = classifier_output.emotion if classifier_output else "calm"
        llm_response = self._generate_llm_response(
            session_id=request.session_id,
            current_state_id=orchestrator_response.next_state_id or orchestrator_response.state.get("id"),
            user_message=request.message,
            emotion=emotion
        )
        logger.info(f"[SessionManager] LLM response generated")

        # Step 5: Assemble response
        response = self._assemble_response(orchestrator_response, llm_response)
        logger.info(f"[SessionManager] Response assembled and ready")

        return response

    def _load_session(self, session_id: UUID) -> Session | None:
        """
        Load session from database.

        Args:
            session_id: UUID of session to load

        Returns:
            Session object or None if not found
        """
        with get_session() as db:
            session = db.query(Session).filter(Session.id == session_id).first()
            return session

    def _generate_llm_response(
        self,
        session_id: UUID,
        current_state_id: UUID,
        user_message: str,
        emotion: str
    ) -> str:
        """
        Generate personalized response using RAG + LLM.

        Args:
            session_id: Current session ID
            current_state_id: Current state UUID
            user_message: User's latest message
            emotion: Classified emotional state

        Returns:
            Generated response text from Claude
        """
        try:
            logger.info(f"[SessionManager] Generating LLM response")

            # Retrieve context
            rag_context = RAGRetriever.retrieve_context(
                session_id=session_id,
                current_state_id=current_state_id,
                message=user_message,
                emotion=emotion
            )

            # Generate response with LLM
            llm_generator = get_llm_generator()
            response = llm_generator.generate_response(rag_context)

            return response

        except Exception as e:
            logger.error(f"[SessionManager] Error generating LLM response: {str(e)}")
            # Fallback to generic response
            return "I'm here to support you. Please continue at your own pace."

    def _assemble_response(self, orchestrator_response, llm_response: str = None) -> SessionManagerResponse:
        """
        Assemble SessionManagerResponse from orchestrator output.

        The orchestrator returns an OrchestratorResponse object with:
        - session: session data
        - process: process definition
        - state: current state
        - content: list of library items
        - next_state_id: next state (if available)
        - transition_taken: which transition was taken (if any)

        We transform this into a user-friendly SessionManagerResponse.

        Args:
            orchestrator_response: OrchestratorResponse returned by OrchestratorEngine.process()

        Returns:
            SessionManagerResponse
        """
        # Access attributes from OrchestratorResponse object
        session_data = orchestrator_response.session
        state_data = orchestrator_response.state
        content_data = orchestrator_response.content
        transition_taken = orchestrator_response.transition_taken

        ### Ritesh Oraon ###
        process_data = orchestrator_response.process   # Find if this can be implemented
        #####################

        # Helper to safely get value from dict or object
        def get_attr(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            else:
                return getattr(obj, key, None)

        # Build StateInfo from orchestrator state
        current_state = StateInfo(
            state_id=get_attr(state_data, "id"),
            state_code=get_attr(state_data, "code"),
            state_name=get_attr(state_data, "name"),
        )

        # Transform library items to LibraryItemResponse
        content = []
        for item in content_data:
            # Items are dicts
            lib_item = LibraryItemResponse(
                kind=item.get("kind"),
                title=item.get("title"),
                body=item.get("body"),
                metadata=item.get("item_metadata", {}),
            )
            content.append(lib_item)

        # Build response
        # Session data is a dict
        messages = get_attr(session_data, "session_metadata") or {}
        if isinstance(messages, dict):
            message_count = len(messages.get("messages", []))
        else:
            message_count = 0

        response = SessionManagerResponse(
            session_id=get_attr(session_data, "id"),
            current_state=current_state,
            content=content,
            process_text = get_attr(process_data, "name"),
            llm_response=llm_response,
            message_count=message_count,
            started_at=get_attr(session_data, "started_at"),
            transition_taken=transition_taken,
        )

        ### Ritesh Oraon ###
        #process_text = process_data.name,
        ####################

        return response


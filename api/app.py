"""
api/app.py
FastAPI application with chatbot endpoints.

Main entry point for the relaxbot API.
Exposes /chat endpoint for user interactions.
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from uuid import UUID
from pydantic import BaseModel, Field

from orchestrator.session_manager import SessionManager
from orchestrator.session_manager_schemas import SessionManagerRequest
from services.session_service import SessionService
from classifier.simple_classifier import classifier

from api.schemas import ChatRequest, ChatResponse, ErrorResponse

from library.models import LibraryItem
from states.models import State
from processes.models import Process
from db import SessionLocal
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RelaxBot API",
    description="Chatbot for oncology patients - guided relaxation and coping strategies",
    version="0.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Session Manager with classifier
session_manager = SessionManager(classifier_fn=classifier.classify)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: {"status": "healthy"}
    """
    return {"status": "healthy"}


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    patient_id: str = Field(..., description="Patient identifier")
    process_code: str = Field(default="guided_imagery_v1", description="Process code (e.g., guided_imagery_v1)")


@app.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """
    Auto-create a new session with a process.

    The session is created with the process's initial state.
    All subsequent messages go to /chat with this session_id.

    Args:
        request: CreateSessionRequest with patient_id and process_code

    Returns:
        dict with session_id and session info

    Raises:
        HTTPException: 400 if process not found
    """
    try:
        logger.info(f"[API] Creating session for patient {request.patient_id}")

        session = SessionService.create_session(
            patient_id=request.patient_id,
            process_code=request.process_code
        )

        logger.info(f"[API] Session created: {session.id}")

        return {
            "success": True,
            "session_id": str(session.id),
            "patient_id": session.patient_id,
            "message": f"Session created. Use this session_id for /chat endpoint."
        }

    except ValueError as e:
        logger.error(f"[API] Error creating session: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Processes user message, coordinates with Session Manager,
    and returns orchestrated response.

    Args:
        request: ChatRequest with session_id and message

    Returns:
        ChatResponse with current state and content

    Raises:
        HTTPException: 404 if session not found, 500 if processing error
    """
    try:
        logger.info(f"[API] /chat request - session: {request.session_id}, message: {request.message[:50] if request.message else '(empty)'}...")

        # Call Session Manager
        session_manager_request = SessionManagerRequest(
            session_id=UUID(request.session_id),
            message=request.message
        )

        session_manager_response = session_manager.process(session_manager_request)
        logger.info(f"[API] Session Manager processed request successfully")

        # Get emotion from classifier (classify the user message if provided)
        emotion = None
        if request.message:
            classifier_output = classifier.classify(request.message)
            emotion = classifier_output.emotion

        # Transform SessionManagerResponse to ChatResponse
        response = ChatResponse(
            success=True,
            session_id=session_manager_response.session_id,
            emotion=emotion,
            current_state={
                "state_id": session_manager_response.current_state.state_id,
                "state_code": session_manager_response.current_state.state_code,
                "state_name": session_manager_response.current_state.state_name,
            },
            content=[
                {
                    "kind": item.kind,
                    "title": item.title,
                    "body": item.body,
                    "metadata": item.metadata,
                }
                for item in session_manager_response.content
            ],
            llm_response=session_manager_response.llm_response or "I'm here to support you.",
            message_count=session_manager_response.message_count,
            started_at=session_manager_response.started_at,
        )

        logger.info(f"[API] Returning response for session {request.session_id}")
        return response

    except ValueError as e:
        # Session not found
        logger.error(f"[API] ValueError: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected error
        logger.error(f"[API] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.get("/docs")
async def docs():
    """
    API documentation endpoint.

    Redirects to Swagger UI.
    """
    return {"message": "API docs available at /docs (Swagger UI)"}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Fetch a session by ID with process and state details.
    """
    try:
        from uuid import UUID
        from sessions.models import Session
        from processes.models import Process
        from states.models import State

        db = SessionLocal()
        session = db.query(Session).filter(Session.id == UUID(session_id)).first()

        if not session:
            db.close()
            raise HTTPException(status_code=404, detail="Session not found")

        # Get process details
        process = db.query(Process).filter(Process.id == session.process_id).first()
        process_code = process.code if process else None
        process_name = process.name if process else None

        # Get current state details
        state = db.query(State).filter(State.id == session.current_state_id).first() if session.current_state_id else None
        state_code = state.code if state else None
        state_name = state.name if state else None

        db.close()

        return {
            "session_id": str(session.id),
            "patient_id": session.patient_id,
            "process_id": str(session.process_id),
            "process_code": process_code,
            "process_name": process_name,
            "current_state_id": str(session.current_state_id) if session.current_state_id else None,
            "current_state_code": state_code,
            "current_state_name": state_name,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None
        }
    except Exception as e:
        logger.error(f"[API] Error fetching session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/library-items/{item_id}")
async def get_library_item(item_id: str):
    """
    Fetch a single library item by ID.

    used to get technique names and details from database.

    Args:
    item_id: Item IDitem_id: UUID of library item

    Returns:
        Library item with title, kind, body, metadata

    """

    try:
        db = SessionLocal()
        item = db.query(LibraryItem).filter(LibraryItem.id == item_id).first()
        db.close()

        if not item:
            raise HTTPException(status_code=404, detail="Library Item not found")

        return {
            "id": str(item.id),
            "kind": item.kind,
            "title": item.title,
            "body": item.body,
            "metadata": item.item_metadata,
        }
    except Exception as e:
        logger.error(f"[API] Error fetching library item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/states/{state_code}")
async def get_state(state_code: str):
    """
    Fetch a state by code (e.g., 'introduction', 'breathing', 'anxious').

    Used to get emotion/state names from database.

    Args:
        state_code: State code (e.g., 'anxious', 'calm')

    Returns:
        State with code, name, description
    """
    try:
        db = SessionLocal()
        state = db.query(State).filter(State.code == state_code).first()
        db.close()

        if not state:
            raise HTTPException(status_code=404, detail="State not found")

        return {
            "id": str(state.id),
            "code": state.code,
            "name": state.name,
            "description": state.description
        }
    except Exception as e:
        logger.error(f"[API] Error fetching state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processes/{process_code}")
async def get_process(process_code: str):
    """
    Fetch a process by code (e.g., 'guided_imagery_v1').

    Used to get process name and definition from database.

    Args:
        process_code: Process code (e.g., 'guided_imagery_v1')

    Returns:
        Process with code, name, description, definition
    """
    try:
        db = SessionLocal()
        process = db.query(Process).filter(Process.code == process_code).first()
        db.close()

        if not process:
            raise HTTPException(status_code=404, detail="Process not found")

        return {
            "id": str(process.id),
            "code": process.code,
            "name": process.name,
            "description": process.description,
            "definition": process.definition,
            "is_active": process.is_active
        }
    except Exception as e:
        logger.error(f"[API] Error fetching process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

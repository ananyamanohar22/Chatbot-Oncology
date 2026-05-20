"""
api/response_templates_routes.py
API routes for managing response templates.

Endpoints:
- POST /response-templates — Create a new template
- GET /response-templates — List all templates
- GET /response-templates/{template_id} — Get a specific template
- PUT /response-templates/{template_id} — Update a template
- DELETE /response-templates/{template_id} — Delete a template
- POST /response-templates/retrieve — Retrieve best matching response for a query
"""

import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException
from db import SessionLocal
from response_templates.models import ResponseTemplate
from response_templates.schemas import (
    ResponseTemplateCreate,
    ResponseTemplateUpdate,
    ResponseTemplateResponse,
    RAGRetrievalResult,
)
from response_templates.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/response-templates", tags=["response-templates"])


@router.post("", response_model=ResponseTemplateResponse)
async def create_response_template(request: ResponseTemplateCreate):
    """
    Create a new response template.

    Args:
        request: ResponseTemplateCreate with template details

    Returns:
        Created ResponseTemplate
    """
    try:
        db = SessionLocal()

        # Check if pattern already exists
        existing = db.query(ResponseTemplate).filter(
            ResponseTemplate.query_pattern == request.query_pattern
        ).first()

        if existing:
            db.close()
            raise HTTPException(
                status_code=400,
                detail=f"Template with pattern '{request.query_pattern}' already exists"
            )

        template = ResponseTemplate(
            query_pattern=request.query_pattern,
            intent_category=request.intent_category,
            description=request.description,
            responses=request.responses,
            keywords=request.keywords,
            relevance_score=request.relevance_score,
        )

        db.add(template)
        db.commit()
        db.refresh(template)
        db.close()

        logger.info(f"[API] Created response template: {request.query_pattern}")

        return ResponseTemplateResponse.from_orm(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error creating response template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ResponseTemplateResponse])
async def list_response_templates(active_only: bool = True):
    """
    List all response templates.

    Args:
        active_only: Filter to only active templates (default: True)

    Returns:
        List of ResponseTemplates
    """
    try:
        db = SessionLocal()
        query = db.query(ResponseTemplate)

        if active_only:
            query = query.filter(ResponseTemplate.is_active == True)

        templates = query.order_by(ResponseTemplate.intent_category).all()
        db.close()

        return [ResponseTemplateResponse.from_orm(t) for t in templates]

    except Exception as e:
        logger.error(f"[API] Error listing response templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=ResponseTemplateResponse)
async def get_response_template(template_id: str):
    """
    Get a specific response template by ID.

    Args:
        template_id: UUID of the template

    Returns:
        ResponseTemplate
    """
    try:
        db = SessionLocal()
        template = db.query(ResponseTemplate).filter(
            ResponseTemplate.id == UUID(template_id)
        ).first()
        db.close()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return ResponseTemplateResponse.from_orm(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error fetching template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=ResponseTemplateResponse)
async def update_response_template(template_id: str, request: ResponseTemplateUpdate):
    """
    Update a response template.

    Args:
        template_id: UUID of the template
        request: ResponseTemplateUpdate with fields to update

    Returns:
        Updated ResponseTemplate
    """
    try:
        db = SessionLocal()
        template = db.query(ResponseTemplate).filter(
            ResponseTemplate.id == UUID(template_id)
        ).first()

        if not template:
            db.close()
            raise HTTPException(status_code=404, detail="Template not found")

        # Update only provided fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)
        db.close()

        logger.info(f"[API] Updated response template: {template_id}")

        return ResponseTemplateResponse.from_orm(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error updating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_response_template(template_id: str):
    """
    Delete a response template (soft delete via is_active flag).

    Args:
        template_id: UUID of the template

    Returns:
        Success message
    """
    try:
        db = SessionLocal()
        template = db.query(ResponseTemplate).filter(
            ResponseTemplate.id == UUID(template_id)
        ).first()

        if not template:
            db.close()
            raise HTTPException(status_code=404, detail="Template not found")

        # Soft delete
        template.is_active = False
        db.commit()
        db.close()

        logger.info(f"[API] Deleted response template: {template_id}")

        return {"success": True, "message": "Template deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error deleting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve", response_model=RAGRetrievalResult)
async def retrieve_response(
    query: str,
    intent_category: str | None = None
):
    """
    Retrieve best matching response template for a patient query (RAG retrieval).

    Uses hybrid approach: pattern matching + semantic search.

    Args:
        query: Patient query (e.g., "I'm not ready")
        intent_category: Optional intent category filter

    Returns:
        RAGRetrievalResult with matched template and confidence score
    """
    try:
        retriever = RAGRetriever()
        template = retriever.retrieve(query, intent_category)

        if not template:
            return RAGRetrievalResult(
                template=None,
                matched_query_pattern=None,
                retrieval_method=None,
                confidence_score=0.0,
            )

        return RAGRetrievalResult(
            template=ResponseTemplateResponse.from_orm(template),
            matched_query_pattern=template.query_pattern,
            retrieval_method="pattern_match",  # TODO: Track which method was used
            confidence_score=template.relevance_score,
        )

    except Exception as e:
        logger.error(f"[API] Error retrieving response template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

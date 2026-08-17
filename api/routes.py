"""
API Routes: Health, Grounded Question Answering (/ask), and Metadata.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from api.models import (
    AskRequest,
    AskResponse,
    CitationResponse,
    EvidenceResponse,
    HealthResponse,
    MetadataResponse,
    ErrorResponse,
)
from api.dependencies import get_rag_service
from api.service import RAGService
from generation.models import GenerationResult

logger = logging.getLogger("rag_api.routes")

router = APIRouter()


def _map_generation_result_to_response(result: GenerationResult) -> AskResponse:
    """Helper to convert internal GenerationResult to public AskResponse."""
    # Map evidence items
    evidence_responses: List[EvidenceResponse] = [
        EvidenceResponse(
            evidence_id=e.evidence_id,
            chunk_id=e.chunk_id,
            specification=e.specification,
            version=e.version,
            clause_number=e.clause_number,
            clause_title=e.clause_title,
            table_id=e.table_id,
            table_caption=e.table_caption,
        )
        for e in result.evidence_items
    ]

    # Map evidence lookup for version info
    evidence_map = {e.evidence_id: e for e in result.evidence_items}

    if result.status == "abstain":
        return AskResponse(
            status="abstain",
            answer=None,
            citations=[],
            evidence=evidence_responses,
            reason=result.abstention_reason or "The requested information could not be supported by the provided 3GPP evidence.",
            latency_breakdown=result.latency_breakdown or None,
        )

    # Map citations
    citation_responses: List[CitationResponse] = []
    for c in result.citations:
        ev_item = evidence_map.get(c.evidence_id)
        ver = ev_item.version if ev_item else None
        formatted = c.formatted_citation() if hasattr(c, "formatted_citation") else f"[{c.specification}, Clause {c.clause_number}]"
        citation_responses.append(
            CitationResponse(
                specification=c.specification,
                version=ver,
                clause_number=c.clause_number,
                clause_title=c.clause_title,
                table_id=c.table_id,
                table_caption=c.table_caption,
                formatted_citation=formatted,
            )
        )

    return AskResponse(
        status="answered",
        answer=result.answer,
        citations=citation_responses,
        evidence=evidence_responses,
        reason=None,
        latency_breakdown=result.latency_breakdown or None,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns lightweight readiness and component availability status without running heavy inference.",
    responses={
        200: {"description": "Service is healthy and ready"},
        503: {"description": "Service is degraded or indices are unavailable", "model": HealthResponse},
    },
)
def get_health(service: RAGService = Depends(get_rag_service)):
    """Health check endpoint."""
    try:
        health_info = service.get_health()
        is_healthy = health_info.get("vector_store_ready", False) or health_info.get("bm25_ready", False)
        
        status_str = "ok" if is_healthy else "degraded"
        response_data = HealthResponse(
            status=status_str,
            service="mavenir-3gpp-rag",
            version="1.0.0",
            details=health_info,
        )
        if not is_healthy and not health_info.get("initialized", False):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response_data.model_dump(),
            )
        return response_data
    except Exception as e:
        logger.error(f"Health check failed with error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(
                status="unhealthy",
                service="mavenir-3gpp-rag",
                version="1.0.0",
                details={"error": "Service health check encountered an error."},
            ).model_dump(),
        )


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask 3GPP Technical Question",
    description="Processes a user question through hybrid retrieval, evidence gating, LLM generation, citation validation, and claim verification.",
    responses={
        200: {"description": "Successful question processing (answered or safe abstention)", "model": AskResponse},
        422: {"description": "Validation error for empty or invalid query", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
        503: {"description": "RAG pipeline service unavailable", "model": ErrorResponse},
    },
)
def ask_question(
    request: AskRequest,
    service: RAGService = Depends(get_rag_service),
):
    """Processes grounded question answering query."""
    try:
        result = service.ask(question=request.question, top_k=request.top_k)
        return _map_generation_result_to_response(result)
    except ValueError as ve:
        logger.warning(f"Request validation issue in RAG service: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except ConnectionError as ce:
        logger.error(f"External service connection failed: {ce}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The underlying retrieval or LLM inference service is currently unreachable.",
        )
    except Exception as e:
        logger.error(f"Unexpected error in /ask: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the 3GPP RAG query.",
        )


@router.get(
    "/metadata",
    response_model=MetadataResponse,
    summary="Corpus and Model Metadata",
    description="Returns metadata about loaded 3GPP specifications, chunk counts, and model configurations.",
)
def get_metadata(service: RAGService = Depends(get_rag_service)):
    """Metadata endpoint."""
    try:
        meta = service.get_metadata()
        return MetadataResponse(**meta)
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service metadata.",
        )

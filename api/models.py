"""
Pydantic Request and Response Models for 3GPP RAG API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Request payload for /ask endpoint."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question regarding 3GPP 5G specifications",
        examples=["What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?"]
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of evidence chunks to retrieve and consider",
        examples=[5]
    )

    @field_validator("question", mode="before")
    @classmethod
    def validate_and_strip_question(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("question must be a string")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("question cannot be empty or whitespace-only")
        return cleaned


class CitationResponse(BaseModel):
    """Authoritative citation referencing specific 3GPP specification and clause."""
    specification: str = Field(description="3GPP specification identifier, e.g. 'TS 23.501'")
    version: Optional[str] = Field(default=None, description="Specification release/version if known")
    clause_number: str = Field(description="Exact clause number, e.g. '6.2.1'")
    clause_title: str = Field(description="Title of the cited clause, e.g. 'AMF'")
    table_id: Optional[str] = Field(default=None, description="Table identifier if citation references a table")
    table_caption: Optional[str] = Field(default=None, description="Table caption if citation references a table")
    formatted_citation: Optional[str] = Field(default=None, description="Human-readable citation string")


class EvidenceResponse(BaseModel):
    """Structured evidence item metadata used for grounding."""
    evidence_id: str = Field(description="Evidence identifier, e.g. 'E1'")
    chunk_id: str = Field(description="Unique internal chunk identifier")
    specification: str = Field(description="3GPP specification identifier")
    version: str = Field(description="Specification version")
    clause_number: str = Field(description="Clause number")
    clause_title: str = Field(description="Clause title")
    table_id: Optional[str] = Field(default=None, description="Table ID if evidence is a table")
    table_caption: Optional[str] = Field(default=None, description="Table caption if evidence is a table")


class AskResponse(BaseModel):
    """Response payload for /ask endpoint."""
    status: str = Field(
        description="Outcome of RAG query: 'answered' or 'abstain'",
        examples=["answered"]
    )
    answer: Optional[str] = Field(
        default=None,
        description="Synthesized grounded answer adhering to 3GPP specifications",
        examples=["The AMF is responsible for registration management, connection management, reachability management, and mobility management."]
    )
    citations: List[CitationResponse] = Field(
        default_factory=list,
        description="Authoritative citations backing each claim in the answer"
    )
    evidence: List[EvidenceResponse] = Field(
        default_factory=list,
        description="Retrieved evidence items presented to the generation pipeline"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Explanation when the system safely abstains from answering"
    )
    latency_breakdown: Optional[Dict[str, float]] = Field(
        default=None,
        description="Latency breakdown in milliseconds across pipeline stages"
    )


class HealthResponse(BaseModel):
    """Response payload for /health endpoint."""
    status: str = Field(description="'ok' if healthy, 'degraded' or 'unhealthy' if dependencies fail", examples=["ok"])
    service: str = Field(default="3gpp-grounded-rag", description="Service identifier")
    version: str = Field(default="1.0.0", description="API version")
    details: Dict[str, Any] = Field(default_factory=dict, description="Component readiness and availability status")


class MetadataResponse(BaseModel):
    """Response payload for /metadata endpoint."""
    service: str = Field(default="3gpp-grounded-rag")
    specifications: List[str] = Field(description="List of 3GPP specifications covered in the index")
    total_chunks: int = Field(description="Total number of indexed chunks across specifications")
    embedding_model: str = Field(description="Configured embedding model")
    generation_model: str = Field(description="Configured generation model")
    vector_store_collection: str = Field(description="ChromaDB collection name")


class ErrorResponse(BaseModel):
    """Standard sanitized error response."""
    detail: str = Field(description="Human-readable error description without internal traces")
    error_code: Optional[str] = Field(default=None, description="Error classification code")

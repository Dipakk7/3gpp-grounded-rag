"""
FastAPI Dependencies and Application State.
"""

from typing import Optional
from api.service import RAGService

# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Dependency provider for RAGService."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def set_rag_service(service: RAGService) -> None:
    """Explicitly set or mock the RAGService instance."""
    global _rag_service
    _rag_service = service

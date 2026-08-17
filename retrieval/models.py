"""
Data models for the Retrieval and Evaluation subsystem.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RetrievedChunk:
    """A retrieved chunk enriched with retrieval scoring and rank."""
    chunk_id: str
    specification: str
    document_title: str
    version: str
    release: str
    source_filename: str
    clause_number: str
    clause_title: str
    breadcrumb: List[Dict[str, str]]
    source_type: str
    document_order: int
    text: str
    content_hash: str
    score: float
    rank: int = 1
    table_id: Optional[str] = None
    table_caption: Optional[str] = None
    retrieval_method: str = "semantic"  # semantic, bm25, hybrid

    def to_dict(self) -> Dict[str, Any]:
        """Convert retrieved chunk to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "specification": self.specification,
            "document_title": self.document_title,
            "version": self.version,
            "release": self.release,
            "source_filename": self.source_filename,
            "clause_number": self.clause_number,
            "clause_title": self.clause_title,
            "breadcrumb": self.breadcrumb,
            "source_type": self.source_type,
            "document_order": self.document_order,
            "text": self.text,
            "content_hash": self.content_hash,
            "score": round(self.score, 6),
            "rank": self.rank,
            "table_id": self.table_id,
            "table_caption": self.table_caption,
            "retrieval_method": self.retrieval_method,
        }


@dataclass
class ExpectedTarget:
    """Target expectation for ground-truth benchmark evaluation."""
    specification: str
    clause_number: str
    table_id: Optional[str] = None


@dataclass
class BenchmarkQueryItem:
    """A benchmark query entry."""
    id: str
    category: str
    question: str
    expected: List[ExpectedTarget]
    notes: Optional[str] = None


@dataclass
class EvaluationMetrics:
    """Retrieval benchmark metrics summary."""
    total_queries: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    hit_at_10: float
    mrr: float
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "hit@1": round(self.hit_at_1, 4),
            "hit@3": round(self.hit_at_3, 4),
            "hit@5": round(self.hit_at_5, 4),
            "hit@10": round(self.hit_at_10, 4),
            "mrr": round(self.mrr, 4),
            "detailed_results": self.detailed_results,
        }

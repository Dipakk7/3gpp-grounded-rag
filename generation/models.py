"""
Data Models for Grounded Generation, Citation Validation, and Claim Verification.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class EvidenceItem:
    """Structured evidence item presented to the generator."""
    evidence_id: str  # e.g. 'E1', 'E2'
    chunk_id: str
    specification: str
    version: str
    clause_number: str
    clause_title: str
    breadcrumb: List[Dict[str, str]]
    source_type: str
    text: str
    retrieval_score: float = 0.0
    table_id: Optional[str] = None
    table_caption: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_retrieved_chunk(cls, chunk: Any, evidence_id: str) -> "EvidenceItem":
        breadcrumb_data = []
        if hasattr(chunk, "breadcrumb") and chunk.breadcrumb:
            breadcrumb_data = [
                b.to_dict() if hasattr(b, "to_dict") else dict(b)
                for b in chunk.breadcrumb
            ]
        return cls(
            evidence_id=evidence_id,
            chunk_id=getattr(chunk, "chunk_id", ""),
            specification=getattr(chunk, "specification", ""),
            version=getattr(chunk, "version", ""),
            clause_number=getattr(chunk, "clause_number", ""),
            clause_title=getattr(chunk, "clause_title", ""),
            breadcrumb=breadcrumb_data,
            source_type=getattr(chunk, "source_type", "prose"),
            text=getattr(chunk, "text", ""),
            retrieval_score=getattr(chunk, "score", 0.0),
            table_id=getattr(chunk, "table_id", None),
            table_caption=getattr(chunk, "table_caption", None),
        )


@dataclass
class Citation:
    """Authoritative citation referencing specific retrieved evidence."""
    evidence_id: str
    specification: str
    clause_number: str
    clause_title: str
    table_id: Optional[str] = None
    table_caption: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_evidence_item(cls, item: "EvidenceItem") -> "Citation":
        """Constructs an authoritative Citation object from a retrieved EvidenceItem."""
        return cls(
            evidence_id=item.evidence_id,
            specification=item.specification,
            clause_number=item.clause_number,
            clause_title=item.clause_title,
            table_id=item.table_id,
            table_caption=item.table_caption,
        )

    def formatted_citation(self) -> str:
        """Returns standard citation format: [TS 23.501, Clause 6.2.1 — AMF]."""
        if self.table_caption or self.table_id:
            cap = self.table_caption or self.table_id
            return f"[{self.specification}, Clause {self.clause_number} — {self.clause_title}, {cap}]"
        return f"[{self.specification}, Clause {self.clause_number} — {self.clause_title}]"



@dataclass
class Claim:
    """Atomic substantive claim extracted from generated answer."""
    claim_id: str
    text: str
    citations: List[str] = field(default_factory=list)  # List of evidence_ids e.g. ['E1']

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClaimVerificationResult:
    """Verification verdict for a single claim."""
    claim_id: str
    verdict: str  # 'SUPPORTED' | 'UNSUPPORTED' | 'UNCERTAIN'
    evidence_ids: List[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationResult:
    """Complete output from the Grounded Generation Pipeline."""
    status: str  # 'answered' | 'abstain'
    answer: Optional[str]
    claims: List[Claim] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    abstention_reason: Optional[str] = None
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    claim_verifications: List[ClaimVerificationResult] = field(default_factory=list)
    citation_valid: bool = True
    citation_validation_errors: List[str] = field(default_factory=list)
    gate_passed: bool = True
    gate_reason: Optional[str] = None
    latency_breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "answer": self.answer,
            "claims": [c.to_dict() for c in self.claims],
            "citations": [cit.to_dict() for cit in self.citations],
            "abstention_reason": self.abstention_reason,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "claim_verifications": [v.to_dict() for v in self.claim_verifications],
            "citation_valid": self.citation_valid,
            "citation_validation_errors": self.citation_validation_errors,
            "gate_passed": self.gate_passed,
            "gate_reason": self.gate_reason,
            "latency_breakdown": self.latency_breakdown,
        }

"""
Data models for 3GPP document elements, metadata, and chunk outputs.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import hashlib
import json


@dataclass(frozen=True)
class BreadcrumbItem:
    """Represents one step in the section hierarchy breadcrumb trail."""
    number: str
    title: str

    def to_dict(self) -> Dict[str, str]:
        return {"number": self.number, "title": self.title}


@dataclass
class DocumentMetadata:
    """Document-level metadata extracted from cover and document properties."""
    specification: str
    version: str
    release: str
    date: str
    title: str
    source_filename: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ClauseInfo:
    """Structural clause boundary metadata."""
    clause_number: str
    clause_title: str
    level: int
    style_name: str
    breadcrumb: List[BreadcrumbItem] = field(default_factory=list)
    parent_clause: Optional[str] = None
    is_annex: bool = False
    annex_type: Optional[str] = None  # "normative" or "informative"


@dataclass
class Chunk:
    """
    Formal Chunk Schema for the 3GPP-Grounded-RAG pipeline.
    All fields are strictly typed, serializable to JSON/JSONL, and deterministic.
    """
    chunk_id: str
    specification: str
    document_title: str
    version: str
    release: str
    source_filename: str
    clause_number: str
    clause_title: str
    breadcrumb: List[Dict[str, str]]
    source_type: str  # "prose" | "table" | "annex" | "definition"
    text: str
    document_order: int
    parent_clause: Optional[str] = None
    section_level: Optional[int] = None
    table_id: Optional[str] = None
    table_caption: Optional[str] = None
    content_hash: Optional[str] = None

    def compute_content_hash(self) -> str:
        """Computes a deterministic SHA-256 hash across the chunk text and structural keys."""
        payload = f"{self.specification}|{self.version}|{self.clause_number}|{self.source_type}|{self.text}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Converts chunk to a clean dictionary matching the formal schema."""
        d = asdict(self)
        if not self.content_hash:
            d["content_hash"] = self.compute_content_hash()
        return d

    def to_json(self) -> str:
        """Serializes chunk to a single-line JSON string for JSONL."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

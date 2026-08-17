"""
Mavenir 3GPP RAG — Document Ingestion & Chunking Package.
"""

from ingestion.models import Chunk, DocumentMetadata, BreadcrumbItem, ClauseInfo
from ingestion.docx_parser import DocxParser
from ingestion.chunker import HierarchicalChunker
from ingestion.config import EXPECTED_FILES, RAW_DATA_DIR, PROCESSED_DATA_DIR

__all__ = [
    "Chunk",
    "DocumentMetadata",
    "BreadcrumbItem",
    "ClauseInfo",
    "DocxParser",
    "HierarchicalChunker",
    "EXPECTED_FILES",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
]

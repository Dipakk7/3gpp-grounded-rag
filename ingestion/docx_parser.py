"""
Sequential DOCX document parser for 3GPP Technical Specifications.
Traverses body XML elements in exact document order, interleaving paragraphs and tables.
"""

from typing import Generator, Tuple, Any
from pathlib import Path
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table
from ingestion.models import DocumentMetadata
from ingestion.metadata import extract_document_metadata


def iter_body_elements(doc: docx.Document) -> Generator[Tuple[str, Any], None, None]:
    """
    Yields ('p', Paragraph) or ('tbl', Table) in exact sequential body order.
    """
    for child in doc.element.body:
        tag = child.tag.split("}")[-1]
        if tag == "p":
            yield ("p", Paragraph(child, doc))
        elif tag == "tbl":
            yield ("tbl", Table(child, doc))


class DocxParser:
    """
    Parses a 3GPP specification DOCX file and extracts metadata and ordered body elements.
    """

    def __init__(self, doc_path: Path):
        self.doc_path = doc_path
        if not doc_path.exists():
            raise FileNotFoundError(f"Source file not found: {doc_path}")
        self.doc = docx.Document(str(doc_path))
        self.metadata: DocumentMetadata = extract_document_metadata(self.doc, self.doc_path)

    def parse_elements(self) -> Generator[Tuple[str, Any], None, None]:
        """
        Yields all body elements in original document order.
        """
        yield from iter_body_elements(self.doc)

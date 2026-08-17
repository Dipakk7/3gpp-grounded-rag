"""
Hierarchy-aware semantic chunking engine for 3GPP Technical Specifications.
Preserves clause context, tables, breadcrumbs, and splits oversized clauses along paragraph boundaries.
"""

from typing import List, Optional, Tuple, Dict, Any
from collections import defaultdict
import re
from ingestion.models import Chunk, DocumentMetadata, ClauseInfo, BreadcrumbItem
from ingestion.config import (
    MAX_CHUNK_CHARS,
    MIN_SPLIT_CHARS,
    TABLE_CAPTION_REGEX,
)
from ingestion.clause_parser import ClauseParser
from ingestion.table_parser import TableParser
from ingestion.toc_filter import TOCFilter
from ingestion.docx_parser import DocxParser


def sanitize_slug(text: str) -> str:
    """Converts a clause number or title into a clean filename/ID slug."""
    clean = re.sub(r"[^\w\.\-]", "_", text.strip())
    return clean.strip("_")


def split_oversized_prose(paragraphs: List[str], max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """
    Splits a list of paragraphs into semantic blocks without breaking paragraphs or sentences.
    """
    if not paragraphs:
        return []

    chunks: List[str] = []
    current_block: List[str] = []
    current_length = 0

    for p in paragraphs:
        p_len = len(p)
        if current_block and (current_length + p_len + 2 > max_chars):
            chunks.append("\n\n".join(current_block))
            current_block = [p]
            current_length = p_len
        else:
            current_block.append(p)
            current_length += p_len + 2

    if current_block:
        chunks.append("\n\n".join(current_block))

    return chunks


class HierarchicalChunker:
    """
    Orchestrates sequential parsing, clause tracking, table integration, and chunk generation.
    """

    def __init__(self, parser: DocxParser):
        self.parser = parser
        self.metadata = parser.metadata
        self.toc_filter = TOCFilter()
        self.clause_parser = ClauseParser()
        self.table_parser = TableParser(self.metadata.specification)

        self.chunks: List[Chunk] = []
        self.document_order_counter: int = 0
        self.pending_paragraphs: List[str] = []
        self.active_clause: Optional[ClauseInfo] = None
        self.pending_caption: Optional[str] = None
        self.clause_prose_counters: Dict[str, int] = defaultdict(int)

    def _flush_pending_prose(self):
        """Flushes accumulated paragraphs under the active clause into one or more prose chunks."""
        if not self.pending_paragraphs:
            return

        if self.active_clause:
            clause_num = self.active_clause.clause_number
            clause_title = self.active_clause.clause_title
            level = self.active_clause.level
            parent = self.active_clause.parent_clause
            is_annex = self.active_clause.is_annex
            breadcrumbs = [b.to_dict() for b in self.active_clause.breadcrumb]
        else:
            clause_num = "Foreword"
            clause_title = "Foreword"
            level = 1
            parent = None
            is_annex = False
            breadcrumbs = [{"number": "Foreword", "title": "Foreword"}]

        source_type = "annex" if is_annex else ("definition" if "definition" in clause_title.lower() else "prose")
        blocks = split_oversized_prose(self.pending_paragraphs, MAX_CHUNK_CHARS)

        clean_spec = sanitize_slug(self.metadata.specification)
        clean_ver = sanitize_slug(self.metadata.version)
        clause_slug = sanitize_slug(clause_num)

        for block in blocks:
            self.document_order_counter += 1
            self.clause_prose_counters[clause_num] += 1
            idx = self.clause_prose_counters[clause_num]
            chunk_id = f"{clean_spec}-{clean_ver}-{clause_slug}-P{idx:03d}"

            chunk = Chunk(
                chunk_id=chunk_id,
                specification=self.metadata.specification,
                document_title=self.metadata.title,
                version=self.metadata.version,
                release=self.metadata.release,
                source_filename=self.metadata.source_filename,
                clause_number=clause_num,
                clause_title=clause_title,
                breadcrumb=breadcrumbs,
                source_type=source_type,
                text=block,
                document_order=self.document_order_counter,
                parent_clause=parent,
                section_level=level,
                table_id=None,
                table_caption=None,
            )
            chunk.content_hash = chunk.compute_content_hash()
            self.chunks.append(chunk)

        self.pending_paragraphs = []

    def chunk_document(self) -> List[Chunk]:
        """Processes all elements and returns the complete list of structured chunks."""
        raw_p_index = 0

        for elem_type, elem in self.parser.parse_elements():
            if elem_type == "p":
                raw_p_index += 1
                text = elem.text.strip()
                style_name = elem.style.name

                is_toc, is_body = self.toc_filter.process_paragraph(text, style_name, raw_p_index)
                if is_toc or not is_body:
                    continue

                if not text:
                    continue

                # Check if this paragraph is a table caption (e.g. "Table 4.2.3-1: ...")
                if TABLE_CAPTION_REGEX.match(text) or (style_name == "TH" and text.startswith("Table ")):
                    self.pending_caption = text
                    continue

                # Check if this paragraph is a new clause heading
                new_clause = self.clause_parser.parse_heading(text, style_name, is_toc=False)
                if new_clause:
                    # Flush prose from previous clause before switching
                    self._flush_pending_prose()
                    self.active_clause = new_clause
                    continue

                # Normal body paragraph
                self.pending_paragraphs.append(text)

            elif elem_type == "tbl":
                # If table occurs during front-matter before body starts, skip cover layout tables
                if not self.toc_filter.toc_ended:
                    continue

                # Flush preceding paragraphs before table
                self._flush_pending_prose()

                table_id, table_md, caption = self.table_parser.parse(elem, self.pending_caption)
                self.pending_caption = None

                if not table_md:
                    continue

                if self.active_clause:
                    clause_num = self.active_clause.clause_number
                    clause_title = self.active_clause.clause_title
                    level = self.active_clause.level
                    parent = self.active_clause.parent_clause
                    breadcrumbs = [b.to_dict() for b in self.active_clause.breadcrumb]
                else:
                    clause_num = "Scope"
                    clause_title = "Scope"
                    level = 1
                    parent = None
                    breadcrumbs = [{"number": "Scope", "title": "Scope"}]

                clean_spec = sanitize_slug(self.metadata.specification)
                clean_ver = sanitize_slug(self.metadata.version)
                clause_slug = sanitize_slug(clause_num)

                self.document_order_counter += 1
                chunk_id = f"{clean_spec}-{clean_ver}-{clause_slug}-{table_id}"

                chunk = Chunk(
                    chunk_id=chunk_id,
                    specification=self.metadata.specification,
                    document_title=self.metadata.title,
                    version=self.metadata.version,
                    release=self.metadata.release,
                    source_filename=self.metadata.source_filename,
                    clause_number=clause_num,
                    clause_title=clause_title,
                    breadcrumb=breadcrumbs,
                    source_type="table",
                    text=table_md,
                    document_order=self.document_order_counter,
                    parent_clause=parent,
                    section_level=level,
                    table_id=table_id,
                    table_caption=caption,
                )
                chunk.content_hash = chunk.compute_content_hash()
                self.chunks.append(chunk)

        # Flush any trailing paragraphs
        self._flush_pending_prose()
        return self.chunks

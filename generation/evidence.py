"""
Evidence Formatting Module:
Converts retrieved chunks into standardized, deterministic evidence blocks for the LLM.
"""

from typing import List, Dict, Any, Union
from retrieval.models import RetrievedChunk
from generation.models import EvidenceItem


def chunks_to_evidence_items(chunks: List[Union[RetrievedChunk, Dict[str, Any]]]) -> List[EvidenceItem]:
    """
    Converts a list of retrieved chunks into deterministic EvidenceItem instances
    with identifiers E1, E2, ..., EN.
    """
    evidence_items: List[EvidenceItem] = []
    for idx, chunk in enumerate(chunks, start=1):
        ev_id = f"E{idx}"
        if isinstance(chunk, EvidenceItem):
            evidence_items.append(chunk)
        elif isinstance(chunk, RetrievedChunk):
            evidence_items.append(EvidenceItem.from_retrieved_chunk(chunk, ev_id))
        elif isinstance(chunk, dict):
            # Parse dict chunk
            evidence_items.append(
                EvidenceItem(
                    evidence_id=ev_id,
                    chunk_id=chunk.get("chunk_id", ""),
                    specification=chunk.get("specification", ""),
                    version=chunk.get("version", ""),
                    clause_number=chunk.get("clause_number", ""),
                    clause_title=chunk.get("clause_title", ""),
                    breadcrumb=chunk.get("breadcrumb", []),
                    source_type=chunk.get("source_type", "prose"),
                    text=chunk.get("text", ""),
                    retrieval_score=chunk.get("score", 0.0),
                    table_id=chunk.get("table_id"),
                    table_caption=chunk.get("table_caption"),
                )
            )
    return evidence_items


def format_evidence_blocks(evidence_items: List[EvidenceItem]) -> str:
    """
    Renders structured evidence items into a controlled prompt context string.
    Treats all 3GPP document text strictly as data.
    """
    if not evidence_items:
        return "No evidence provided."

    blocks = []
    for item in evidence_items:
        caption_info = f"Table Caption: {item.table_caption}\n" if item.table_caption else ""
        table_id_info = f"Table ID: {item.table_id}\n" if item.table_id else ""
        block = (
            f"[EVIDENCE {item.evidence_id}]\n"
            f"Specification: {item.specification}\n"
            f"Version: {item.version}\n"
            f"Clause: {item.clause_number}\n"
            f"Title: {item.clause_title}\n"
            f"{table_id_info}"
            f"{caption_info}"
            f"Content:\n{item.text.strip()}\n"
            f"[END EVIDENCE {item.evidence_id}]"
        )
        blocks.append(block)

    return "\n\n".join(blocks)

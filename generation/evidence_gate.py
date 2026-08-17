"""
Evidence Sufficiency Gate:
Deterministic, pre-generation filter that checks if retrieved evidence is
sufficiently plausible and non-empty before invoking the LLM generator.
"""

from typing import List, Tuple, Optional
from generation.models import EvidenceItem


class EvidenceSufficiencyGate:
    """
    Deterministic gate that evaluates retrieved evidence candidates
    prior to calling the LLM generation layer.
    """

    def __init__(
        self,
        min_evidence_count: int = 1,
        min_top_score: float = 0.01,
        min_char_length: int = 20,
    ):
        self.min_evidence_count = min_evidence_count
        self.min_top_score = min_top_score
        self.min_char_length = min_char_length

    def evaluate(
        self,
        query: str,
        evidence_items: List[EvidenceItem]
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether evidence meets minimum criteria for generation.
        Returns:
            (passed: bool, reason: Optional[str])
        """
        if not query or not query.strip():
            return False, "Query is empty or whitespace."

        if not evidence_items or len(evidence_items) < self.min_evidence_count:
            return False, "No evidence chunks were retrieved from the knowledge base."

        # Check if top item has reasonable non-empty content
        top_item = evidence_items[0]
        if not top_item.text or len(top_item.text.strip()) < self.min_char_length:
            return False, f"Top retrieved evidence [{top_item.evidence_id}] contains insufficient text."

        # Check if all items are completely empty
        total_text_len = sum(len(item.text.strip()) for item in evidence_items)
        if total_text_len < self.min_char_length:
            return False, "Total retrieved evidence length is below minimum substantive threshold."

        # Check score if score is tracked and strictly positive
        if top_item.retrieval_score is not None and top_item.retrieval_score < self.min_top_score:
            return False, f"Top retrieval confidence score ({top_item.retrieval_score:.4f}) is below minimum gate threshold."

        return True, None

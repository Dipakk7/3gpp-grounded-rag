"""
Citation Validation Subsystem:
Strictly verifies that all generated citations map to actual, supplied evidence items,
and that claimed metadata (spec, clause, title) was not fabricated or distorted.
"""

from typing import List, Dict, Tuple, Optional
from generation.models import EvidenceItem, Citation, Claim


class CitationValidator:
    """
    Validates evidence ID references and deterministically constructs authoritative
    citations from the actual supplied evidence blocks.
    """

    def validate(
        self,
        status: str,
        claims: List[Claim],
        citations: Optional[List[Citation]] = None,
        evidence_items: Optional[List[EvidenceItem]] = None,
    ) -> Tuple[bool, List[str], List[Citation]]:
        """
        Validates claims and evidence IDs against supplied evidence.
        Deterministically builds authoritative Citation objects from evidence metadata.

        Returns:
            (is_valid: bool, errors: List[str], constructed_citations: List[Citation])
        """
        if evidence_items is None:
            evidence_items = []

        errors: List[str] = []
        evidence_map: Dict[str, EvidenceItem] = {e.evidence_id: e for e in evidence_items}
        valid_citations: List[Citation] = []
        seen_ev_ids = set()

        if status == "abstain":
            return True, [], []

        # 1. Answered status must contain claims
        if status == "answered" and not claims:
            errors.append("Response status is 'answered' but contains zero claims.")

        # 2. Check each claim and resolve its evidence IDs
        total_referenced_ids = 0
        for claim in claims:
            if not claim.citations:
                errors.append(f"Claim '{claim.claim_id}' has no supporting citations.")
                continue

            for ev_id in claim.citations:
                total_referenced_ids += 1
                if ev_id not in evidence_map:
                    errors.append(f"Claim '{claim.claim_id}' cites non-existent evidence ID '{ev_id}'.")
                elif ev_id not in seen_ev_ids:
                    actual_ev = evidence_map[ev_id]
                    valid_citations.append(Citation.from_evidence_item(actual_ev))
                    seen_ev_ids.add(ev_id)

        # 3. If answered but zero valid citations were referenced
        if status == "answered" and total_referenced_ids == 0:
            errors.append("Response status is 'answered' but contains zero citations.")

        # 4. Handle legacy top-level citations if provided (for backwards compatibility)
        if citations:
            for cit in citations:
                ev_id = cit.evidence_id
                if ev_id not in evidence_map:
                    if not any(f"non-existent evidence ID '{ev_id}'" in err for err in errors):
                        errors.append(f"Citation references non-existent evidence ID '{ev_id}'.")
                elif ev_id not in seen_ev_ids:
                    actual_ev = evidence_map[ev_id]
                    valid_citations.append(Citation.from_evidence_item(actual_ev))
                    seen_ev_ids.add(ev_id)

        is_valid = len(errors) == 0
        return is_valid, errors, valid_citations


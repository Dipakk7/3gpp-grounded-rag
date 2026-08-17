"""
Abstention Policy Subsystem:
Implements conservative fail-safe logic to convert unverified or invalid responses
into clean, structured abstentions.
"""

from typing import List, Optional, Tuple
from generation.models import Claim, Citation, ClaimVerificationResult, GenerationResult, EvidenceItem

DEFAULT_ABSTENTION_MESSAGE = "I couldn't find sufficient authoritative evidence in the provided 3GPP specifications to answer this question."


class AbstentionPolicy:
    """
    Evaluates whether a generated response must be abstained or revised.
    """

    def __init__(
        self,
        strict_mode: bool = True,
        allow_claim_filtering: bool = False,
    ):
        self.strict_mode = strict_mode
        self.allow_claim_filtering = allow_claim_filtering

    def create_abstention(
        self,
        reason: str,
        evidence_items: Optional[List[EvidenceItem]] = None,
        gate_passed: bool = True,
        gate_reason: Optional[str] = None,
        citation_valid: bool = True,
        citation_errors: Optional[List[str]] = None,
    ) -> GenerationResult:
        """Constructs a deterministic, structured abstention result."""
        return GenerationResult(
            status="abstain",
            answer=None,
            claims=[],
            citations=[],
            abstention_reason=reason,
            evidence_items=evidence_items or [],
            claim_verifications=[],
            citation_valid=citation_valid,
            citation_validation_errors=citation_errors or [],
            gate_passed=gate_passed,
            gate_reason=gate_reason,
        )

    def apply_policy(
        self,
        result: GenerationResult,
    ) -> GenerationResult:
        """
        Applies conservative fail-safe rules:
        1. If gate failed -> Abstain
        2. If citations invalid -> Abstain
        3. If any claim is UNSUPPORTED or UNCERTAIN in strict mode -> Abstain
        4. If answered with 0 claims or 0 citations -> Abstain
        """
        if result.status == "abstain":
            return result

        if not result.gate_passed:
            return self.create_abstention(
                reason=f"Evidence Sufficiency Gate failed: {result.gate_reason}",
                evidence_items=result.evidence_items,
                gate_passed=False,
                gate_reason=result.gate_reason,
            )

        if not result.citation_valid:
            err_msg = "; ".join(result.citation_validation_errors)
            return self.create_abstention(
                reason=f"Invalid citations detected: {err_msg}",
                evidence_items=result.evidence_items,
                citation_valid=False,
                citation_errors=result.citation_validation_errors,
            )

        if not result.claims or not result.citations:
            return self.create_abstention(
                reason="Response lacks verifiable claims or authoritative citations.",
                evidence_items=result.evidence_items,
            )

        # Check claim verifications
        unsupported = [v for v in result.claim_verifications if v.verdict == "UNSUPPORTED"]
        uncertain = [v for v in result.claim_verifications if v.verdict == "UNCERTAIN"]

        if unsupported:
            reasons = [f"Claim '{u.claim_id}': {u.reason}" for u in unsupported]
            return self.create_abstention(
                reason=f"Unsupported claims detected: {'; '.join(reasons)}",
                evidence_items=result.evidence_items,
            )

        if self.strict_mode and uncertain:
            reasons = [f"Claim '{u.claim_id}': {u.reason}" for u in uncertain]
            return self.create_abstention(
                reason=f"Uncertain claims detected under strict verification: {'; '.join(reasons)}",
                evidence_items=result.evidence_items,
            )

        return result

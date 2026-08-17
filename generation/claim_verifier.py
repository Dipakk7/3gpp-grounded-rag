"""
Claim / Evidence Verification Subsystem:
Evaluates whether each extracted substantive claim is factually supported
by the exact text of its cited evidence blocks.
"""

import json
import urllib.request
from typing import List, Dict, Any, Optional
from generation.models import EvidenceItem, Claim, ClaimVerificationResult
from generation.prompt import CLAIM_VERIFICATION_PROMPT, build_claim_verification_prompt


class ClaimVerifier:
    """
    Verifies substantive claims against cited evidence blocks using local LLM verification
    or deterministic lexical fallback.
    """

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        ollama_url: str = "http://localhost:11434",
        use_llm: bool = True,
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.use_llm = use_llm

    def verify_claim_llm(
        self,
        claim: Claim,
        cited_evidence_text: str,
        evidence_ids: List[str]
    ) -> ClaimVerificationResult:
        """Runs LLM verification for a single claim against cited text."""
        prompt = build_claim_verification_prompt(claim.text, cited_evidence_text, ", ".join(evidence_ids))
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": CLAIM_VERIFICATION_PROMPT,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0, "num_predict": 256}
        }
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_json = json.loads(resp.read().decode("utf-8")).get("response", "{}")
                data = json.loads(raw_json)
                verdict = data.get("verdict", "UNCERTAIN").upper()
                if verdict not in ["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"]:
                    verdict = "UNCERTAIN"
                reason = data.get("reason", "Verification evaluated against cited evidence.")
                return ClaimVerificationResult(
                    claim_id=claim.claim_id,
                    verdict=verdict,
                    evidence_ids=evidence_ids,
                    reason=reason
                )
        except Exception as e:
            # Fallback to lexical verification if LLM request fails
            return self.verify_claim_lexical(claim, cited_evidence_text, evidence_ids)

    def verify_claim_lexical(
        self,
        claim: Claim,
        cited_evidence_text: str,
        evidence_ids: List[str]
    ) -> ClaimVerificationResult:
        """Deterministic lexical verification fallback based on key phrase presence."""
        c_text_lower = claim.text.lower()
        e_text_lower = cited_evidence_text.lower()

        # Check for substantive overlap (including acronyms like N2, CP, NAS, AMF and stems)
        words = [w.strip(".,;:()[]{}'\"") for w in c_text_lower.split()]
        words = [w for w in words if len(w) >= 2 and w not in {"the", "and", "for", "with", "this", "that", "from"}]
        if not words:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verdict="UNCERTAIN",
                evidence_ids=evidence_ids,
                reason="Claim is too brief for lexical verification."
            )

        match_count = 0
        for w in words:
            if w in e_text_lower:
                match_count += 1
            elif len(w) >= 5 and (w[:4] in e_text_lower or w[:5] in e_text_lower):
                match_count += 1

        ratio = match_count / len(words)

        if ratio >= 0.5:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verdict="SUPPORTED",
                evidence_ids=evidence_ids,
                reason=f"Substantive terminology ({match_count}/{len(words)} terms) confirmed in cited evidence."
            )
        elif ratio >= 0.25:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verdict="UNCERTAIN",
                evidence_ids=evidence_ids,
                reason=f"Partial overlap ({match_count}/{len(words)} terms) detected in cited evidence."
            )
        else:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verdict="UNSUPPORTED",
                evidence_ids=evidence_ids,
                reason="Insufficient overlap with cited evidence text."
            )

    def verify_claims(
        self,
        claims: List[Claim],
        evidence_items: List[EvidenceItem]
    ) -> List[ClaimVerificationResult]:
        """Verifies all claims against the supplied evidence objects."""
        ev_map = {e.evidence_id: e.text for e in evidence_items}
        results = []

        for claim in claims:
            cited_texts = [ev_map[eid] for eid in claim.citations if eid in ev_map]
            combined_text = "\n".join(cited_texts)

            if not combined_text:
                results.append(
                    ClaimVerificationResult(
                        claim_id=claim.claim_id,
                        verdict="UNSUPPORTED",
                        evidence_ids=claim.citations,
                        reason="No valid cited evidence found for this claim."
                    )
                )
                continue

            if self.use_llm:
                res = self.verify_claim_llm(claim, combined_text, claim.citations)
            else:
                res = self.verify_claim_lexical(claim, combined_text, claim.citations)

            results.append(res)

        return results

"""
End-to-End Grounded Generation Pipeline:
Orchestrates Hybrid Retrieval -> Evidence Gate -> LLM Generator -> Citation Validator -> Claim Verifier -> Abstention Policy.
"""

import time
from typing import Optional, List, Dict, Any, Union
from retrieval.retriever import HybridRetriever
from retrieval.models import RetrievedChunk
from generation.models import EvidenceItem, GenerationResult
from generation.evidence import chunks_to_evidence_items
from generation.evidence_gate import EvidenceSufficiencyGate
from generation.generator import GroundedGenerator
from generation.citation_validator import CitationValidator
from generation.claim_verifier import ClaimVerifier
from generation.abstention import AbstentionPolicy


class GroundedGenerationPipeline:
    """
    Production-grade, end-to-end grounded 3GPP RAG generation pipeline with multi-stage verification.
    """

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        generator: Optional[GroundedGenerator] = None,
        gate: Optional[EvidenceSufficiencyGate] = None,
        citation_validator: Optional[CitationValidator] = None,
        claim_verifier: Optional[ClaimVerifier] = None,
        abstention_policy: Optional[AbstentionPolicy] = None,
    ):
        self.retriever = retriever
        self.generator = generator or GroundedGenerator()
        self.gate = gate or EvidenceSufficiencyGate()
        self.citation_validator = citation_validator or CitationValidator()
        self.claim_verifier = claim_verifier or ClaimVerifier(use_llm=False)  # Fast deterministic verification
        self.abstention_policy = abstention_policy or AbstentionPolicy()

    def process(
        self,
        question: str,
        top_k: int = 5,
        provided_evidence: Optional[List[Union[RetrievedChunk, Dict[str, Any], EvidenceItem]]] = None
    ) -> GenerationResult:
        """
        Executes full grounded answer generation for a question.
        If provided_evidence is given, skips retriever and uses the explicit evidence items.
        """
        t_start = time.time()
        latencies: Dict[str, float] = {}

        # 1. Retrieval
        t0 = time.time()
        if provided_evidence is not None:
            evidence_items = chunks_to_evidence_items(provided_evidence)
            lat_retrieval = (time.time() - t0) * 1000
        else:
            if self.retriever is None:
                raise ValueError("Retriever must be configured if provided_evidence is None.")
            retrieved_chunks = self.retriever.retrieve(question, top_k=top_k)
            evidence_items = chunks_to_evidence_items(retrieved_chunks)
            lat_retrieval = (time.time() - t0) * 1000
        latencies["retrieval_ms"] = round(lat_retrieval, 2)

        # 2. Evidence Sufficiency Gate
        t0 = time.time()
        gate_passed, gate_reason = self.gate.evaluate(question, evidence_items)
        lat_gate = (time.time() - t0) * 1000
        latencies["gate_ms"] = round(lat_gate, 2)

        if not gate_passed:
            abstention = self.abstention_policy.create_abstention(
                reason=f"Evidence Sufficiency Gate rejected: {gate_reason}",
                evidence_items=evidence_items,
                gate_passed=False,
                gate_reason=gate_reason,
            )
            latencies["total_ms"] = round((time.time() - t_start) * 1000, 2)
            abstention.latency_breakdown = latencies
            return abstention

        # 3. Grounded Generation
        raw_result, lat_gen = self.generator.generate(question, evidence_items)
        latencies["generation_ms"] = round(lat_gen, 2)

        if raw_result.status == "abstain":
            latencies["total_ms"] = round((time.time() - t_start) * 1000, 2)
            raw_result.latency_breakdown = latencies
            return raw_result

        # 4. Citation Validation
        t0 = time.time()
        is_cit_valid, cit_errors, cleaned_citations = self.citation_validator.validate(
            status=raw_result.status,
            claims=raw_result.claims,
            citations=raw_result.citations,
            evidence_items=evidence_items,
        )
        lat_val = (time.time() - t0) * 1000
        latencies["validation_ms"] = round(lat_val, 2)
        raw_result.citation_valid = is_cit_valid
        raw_result.citation_validation_errors = cit_errors
        raw_result.citations = cleaned_citations

        # 5. Claim / Evidence Verification
        t0 = time.time()
        verifications = self.claim_verifier.verify_claims(raw_result.claims, evidence_items)
        lat_ver = (time.time() - t0) * 1000
        latencies["verification_ms"] = round(lat_ver, 2)
        raw_result.claim_verifications = verifications

        # 6. Apply Conservative Abstention Policy
        final_result = self.abstention_policy.apply_policy(raw_result)

        latencies["total_ms"] = round((time.time() - t_start) * 1000, 2)
        final_result.latency_breakdown = latencies
        return final_result

"""
Grounded Generation and Anti-Hallucination Subsystem.
"""

from generation.models import (
    EvidenceItem,
    Citation,
    Claim,
    ClaimVerificationResult,
    GenerationResult,
)
from generation.evidence import chunks_to_evidence_items, format_evidence_blocks
from generation.prompt import (
    GROUNDING_SYSTEM_PROMPT,
    CLAIM_VERIFICATION_PROMPT,
    build_generation_user_prompt,
    build_claim_verification_prompt,
)
from generation.evidence_gate import EvidenceSufficiencyGate
from generation.generator import GroundedGenerator
from generation.citation_validator import CitationValidator
from generation.claim_verifier import ClaimVerifier
from generation.abstention import AbstentionPolicy
from generation.pipeline import GroundedGenerationPipeline

__all__ = [
    "EvidenceItem",
    "Citation",
    "Claim",
    "ClaimVerificationResult",
    "GenerationResult",
    "chunks_to_evidence_items",
    "format_evidence_blocks",
    "GROUNDING_SYSTEM_PROMPT",
    "CLAIM_VERIFICATION_PROMPT",
    "build_generation_user_prompt",
    "build_claim_verification_prompt",
    "EvidenceSufficiencyGate",
    "GroundedGenerator",
    "CitationValidator",
    "ClaimVerifier",
    "AbstentionPolicy",
    "GroundedGenerationPipeline",
]

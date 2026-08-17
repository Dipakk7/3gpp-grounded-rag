"""
LLM Generator Module:
Invokes local Ollama LLM to synthesize grounded responses adhering to strict structured JSON output.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
from generation.models import EvidenceItem, Claim, Citation, GenerationResult
from generation.prompt import GROUNDING_SYSTEM_PROMPT, build_generation_user_prompt
from generation.evidence import format_evidence_blocks

DEFAULT_MODEL = "qwen2.5:1.5b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class GroundedGenerator:
    """
    Handles local LLM inference, prompt formatting, and structured JSON parsing.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        temperature: float = 0.0,
        num_predict: int = 1024,
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.temperature = temperature
        self.num_predict = num_predict

    def _call_ollama(self, prompt: str, system: str) -> Tuple[Dict[str, Any], float]:
        """Performs HTTP request to Ollama /api/generate in JSON format mode."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
            }
        }
        t0 = time.time()
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            lat_ms = (time.time() - t0) * 1000
            return data, lat_ms
        except Exception as e:
            lat_ms = (time.time() - t0) * 1000
            return {"error": str(e), "response": ""}, lat_ms

    def _parse_llm_json(self, raw_response: str) -> Dict[str, Any]:
        """Safely parses JSON string with fallback heuristics."""
        if not raw_response or not raw_response.strip():
            return {"status": "abstain", "abstention_reason": "Empty response from LLM."}

        try:
            return json.loads(raw_response)
        except Exception:
            # Attempt to locate JSON block within markdown code fences
            text = raw_response.strip()
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
            try:
                return json.loads(text)
            except Exception:
                return {
                    "status": "abstain",
                    "abstention_reason": f"Malformed JSON output from model: {raw_response[:100]}..."
                }

    def generate(
        self,
        question: str,
        evidence_items: List[EvidenceItem]
    ) -> Tuple[GenerationResult, float]:
        """
        Generates a grounded response given a question and structured evidence.
        Returns:
            (GenerationResult, generation_latency_ms)
        """
        formatted_evidence = format_evidence_blocks(evidence_items)
        user_prompt = build_generation_user_prompt(question, formatted_evidence)

        data, lat_ms = self._call_ollama(user_prompt, GROUNDING_SYSTEM_PROMPT)

        if "error" in data:
            return (
                GenerationResult(
                    status="abstain",
                    answer=None,
                    claims=[],
                    citations=[],
                    abstention_reason=f"LLM generation failed: {data['error']}",
                    evidence_items=evidence_items,
                ),
                lat_ms
            )

        raw_response = data.get("response", "")
        parsed = self._parse_llm_json(raw_response)

        status = parsed.get("status", "abstain").lower()
        if status not in ["answered", "abstain"]:
            status = "abstain"

        raw_claims = parsed.get("claims", [])
        claims: List[Claim] = []
        if isinstance(raw_claims, list):
            for idx, c in enumerate(raw_claims, start=1):
                if isinstance(c, dict) and c.get("text"):
                    # Support evidence_ids (primary) or citations (legacy)
                    raw_ev = c.get("evidence_ids", c.get("citations", []))
                    if isinstance(raw_ev, str):
                        raw_ev = [raw_ev]
                    elif not isinstance(raw_ev, list):
                        raw_ev = []

                    clean_ev_ids = []
                    for eid in raw_ev:
                        if isinstance(eid, str):
                            # Split on commas/spaces if model joined them into a single string
                            for token in eid.replace(",", " ").replace(";", " ").split():
                                clean_token = token.strip("[]'\" ")
                                if clean_token:
                                    clean_ev_ids.append(clean_token)

                    claims.append(
                        Claim(
                            claim_id=f"C{idx}",
                            text=str(c.get("text", "")).strip(),
                            citations=clean_ev_ids,
                        )
                    )

        answer = parsed.get("answer") if status == "answered" else None
        abstention_reason = parsed.get("abstention_reason") if status == "abstain" else None

        result = GenerationResult(
            status=status,
            answer=answer,
            claims=claims,
            citations=[],
            abstention_reason=abstention_reason,
            evidence_items=evidence_items,
        )

        return result, lat_ms


"""
Unit and Integration Test Suite for FastAPI API Wrapper (Phase 5).
Covers endpoints, Pydantic validation, response contracts, error handling, and security sanitization.
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_rag_service
from api.service import RAGService
from generation.models import (
    GenerationResult,
    Citation,
    EvidenceItem,
    Claim,
    ClaimVerificationResult,
)


class TestFastAPIWrapper(unittest.TestCase):
    """Test suite for Phase 5 FastAPI API Wrapper."""

    def setUp(self):
        self.mock_service = MagicMock(spec=RAGService)
        app.dependency_overrides[get_rag_service] = lambda: self.mock_service
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    # 1. Health endpoint returns healthy response
    def test_01_health_healthy(self):
        """Verify GET /health returns 200 and healthy service readiness info."""
        self.mock_service.get_health.return_value = {
            "initialized": True,
            "vector_store_ready": True,
            "vector_store_chunk_count": 6737,
            "bm25_ready": True,
            "bm25_chunk_count": 6737,
            "embedding_model": "nomic-embed-text",
            "generation_model": "qwen2.5:1.5b",
            "ollama_url": "http://localhost:11434",
        }
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "3gpp-grounded-rag")
        self.assertEqual(data["details"]["vector_store_chunk_count"], 6737)

    # 2. Health endpoint returns degraded response on uninitialized components
    def test_02_health_degraded(self):
        """Verify GET /health returns 503 if dependencies are unready/unavailable."""
        self.mock_service.get_health.return_value = {
            "initialized": False,
            "vector_store_ready": False,
            "vector_store_chunk_count": 0,
            "bm25_ready": False,
            "bm25_chunk_count": 0,
            "embedding_model": "nomic-embed-text",
            "generation_model": "qwen2.5:1.5b",
            "ollama_url": "http://localhost:11434",
        }
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 503)
        data = resp.json()
        self.assertEqual(data["status"], "degraded")

    # 3. Valid /ask request accepted with answered response
    def test_03_ask_answered_contract(self):
        """Verify POST /ask processes answered question and returns correct contract."""
        mock_evidence = [
            EvidenceItem(
                evidence_id="E1",
                chunk_id="TS_23_501_chunk_42",
                specification="TS 23.501",
                version="Rel-18",
                clause_number="6.2.1",
                clause_title="AMF",
                breadcrumb=[{"clause_number": "6.2.1", "clause_title": "AMF"}],
                source_type="prose",
                text="The AMF is responsible for registration management and connection management.",
                retrieval_score=0.95,
            )
        ]
        mock_citation = Citation(
            evidence_id="E1",
            specification="TS 23.501",
            clause_number="6.2.1",
            clause_title="AMF",
        )
        self.mock_service.ask.return_value = GenerationResult(
            status="answered",
            answer="The AMF handles registration management [TS 23.501, Clause 6.2.1 — AMF].",
            citations=[mock_citation],
            evidence_items=mock_evidence,
            latency_breakdown={"retrieval_ms": 12.5, "generation_ms": 150.0, "total_ms": 165.0},
        )

        resp = self.client.post("/ask", json={"question": "What does the AMF do?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "answered")
        self.assertIn("registration management", data["answer"])
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0]["specification"], "TS 23.501")
        self.assertEqual(data["citations"][0]["clause_number"], "6.2.1")
        self.assertEqual(data["citations"][0]["clause_title"], "AMF")
        self.assertEqual(len(data["evidence"]), 1)
        self.assertEqual(data["evidence"][0]["evidence_id"], "E1")
        self.assertEqual(data["evidence"][0]["chunk_id"], "TS_23_501_chunk_42")
        self.assertIsNone(data["reason"])
        self.assertIsNotNone(data["latency_breakdown"])

    # 4. Empty question rejected
    def test_04_empty_question_rejected(self):
        """Verify POST /ask rejects empty string with HTTP 422."""
        resp = self.client.post("/ask", json={"question": ""})
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

    # 5. Whitespace-only question rejected
    def test_05_whitespace_question_rejected(self):
        """Verify POST /ask rejects whitespace-only string with HTTP 422."""
        resp = self.client.post("/ask", json={"question": "   \n\t  "})
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

    # 6. Oversized question rejected
    def test_06_oversized_question_rejected(self):
        """Verify POST /ask rejects questions exceeding max length with HTTP 422."""
        huge_q = "A" * 2005
        resp = self.client.post("/ask", json={"question": huge_q})
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

    # 7. Missing question field rejected
    def test_07_missing_question_rejected(self):
        """Verify POST /ask rejects missing question payload with HTTP 422."""
        resp = self.client.post("/ask", json={})
        self.assertEqual(resp.status_code, 422)
        data = resp.json()
        self.assertEqual(data["error_code"], "VALIDATION_ERROR")

    # 8. Abstention result mapped correctly
    def test_08_abstention_contract(self):
        """Verify POST /ask maps abstention cleanly with reason and null answer."""
        self.mock_service.ask.return_value = GenerationResult(
            status="abstain",
            answer=None,
            citations=[],
            abstention_reason="Evidence Sufficiency Gate rejected: No relevant evidence found in 3GPP corpus.",
            evidence_items=[],
            latency_breakdown={"retrieval_ms": 10.0, "total_ms": 12.0},
        )
        resp = self.client.post(
            "/ask",
            json={"question": "What is the standardized 5QI value for 7G holographic teleportation?"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "abstain")
        self.assertIsNone(data["answer"])
        self.assertEqual(data["citations"], [])
        self.assertIn("Evidence Sufficiency Gate rejected", data["reason"])

    # 9. Citations preserved with authoritative fields
    def test_09_citations_preserved_authoritatively(self):
        """Verify citations maintain exact clause and table metadata."""
        mock_evidence = [
            EvidenceItem(
                evidence_id="E1",
                chunk_id="TS_23_501_table_9",
                specification="TS 23.501",
                version="Rel-18",
                clause_number="5.7.1.3",
                clause_title="Standardized 5QI",
                breadcrumb=[],
                source_type="table",
                text="Table data",
                table_id="Table 5.7.1.3-1",
                table_caption="Standardized 5QI to QoS characteristics mapping",
            )
        ]
        mock_citation = Citation(
            evidence_id="E1",
            specification="TS 23.501",
            clause_number="5.7.1.3",
            clause_title="Standardized 5QI",
            table_id="Table 5.7.1.3-1",
            table_caption="Standardized 5QI to QoS characteristics mapping",
        )
        self.mock_service.ask.return_value = GenerationResult(
            status="answered",
            answer="5QI values are listed in Table 5.7.1.3-1.",
            citations=[mock_citation],
            evidence_items=mock_evidence,
        )
        resp = self.client.post("/ask", json={"question": "Where is 5QI mapped?"})
        data = resp.json()
        cit = data["citations"][0]
        self.assertEqual(cit["table_id"], "Table 5.7.1.3-1")
        self.assertEqual(cit["table_caption"], "Standardized 5QI to QoS characteristics mapping")
        self.assertIn("Standardized 5QI", cit["formatted_citation"])

    # 10. Internal errors sanitized (no stack traces / file paths)
    def test_10_internal_error_sanitization(self):
        """Verify unhandled exceptions return safe HTTP 500 without leaking stack traces or paths."""
        self.mock_service.ask.side_effect = RuntimeError("Private DB connection failure at C:\\secret\\path")
        resp = self.client.post("/ask", json={"question": "What is the SMF?"})
        self.assertEqual(resp.status_code, 500)
        data = resp.json()
        self.assertNotIn("secret", data["detail"])
        self.assertNotIn("Traceback", data["detail"])
        self.assertIn(data["error_code"], ["HTTP_500", "INTERNAL_SERVER_ERROR"])

    # 11. Metadata endpoint returns configuration
    def test_11_metadata_endpoint(self):
        """Verify GET /metadata exposes specifications and models."""
        self.mock_service.get_metadata.return_value = {
            "service": "3gpp-grounded-rag",
            "specifications": ["TS 23.501", "TS 23.502", "TS 24.501", "TS 28.535", "TS 38.300"],
            "total_chunks": 6737,
            "embedding_model": "nomic-embed-text",
            "generation_model": "qwen2.5:1.5b",
            "vector_store_collection": "telecom_3gpp_knowledge",
        }
        resp = self.client.get("/metadata")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["specifications"]), 5)
        self.assertEqual(data["total_chunks"], 6737)

    # 12. OpenAPI and Swagger UI documentation available
    def test_12_openapi_docs_accessible(self):
        """Verify /docs and /openapi.json are accessible."""
        resp_docs = self.client.get("/docs")
        self.assertEqual(resp_docs.status_code, 200)
        resp_openapi = self.client.get("/openapi.json")
        self.assertEqual(resp_openapi.status_code, 200)
        openapi_data = resp_openapi.json()
        self.assertIn("paths", openapi_data)
        self.assertIn("/ask", openapi_data["paths"])
        self.assertIn("/health", openapi_data["paths"])
        self.assertIn("/metadata", openapi_data["paths"])


if __name__ == "__main__":
    unittest.main()

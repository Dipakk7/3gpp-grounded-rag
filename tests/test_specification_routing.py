"""
Unit Test Suite for Fix #2: Specification-Aware Retrieval Routing.
Validates deterministic query parsing, multi-spec handling, boundary cases, and routing behavior.
"""

import unittest
from unittest.mock import MagicMock
from retrieval.router import parse_query_specifications
from retrieval.retriever import HybridRetriever, SemanticRetriever
from retrieval.bm25 import BM25Index
from retrieval.models import RetrievedChunk


class TestSpecificationRouting(unittest.TestCase):
    """Test suite covering deterministic 3GPP specification routing."""

    # 1. Detect TS 23.501
    def test_01_detect_ts_23_501(self):
        query = "What does TS 23.501 say about AMF functional responsibilities?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 23.501"])

    # 2. Detect TS 23.502
    def test_02_detect_ts_23_502(self):
        query = "Explain registration management procedures in TS 23.502."
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 23.502"])

    # 3. Detect TS 24.501
    def test_03_detect_ts_24_501(self):
        query = "What NAS security context handling is described in TS 24.501?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 24.501"])

    # 4. Detect TS 28.535
    def test_04_detect_ts_28_535(self):
        query = "What business-level functional requirements does TS 28.535 define for communication service assurance?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 28.535"])

    # 5. Detect TS 38.300
    def test_05_detect_ts_38_300(self):
        query = "How is NG-RAN architecture structured across user plane and control plane in TS 38.300?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 38.300"])

    # 6. Detect 3GPP prefix variant
    def test_06_detect_3gpp_ts_prefix(self):
        query = "According to 3GPP TS 28.535, what are closed control loop governance requirements?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 28.535"])

    # 7. Detect compressed TS prefix variant
    def test_07_detect_compressed_ts_prefix(self):
        query = "Check TS28.535 and TS38.300 specifications."
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 28.535", "TS 38.300"])

    # 8. Unscoped query returns empty list (no routing)
    def test_08_unscoped_query_no_routing(self):
        query = "What are the primary functional responsibilities of the AMF?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, [])

    # 9. Multiple specifications mentioned
    def test_09_multiple_specifications(self):
        query = "How does TS 23.501 relate to TS 23.502 for PDU session management?"
        specs = parse_query_specifications(query)
        self.assertEqual(specs, ["TS 23.501", "TS 23.502"])

    # 10. Non-spec numbers do not cause false positive detection
    def test_10_non_spec_numbers_no_false_positive(self):
        queries = [
            "What is the standardized 5QI value for 5G QoS in Clause 5.7.1.3?",
            "How many users can connect on port 501 or 502 with 23501 connections?",
            "Explain 38300 packet delay budget in milliseconds.",
        ]
        for q in queries:
            specs = parse_query_specifications(q)
            self.assertEqual(specs, [], f"Query '{q}' should not match any 3GPP specification.")

    # 11. Specification-aware retrieval filters candidates to target specification
    def test_11_hybrid_retriever_routes_to_target_spec(self):
        mock_semantic = MagicMock(spec=SemanticRetriever)
        mock_bm25 = MagicMock(spec=BM25Index)

        mock_semantic.retrieve.return_value = [
            RetrievedChunk(
                chunk_id="c1",
                specification="TS 28.535",
                document_title="Assurance",
                version="Rel-18",
                release="18",
                source_filename="28535.docx",
                clause_number="5.1.1",
                clause_title="Communication service assurance",
                breadcrumb=[],
                source_type="prose",
                document_order=1,
                text="REQ-CSA_NSA-FUN-01",
                content_hash="h1",
                score=0.9,
                rank=1,
            )
        ]
        mock_bm25.query.return_value = [
            RetrievedChunk(
                chunk_id="c1",
                specification="TS 28.535",
                document_title="Assurance",
                version="Rel-18",
                release="18",
                source_filename="28535.docx",
                clause_number="5.1.1",
                clause_title="Communication service assurance",
                breadcrumb=[],
                source_type="prose",
                document_order=1,
                text="REQ-CSA_NSA-FUN-01",
                content_hash="h1",
                score=0.95,
                rank=1,
            )
        ]

        retriever = HybridRetriever(semantic_retriever=mock_semantic, bm25_index=mock_bm25)
        query = "What business requirements does TS 28.535 define?"
        results = retriever.retrieve(query, top_k=1)

        # Verify router passed specification_filter='TS 28.535' to both sub-retrievers
        mock_semantic.retrieve.assert_called_once()
        _, sem_kwargs = mock_semantic.retrieve.call_args
        self.assertEqual(sem_kwargs.get("specification_filter"), "TS 28.535")

        mock_bm25.query.assert_called_once()
        _, bm_kwargs = mock_bm25.query.call_args
        self.assertEqual(bm_kwargs.get("specification_filter"), "TS 28.535")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].specification, "TS 28.535")

    # 12. Global retrieval unchanged for unscoped queries
    def test_12_hybrid_retriever_unscoped_query_global(self):
        mock_semantic = MagicMock(spec=SemanticRetriever)
        mock_bm25 = MagicMock(spec=BM25Index)
        mock_semantic.retrieve.return_value = []
        mock_bm25.query.return_value = []

        retriever = HybridRetriever(semantic_retriever=mock_semantic, bm25_index=mock_bm25)
        query = "What is the primary role of the AMF?"
        retriever.retrieve(query, top_k=5)

        # Verify specification_filter is None for unscoped queries
        _, sem_kwargs = mock_semantic.retrieve.call_args
        self.assertIsNone(sem_kwargs.get("specification_filter"))

        _, bm_kwargs = mock_bm25.query.call_args
        self.assertIsNone(bm_kwargs.get("specification_filter"))


if __name__ == "__main__":
    unittest.main()

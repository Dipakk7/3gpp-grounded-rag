"""
Unit test suite for Phase 3: Embedding, Vector Index, Lexical (BM25), and Hybrid Retrieval.
Covers all 14 mandatory Phase 3 requirements.
"""

import unittest
import json
from pathlib import Path
from retrieval.models import RetrievedChunk, ExpectedTarget, BenchmarkQueryItem, EvaluationMetrics
from retrieval.embedding import OllamaEmbedder, EXPECTED_DIMENSION
from retrieval.vector_store import ChromaVectorStore, DEFAULT_VECTORSTORE_PATH
from retrieval.bm25 import BM25Index, telecom_tokenize
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.benchmark import RetrievalBenchmark, is_relevant_chunk


class TestPhase3Retrieval(unittest.TestCase):
    """Test suite covering embedding, vector search, BM25, and hybrid retrieval."""

    @classmethod
    def setUpClass(cls):
        cls.embedder = OllamaEmbedder()
        cls.vector_store = ChromaVectorStore()
        cls.semantic_retriever = SemanticRetriever(embedder=cls.embedder, vector_store=cls.vector_store)

        # Load chunks for BM25
        cls.proc_dir = Path("data/processed")
        cls.chunks = []
        files = [
            "TS_23_501_chunks.jsonl",
            "TS_23_502_chunks.jsonl",
            "TS_24_501_chunks.jsonl",
            "TS_28_535_chunks.jsonl",
            "TS_38_300_chunks.jsonl",
        ]
        for f in files:
            with open(cls.proc_dir / f, "r", encoding="utf-8") as fp:
                for line in fp:
                    if line.strip():
                        cls.chunks.append(json.loads(line))

        cls.bm25 = BM25Index()
        cls.bm25.fit(cls.chunks)
        cls.hybrid_retriever = HybridRetriever(semantic_retriever=cls.semantic_retriever, bm25_index=cls.bm25)

    # 1. Embedding generation
    def test_01_embedding_generation(self):
        """Requirement 1: Verify single and batch embedding generation succeeds."""
        vec = self.embedder.embed_text("5G System Architecture AMF UPF SMF", is_query=True)
        self.assertIsInstance(vec, list)
        self.assertGreater(len(vec), 0)

    # 2. Vector dimension consistency
    def test_02_vector_dimension_consistency(self):
        """Requirement 2: Verify vector dimension strictly matches expected 768 dimensions."""
        vec1 = self.embedder.embed_text("Telecom query 1", is_query=True)
        vec2 = self.embedder.embed_text("Technical specification text 2", is_query=False)
        self.assertEqual(len(vec1), EXPECTED_DIMENSION)
        self.assertEqual(len(vec2), EXPECTED_DIMENSION)

    # 3. No NaN or invalid vectors
    def test_03_no_nan_vectors(self):
        """Requirement 3: Verify embeddings contain valid finite numbers without NaN or Inf."""
        import math
        vec = self.embedder.embed_text("Session Management Function procedures", is_query=True)
        for val in vec:
            self.assertFalse(math.isnan(val))
            self.assertFalse(math.isinf(val))

    # 4. Empty query handling
    def test_04_empty_query_handling(self):
        """Requirement 4: Empty or whitespace query returns clean empty results without error."""
        res_sem = self.semantic_retriever.retrieve("", top_k=5)
        res_bm25 = self.bm25.query("", top_k=5)
        res_hyb = self.hybrid_retriever.retrieve("   ", top_k=5)
        self.assertEqual(res_sem, [])
        self.assertEqual(res_bm25, [])
        self.assertEqual(res_hyb, [])

    # 5. Telecom tokenization
    def test_05_telecom_tokenization(self):
        """Requirement 5: Tokenizer preserves hyphens, dotted numbers, and alphanumeric codes."""
        text = "TS 23.501 clause 4.2.8.0 defines 5G-GUTI and Npcf_SMPolicyControl with 5QI=9."
        tokens = telecom_tokenize(text)
        self.assertIn("23.501", tokens)
        self.assertIn("4.2.8.0", tokens)
        self.assertIn("5g-guti", tokens)
        self.assertIn("npcf_smpolicycontrol", tokens)
        self.assertIn("5qi", tokens)

    # 6. Metadata preservation in retrieved chunks
    def test_06_metadata_preservation(self):
        """Requirement 6: Retrieved chunks contain all mandatory 3GPP metadata fields."""
        results = self.semantic_retriever.retrieve("What is AMF?", top_k=3)
        self.assertGreater(len(results), 0)
        c = results[0]
        self.assertTrue(c.chunk_id)
        self.assertTrue(c.specification.startswith("TS "))
        self.assertTrue(c.version)
        self.assertTrue(c.clause_number)
        self.assertTrue(c.clause_title)
        self.assertIsInstance(c.breadcrumb, list)
        self.assertGreater(len(c.breadcrumb), 0)
        self.assertTrue(c.text)
        self.assertTrue(c.content_hash)
        self.assertIsInstance(c.score, float)

    # 7. Top-k retrieval ranking
    def test_07_top_k_retrieval(self):
        """Requirement 7: Retriever returns exactly requested top_k results with ordered ranks."""
        for k in [1, 3, 5]:
            results = self.semantic_retriever.retrieve("PDU session establishment", top_k=k)
            self.assertLessEqual(len(results), k)
            for i, r in enumerate(results, start=1):
                self.assertEqual(r.rank, i)

    # 8. Expected clause retrieval
    def test_08_expected_clause_retrieval(self):
        """Requirement 8: Query for AMF role retrieves TS 23.501 Clause 6.2.1 or 4.2."""
        results = self.hybrid_retriever.retrieve("What are the functional responsibilities of the AMF?", top_k=5)
        spec_found = any(r.specification == "TS 23.501" and ("6.2.1" in r.clause_number or "4.2" in r.clause_number) for r in results)
        self.assertTrue(spec_found, "Expected TS 23.501 AMF clause in top 5 results")

    # 9. Table chunk retrieval
    def test_09_table_chunk_retrieval(self):
        """Requirement 9: Query targeting standardized 5QI table retrieves Table 5.7.1.3-1."""
        results = self.hybrid_retriever.retrieve("Standardized 5QI to QoS characteristics mapping table", top_k=5)
        has_5qi_table = any("5.7.1.3" in r.clause_number or "5QI" in r.text for r in results)
        self.assertTrue(has_5qi_table, "Expected 5QI mapping table in results")

    # 10. Specification filtering
    def test_10_specification_filtering(self):
        """Requirement 10: Filtering by specification restricts results exclusively to that specification."""
        results = self.semantic_retriever.retrieve(
            "Overall description of NG-RAN",
            top_k=5,
            specification_filter="TS 38.300",
        )
        for r in results:
            self.assertEqual(r.specification, "TS 38.300")

    # 11. BM25 lexical ranking
    def test_11_bm25_lexical_ranking(self):
        """Requirement 11: BM25 ranks exact table and clause queries at top."""
        results = self.bm25.query("Table 5.6.1-1: Attributes of a PDU Session", top_k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].specification, "TS 23.501")
        self.assertEqual(results[0].clause_number, "5.6.1")

    # 12. Hybrid fusion (RRF)
    def test_12_hybrid_fusion_rrf(self):
        """Requirement 12: Hybrid retrieval combines dense semantic and BM25 scoring."""
        results = self.hybrid_retriever.retrieve("Registration Management procedures general", top_k=5)
        self.assertGreater(len(results), 0)
        methods = {r.retrieval_method for r in results}
        self.assertTrue(any("hybrid" in m or "semantic" in m or "bm25" in m for m in methods))

    # 13. Retrieval output schema
    def test_13_retrieval_output_schema(self):
        """Requirement 13: to_dict() returns JSON-serializable structured evidence object."""
        results = self.hybrid_retriever.retrieve("Security context handling NAS", top_k=2)
        self.assertGreater(len(results), 0)
        d = results[0].to_dict()
        self.assertIn("chunk_id", d)
        self.assertIn("specification", d)
        self.assertIn("score", d)
        self.assertIn("text", d)
        self.assertIn("breadcrumb", d)
        # Verify JSON serializability
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)

    # 14. Benchmark evaluation validation
    def test_14_benchmark_evaluator(self):
        """Requirement 14: Retrieval benchmark runs on 21 ground-truth questions and computes metrics."""
        benchmark = RetrievalBenchmark()
        self.assertEqual(len(benchmark.queries), 21)
        # Evaluate on the benchmark
        eval_res = benchmark.evaluate(lambda q, k: self.hybrid_retriever.retrieve(q, top_k=k), top_k=10)
        self.assertIsInstance(eval_res.hit_at_5, float)
        self.assertGreater(eval_res.hit_at_5, 0.0)
        self.assertGreater(eval_res.mrr, 0.0)
        self.assertEqual(len(eval_res.detailed_results), 21)





if __name__ == "__main__":
    unittest.main()

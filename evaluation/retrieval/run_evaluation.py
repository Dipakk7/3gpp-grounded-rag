"""
Retrieval Evaluation Runner:
Executes benchmark against:
1. Semantic Retriever (Dense Vector)
2. BM25 Lexical Retriever
3. Hybrid Retriever (Dense + BM25 via Reciprocal Rank Fusion)
Measures Hit@1, Hit@3, Hit@5, Hit@10, MRR, and component latencies.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure project root in sys.path
ROOT_PATH = Path(__file__).resolve().parent.parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.benchmark import RetrievalBenchmark
from retrieval.index_corpus import load_all_chunks


def run_full_evaluation() -> Dict[str, Any]:
    print("=== Loading Corpus & Retrieval Engines ===")
    chunks = load_all_chunks()
    print(f"Loaded {len(chunks)} chunks for BM25 and context validation.")

    # Initialize components
    embedder = OllamaEmbedder()
    vector_store = ChromaVectorStore()
    indexed_count = vector_store.count()
    print(f"Vector store connected with {indexed_count} indexed chunks.")

    bm25 = BM25Index()
    bm25.fit(chunks)
    print(f"BM25 index ready with {bm25.num_docs} documents.")

    semantic_retriever = SemanticRetriever(embedder=embedder, vector_store=vector_store)
    hybrid_retriever = HybridRetriever(semantic_retriever=semantic_retriever, bm25_index=bm25)

    benchmark = RetrievalBenchmark()
    print(f"Loaded benchmark with {len(benchmark.queries)} ground-truth questions.")

    # 1. Semantic Baseline Evaluation
    print("\n--- Running Semantic Baseline Evaluation ---")
    semantic_eval = benchmark.evaluate(
        retriever_fn=lambda q, k: semantic_retriever.retrieve(q, top_k=k),
        top_k=10,
    )
    print(f"Semantic Baseline: Hit@1={semantic_eval.hit_at_1*100:.1f}%, Hit@3={semantic_eval.hit_at_3*100:.1f}%, Hit@5={semantic_eval.hit_at_5*100:.1f}%, Hit@10={semantic_eval.hit_at_10*100:.1f}%, MRR={semantic_eval.mrr:.4f}")

    # 2. BM25 Lexical Evaluation
    print("\n--- Running BM25 Lexical Evaluation ---")
    bm25_eval = benchmark.evaluate(
        retriever_fn=lambda q, k: bm25.query(q, top_k=k),
        top_k=10,
    )
    print(f"BM25 Lexical: Hit@1={bm25_eval.hit_at_1*100:.1f}%, Hit@3={bm25_eval.hit_at_3*100:.1f}%, Hit@5={bm25_eval.hit_at_5*100:.1f}%, Hit@10={bm25_eval.hit_at_10*100:.1f}%, MRR={bm25_eval.mrr:.4f}")

    # 3. Hybrid Evaluation (Dense + BM25 RRF)
    print("\n--- Running Hybrid Evaluation (Dense + BM25 RRF) ---")
    hybrid_eval = benchmark.evaluate(
        retriever_fn=lambda q, k: hybrid_retriever.retrieve(q, top_k=k),
        top_k=10,
    )
    print(f"Hybrid RRF: Hit@1={hybrid_eval.hit_at_1*100:.1f}%, Hit@3={hybrid_eval.hit_at_3*100:.1f}%, Hit@5={hybrid_eval.hit_at_5*100:.1f}%, Hit@10={hybrid_eval.hit_at_10*100:.1f}%, MRR={hybrid_eval.mrr:.4f}")

    # 4. Latency Benchmarking (Averaged over 10 iterations of 3 distinct telecom queries)
    print("\n--- Running Latency Benchmarks ---")
    sample_queries = [
        "What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?",
        "What are the standardized 5QI characteristics and QoS packet delay budgets defined in 5GS?",
        "What behavior is specified in the table for change of UE usage setting in single-registration mode?",
    ]

    lat_emb = []
    lat_vec = []
    lat_bm25 = []
    lat_hybrid = []

    for sq in sample_queries:
        for _ in range(3):
            # Query embedding latency
            t0 = time.time()
            q_emb = embedder.embed_text(sq, is_query=True)
            t1 = time.time()
            lat_emb.append((t1 - t0) * 1000)

            # Vector search latency
            t0 = time.time()
            vector_store.query(q_emb, top_k=5)
            t1 = time.time()
            lat_vec.append((t1 - t0) * 1000)

            # BM25 latency
            t0 = time.time()
            bm25.query(sq, top_k=5)
            t1 = time.time()
            lat_bm25.append((t1 - t0) * 1000)

            # Full hybrid latency
            t0 = time.time()
            hybrid_retriever.retrieve(sq, top_k=5)
            t1 = time.time()
            lat_hybrid.append((t1 - t0) * 1000)

    avg_emb_ms = sum(lat_emb) / len(lat_emb)
    avg_vec_ms = sum(lat_vec) / len(lat_vec)
    avg_bm25_ms = sum(lat_bm25) / len(lat_bm25)
    avg_hybrid_ms = sum(lat_hybrid) / len(lat_hybrid)

    print(f"Latency Results (ms):")
    print(f"  Query Embedding: {avg_emb_ms:.2f} ms")
    print(f"  Vector Search:   {avg_vec_ms:.2f} ms")
    print(f"  BM25 Search:     {avg_bm25_ms:.2f} ms")
    print(f"  Total Hybrid:    {avg_hybrid_ms:.2f} ms")

    results_data = {
        "benchmark_queries_count": len(benchmark.queries),
        "corpus_total_chunks": len(chunks),
        "indexed_chunks_chromadb": indexed_count,
        "semantic_baseline": semantic_eval.to_dict(),
        "bm25_lexical": bm25_eval.to_dict(),
        "hybrid_rrf": hybrid_eval.to_dict(),
        "latency_ms": {
            "query_embedding_avg_ms": round(avg_emb_ms, 2),
            "vector_search_avg_ms": round(avg_vec_ms, 2),
            "bm25_search_avg_ms": round(avg_bm25_ms, 2),
            "total_hybrid_avg_ms": round(avg_hybrid_ms, 2),
        },
    }

    out_file = ROOT_PATH / "evaluation" / "retrieval" / "retrieval_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\nSaved evaluation metrics to {out_file}")
    return results_data



if __name__ == "__main__":
    run_full_evaluation()

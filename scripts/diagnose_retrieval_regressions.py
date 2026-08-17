"""
Phase 7B — Retrieval Regression Deep Diagnostic Script
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.router import parse_query_specifications
from retrieval.benchmark import is_relevant_chunk
from retrieval.index_corpus import load_all_chunks

FAILED_QIDS = ["R004", "R005", "R007", "R009", "R010", "R012", "R020"]

def run_diagnostic():
    print("=== Loading Corpus & Initializing Retrievers ===")
    all_chunks = load_all_chunks()
    store = ChromaVectorStore()
    embedder = OllamaEmbedder()
    bm25 = BM25Index()
    bm25.fit(all_chunks)

    sem_retriever = SemanticRetriever(embedder=embedder, vector_store=store)
    hybrid_retriever = HybridRetriever(semantic_retriever=sem_retriever, bm25_index=bm25)

    with open(ROOT_PATH / "evaluation" / "retrieval" / "retrieval_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_queries = [q for q in dataset if q["id"] in FAILED_QIDS]

    results_report = {}

    for qitem in target_queries:
        qid = qitem["id"]
        qtext = qitem["question"]
        expected = qitem["expected"]

        print(f"\n{'='*80}")
        print(f"DIAGNOSTIC FOR {qid}: {qtext}")
        print(f"Expected: {expected}")
        print(f"{'='*80}")

        # Routing check
        detected_specs = parse_query_specifications(qtext)
        has_spec_ident = len(detected_specs) > 0
        routing_triggered = has_spec_ident
        active_filter = None
        if len(detected_specs) == 1:
            active_filter = detected_specs[0]
        elif len(detected_specs) > 1:
            active_filter = detected_specs

        print(f"Explicit Spec Identifier in Query: {has_spec_ident} (Detected: {detected_specs})")
        print(f"Routing Triggered: {routing_triggered} (Active Filter: {active_filter})")

        # Dense-only evaluation (up to 50)
        dense_candidates = sem_retriever.retrieve(qtext, top_k=50, specification_filter=active_filter)
        dense_first_rank = None
        for r, c in enumerate(dense_candidates, 1):
            if is_relevant_chunk(c, expected):
                dense_first_rank = r
                break

        # BM25-only evaluation (up to 50)
        bm25_candidates = bm25.query(qtext, top_k=50, specification_filter=active_filter)
        bm25_first_rank = None
        for r, c in enumerate(bm25_candidates, 1):
            if is_relevant_chunk(c, expected):
                bm25_first_rank = r
                break

        # Hybrid RRF (top 20)
        hybrid_candidates = hybrid_retriever.retrieve(qtext, top_k=20, specification_filter=active_filter)
        hybrid_first_rank = None
        for r, c in enumerate(hybrid_candidates, 1):
            if is_relevant_chunk(c, expected):
                hybrid_first_rank = r
                break

        # Detailed mapping of dense & bm25 for candidate pool
        # Inspect top 10 hybrid
        print(f"\n--- Subsystem First Relevant Rank ---")
        print(f"  Dense-only (top 50):   Rank {dense_first_rank}")
        print(f"  BM25-only (top 50):    Rank {bm25_first_rank}")
        print(f"  Hybrid RRF (top 20):   Rank {hybrid_first_rank}")

        print(f"\n--- Top 10 Hybrid Results ---")
        print(f"{'Rank':<5} | {'Chunk ID':<33} | {'Spec':<9} | {'Clause':<12} | {'Dense(R/S)':<16} | {'BM25(R/S)':<16} | {'RRF':<7} | {'Rel?'}")
        print("-" * 115)

        # Dense map for rank & score
        dense_map = {c.chunk_id: (i+1, c.score) for i, c in enumerate(dense_candidates)}
        bm25_map = {c.chunk_id: (i+1, c.score) for i, c in enumerate(bm25_candidates)}

        for r, c in enumerate(hybrid_candidates[:10], 1):
            d_info = f"#{dense_map[c.chunk_id][0]} ({dense_map[c.chunk_id][1]:.3f})" if c.chunk_id in dense_map else "None"
            b_info = f"#{bm25_map[c.chunk_id][0]} ({bm25_map[c.chunk_id][1]:.3f})" if c.chunk_id in bm25_map else "None"
            is_rel = is_relevant_chunk(c, expected)
            rel_str = "YES (TARGET)" if is_rel else "NO"
            print(f"{r:<5} | {c.chunk_id:<33} | {c.specification:<9} | {c.clause_number:<12} | {d_info:<16} | {b_info:<16} | {c.score:<7.4f} | {rel_str}")
            print(f"      Title: {c.clause_title}")

        # Check ranks 11-20
        print(f"\n--- Ranks 11-20 Hybrid Results ---")
        for r, c in enumerate(hybrid_candidates[10:20], 11):
            d_info = f"#{dense_map[c.chunk_id][0]}" if c.chunk_id in dense_map else "None"
            b_info = f"#{bm25_map[c.chunk_id][0]}" if c.chunk_id in bm25_map else "None"
            is_rel = is_relevant_chunk(c, expected)
            rel_str = "YES (TARGET)" if is_rel else "NO"
            print(f"  #{r:<2} | {c.chunk_id} | {c.specification} §{c.clause_number} | Dense: {d_info}, BM25: {b_info} | Rel: {rel_str}")

        # Check where the expected target chunk actually is in all_chunks
        target_chunks_in_corpus = []
        for target in expected:
            t_spec = target["specification"]
            t_clause = target["clause_number"]
            for c in all_chunks:
                if c.get("specification") == t_spec and (c.get("clause_number") == t_clause or c.get("clause_number", "").startswith(f"{t_clause}.")):
                    target_chunks_in_corpus.append(c)

        print(f"\n--- Corpus Check for Expected Target ---")
        print(f"  Target chunks matching in corpus: {len(target_chunks_in_corpus)}")
        for tc in target_chunks_in_corpus[:3]:
            cid = tc["chunk_id"]
            d_rank = dense_map.get(cid, ("Not in top 50", 0))[0]
            b_rank = bm25_map.get(cid, ("Not in top 50", 0))[0]
            print(f"  Target Chunk: {cid} (§{tc.get('clause_number')} {tc.get('clause_title')}) -> Dense Rank: {d_rank}, BM25 Rank: {b_rank}")

        # Check cross-specification competition
        specs_in_top10 = [c.specification for c in hybrid_candidates[:10]]
        expected_spec_set = {t["specification"] for t in expected}
        cross_spec_count = sum(1 for s in specs_in_top10 if s not in expected_spec_set)
        new_specs_present = [s for s in specs_in_top10 if s in ["TS 24.501", "TS 28.535", "TS 38.300"] and s not in expected_spec_set]

        print(f"\n--- Specification Competition in Top 10 ---")
        print(f"  Expected specification: {expected_spec_set}")
        print(f"  Top 10 specifications: {specs_in_top10}")
        print(f"  Foreign specifications in top 10: {cross_spec_count}/10")
        print(f"  Newly added specs competing: {new_specs_present}")

if __name__ == "__main__":
    run_diagnostic()

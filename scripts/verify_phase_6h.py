"""
Phase 6H Independent Verification & Targeted Retrieval Checks
"""

import json
import sys
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.index_corpus import load_all_chunks

def run_verification():
    print("=================================================================")
    print("PHASE 6H INDEPENDENT VERIFICATION & TARGETED CHECKS")
    print("=================================================================")

    # 1. Total Processed Chunks
    all_chunks = load_all_chunks()
    total_processed = len(all_chunks)
    print(f"Total processed chunks: {total_processed}")

    # 2. Chroma Vector Store Verification
    store = ChromaVectorStore()
    total_chroma = store.count()
    print(f"Total Chroma vectors: {total_chroma}")

    # Inspect all records metadata
    results = store.collection.get(include=["metadatas"])
    ids = results["ids"]
    metas = results["metadatas"]

    unique_ids = set(ids)
    duplicate_count = len(ids) - len(unique_ids)
    missing_vectors = total_processed - total_chroma

    spec_counts = {}
    missing_meta = 0
    for meta in metas:
        spec = meta.get("specification", "")
        if not spec:
            missing_meta += 1
        spec_counts[spec] = spec_counts.get(spec, 0) + 1

    expected_specs = {
        "TS 23.501": 1437,
        "TS 23.502": 1719,
        "TS 24.501": 2968,
        "TS 28.535": 39,
        "TS 38.300": 574,
    }

    print("\nChroma Vector Counts by Specification:")
    all_specs_match = True
    for spec, expected_n in expected_specs.items():
        actual_n = spec_counts.get(spec, 0)
        match_str = "MATCH" if actual_n == expected_n else f"MISMATCH (expected {expected_n})"
        if actual_n != expected_n:
            all_specs_match = False
        print(f"  {spec}: {actual_n} ({match_str})")

    print(f"\nMissing vectors: {missing_vectors}")
    print(f"Duplicate IDs: {duplicate_count}")
    print(f"Missing specification metadata: {missing_meta}")

    # 3. Test Metadata Filtering for all five specifications
    print("\n--- Testing Metadata Filtering for All 5 Specifications ---")
    dummy_emb = [0.0] * 768
    filter_all_pass = True
    for s in expected_specs.keys():
        res = store.query(dummy_emb, top_k=5, where_filter={"specification": s})
        res_specs = {c.specification for c in res}
        passed = (len(res) > 0) and (res_specs == {s})
        if not passed:
            filter_all_pass = False
        print(f"  Filter '{s}': returned {len(res)} chunks, specs present: {res_specs} -> {'PASS' if passed else 'FAIL'}")
    print(f"Metadata filter tests: {'ALL PASS' if filter_all_pass else 'FAIL'}")

    # 4. Setup Retrievers for Targeted Retrieval Checks
    bm25 = BM25Index()
    bm25.fit(all_chunks)
    sem_retriever = SemanticRetriever(vector_store=store)
    hybrid_retriever = HybridRetriever(semantic_retriever=sem_retriever, bm25_index=bm25)

    # 5. Targeted Checks: G007, G019, G020
    target_questions = [
        {
            "id": "G007",
            "question": "What business-level functional requirements does TS 28.535 define for communication service assurance?",
            "expected_clauses": ["5.1.1"],
            "expected_specs": ["TS 28.535"],
        },
        {
            "id": "G019",
            "question": "What does TS 28.535 specify about closed control loops and their governance?",
            "expected_clauses": ["4.2.4", "4.2.5.2"],
            "expected_specs": ["TS 28.535"],
        },
        {
            "id": "G020",
            "question": "How are NG-RAN architecture and NG interface protocols structured across user plane and control plane in TS 38.300?",
            "expected_clauses": ["4.3.1.1", "4.3.1.2"],
            "expected_specs": ["TS 38.300"],
        },
    ]

    print("\n--- Targeted Retrieval Checks ---")
    for item in target_questions:
        qid = item["id"]
        q = item["question"]
        clauses = item["expected_clauses"]
        specs = item["expected_specs"]

        print(f"\n==========================================")
        print(f"Target: {qid}")
        print(f"Question: {q}")
        print(f"Expected Clauses: {clauses} in {specs}")
        print(f"==========================================")

        # 1. Semantic / Dense (unfiltered & filtered)
        dense_results = sem_retriever.retrieve(q, top_k=10)
        dense_rank = None
        for r, chunk in enumerate(dense_results, 1):
            if chunk.specification in specs and any(chunk.clause_number.startswith(c) for c in clauses):
                dense_rank = r
                break

        # 2. BM25
        bm25_results = bm25.query(q, top_k=10)
        bm25_rank = None
        for r, chunk in enumerate(bm25_results, 1):
            if chunk.specification in specs and any(chunk.clause_number.startswith(c) for c in clauses):
                bm25_rank = r
                break

        # 3. Hybrid
        hybrid_results = hybrid_retriever.retrieve(q, top_k=5)
        hybrid_rank = None
        for r, chunk in enumerate(hybrid_results, 1):
            if chunk.specification in specs and any(chunk.clause_number.startswith(c) for c in clauses):
                hybrid_rank = r
                break

        print(f"Dense First Relevant Rank: {dense_rank} | Hit: {'YES' if dense_rank is not None else 'NO'}")
        print(f"BM25 First Relevant Rank: {bm25_rank} | Hit: {'YES' if bm25_rank is not None else 'NO'}")
        print(f"Hybrid First Relevant Rank: {hybrid_rank} | Within Top 5: {'YES' if hybrid_rank is not None and hybrid_rank <= 5 else 'NO'}")

        print("\nTop 5 Hybrid Chunks:")
        for r, chunk in enumerate(hybrid_results, 1):
            is_rel = chunk.specification in specs and any(chunk.clause_number.startswith(c) for c in clauses)
            rel_mark = " [RELEVANT TARGET]" if is_rel else ""
            print(f"  #{r}: [{chunk.specification} §{chunk.clause_number}] {chunk.clause_title} (score: {chunk.score:.4f}, method: {chunk.retrieval_method}){rel_mark}")

if __name__ == "__main__":
    run_verification()

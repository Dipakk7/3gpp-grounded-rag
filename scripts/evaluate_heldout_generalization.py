"""
Held-out evaluation script for Phase 7G.
Tests 6 new independent questions against the CURRENT Fix #3 production HybridRetriever.
DOES NOT MODIFY ANY PRODUCTION CODE OR BENCHMARK FILES.
"""

import sys
import json
from pathlib import Path

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

HELDOUT_DATASET = [
    # Category A: Definition / Terminology
    {
        "id": "H001",
        "category": "Definition / Terminology",
        "question": "What definitions are specified for Network Slice and PDU Session in 5G system architecture?",
        "expected": [{"specification": "TS 23.501", "clause_number": "3.1"}],
        "source_docx": "23501-ic0.docx",
        "heading": "3.1 Definitions",
        "reason": "TS 23.501 Clause 3.1 defines architectural terms including Network Slice and PDU Session."
    },
    {
        "id": "H002",
        "category": "Definition / Terminology",
        "question": "What definitions are provided for gNB and ng-eNB nodes in the NG-RAN overall architecture?",
        "expected": [{"specification": "TS 38.300", "clause_number": "3.2"}],
        "source_docx": "38300-ia0.docx",
        "heading": "3.2 Definitions",
        "reason": "TS 38.300 Clause 3.2 defines NG-RAN node types including gNB and ng-eNB."
    },
    # Category B: Procedural / Step-by-Step
    {
        "id": "H003",
        "category": "Procedural / Step-by-Step",
        "question": "What are the procedural steps for UE-initiated Deregistration in the 5G System?",
        "expected": [{"specification": "TS 23.502", "clause_number": "4.2.2.3.2"}],
        "source_docx": "23502-ie0.docx",
        "heading": "4.2.2.3.2 UE-initiated Deregistration",
        "reason": "TS 23.502 Clause 4.2.2.3.2 specifies the call flow steps 1 to 5 for UE-initiated deregistration."
    },
    {
        "id": "H004",
        "category": "Procedural / Step-by-Step",
        "question": "What procedural steps are executed during a UE Triggered Service Request in the 5G System?",
        "expected": [{"specification": "TS 23.502", "clause_number": "4.2.3.2"}],
        "source_docx": "23502-ie0.docx",
        "heading": "4.2.3.2 UE Triggered Service Request",
        "reason": "TS 23.502 Clause 4.2.3.2 defines the procedure steps 1 to 22 for UE-triggered service requests."
    },
    # Category C: Description / Overview
    {
        "id": "H005",
        "category": "Description / Overview",
        "question": "How are the 5GS Registration Management states described and modeled for the UE and AMF?",
        "expected": [{"specification": "TS 23.501", "clause_number": "5.3.2.2"}],
        "source_docx": "23501-ic0.docx",
        "heading": "5.3.2.2 5GS Registration Management states",
        "reason": "TS 23.501 Clause 5.3.2.2 provides the architectural description and state models for RM-DEREGISTERED and RM-REGISTERED."
    },
    {
        "id": "H006",
        "category": "Description / Overview",
        "question": "How is the Layer 2 protocol stack overview and functional structure described in NR?",
        "expected": [{"specification": "TS 38.300", "clause_number": "6.1"}],
        "source_docx": "38300-ia0.docx",
        "heading": "6.1 Overview",
        "reason": "TS 38.300 Clause 6.1 describes the Layer 2 architecture overview covering SDAP, PDCP, RLC, and MAC."
    }
]

def evaluate_heldout():
    all_chunks = load_all_chunks()
    store = ChromaVectorStore()
    embedder = OllamaEmbedder()
    bm25 = BM25Index()
    bm25.fit(all_chunks)
    sem = SemanticRetriever(embedder=embedder, vector_store=store)
    hybrid = HybridRetriever(semantic_retriever=sem, bm25_index=bm25)

    print("=== EXECUTING PHASE 7G HELD-OUT GENERALIZATION VALIDATION ===\n")

    results = []
    cat_counts = {"Definition / Terminology": {"hit5": 0, "total": 0},
                  "Procedural / Step-by-Step": {"hit5": 0, "total": 0},
                  "Description / Overview": {"hit5": 0, "total": 0}}

    h1_total = 0
    h3_total = 0
    h5_total = 0

    for item in HELDOUT_DATASET:
        qid = item["id"]
        cat = item["category"]
        qtext = item["question"]
        expected = item["expected"]

        # 1. Dense retrieval
        dense_chunks = sem.retrieve(query=qtext, top_k=20)
        dense_rank = None
        for r, c in enumerate(dense_chunks, 1):
            if is_relevant_chunk(c, expected):
                dense_rank = r
                break

        # 2. BM25 retrieval
        bm25_chunks = bm25.query(query_text=qtext, top_k=20)
        bm25_rank = None
        for r, c in enumerate(bm25_chunks, 1):
            if is_relevant_chunk(c, expected):
                bm25_rank = r
                break

        # 3. Hybrid RRF retrieval (Production top_k=5)
        hybrid_chunks = hybrid.retrieve(query=qtext, top_k=5)
        hybrid_rank = None
        for r, c in enumerate(hybrid_chunks, 1):
            if is_relevant_chunk(c, expected):
                hybrid_rank = r
                break

        h1 = hybrid_rank == 1
        h3 = hybrid_rank is not None and hybrid_rank <= 3
        h5 = hybrid_rank is not None and hybrid_rank <= 5

        if h1: h1_total += 1
        if h3: h3_total += 1
        if h5: h5_total += 1

        cat_counts[cat]["total"] += 1
        if h5:
            cat_counts[cat]["hit5"] += 1

        detected_specs = parse_query_specifications(qtext)
        routed = len(detected_specs) > 0

        res = {
            "id": qid,
            "category": cat,
            "question": qtext,
            "expected_spec": expected[0]["specification"],
            "expected_clause": expected[0]["clause_number"],
            "first_relevant_rank": hybrid_rank,
            "hit@1": h1,
            "hit@3": h3,
            "hit@5": h5,
            "routed": routed,
            "detected_specs": detected_specs,
            "dense_rank": dense_rank,
            "bm25_rank": bm25_rank,
            "hybrid_rank": hybrid_rank,
            "source_docx": item["source_docx"],
            "heading": item["heading"],
            "reason": item["reason"]
        }
        results.append(res)

        print(f"[{qid}] Category: {cat}")
        print(f"  Question:        \"{qtext}\"")
        print(f"  Expected:        {expected[0]['specification']} §{expected[0]['clause_number']} ({item['heading']})")
        print(f"  Dense Rank:      {dense_rank}")
        print(f"  BM25 Rank:       {bm25_rank}")
        print(f"  Hybrid Rank:     {hybrid_rank}")
        print(f"  Hit@1 / 3 / 5:   {h1} / {h3} / {h5}")
        print(f"  Routing:         {routed} ({detected_specs})")
        print()

    n = len(HELDOUT_DATASET)
    print("=== SUMMARY METRICS ===")
    print(f"Held-out Hit@1: {h1_total}/{n} ({h1_total/n*100:.1f}%)")
    print(f"Held-out Hit@3: {h3_total}/{n} ({h3_total/n*100:.1f}%)")
    print(f"Held-out Hit@5: {h5_total}/{n} ({h5_total/n*100:.1f}%)")
    print()
    print("Category Breakdown (Hit@5):")
    for cat, data in cat_counts.items():
        print(f"  {cat}: {data['hit5']}/{data['total']}")

    with open("evaluation/retrieval/heldout_results.json", "w", encoding="utf-8") as f:
        json.dump({"summary": {"hit@1": h1_total/n, "hit@3": h3_total/n, "hit@5": h5_total/n, "category_counts": cat_counts}, "details": results}, f, indent=2)

if __name__ == "__main__":
    evaluate_heldout()

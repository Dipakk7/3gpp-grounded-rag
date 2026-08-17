import sys
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.index_corpus import load_all_chunks
from generation.evidence import chunks_to_evidence_items

def trace_diagnostic():
    chunks = load_all_chunks()
    emb = OllamaEmbedder()
    vs = ChromaVectorStore()
    bm = BM25Index()
    bm.fit(chunks)
    sem = SemanticRetriever(emb, vs)
    hyb = HybridRetriever(sem, bm)

    queries = [
        ("G007", "What business-level functional requirements does TS 28.535 define for communication service assurance?", "TS 28.535", ["5.1.1"]),
        ("G019", "What does TS 28.535 specify about closed control loops and their governance?", "TS 28.535", ["4.2.4", "4.2.4.1", "4.2.4.2", "4.2.5.2"]),
        ("G020", "How are NG-RAN architecture and NG interface protocols structured across user plane and control plane in TS 38.300?", "TS 38.300", ["4.3.1.1", "4.3.1.2"]),
    ]

    for qid, qtext, exp_spec, exp_clauses in queries:
        print(f"\n=======================================================")
        print(f"TRACE FOR {qid}")
        print(f"Question: '{qtext}'")
        print(f"Target: {exp_spec} Clause(s): {exp_clauses}")
        print(f"=======================================================")

        # 1. Retrieve top 10
        retrieved_10 = hyb.retrieve(qtext, top_k=10)
        print(f"\n--- Ranked Retrieved Chunks (Top 10) ---")
        print(f"Total retrieved chunks (top_k=10): {len(retrieved_10)}")
        for rank, r in enumerate(retrieved_10, start=1):
            is_relevant = (r.specification == exp_spec and any(c in r.clause_number for c in exp_clauses))
            rel_str = " -> [RELEVANT GROUND TRUTH]" if is_relevant else ""
            print(f"Rank {rank:2d} | {r.specification:9s} | Clause {r.clause_number:10s} | {r.chunk_id} | Title: '{r.clause_title}'{rel_str}")

        # 2. Top-5 default pipeline trace
        retrieved_5 = hyb.retrieve(qtext, top_k=5)
        evidence_5 = chunks_to_evidence_items(retrieved_5)
        print(f"\n--- Production Default Pipeline Trace (top_k=5) ---")
        print(f"Retrieved candidate count: {len(retrieved_5)}")
        print(f"EvidenceItems created: {len(evidence_5)}")
        evidence_ids_5 = [e.evidence_id for e in evidence_5]
        print(f"Evidence IDs passed to generator: {evidence_ids_5}")
        
        has_target_in_5 = any(
            e.specification == exp_spec and any(c in e.clause_number for c in exp_clauses)
            for e in evidence_5
        )
        print(f"Target evidence present in top_k=5 generator context: {has_target_in_5}")
        if not has_target_in_5:
            first_rel_rank = next((rank for rank, r in enumerate(retrieved_10, start=1) if r.specification == exp_spec and any(c in r.clause_number for c in exp_clauses)), None)
            print(f"EXACT DROP POINT: Target evidence appears at rank {first_rel_rank}, but top_k=5 slices candidates to top 5, dropping rank {first_rel_rank} before EvidenceItem creation.")

if __name__ == "__main__":
    trace_diagnostic()

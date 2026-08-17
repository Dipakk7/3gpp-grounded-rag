import sys
import json
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.router import parse_query_specifications
from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.index_corpus import load_all_chunks

def run_diagnostic():
    query = "What business-level functional requirements does TS 28.535 define for communication service assurance?"
    print("=================================================================")
    print("PHASE 6D DIAGNOSTIC: G007 CANDIDATE POOL TRACE")
    print(f"Query: '{query}'")
    print("=================================================================")

    # 1. Specification detection
    detected = parse_query_specifications(query)
    print(f"\n1. SPECIFICATION DETECTION:")
    print(f"   Detected specifications: {detected}")

    # 2. Total chunks in corpus and TS 28.535
    all_chunks = load_all_chunks()
    ts28535_chunks = [c for c in all_chunks if c.get("specification") == "TS 28.535"]
    print(f"\n2. CORPUS SIZES:")
    print(f"   Total corpus chunks across all specs: {len(all_chunks)}")
    print(f"   Total TS 28.535 chunks in processed corpus: {len(ts28535_chunks)}")

    # 3. Setup retrievers
    emb = OllamaEmbedder()
    vs = ChromaVectorStore()
    bm = BM25Index()
    bm.fit(all_chunks)
    sem = SemanticRetriever(emb, vs)
    hyb = HybridRetriever(sem, bm)

    # 4. Dense candidate retrieval inspection
    # Candidate pool requested by HybridRetriever is max(top_k * 4, 20) = 20
    num_candidates = 20
    dense_filtered = sem.retrieve(query, top_k=num_candidates, specification_filter="TS 28.535")
    dense_unfiltered = sem.retrieve(query, top_k=num_candidates, specification_filter=None)

    print(f"\n3. DENSE CANDIDATES:")
    print(f"   Chroma total chunks indexed: {vs.count()}")
    print(f"   Dense candidates BEFORE specification filtering (top {num_candidates}): {len(dense_unfiltered)}")
    print(f"     Specs in unfiltered dense: {set(c.specification for c in dense_unfiltered)}")
    print(f"   Dense candidates AFTER specification filtering ('TS 28.535'): {len(dense_filtered)}")
    print(f"     Specs in filtered dense: {set(c.specification for c in dense_filtered) if dense_filtered else 'None (0 chunks in Chroma)'}")

    # 5. BM25 candidate retrieval inspection
    bm25_unfiltered = bm.query(query, top_k=num_candidates, specification_filter=None)
    bm25_filtered = bm.query(query, top_k=num_candidates, specification_filter="TS 28.535")

    print(f"\n4. BM25 CANDIDATES:")
    print(f"   BM25 candidates BEFORE specification filtering (top {num_candidates}): {len(bm25_unfiltered)}")
    print(f"     Specs in unfiltered BM25: {set(c.specification for c in bm25_unfiltered)}")
    print(f"   BM25 candidates AFTER specification filtering ('TS 28.535'): {len(bm25_filtered)}")
    print(f"     Specs in filtered BM25: {set(c.specification for c in bm25_filtered)}")

    # 6. RRF Fusion Pool inspection
    # Trace exactly how HybridRetriever constructs RRF pool
    # It retrieves num_candidates from dense and num_candidates from BM25 with active_spec_filter
    rrf_scores = {}
    chunk_map = {}
    dense_ranks = {}
    bm25_ranks = {}

    for rank, chunk in enumerate(dense_filtered, start=1):
        cid = chunk.chunk_id
        dense_ranks[cid] = (rank, chunk.score)
        rrf_score = 0.6 * (1.0 / (60 + rank))
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
        chunk_map[cid] = chunk

    for rank, chunk in enumerate(bm25_filtered, start=1):
        cid = chunk.chunk_id
        bm25_ranks[cid] = (rank, chunk.score)
        rrf_score = 0.4 * (1.0 / (60 + rank))
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
        if cid not in chunk_map:
            chunk_map[cid] = chunk

    sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    max_rrf = rrf_scores[sorted_cids[0]] if sorted_cids else 1.0

    print(f"\n5. RRF INPUTS & FUSION POOL:")
    print(f"   Total candidates entering RRF fusion: {len(sorted_cids)}")
    specs_in_rrf = set(chunk_map[cid].specification for cid in sorted_cids)
    print(f"   Specifications represented in RRF pool: {specs_in_rrf}")
    all_ts28535 = all(chunk_map[cid].specification == "TS 28.535" for cid in sorted_cids)
    print(f"   All RRF candidates restricted to TS 28.535: {all_ts28535}")

    # 7. Complete Full Filtered Ranking Table
    print(f"\n6. COMPLETE FILTERED RANKING TABLE (All {len(sorted_cids)} candidates in filtered pool):")
    print("-" * 125)
    print(f"{'Rank':<5} | {'Spec':<9} | {'Clause':<15} | {'Title':<45} | {'Dense Rank/Score':<18} | {'BM25 Rank/Score':<18} | {'RRF Score':<10} | {'Relevant?'}")
    print("-" * 125)

    target_found_rank = None
    for rank, cid in enumerate(sorted_cids, start=1):
        c = chunk_map[cid]
        d_info = f"Rank {dense_ranks[cid][0]} ({dense_ranks[cid][1]:.4f})" if cid in dense_ranks else "None (Dense 0)"
        b_info = f"Rank {bm25_ranks[cid][0]} ({bm25_ranks[cid][1]:.4f})" if cid in bm25_ranks else "None"
        norm_rrf = rrf_scores[cid] / max_rrf if max_rrf > 0 else 0.0
        is_rel = (c.specification == "TS 28.535" and c.clause_number == "5.1.1")
        if is_rel and target_found_rank is None:
            target_found_rank = rank
        rel_str = "YES (Target)" if is_rel else "NO"
        print(f"{rank:<5} | {c.specification:<9} | {c.clause_number:<15} | {c.clause_title[:43]:<45} | {d_info:<18} | {b_info:<18} | {norm_rrf:<10.4f} | {rel_str}")
    print("-" * 125)

    print(f"\n7. RANK BASIS DETERMINATION:")
    print(f"   Clause 5.1.1 is ranked #{target_found_rank} out of {len(sorted_cids)} candidates in the FILTERED TS 28.535 candidate pool.")
    print(f"   Every single candidate in the ranked pool is from TS 28.535.")

if __name__ == "__main__":
    run_diagnostic()

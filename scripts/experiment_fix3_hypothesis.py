"""
Testing intent & title-aware re-ranking in HybridRetriever
"""

import sys
import json
import math
import re
from pathlib import Path
from collections import defaultdict, Counter

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index, telecom_tokenize
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.router import parse_query_specifications
from retrieval.benchmark import is_relevant_chunk
from retrieval.index_corpus import load_all_chunks
from retrieval.models import RetrievedChunk

def evaluate_retriever_on_subset(retriever_fn, queries_subset):
    results = {}
    for q in queries_subset:
        qid = q["id"]
        qtext = q["question"]
        expected = q["expected"]
        chunks = retriever_fn(qtext, 20)
        first_rank = None
        for r, c in enumerate(chunks, 1):
            if is_relevant_chunk(c, expected):
                first_rank = r
                break
        results[qid] = first_rank
    return results

def test_intent_boost():
    all_chunks = load_all_chunks()
    store = ChromaVectorStore()
    embedder = OllamaEmbedder()
    
    with open("evaluation/retrieval/retrieval_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    test_qids = ["R005", "R010", "R012", "R001", "R003", "R004", "R007", "R009", "R014", "R017", "R020", "R021"]
    subset = [q for q in dataset if q["id"] in test_qids]

    bm25 = BM25Index()
    bm25.fit(all_chunks)
    sem = SemanticRetriever(embedder=embedder, vector_store=store)

    class EnhancedHybridRetriever(HybridRetriever):
        def retrieve(self, query: str, top_k: int = 5, candidate_multiplier: int = 4, specification_filter = None):
            if not query or not query.strip():
                return []

            active_spec_filter = specification_filter
            if active_spec_filter is None:
                detected_specs = parse_query_specifications(query)
                if len(detected_specs) == 1:
                    active_spec_filter = detected_specs[0]
                elif len(detected_specs) > 1:
                    active_spec_filter = detected_specs

            num_candidates = max(top_k * candidate_multiplier, 30)

            semantic_candidates = self.semantic_retriever.retrieve(
                query=query,
                top_k=num_candidates,
                specification_filter=active_spec_filter,
            )

            bm25_candidates = self.bm25_index.query(
                query_text=query,
                top_k=num_candidates,
                specification_filter=active_spec_filter,
            )

            # Query intent keywords
            q_lower = query.lower()
            q_tokens = set(telecom_tokenize(query))

            is_def_query = any(w in q_lower for w in ["definition", "definitions", "terms", "defined as", "meaning of"])
            is_desc_query = any(w in q_lower for w in ["described", "description", "overview", "what is a "])
            is_system_proc_query = ("procedur" in q_lower or "call flow" in q_lower or "steps for" in q_lower) and ("5g system" in q_lower or "5gs" in q_lower)

            rrf_scores = {}
            chunk_map = {}
            contributing_methods = {}

            for rank, chunk in enumerate(semantic_candidates, start=1):
                cid = chunk.chunk_id
                rrf_score = self.semantic_weight * (1.0 / (self.rrf_k + rank))
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
                chunk_map[cid] = chunk
                contributing_methods.setdefault(cid, set()).add("semantic")

            for rank, chunk in enumerate(bm25_candidates, start=1):
                cid = chunk.chunk_id
                rrf_score = self.bm25_weight * (1.0 / (self.rrf_k + rank))
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
                if cid not in chunk_map:
                    chunk_map[cid] = chunk
                contributing_methods.setdefault(cid, set()).add("bm25")

            # Deterministic, explainable structural boost
            for cid, chunk in chunk_map.items():
                title = chunk.clause_title or ""
                title_lower = title.lower()
                clause_num = chunk.clause_number or ""
                title_tokens = set(telecom_tokenize(title))

                # Exact title phrase or high token match boost
                if title_tokens and title_tokens.issubset(q_tokens) and len(title_tokens) >= 2:
                    rrf_scores[cid] *= 1.25

                # 1. Definition intent: boost Clause 3 / 3.1 / 3.2 or title "Terms" / "Definitions"
                if is_def_query:
                    if clause_num.startswith("3.") or "term" in title_lower or "definition" in title_lower:
                        rrf_scores[cid] *= 1.40

                # 2. Description intent: boost "Description" / "Overview" clauses
                if is_desc_query:
                    if "description" in title_lower or "overview" in title_lower:
                        rrf_scores[cid] *= 1.20

                # 3. System-level procedure intent: boost TS 23.502 procedure clauses when query explicitly asks for 5G System procedural steps
                if is_system_proc_query:
                    if chunk.specification == "TS 23.502" and chunk.source_type != "table":
                        rrf_scores[cid] *= 1.30

            sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]
            if not sorted_cids:
                return []

            max_rrf = rrf_scores[sorted_cids[0]]
            final_results = []
            for rank, cid in enumerate(sorted_cids, start=1):
                base_chunk = chunk_map[cid]
                methods = contributing_methods.get(cid, set())
                method_label = "hybrid (dense+bm25)" if len(methods) > 1 else list(methods)[0]
                norm_score = rrf_scores[cid] / max_rrf if max_rrf > 0 else 0.0

                final_results.append(RetrievedChunk(
                    chunk_id=base_chunk.chunk_id,
                    specification=base_chunk.specification,
                    document_title=base_chunk.document_title,
                    version=base_chunk.version,
                    release=base_chunk.release,
                    source_filename=base_chunk.source_filename,
                    clause_number=base_chunk.clause_number,
                    clause_title=base_chunk.clause_title,
                    breadcrumb=base_chunk.breadcrumb,
                    source_type=base_chunk.source_type,
                    document_order=base_chunk.document_order,
                    text=base_chunk.text,
                    content_hash=base_chunk.content_hash,
                    score=norm_score,
                    rank=rank,
                    table_id=base_chunk.table_id,
                    table_caption=base_chunk.table_caption,
                    retrieval_method=method_label,
                ))
            return final_results

    enhanced_retriever = EnhancedHybridRetriever(semantic_retriever=sem, bm25_index=bm25)
    ranks = evaluate_retriever_on_subset(lambda q, k: enhanced_retriever.retrieve(q, top_k=k), subset)

    print("=== TARGET AND REGRESSION RANKS WITH ENHANCED HYBRID RETRIEVER ===")
    for qid in test_qids:
        print(f"  {qid}: Rank {ranks[qid]}")

if __name__ == "__main__":
    test_intent_boost()

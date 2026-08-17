"""
Unified Retrieval Interfaces: Semantic, Lexical (BM25), and Hybrid (RRF).
"""

from typing import List, Dict, Any, Optional, Union
from retrieval.models import RetrievedChunk
from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index, telecom_tokenize
from retrieval.router import parse_query_specifications


class SemanticRetriever:
    """Pure semantic vector retriever backed by Ollama and ChromaDB."""

    def __init__(
        self,
        embedder: Optional[OllamaEmbedder] = None,
        vector_store: Optional[ChromaVectorStore] = None,
    ):
        self.embedder = embedder or OllamaEmbedder()
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        specification_filter: Optional[Union[str, List[str]]] = None,
    ) -> List[RetrievedChunk]:
        """Perform semantic search for query."""
        if not query or not query.strip():
            return []

        query_emb = self.embedder.embed_text(query, is_query=True)
        where_filter = None
        if specification_filter:
            if isinstance(specification_filter, str):
                where_filter = {"specification": specification_filter}
            elif isinstance(specification_filter, (list, set, tuple)):
                spec_list = list(specification_filter)
                if len(spec_list) == 1:
                    where_filter = {"specification": spec_list[0]}
                elif len(spec_list) > 1:
                    where_filter = {"specification": {"$in": spec_list}}

        results = self.vector_store.query(
            query_embedding=query_emb,
            top_k=top_k,
            where_filter=where_filter,
        )
        for r in results:
            r.retrieval_method = "semantic"
        return results


class HybridRetriever:
    """
    Hybrid retriever combining Dense Semantic Vector Search and Sparse BM25 Lexical Search
    using Reciprocal Rank Fusion (RRF) with deterministic specification-aware routing.
    """

    def __init__(
        self,
        semantic_retriever: SemanticRetriever,
        bm25_index: BM25Index,
        rrf_k: int = 60,
        semantic_weight: float = 0.6,
        bm25_weight: float = 0.4,
    ):
        self.semantic_retriever = semantic_retriever
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_multiplier: int = 4,
        specification_filter: Optional[Union[str, List[str]]] = None,
    ) -> List[RetrievedChunk]:
        """Perform hybrid retrieval using Reciprocal Rank Fusion (RRF)."""
        if not query or not query.strip():
            return []

        # Deterministic specification routing:
        # If no explicit specification_filter passed, parse from query text
        active_spec_filter = specification_filter
        if active_spec_filter is None:
            detected_specs = parse_query_specifications(query)
            if len(detected_specs) == 1:
                active_spec_filter = detected_specs[0]
            elif len(detected_specs) > 1:
                active_spec_filter = detected_specs

        # Retrieve a wider pool of candidates from each method
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

        # Query intent keywords for structural alignment
        q_lower = query.lower()
        q_tokens = set(telecom_tokenize(query))

        is_def_query = any(w in q_lower for w in ["definition", "definitions", "terms", "defined as", "meaning of"])
        is_desc_query = any(w in q_lower for w in ["described", "description", "what is a "])
        is_system_proc_query = ("procedur" in q_lower or "call flow" in q_lower or "steps for" in q_lower) and ("5g system" in q_lower or "5gs" in q_lower)

        # Merge using Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievedChunk] = {}
        contributing_methods: Dict[str, set] = {}

        # Process semantic ranks
        for rank, chunk in enumerate(semantic_candidates, start=1):
            cid = chunk.chunk_id
            rrf_score = self.semantic_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            chunk_map[cid] = chunk
            contributing_methods.setdefault(cid, set()).add("semantic")

        # Process BM25 ranks
        for rank, chunk in enumerate(bm25_candidates, start=1):
            cid = chunk.chunk_id
            rrf_score = self.bm25_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            if cid not in chunk_map:
                chunk_map[cid] = chunk
            contributing_methods.setdefault(cid, set()).add("bm25")

        # Deterministic, explainable structural metadata refinement
        for cid, chunk in chunk_map.items():
            title = chunk.clause_title or ""
            title_lower = title.lower()
            clause_num = chunk.clause_number or ""
            title_tokens = set(telecom_tokenize(title))

            # 1. Exact title phrase or high token match boost
            if title_tokens and title_tokens.issubset(q_tokens) and len(title_tokens) >= 2:
                rrf_scores[cid] *= 1.30

            # 2. Definition intent: boost Clause 3 / 3.1 / 3.2 or title "Terms" / "Definitions"
            if is_def_query:
                if clause_num.startswith("3.") or "term" in title_lower or "definition" in title_lower:
                    rrf_scores[cid] *= 1.45

            # 3. Description intent: boost "Description" / "Overview" clauses when query asks how something is defined/described/structured
            if is_desc_query or is_def_query:
                if "description" in title_lower or "overview" in title_lower:
                    rrf_scores[cid] *= 1.25

            # 4. System-level procedure intent: boost TS 23.502 procedure clauses when query explicitly asks for 5G System procedural steps
            if is_system_proc_query:
                if chunk.specification == "TS 23.502" and chunk.source_type != "table":
                    rrf_scores[cid] *= 1.35

        # Sort merged chunks by RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        final_results: List[RetrievedChunk] = []
        max_rrf = rrf_scores[sorted_cids[0]] if sorted_cids else 1.0

        for rank, cid in enumerate(sorted_cids, start=1):
            base_chunk = chunk_map[cid]
            methods = contributing_methods.get(cid, set())
            method_label = "hybrid (dense+bm25)" if len(methods) > 1 else list(methods)[0]

            normalized_score = rrf_scores[cid] / max_rrf if max_rrf > 0 else 0.0

            retrieved = RetrievedChunk(
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
                score=normalized_score,
                rank=rank,
                table_id=base_chunk.table_id,
                table_caption=base_chunk.table_caption,
                retrieval_method=method_label,
            )
            final_results.append(retrieved)

        return final_results

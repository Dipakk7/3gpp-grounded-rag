"""
Lexical retrieval using BM25 with telecom-tailored tokenization.
"""

import re
import math
import json
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional, Set
from retrieval.models import RetrievedChunk


def telecom_tokenize(text: str) -> List[str]:
    """
    Tokenize telecom technical text preserving:
    - clause numbers (e.g. 4.2.8.0, 5.7.1.3)
    - hyphenated & alphanumeric terms (e.g. 5G-GUTI, TS-23.501, Npcf_SMPolicyControl)
    - acronyms & codes (e.g. AMF, SMF, UPF, 5QI, QFI, S-NSSAI)
    """
    if not text:
        return []
    text_lower = text.lower()
    # Match words, dotted numbers, alphanumeric identifiers with hyphens/underscores
    tokens = re.findall(r"[a-z0-9]+(?:[\.\-_][a-z0-9]+)*", text_lower)
    return tokens


class BM25Index:
    """Okapi BM25 lexical search index tailored for 3GPP technical specifications."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_ids: List[str] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_metadata: List[Dict[str, Any]] = []
        self.inverted_index: Dict[str, List[tuple]] = defaultdict(list)  # token -> [(doc_idx, freq)]
        self.doc_freqs: Dict[str, int] = defaultdict(int)  # token -> df
        self.num_docs: int = 0
        self.idf_cache: Dict[str, float] = {}

    def fit(self, chunks: List[Dict[str, Any]]) -> None:
        """Build BM25 inverted index from processed chunk dictionaries."""
        self.num_docs = len(chunks)
        self.doc_ids = []
        self.doc_lengths = []
        self.doc_metadata = chunks
        self.inverted_index.clear()
        self.doc_freqs.clear()
        self.idf_cache.clear()

        total_len = 0
        for doc_idx, chunk in enumerate(chunks):
            self.doc_ids.append(chunk["chunk_id"])
            # Index text enriched with clause number and title
            index_text = f"{chunk.get('specification', '')} {chunk.get('clause_number', '')} {chunk.get('clause_title', '')} {chunk.get('text', '')}"
            tokens = telecom_tokenize(index_text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            term_counts = Counter(tokens)
            for token, count in term_counts.items():
                self.inverted_index[token].append((doc_idx, count))
                self.doc_freqs[token] += 1

        self.avg_doc_len = total_len / max(1, self.num_docs)

        # Precompute Robertson-Spärck Jones IDF
        for token, df in self.doc_freqs.items():
            # Standard BM25 IDF: log( (N - df + 0.5) / (df + 0.5) + 1 )
            self.idf_cache[token] = math.log(1.0 + (self.num_docs - df + 0.5) / (df + 0.5))

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        specification_filter: Optional[Any] = None,
    ) -> List[RetrievedChunk]:
        """Search BM25 index and return scored RetrievedChunk items."""
        query_tokens = telecom_tokenize(query_text)
        if not query_tokens or self.num_docs == 0:
            return []

        # Normalize specification filter to a set
        allowed_specs = None
        if specification_filter:
            if isinstance(specification_filter, str):
                allowed_specs = {specification_filter}
            elif isinstance(specification_filter, (list, set, tuple)):
                allowed_specs = set(specification_filter)

        scores = defaultdict(float)

        for token in query_tokens:
            if token not in self.inverted_index:
                continue
            idf = self.idf_cache.get(token, 0.0)
            for doc_idx, freq in self.inverted_index[token]:
                chunk_meta = self.doc_metadata[doc_idx]
                if allowed_specs and chunk_meta.get("specification") not in allowed_specs:
                    continue

                doc_len = self.doc_lengths[doc_idx]
                # BM25 term frequency saturation
                tf_component = (freq * (self.k1 + 1)) / (
                    freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                )
                scores[doc_idx] += idf * tf_component

        if not scores:
            return []

        # Sort doc indices by score descending
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Normalize scores to [0, 1] relative to max score
        max_score = sorted_docs[0][1] if sorted_docs[0][1] > 0 else 1.0

        results: List[RetrievedChunk] = []
        for rank, (doc_idx, raw_score) in enumerate(sorted_docs, start=1):
            c = self.doc_metadata[doc_idx]
            norm_score = raw_score / max_score
            results.append(
                RetrievedChunk(
                    chunk_id=c["chunk_id"],
                    specification=c.get("specification", ""),
                    document_title=c.get("document_title", ""),
                    version=c.get("version", ""),
                    release=c.get("release", ""),
                    source_filename=c.get("source_filename", ""),
                    clause_number=c.get("clause_number", ""),
                    clause_title=c.get("clause_title", ""),
                    breadcrumb=c.get("breadcrumb", []),
                    source_type=c.get("source_type", "prose"),
                    document_order=int(c.get("document_order", 0)),
                    text=c.get("text", ""),
                    content_hash=c.get("content_hash", ""),
                    score=norm_score,
                    rank=rank,
                    table_id=c.get("table_id"),
                    table_caption=c.get("table_caption"),
                    retrieval_method="bm25",
                )
            )

        return results

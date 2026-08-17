"""
Corpus Indexing Pipeline:
Embeds all 6,737 processed chunks into ChromaDB and fits the BM25 index.
"""

import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root in sys.path
ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from ingestion.config import PROCESSED_DATA_DIR
from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore, DEFAULT_VECTORSTORE_PATH
from retrieval.bm25 import BM25Index

FILES = [
    "TS_23_501_chunks.jsonl",
    "TS_23_502_chunks.jsonl",
    "TS_24_501_chunks.jsonl",
    "TS_28_535_chunks.jsonl",
    "TS_38_300_chunks.jsonl",
]


def load_all_chunks() -> List[Dict[str, Any]]:
    """Load and combine all chunks across 5 specifications."""
    all_chunks = []
    for fname in FILES:
        fpath = PROCESSED_DATA_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_chunks.append(json.loads(line))
    return all_chunks


def run_indexing(batch_size: int = 50) -> Dict[str, Any]:
    """Execute full corpus embedding and indexing."""
    print("=== Starting Corpus Indexing ===")
    t_start = time.time()

    chunks = load_all_chunks()
    total_chunks = len(chunks)
    print(f"Loaded {total_chunks} chunks from {PROCESSED_DATA_DIR}")

    if total_chunks != 6737:
        print(f"WARNING: Expected 6,737 chunks, found {total_chunks}")

    embedder = OllamaEmbedder()
    smoke = embedder.verify_service()
    print(f"Ollama connection verified: Model={smoke['model']}, Dim={smoke['dimension']}")

    vector_store = ChromaVectorStore()
    vector_store.clear()  # Ensure clean slate

    print(f"\nGenerating embeddings in batches of {batch_size}...")
    all_embeddings: List[List[float]] = []

    # Batch embedding loop
    for i in range(0, total_chunks, batch_size):
        sub_chunks = chunks[i : i + batch_size]
        texts = [
            f"{c.get('specification', '')} Clause {c.get('clause_number', '')} {c.get('clause_title', '')}\n{c.get('text', '')}"
            for c in sub_chunks
        ]
        t0 = time.time()
        sub_embs = embedder.embed_batch(texts, is_query=False, batch_size=batch_size)
        all_embeddings.extend(sub_embs)
        dt = time.time() - t0

        # Upsert sub-batch to ChromaDB immediately
        vector_store.add_chunks(sub_chunks, sub_embs, batch_size=len(sub_chunks))

        indexed_so_far = min(i + batch_size, total_chunks)
        if indexed_so_far % 500 == 0 or indexed_so_far == total_chunks:
            pct = (indexed_so_far / total_chunks) * 100
            print(f"  Progress: {indexed_so_far}/{total_chunks} ({pct:.1f}%) indexed (batch took {dt:.2f}s)")

    indexed_count = vector_store.count()
    t_end = time.time()
    total_time = t_end - t_start

    print(f"\n=== Indexing Completed in {total_time:.2f}s ({total_time/60:.2f} min) ===")
    print(f"Total chunks processed: {total_chunks}")
    print(f"Total chunks indexed in ChromaDB: {indexed_count}")

    # Build and verify BM25 Index
    print("\nFitting BM25 lexical index...")
    bm25 = BM25Index()
    bm25.fit(chunks)
    print(f"BM25 index built with {bm25.num_docs} documents, avg doc length {bm25.avg_doc_len:.1f} tokens, vocabulary size {len(bm25.doc_freqs)}")

    return {
        "total_chunks": total_chunks,
        "indexed_count": indexed_count,
        "embedding_failures": total_chunks - len(all_embeddings),
        "total_time_sec": round(total_time, 2),
        "avg_ms_per_chunk": round((total_time / total_chunks) * 1000, 2),
        "vector_dim": smoke["dimension"],
        "bm25_docs": bm25.num_docs,
        "bm25_vocab": len(bm25.doc_freqs),
    }


if __name__ == "__main__":
    run_indexing()

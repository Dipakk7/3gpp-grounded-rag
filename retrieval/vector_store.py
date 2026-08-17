"""
Persistent Vector Store interface using ChromaDB.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from retrieval.models import RetrievedChunk

DEFAULT_VECTORSTORE_PATH = Path("data/vectorstore")
COLLECTION_NAME = "telecom_3gpp_knowledge"


class ChromaVectorStore:
    """ChromaDB Vector Store wrapper for 3GPP technical specifications."""

    def __init__(
        self,
        persist_directory: Path = DEFAULT_VECTORSTORE_PATH,
        collection_name: str = COLLECTION_NAME,
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        # Using cosine distance
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Return number of items in collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear existing collection."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        batch_size: int = 500,
    ) -> None:
        """Add chunks and precomputed embeddings in batches."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
            )

        total = len(chunks)
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            batch_chunks = chunks[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]

            ids: List[str] = []
            documents: List[str] = []
            metadatas: List[Dict[str, Any]] = []

            for c in batch_chunks:
                ids.append(c["chunk_id"])
                documents.append(c["text"])

                # Chroma metadata supports str, int, float, bool
                meta = {
                    "specification": str(c.get("specification", "")),
                    "document_title": str(c.get("document_title", "")),
                    "version": str(c.get("version", "")),
                    "release": str(c.get("release", "")),
                    "source_filename": str(c.get("source_filename", "")),
                    "clause_number": str(c.get("clause_number", "")),
                    "clause_title": str(c.get("clause_title", "")),
                    "breadcrumb_json": json.dumps(c.get("breadcrumb", [])),
                    "source_type": str(c.get("source_type", "prose")),
                    "document_order": int(c.get("document_order", 0)),
                    "content_hash": str(c.get("content_hash", "")),
                    "table_id": str(c.get("table_id") or ""),
                    "table_caption": str(c.get("table_caption") or ""),
                }
                metadatas.append(meta)

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas,
            )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        """Query vector store for top-k similar chunks using cosine similarity."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )

        retrieved: List[RetrievedChunk] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return retrieved

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        dists = results["distances"][0] if results.get("distances") else []

        for rank, (cid, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
            # Chroma returns cosine distance in [0, 2]; cosine similarity = 1 - distance
            sim_score = max(0.0, min(1.0, 1.0 - dist))
            bc = json.loads(meta.get("breadcrumb_json", "[]"))

            chunk = RetrievedChunk(
                chunk_id=cid,
                specification=meta.get("specification", ""),
                document_title=meta.get("document_title", ""),
                version=meta.get("version", ""),
                release=meta.get("release", ""),
                source_filename=meta.get("source_filename", ""),
                clause_number=meta.get("clause_number", ""),
                clause_title=meta.get("clause_title", ""),
                breadcrumb=bc,
                source_type=meta.get("source_type", "prose"),
                document_order=int(meta.get("document_order", 0)),
                text=doc,
                content_hash=meta.get("content_hash", ""),
                score=sim_score,
                rank=rank,
                table_id=meta.get("table_id") or None,
                table_caption=meta.get("table_caption") or None,
                retrieval_method="semantic",
            )
            retrieved.append(chunk)

        return retrieved

"""
RAG Service Wrapper:
Encapsulates existing GroundedGenerationPipeline, HybridRetriever, and BM25 index
into a clean service interface for FastAPI dependency injection.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from retrieval.embedding import OllamaEmbedder, DEFAULT_OLLAMA_URL, DEFAULT_EMBED_MODEL
from retrieval.vector_store import ChromaVectorStore, DEFAULT_VECTORSTORE_PATH, COLLECTION_NAME
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.index_corpus import load_all_chunks
from generation.generator import GroundedGenerator, DEFAULT_MODEL
from generation.evidence_gate import EvidenceSufficiencyGate
from generation.citation_validator import CitationValidator
from generation.claim_verifier import ClaimVerifier
from generation.abstention import AbstentionPolicy
from generation.pipeline import GroundedGenerationPipeline
from generation.models import GenerationResult

logger = logging.getLogger("rag_api.service")


class RAGService:
    """
    Singleton-ready service adapter around the Grounded Generation Pipeline.
    """

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        embed_model: Optional[str] = None,
        gen_model: Optional[str] = None,
        vectorstore_path: Optional[Path] = None,
    ):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL)
        self.embed_model = embed_model or os.getenv("EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self.gen_model = gen_model or os.getenv("GEN_MODEL", DEFAULT_MODEL)
        self.vectorstore_path = vectorstore_path or Path(os.getenv("VECTORSTORE_PATH", str(DEFAULT_VECTORSTORE_PATH)))

        self.embedder: Optional[OllamaEmbedder] = None
        self.vector_store: Optional[ChromaVectorStore] = None
        self.bm25: Optional[BM25Index] = None
        self.semantic_retriever: Optional[SemanticRetriever] = None
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self.pipeline: Optional[GroundedGenerationPipeline] = None
        self._is_initialized = False

    def initialize(self) -> None:
        """Initializes retrieval indices and grounded generation pipeline."""
        if self._is_initialized:
            return

        logger.info("Initializing RAG Service components...")
        self.embedder = OllamaEmbedder(
            base_url=self.ollama_url,
            model=self.embed_model,
        )
        self.vector_store = ChromaVectorStore(
            persist_directory=self.vectorstore_path,
            collection_name=COLLECTION_NAME,
        )

        # Load chunks and fit BM25 index
        chunks = load_all_chunks()
        self.bm25 = BM25Index()
        self.bm25.fit(chunks)

        self.semantic_retriever = SemanticRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
        )
        self.hybrid_retriever = HybridRetriever(
            semantic_retriever=self.semantic_retriever,
            bm25_index=self.bm25,
        )

        generator = GroundedGenerator(
            model=self.gen_model,
            ollama_url=self.ollama_url,
        )
        gate = EvidenceSufficiencyGate()
        citation_validator = CitationValidator()
        claim_verifier = ClaimVerifier(use_llm=False)
        abstention_policy = AbstentionPolicy()

        self.pipeline = GroundedGenerationPipeline(
            retriever=self.hybrid_retriever,
            generator=generator,
            gate=gate,
            citation_validator=citation_validator,
            claim_verifier=claim_verifier,
            abstention_policy=abstention_policy,
        )

        self._is_initialized = True
        logger.info("RAG Service successfully initialized.")

    @property
    def is_ready(self) -> bool:
        return self._is_initialized and self.pipeline is not None

    def ask(self, question: str, top_k: int = 5) -> GenerationResult:
        """Executes grounded generation for the provided question."""
        if not self.is_ready:
            self.initialize()

        if self.pipeline is None:
            raise RuntimeError("RAG Pipeline is not initialized.")

        return self.pipeline.process(question=question, top_k=top_k)

    def get_health(self) -> Dict[str, Any]:
        """Fast non-inferencing readiness check."""
        vs_count = 0
        vs_ready = False
        try:
            if self.vector_store is None:
                self.vector_store = ChromaVectorStore(
                    persist_directory=self.vectorstore_path,
                    collection_name=COLLECTION_NAME,
                )
            vs_count = self.vector_store.count()
            vs_ready = vs_count > 0
        except Exception as e:
            logger.warning(f"Vector store health check warning: {e}")

        bm25_count = self.bm25.num_docs if self.bm25 else 0
        bm25_ready = self.bm25 is not None and bm25_count > 0

        return {
            "initialized": self._is_initialized,
            "vector_store_ready": vs_ready,
            "vector_store_chunk_count": vs_count,
            "bm25_ready": bm25_ready,
            "bm25_chunk_count": bm25_count,
            "embedding_model": self.embed_model,
            "generation_model": self.gen_model,
            "ollama_url": self.ollama_url,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Exposes corpus and model configuration metadata."""
        specs = ["TS 23.501", "TS 23.502", "TS 24.501", "TS 28.535", "TS 38.300"]
        chunk_count = 0
        try:
            if self.vector_store is None:
                self.vector_store = ChromaVectorStore(
                    persist_directory=self.vectorstore_path,
                    collection_name=COLLECTION_NAME,
                )
            chunk_count = self.vector_store.count()
        except Exception:
            if self.bm25:
                chunk_count = self.bm25.num_docs

        return {
            "service": "3gpp-grounded-rag",
            "specifications": specs,
            "total_chunks": chunk_count,
            "embedding_model": self.embed_model,
            "generation_model": self.gen_model,
            "vector_store_collection": COLLECTION_NAME,
        }

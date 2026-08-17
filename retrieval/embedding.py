"""
Embedding generation subsystem using Ollama (nomic-embed-text).
"""

import json
import urllib.request
import urllib.error
import time
from typing import List, Dict, Any, Optional

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
EXPECTED_DIMENSION = 768


class OllamaEmbedder:
    """Interface to Ollama embedding service."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_EMBED_MODEL,
        dimension: int = EXPECTED_DIMENSION,
        use_prefix: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimension = dimension
        self.use_prefix = use_prefix
        self.endpoint = f"{self.base_url}/api/embeddings"

    def embed_text(self, text: str, is_query: bool = False) -> List[float]:
        """Embed a single text string."""
        batch_res = self.embed_batch([text], is_query=is_query, batch_size=1)
        return batch_res[0] if batch_res else [0.0] * self.dimension

    def embed_batch(
        self,
        texts: List[str],
        is_query: bool = False,
        batch_size: int = 50,
        max_retries: int = 3,
    ) -> List[List[float]]:
        """Embed a batch of text strings using Ollama /api/embed with automatic chunking."""
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        # Prepare prefixed prompts
        prefix = ("search_query: " if is_query else "search_document: ") if self.use_prefix else ""
        processed_prompts = [
            f"{prefix}{t.strip()}" if t and t.strip() else ""
            for t in texts
        ]

        # Chunk into sub-batches
        for start_idx in range(0, len(processed_prompts), batch_size):
            sub_batch = processed_prompts[start_idx : start_idx + batch_size]
            
            # Replace empty strings with a minimal placeholder to prevent Ollama errors, then zero-vector them
            non_empty_indices = [i for i, p in enumerate(sub_batch) if p]
            cleaned_sub = [p if p else "empty" for p in sub_batch]

            success = False
            last_err = None
            for attempt in range(max_retries):
                try:
                    payload = json.dumps({"model": self.model, "input": cleaned_sub}).encode("utf-8")
                    req = urllib.request.Request(
                        f"{self.base_url}/api/embed",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        embs = data.get("embeddings", [])
                        if len(embs) != len(sub_batch):
                            raise ValueError(
                                f"Expected {len(sub_batch)} embeddings, got {len(embs)}"
                            )
                        # Zero out empty inputs
                        for i in range(len(sub_batch)):
                            if not sub_batch[i]:
                                embs[i] = [0.0] * self.dimension
                        all_embeddings.extend(embs)
                        success = True
                        break
                except Exception as e:
                    last_err = e
                    # Fallback single embedding if batch fails
                    time.sleep(1.0 * (attempt + 1))
            
            if not success:
                raise RuntimeError(
                    f"Failed embedding batch {start_idx} to {start_idx + len(sub_batch)} after {max_retries} attempts: {last_err}"
                )

        return all_embeddings


    def verify_service(self) -> Dict[str, Any]:
        """Smoke test the embedding service on a simple test sentence."""
        t0 = time.time()
        test_text = "3GPP 5G System Architecture and Core Network Functions"
        vec = self.embed_text(test_text, is_query=False)
        lat = time.time() - t0
        return {
            "status": "OK",
            "model": self.model,
            "dimension": len(vec),
            "latency_sec": round(lat, 4),
            "sample_vector_head": vec[:5],
        }

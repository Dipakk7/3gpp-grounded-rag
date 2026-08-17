# Retrieval Architecture: 3GPP Technical Specifications RAG

> **System Component:** Phase 3 — Embedding, Vector Store, Lexical Index & Hybrid Fusion  
> **Target Audience:** Technical Assessment / Engineering Interview Review

---

## 1. Architectural Overview

The Phase 3 retrieval engine operates as an independent, modular evidence retrieval layer preceding LLM generation. It transforms natural language engineering queries into grounded, citation-ready evidence chunks extracted from the 3GPP knowledge base.

```
                  ┌───────────────────────────────┐
                  │    User Technical Query       │
                  └──────────────┬────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │   Ollama Embed    │           │  Telecom Regex    │
       │ (nomic-embed-text)│           │    Tokenizer      │
       └─────────┬─────────┘           └─────────┬─────────┘
                 │ (768-dim vector)              │ (Tokens)
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │     ChromaDB      │           │    Okapi BM25     │
       │ (Persistent HNSW) │           │  Inverted Index   │
       └─────────┬─────────┘           └─────────┬─────────┘
                 │ Top-K Candidates              │ Top-K Candidates
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │    Reciprocal Rank Fusion     │
                 │      (RRF, k=60, w=0.6/0.4)   │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │ Structured Evidence Objects   │
                 │ (Chunk ID, Clause, Breadcrumb,│
                 │  Metadata, Text, Score)       │
                 └───────────────────────────────┘
```

---

## 2. Core Components

### 2.1 Embedding Model: `nomic-embed-text`
- **Dimensionality:** 768 float32 values.
- **Context Length:** 8,192 tokens (accommodates multi-paragraph clauses and large Markdown tables).
- **Task Prefixing:** Uses `search_document: ` for corpus indexing and `search_query: ` for runtime retrieval.
- **Rationale for Selection:**
  1. High performance on technical and domain-specific retrieval benchmarks.
  2. Runs locally via Ollama without requiring external cloud API keys or external data transmission.
  3. Consistent 768-dimensional space suitable for local vector indices.

### 2.2 Vector Database: ChromaDB
- **Storage Location:** `data/vectorstore/` (persistent local SQLite + HNSW index).
- **Distance Metric:** Cosine similarity ($1.0 - \text{cosine\_distance}$).
- **Metadata Enriched Indexing:** Stores `specification`, `version`, `clause_number`, `clause_title`, `breadcrumb_json`, `source_type`, `document_order`, `content_hash`, and `table_id`.
- **Query Capabilities:** Supports exact specification filtering (`specification == 'TS 38.300'`) and top-k vector nearest-neighbor search.

### 2.3 Lexical Engine: Okapi BM25
- **Implementation:** Native Python BM25 index with inverted index and Robertson-Spärck Jones IDF precomputation.
- **Telecom Tokenizer:** Preserves dotted numbers (`4.2.8.0`), hyphenated identifiers (`5G-GUTI`, `TS 23.501`, `REQ-ACCL_GOV-CON-05`), and acronyms (`AMF`, `UPF`, `5QI`).
- **Vocabulary Size:** 24,523 distinct technical tokens across 6,737 chunks.

### 2.4 Fusion Strategy: Reciprocal Rank Fusion (RRF)
Rather than raw score addition (which suffers from disparate scale calibrations between cosine distance and BM25 scores), RRF computes a unified score based on rank positions:
$$RRF(d) = w_{\text{dense}} \cdot \frac{1}{k + \text{rank}_{\text{dense}}(d)} + w_{\text{lexical}} \cdot \frac{1}{k + \text{rank}_{\text{lexical}}(d)}$$
with $k=60$, $w_{\text{dense}}=0.6$, and $w_{\text{lexical}}=0.4$.

---

## 3. Retrieval Interface Schema

The primary retrieval method returns strongly-typed `RetrievedChunk` instances:

```python
retriever = HybridRetriever(...)
results = retriever.retrieve(query="What are the main functions of UPF?", top_k=5)
```

Each item adheres to the JSON schema:

```json
{
  "chunk_id": "TS_23.501-V18.12.0-6.2.3-P001",
  "specification": "TS 23.501",
  "document_title": "System architecture for the 5G System (5GS); Stage 2",
  "version": "18.12.0",
  "release": "18",
  "clause_number": "6.2.3",
  "clause_title": "UPF",
  "breadcrumb": [
    {"number": "6", "title": "High level architecture and functional entities"},
    {"number": "6.2", "title": "Network Functions"},
    {"number": "6.2.3", "title": "UPF"}
  ],
  "source_type": "prose",
  "document_order": 204,
  "text": "The User Plane Function (UPF) includes the following functionality...",
  "content_hash": "...",
  "score": 1.0,
  "rank": 1,
  "table_id": null,
  "table_caption": null,
  "retrieval_method": "hybrid (dense+bm25)"
}
```

---

## 4. Benchmark Methodology & Anti-Bias Controls

1. **Frozen Ground-Truth Dataset:** 20 queries spanning 5 technical categories (direct factual, procedural, conceptual, clause-specific, and table-related) created and frozen before running evaluations.
2. **Deterministic Evaluation:** Ground-truth matches require exact specification match and clause hierarchy containment or table ID matching.
3. **Reproducibility:** Test suite in `tests/test_retrieval.py` guarantees that retrieval behavior is verified and reproducible on every commit.

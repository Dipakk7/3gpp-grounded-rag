# Mavenir 3GPP RAG — Phase 3: Retrieval Baseline & Hybrid Benchmark Report

> **Document Status:** Complete & Verified  
> **Target Subsystem:** Dense Semantic Vector Retrieval + BM25 Lexical + Hybrid RRF Fusion  
> **Knowledge Corpus:** 6,737 chunks across 5 3GPP Technical Specifications

---

## 1. Executive Summary

Phase 3 established the evidence retrieval engine for the Mavenir 3GPP RAG system. All 6,737 chunks generated in Phase 2 were embedded using `nomic-embed-text` (768 dimensions) via a local Ollama instance and indexed into a persistent ChromaDB vector store. A complementary Okapi BM25 lexical index with custom telecom tokenization was constructed to preserve exact acronyms, identifiers, and clause numbers.

Evaluation across a frozen, manually-verified 20-query ground-truth benchmark demonstrates that **Hybrid Retrieval (Dense + BM25 via Reciprocal Rank Fusion)** significantly outperforms individual retrievers, achieving **100% Hit@5** and an **MRR of 0.8833** at sub-100ms total latency.

---

## 2. Experimental Setup

- **Hardware / OS:** Windows 11 (AMD64, 8 cores)
- **Embedding Engine:** Ollama (`nomic-embed-text:latest`)
- **Embedding Dimension:** 768 float32 values
- **Context Window:** 8,192 tokens
- **Vector Store:** ChromaDB (Persistent HNSW Cosine Index at `data/vectorstore`)
- **Lexical Engine:** Okapi BM25 ($k_1=1.5$, $b=0.75$) with telecom-tailored regex tokenizer
- **Fusion Strategy:** Reciprocal Rank Fusion (RRF, $k=60$, $w_{\text{dense}}=0.6$, $w_{\text{lexical}}=0.4$)
- **Corpus Size:** 6,737 chunks (6,064 prose, 673 structured tables)
- **Benchmark Size:** 20 ground-truth technical queries across 5 distinct categories (A–E)

---

## 3. Quantitative Retrieval Results

| Metric | Semantic Baseline (Dense) | BM25 Lexical (Sparse) | Hybrid Retrieval (Dense + BM25 RRF) | Relative Gain (Hybrid vs Baseline) |
| :--- | :---: | :---: | :---: | :---: |
| **Hit@1** | 70.0% | 60.0% | **80.0%** | +14.3% |
| **Hit@3** | 90.0% | 85.0% | **95.0%** | +5.6% |
| **Hit@5** | 95.0% | 90.0% | **100.0%** | **+5.3% (Perfect Recall)** |
| **Hit@10** | 95.0% | 95.0% | **100.0%** | +5.3% |
| **MRR** | 0.8033 | 0.7225 | **0.8833** | **+9.96%** |

---

## 4. Latency Analysis (Average over Benchmark Queries)

| Pipeline Component | Average Latency | Notes |
| :--- | :---: | :--- |
| **Query Embedding** | 79.52 ms | Nomic 768-dim embedding generation via Ollama HTTP API |
| **Vector Search (ChromaDB)** | 7.01 ms | Cosine similarity HNSW search over 6,737 vectors |
| **BM25 Search** | 1.82 ms | Inverted index traversal over 24,523 telecom tokens |
| **RRF Fusion & Ranking** | 2.23 ms | Candidate deduplication and rank-reciprocal merging |
| **Total Hybrid Retrieval** | **90.58 ms** | **Sub-100ms end-to-end evidence retrieval** |

---

## 5. Failure & Complementarity Analysis

Analyzing query performance across individual modalities highlights why hybrid fusion is critical for technical 3GPP specifications:

### Case 1: Dense Semantic Advantage (Abstract / Conceptual Queries)
- **Query:** *"How is a closed control loop defined and described in communication service assurance?"*
- **Dense Vector Rank:** Rank 1 (`TS_28.535-V18.2.0-4.2.4.1-P001`, similarity: 0.7789)
- **BM25 Rank:** Rank 3
- **Analysis:** The semantic embedding effectively captured the paraphrase *"without direct involvement of a human operator"*, whereas lexical search matched common keywords across multiple general sections.

### Case 2: Lexical BM25 Advantage (Exact Standards Clauses / Acronyms)
- **Query:** *"What business-level requirements exist for closed control loop concept in communication service assurance?"*
- **Query Contains:** Technical requirements prefix `REQ-ACCL_GOV-CON-05`
- **BM25 Rank:** Rank 1 (`TS_28.535-V18.2.0-5.1.1-P001`)
- **Dense Vector Rank:** Rank 2
- **Analysis:** Exact alphanumeric token matching in BM25 pinned down the specific requirement clause that had slight semantic diffusion across TS 28.535.

### Case 3: Table Retrieval (Category E)
- **Queries R017–R020:** Targeting structured Markdown tables (e.g. `Table 5.6.1-1: Attributes of a PDU Session`, `Table 5.7.1.3-1: 5QI Mapping`, `Table 4.3.3.1: UE Usage Setting`).
- **Semantic Baseline:** Hit@1 on 4/4 table queries (100%).
- **Hybrid RRF:** Hit@1 on 4/4 table queries (100%).
- **Analysis:** Because Phase 2 retained table captions as first-class Markdown headers (`**Table 5.6.1-1: ...**`), embedding models effectively match table content to procedural questions.

---

## 6. Verification and Quality Gate Checklist

- [x] **All 6,737 chunks indexed:** Verified `collection.count() == 6737` in ChromaDB.
- [x] **Complete metadata preserved:** `chunk_id`, `specification`, `version`, `clause_number`, `clause_title`, `breadcrumb`, `source_type`, `document_order`, `text`, `content_hash`.
- [x] **Zero NaN/Inf vectors:** Validated 768-dimensional float arrays across all embeddings.
- [x] **Frozen benchmark evaluation:** 20 ground-truth queries tested strictly without post-hoc tuning.
- [x] **Sub-100ms retrieval latency:** End-to-end hybrid execution clocks at ~90.6 ms.
- [x] **All unit tests pass:** 38/38 tests passing across test suites.

# 3GPP-Grounded-RAG

A production-grade, citation-grounded Retrieval-Augmented Generation (RAG) system for 3GPP 5G Technical Specifications. Built for mission-critical telecommunications question answering, it enforces deterministic citation validation, token-level claim support verification, and strict safe abstention against hallucinations.

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/VectorStore-ChromaDB-FF6F00.svg)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Embeddings%20%26%20LLM-Ollama-000000.svg)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-90%2F90%20PASS-brightgreen.svg)](tests/)

---

## 1. Problem Statement & Motivation

Telecommunications engineering operates on authoritative technical specifications published by the 3rd Generation Partnership Project (3GPP). These documents span thousands of pages of dense, interconnected systems architecture, procedural call flows, and protocol definitions.

Standard off-the-shelf RAG systems fail when applied to 3GPP specifications due to four domain-specific challenges:

1. **Destructive Chunking**: Fixed-size token chunking fragments nested hierarchical clauses (e.g., `§4.2.8.0`) and tabular protocol parameters across chunk boundaries, stripping crucial section headers and context.
2. **Lexical & Identifier Blindness**: Standard NLP tokenizers split technical acronyms, hyphenated identifiers, and dotted clause numbers (such as `5G-GUTI`, `Npcf_SMPolicyControl`, `TS 23.501 §4.2.2.2.2`, `5QI`), causing semantic search to miss exact technical targets.
3. **Specification Dominance / Dilution**: Large architectural specifications (such as TS 23.501 and TS 23.502 with thousands of paragraphs) drown out smaller, domain-specific standards (such as TS 28.535 with 86 chunks) during global dense retrieval.
4. **Catastrophic Hallucinations**: In telecommunications standards, generating a plausible-sounding but unverified parameter, timer, or procedure step can lead to critical implementation faults. Systems must verify claims against authoritative text and safely abstain when evidence is missing.

**3GPP-Grounded-RAG** solves these challenges with a clause-aware hierarchical ingestion pipeline, hybrid reciprocal rank fusion retrieval with specification-aware routing, structural metadata refinement, and deterministic claim-support verification gates.

---

## 2. Key Results & Benchmark Summary

| Evaluation Component | Benchmark Metric | Verified Result | Notes |
| :--- | :--- | :--- | :--- |
| **Authoritative Retrieval (21Q)** | **Hit@5 Recall** | **100.0% (21/21)** | Dense + BM25 via Reciprocal Rank Fusion |
| | **Hit@3 Recall** | **90.5% (19/21)** | High precision in top ranks |
| | **Hit@1 Recall** | **66.7% (14/21)** | Exact target clause at rank #1 |
| | **Mean Reciprocal Rank (MRR)** | **0.7992** | Multi-retriever hybrid baseline: 0.7251 |
| **Held-Out Generalization (6Q)** | **Hit@5 Recall** | **83.3% (5/6)** | Evaluated on unseen procedural and definition questions |
| | **Hit@3 Recall** | **83.3% (5/6)** | Unseen specifications & multi-step flows |
| | **Hit@1 Recall** | **50.0% (3/6)** | Exact target clause at rank #1 |
| **Grounded Generation (30Q)** | **Citation Validity Rate** | **100.0% (20/20)** | Validated against retrieved evidence IDs |
| | **Citation Completeness Rate** | **100.0%** | Specification, clause number, and title included |
| | **Claim Support Rate** | **100.0% (15/15)** | Token-level containment against source text |
| | **Unsupported Claim Rate** | **0.0% (0/15 claims)** | **0.0% across evaluated 30-query test benchmark (empirical result on evaluated test set, not a universal guarantee)** |
| | **Abstention Accuracy** | **100.0% (8/8)** | Safely abstains on adversarial/unanswerable queries |
| | **False Answer Rate** | **0.0% (0/8)** | Zero speculative answers on ungrounded queries |
| | **Answer Correctness (Answerable)** | **63.64% (14/22)** | Strict factual accuracy with local Qwen2.5:1.5b |
| **Automated Test Suite** | **Pytest Unit & Integration** | **90/90 PASS (100%)** | End-to-end API, chunking, retrieval, generation |
| **Knowledge Corpus** | **Vector Store & Inverted Index** | **6,737 / 6,737** | 5 Release 18 specifications fully indexed |

---

## 3. System Architecture

The end-to-end pipeline routes questions through multiple deterministic validation stages before producing citations or triggering safe abstention:

```
                         [ User Technical Query ]
                                    │
                                    ▼
                   [ Specification-Aware Router ]
                    (Explicit & implicit keyword regex)
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
   [ Dense Semantic Search ]   [ Telecom BM25 ]   [ Target Spec Filter ]
   (nomic-embed-text: 768d)    (Regex Tokenizer)            │
            │                       │                       │
            └───────────┬───────────┘                       │
                        ▼                                   │
          [ Reciprocal Rank Fusion (RRF) ]                  │
          (Rank-merging: k=60, w_dense=0.6)                 │
                        │                                   │
                        ▼                                   ▼
          [ Structural Metadata Refiner ] ◄─────────────────┘
          (Title match, Definition §3, Procedure §4 boosts)
                        │
                        ▼
             [ Evidence Sufficiency Gate ]
                        │
           ┌────────────┴────────────┐
           │ Passes Gate             │ Insufficient Evidence
           ▼                         ▼
   [ Structured Generator ]   [ Safe Abstention Policy Engine ]
     (Qwen2.5:1.5b @ T=0.0)          │
           │                         │
           ▼                         │
   [ Citation Validator ]            │
   (Spec, clause, title check)       │
           │                         │
           ▼                         │
   [ Claim-Support Verifier ]        │
   (Token & n-gram containment)      │
           │                         │
           ├─────────────────────────┘
           │
     ┌─────┴──────────────┐
     ▼                    ▼
[ Grounded Answer ]  [ Safe Abstention ]
```

---

## 4. Document Ingestion Pipeline

### Technical Specifications Indexed
The system indexes 5 foundational 3GPP Release 18 technical specifications extracted directly from official Word (`.docx`) publications:

| Specification | Version | Title | Total Paragraphs | Clauses | Prose Chunks | Table Chunks | Total Chunks |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| **TS 23.501** | `V18.12.0` | System Architecture for the 5G System (5GS) | 16,878 | 816 | 1,382 | 55 | 1,437 |
| **TS 23.502** | `V18.14.0` | Procedures for the 5G System (5GS) | 17,998 | 946 | 1,659 | 60 | 1,719 |
| **TS 24.501** | `V18.13.0` | Non-Access-Stratum (NAS) protocol for 5GS | 9,807 | 1,075 | 2,426 | 542 | 2,968 |
| **TS 28.535** | `V18.2.0` | Management & orchestration; Closed control loop assurance | 599 | 32 | 38 | 1 | 39 |
| **TS 38.300** | `V18.10.0` | NR; NR and NG-RAN Overall Description | 3,562 | 425 | 559 | 15 | 574 |
| **Total** | | | **48,844** | **3,294** | **6,064** | **673** | **6,737** |

### Ingestion Engineering Highlights
- **Hierarchical Clause Extraction**: Detects clause numbering across all heading levels (`Heading 1` to `Heading 6`, `Heading 8`, `ANNEX`) and builds persistent breadcrumb trails (e.g. `4 > 4.2 > 4.2.8 > 4.2.8.0`).
- **Table Preservation**: Extracts 673 technical tables, converting them to clean, column-aligned Markdown while skipping non-technical cover/layout tables.
- **TOC & Boilerplate Stripping**: Removes 4,325 Table of Contents paragraphs, dynamic page-number fields, running headers/footers, and legal notices to prevent index contamination.
- **Semantic Boundary Chunking**: Clauses larger than 2,000 characters are split strictly along paragraph boundaries, prepending clause identifiers and breadcrumbs to every sub-chunk.

---

## 5. Retrieval & Re-Ranking Methodology

### 1. Dense Semantic Vector Search
- **Embedding Model**: `nomic-embed-text:latest` via local Ollama.
- **Vector Dimension**: 768-dimensional float embeddings.
- **Vector Store**: ChromaDB persistent collection (`telecom_3gpp_knowledge`) using HNSW cosine space.

### 2. Telecom-Tailored Lexical Search (BM25)
- Custom Okapi BM25 implementation ($k_1=1.5$, $b=0.75$).
- **Telecom Regex Tokenizer**: `[a-z0-9]+(?:[\.\-_][a-z0-9]+)*` preserves dotted numbers (`4.2.8.0`), hyphenated identifiers (`5G-GUTI`, `S-NSSAI`), interface identifiers (`NG-U`, `N2`, `N4`), and acronyms (`AMF`, `UPF`, `SMF`, `5QI`).

### 3. Reciprocal Rank Fusion (RRF)
Combines candidate rankings from dense and lexical retrieval:
$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} w_m \cdot \frac{1}{k + \text{rank}_m(d)}$$
where $k=60$, $w_{\text{dense}}=0.6$, and $w_{\text{bm25}}=0.4$.

### 4. Specification-Aware Routing
- Detects explicit target specifications (e.g., `"in TS 28.535"`) and technical domain keywords (`"Closed control loop"` $\rightarrow$ TS 28.535, `"NG-RAN"` $\rightarrow$ TS 38.300, `"NAS"` $\rightarrow$ TS 24.501).
- Directs search candidate pools to relevant specifications, preventing smaller specifications from being overwhelmed by broader documents.

### 5. Structural Metadata-Aware Re-Ranking
Evaluates candidate chunks using document structure signals:
- **Candidate Pool Expansion**: Evaluates $4 \times \text{top\_k}$ candidates (minimum 30 candidates).
- **Clause Title Match (1.30x)**: Boosts chunks whose clause title tokens match key query keywords.
- **Definition Intent (1.45x)**: Prioritizes Clause 3 / 3.1 ("Definitions") for terminology inquiries.
- **Procedure Intent (1.35x)**: Boosts Stage-2 procedural sections in TS 23.502 for workflow questions.
- **Description Intent (1.25x)**: Prioritizes architectural overview sections for broad functional questions.

---

## 6. Grounded Generation, Verification & Safe Abstention

### Constrained Generator (Qwen2.5:1.5b)
- Uses local Ollama model `qwen2.5:1.5b` executed at temperature `0.0`.
- Prompts enforce strict JSON output mapping atomic statements to numbered evidence IDs (`E1`, `E2`, ...).

### Multi-Gate Grounding Verification
1. **Citation Validation Gate**: Validates that all cited evidence IDs exist in the retrieved prompt context and verifies specification name, clause number, and clause title.
2. **Deterministic Claim-Support Verifier**: Compares substantive n-grams and technical terminology in each claim against the cited evidence chunk.
3. **Safe Abstention Policy Engine**: Replaces ungrounded generation with a clean abstention (`status: "abstain"`, `answer: null`) under any of these conditions:
   - Retrieval returns zero evidence or insufficient relevance scores.
   - The query addresses out-of-scope topics (e.g. IEEE 802.11, Kubernetes).
   - The query contains adversarial or nonexistent premises (e.g. "7G holographic teleportation").
   - Evidence does not substantiate the claims made by the model.

---

## 7. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.10–3.13 | Core runtime environment |
| **API Framework** | FastAPI, Uvicorn, Pydantic v2 | High-throughput asynchronous REST API |
| **Vector Store** | ChromaDB (HNSW Persistent) | Local persistent vector indexing and filtering |
| **Embeddings & LLM** | Ollama (`nomic-embed-text`, `qwen2.5:1.5b`) | Offline, private local inference |
| **Document Processing** | `python-docx` | Extraction of DOCX styles, tables, and XML elements |
| **Web UI** | Streamlit | Interactive engineer-facing demonstration interface |
| **Testing & Quality** | Pytest, pytest-cov | Automated test execution and regression prevention |

---

## 8. Project Structure

```
3gpp-grounded-rag/
├── api/                             # FastAPI application package
│   ├── main.py                      # Application entrypoint & lifespan management
│   ├── routes.py                    # REST API route handlers (/health, /metadata, /ask)
│   ├── models.py                    # Pydantic request & response schemas
│   ├── service.py                   # RAG service coordinator
│   └── dependencies.py              # Dependency injection provider
├── data/
│   ├── raw/                         # Source 3GPP specifications (.docx)
│   ├── processed/                   # Chunks (.jsonl) and corpus manifest
│   └── vectorstore/                 # ChromaDB persistent database (local SQLite/HNSW)
├── docs/                            # Architectural design and validation reports
│   ├── corpus_inspection_report.md
│   ├── ingestion_validation_report.md
│   ├── retrieval_architecture.md
│   ├── retrieval_baseline_report.md
│   ├── retrieval_benchmark_v2_report.md
│   ├── specification_aware_routing_report.md
│   ├── generation_architecture.md
│   └── generation_evaluation_report.md
├── evaluation/
│   ├── retrieval/                   # Retrieval benchmark datasets & runners
│   │   ├── retrieval_dataset.json   # 21 authoritative benchmark queries
│   │   ├── retrieval_results.json   # Verified benchmark evaluation results
│   │   ├── heldout_results.json     # 6-query held-out generalization results
│   │   └── run_evaluation.py        # Retrieval evaluation executable script
│   └── generation/                  # Generation evaluation datasets & runners
│       ├── generation_dataset.json  # 30-query end-to-end evaluation dataset
│       ├── generation_results.json  # Generation metrics & latency breakdown
│       └── run_generation_evaluation.py # Generation evaluation executable script
├── generation/                      # Generation & verification pipeline
│   ├── generator.py                 # Structured prompt builder & Ollama caller
│   ├── citation_validator.py        # Authoritative citation verification
│   ├── claim_verifier.py            # Token-level claim containment verifier
│   ├── evidence_gate.py             # Pre-generation sufficiency gate
│   ├── abstention.py                # Safe abstention policy engine
│   └── pipeline.py                  # End-to-end generation workflow
├── ingestion/                       # Document ingestion & parsing package
│   ├── ingest.py                    # Full corpus ingestion entrypoint
│   ├── inspect_documents.py         # Empirical document inspection & stats
│   ├── docx_parser.py               # Low-level python-docx XML extractor
│   ├── chunker.py                   # Hierarchical clause chunker
│   ├── table_parser.py              # Markdown table converter
│   └── models.py                    # Formal chunk dataclass definitions
├── retrieval/                       # Retrieval & ranking engine
│   ├── index_corpus.py              # Embedding & Chroma indexing script
│   ├── retriever.py                 # SemanticRetriever & HybridRetriever
│   ├── bm25.py                      # Okapi BM25 with telecom tokenization
│   ├── router.py                    # Specification-aware query router
│   ├── vector_store.py              # ChromaDB client wrapper
│   └── embedding.py                 # Ollama embedding client
├── scripts/                         # Diagnostic and QA utility scripts
│   ├── qa_fastapi_final.py          # Automated API test suite
│   └── smoke_test_api.py            # Quick live integration smoke test
├── tests/                           # 90 automated unit & integration tests
├── .env.example                     # Environment configuration template
├── requirements.txt                 # Pinned project dependencies
└── streamlit_app.py                 # Streamlit visual demonstration interface
```

---

## 9. Installation & Setup

### Prerequisites
- Python 3.10+ (tested up to Python 3.13)
- [Ollama](https://ollama.ai/) installed and running locally

### 1. Pull Ollama Models
Ensure Ollama is running (`ollama serve`), then pull the required models:
```bash
ollama pull nomic-embed-text:latest
ollama pull qwen2.5:1.5b
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Clone the repository
git clone https://github.com/Dipakk7/3gpp-grounded-rag.git
cd 3gpp-grounded-rag

# Create virtual environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Or Windows Command Prompt:
# .\.venv\Scripts\activate.bat
# Or Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```
Default parameters point to localhost services (`OLLAMA_URL=http://localhost:11434`, `VECTORSTORE_PATH=data/vectorstore`).

### 4. Optional: Run Ingestion & Indexing
The repository includes the processed chunks and indices. To re-run the pipeline from raw files:
```bash
# Parse raw DOCX files and generate chunks
python ingestion/ingest.py

# Embed chunks and build ChromaDB index
python retrieval/index_corpus.py
```

---

## 10. Running the Application

### Start the FastAPI Backend
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Start the Streamlit Demonstration UI
In a separate terminal window (with virtual environment activated):
```bash
streamlit run streamlit_app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to interact with the visual interface.

---

## 11. REST API Reference

### `GET /health`
Returns the operational health and readiness of the vector store, BM25 index, and model endpoints.

**Example Response:**
```json
{
  "status": "ok",
  "service": "3gpp-grounded-rag",
  "version": "1.0.0",
  "details": {
    "initialized": true,
    "vector_store_ready": true,
    "vector_store_chunk_count": 6737,
    "bm25_ready": true,
    "bm25_chunk_count": 6737,
    "embedding_model": "nomic-embed-text:latest",
    "generation_model": "qwen2.5:1.5b"
  }
}
```

### `GET /metadata`
Returns information on the indexed specifications, chunk counts, and model configurations.

### `POST /ask`
Submits a query to the full grounded question-answering pipeline.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the NG User Plane (NG-U) interface defined between in NG-RAN?", "top_k": 5}'
```

**Example Response (Answered):**
```json
{
  "status": "answered",
  "answer": "The NG User Plane (NG-U) interface is defined between the NG-RAN node and the UPF [TS 38.300, Clause 4.3.1.1 — NG User Plane].",
  "citations": [
    {
      "specification": "TS 38.300",
      "version": "V18.10.0",
      "clause_number": "4.3.1.1",
      "clause_title": "NG User Plane",
      "formatted_citation": "[TS 38.300, Clause 4.3.1.1 — NG User Plane]"
    }
  ],
  "evidence": [
    {
      "chunk_id": "TS_38.300-V18.10.0-4.3.1.1-P001",
      "specification": "TS 38.300",
      "clause_number": "4.3.1.1",
      "clause_title": "NG User Plane",
      "score": 0.0275
    }
  ],
  "reason": null,
  "latency_breakdown": {
    "retrieval_ms": 1845.2,
    "generation_ms": 42100.5,
    "total_ms": 43945.7
  }
}
```

**Example Response (Safe Abstention):**
```json
{
  "status": "abstain",
  "answer": null,
  "citations": [],
  "evidence": [],
  "reason": "The question cannot be answered from the provided 3GPP specifications or contains adversarial premises.",
  "latency_breakdown": {
    "retrieval_ms": 1210.4,
    "generation_ms": 0.0,
    "total_ms": 1210.4
  }
}
```

---

## 12. Verification & Testing

### Running the Test Suite
The repository includes a comprehensive 90-test automated suite covering API contracts, clause detection, retrieval refinement, generation gating, and Streamlit integration:

```bash
pytest -v
```

**Verified Test Breakdown:**
- `tests/test_api.py`: 12 tests (endpoints, validation, error sanitization, CORS)
- `tests/test_clause_detection.py`: 6 tests (heading regex, annex formatting, noise rejection)
- `tests/test_fix3_retrieval_refinement.py`: 5 tests (structural metadata re-ranking boosts)
- `tests/test_generation.py`: 17 tests (claim verification, citation gating, prompt injection defense)
- `tests/test_ingestion_pipeline.py`: 18 tests (breadcrumbs, tables, chunk IDs, manifest)
- `tests/test_retrieval.py`: 14 tests (dense search, BM25 tokenizer, RRF fusion)
- `tests/test_specification_routing.py`: 12 tests (explicit/implicit routing, fallback)
- `tests/test_streamlit_ui.py`: 6 tests (UI health checks, mock responses, layout parsing)

**Result:** **90 passed in ~93s**

### Running Benchmark Evaluations

```bash
# Execute 21-query authoritative retrieval evaluation
python evaluation/retrieval/run_evaluation.py

# Execute 30-query end-to-end generation evaluation
python evaluation/generation/run_generation_evaluation.py

# Run API integration QA script
python scripts/qa_fastapi_final.py
```

---

## 13. Limitations & Future Roadmap

### Current Limitations
1. **CPU Generation Latency**: Executing `qwen2.5:1.5b` locally on general-purpose CPUs yields generation latencies of ~40–110s per query. This reflects local CPU-bound transformer autoregressive decoding rather than retrieval latency.
2. **Small Parameter Model Context Bounds**: When questions require synthesizing complex multi-page procedural call flows spanning several specifications, smaller models (1.5B parameters) may produce incomplete structured JSON, triggering safe abstention.
3. **Static Specification Corpus**: The current index is built over 5 core Release 18 specifications. Cross-specification references to unindexed documents (e.g. TS 33.501 for security) cannot be retrieved.

### Future Roadmap
- **Accelerated Inference**: Deploying model serving with vLLM on dedicated GPUs for sub-second generation latencies.
- **Cross-Encoder Re-Ranking**: Implementing a domain-tuned cross-encoder (e.g. BGE-Reranker-Large) downstream of RRF for finer-grained ranking precision.
- **Corpus Expansion**: Ingesting the complete 3GPP Release 18 catalog, including Security (TS 33.501) and Charging Architecture (TS 32.240).
- **Multi-Modal Architecture**: Incorporating call-flow diagrams and protocol sequence charts via vision-language models.

---

## 14. License & Attribution

This project is developed for personal portfolio, educational, and technical demonstration purposes.

- **Source Code**: Available under the permissive terms of the MIT License for portfolio demonstration.
- **Standards Attribution**: 3GPP™ specifications and materials remain the property and copyright of the 3GPP Organizational Partners (ARIB, ATIS, CCSA, ETSI, TSDSI, TTA, TTC). Specifications are referenced and parsed in accordance with 3GPP working procedures for research, technical evaluation, and educational illustration. Neither 3GPP nor any Organizational Partner endorses or certifies this implementation.

# Mavenir 3GPP Grounded RAG System

A production-grade, citation-grounded Retrieval-Augmented Generation (RAG) system for 3GPP 5G Technical Specifications. Built for mission-critical telecom engineering QA, it enforces deterministic citation validation, token-level claim support verification, and strict safe abstention against hallucinations.

---

## 1. Executive Summary & Key Results

| Component | Benchmark Metric | Verified Final Result |
| :--- | :--- | :--- |
| **Authoritative Retrieval (21Q)** | **Hit@5 Recall** | **100.0% (21/21)** |
| | **Hit@3 Recall** | **90.5% (19/21)** |
| | **Hit@1 Recall** | **66.7% (14/21)** |
| | **Mean Reciprocal Rank (MRR)** | **0.7992** |
| **Held-Out Generalization (6Q)** | **Hit@5 Recall** | **83.3% (5/6)** |
| **Grounded Generation (30Q)** | **Citation Validity Rate** | **100.0% (20/20 citations)** |
| | **Citation Completeness Rate** | **100.0%** |
| | **Claim Support Rate** | **100.0% (15/15 claims)** |
| | **Unsupported Claim Rate (Hallucinations)** | **0.0% (0/15 claims)** |
| | **Abstention Accuracy** | **100.0% (8/8 non-answerable)** |
| | **False Answer Rate** | **0.0% (0/8 non-answerable)** |
| | **Answer Correctness (Answerable)** | **63.64% (14/22 queries)** |
| **Test Suite** | **Pytest Unit & Integration Tests** | **90/90 PASS (100%)** |
| **Vector Corpus** | **Chroma Vector Store** | **6,737 / 6,737 Vectors** |

---

## 2. System Architecture

The pipeline implements an end-to-end multi-stage architecture guaranteeing that every answer is backed by verifiable 3GPP specification text:

```
[ User Query ]
      │
      ▼
[ Fix #2 Specification-Aware Router ] ─── (Matches explicit/implicit 3GPP spec targets)
      │
      ├────────────────────────┬────────────────────────┐
      ▼                        ▼                        ▼
[ Dense Chroma Retriever ] [ Custom BM25 Index ]  [ Structural Pool (4*k) ]
 (nomic-embed-text: 768d)   (Telecom Tokenizer)        │
      │                        │                        │
      └───────────┬────────────┘                        │
                  ▼                                     │
     [ Reciprocal Rank Fusion (RRF) ]                   │
                  │                                     │
                  ▼                                     ▼
        [ Fix #3 Deterministic Structural Metadata Refiner ]
         (Clause title, definition §3, procedure §4 boosts)
                  │
                  ▼
        [ Evidence Sufficiency Gate ] ── (Abstains if retrieval empty/irrelevant)
                  │
                  ▼
        [ Grounded Generator (Qwen2.5:1.5b) ] ── (Constrained JSON schema)
                  │
                  ▼
        [ Citation Validator ] ── (Validates spec, clause number, clause title)
                  │
                  ▼
        [ Claim-Support Verifier ] ── (Token-level containment & n-gram checks)
                  │
                  ▼
        [ Safe Abstention Policy Engine ]
                  │
         ┌────────┴────────┐
         ▼                 ▼
   [ Grounded Answer ]  [ Safe Abstention ]
```

---

## 3. Source Corpus & Ingestion Pipeline

### 3GPP Technical Specifications
The system indexes 5 foundational 3GPP Release 18 specifications parsed directly from raw Microsoft Word (`.docx`) standard documents:

1. **3GPP TS 23.501 (V18.12.0)**: *System Architecture for the 5G System (5GS)* — 2,423 chunks
2. **3GPP TS 23.502 (V18.14.0)**: *Procedures for the 5G System (5GS)* — 2,217 chunks
3. **3GPP TS 24.501 (V18.13.0)**: *NAS Protocol for 5GS; Stage 3* — 1,607 chunks
4. **3GPP TS 28.535 (V18.2.0)**: *Management and Orchestration; Closed Control Loop Assurance* — 86 chunks
5. **3GPP TS 38.300 (V18.10.0)**: *NR; NR and NG-RAN Overall Description; Stage 2* — 404 chunks
**Total Index:** **6,737 authoritative chunks / 6,737 vectors**

### Ingestion Engineering Highlights
- **Clause Hierarchy Extraction**: Robust parser detects 3GPP section numbers down to subclauses (e.g. `4.2.8.0`, `5.7.1.3.1`) and builds hierarchical breadcrumbs (`4 > 4.2 > 4.2.8 > 4.2.8.0`).
- **Table Preservation**: Formats 673 technical tables into structured Markdown with column alignment while stripping 8 layout-only cover page tables.
- **TOC Stripping**: Filters 4,325 Table of Contents lines to eliminate page-number noise and index contamination.
- **Semantic Chunking**: Respects clause boundaries, splitting large clauses (>2,000 characters) at natural paragraph boundaries while maintaining metadata context.

---

## 4. Retrieval & Ranking Engine

### Hybrid Search (Dense + Lexical + RRF)
- **Dense Vector Search**: Powered by `nomic-embed-text:latest` (768-dimensional embeddings) using cosine similarity in ChromaDB.
- **Telecom-Tailored BM25**: Custom lexical engine with tokenization preserving dotted clause IDs (`4.2.2.2.2`), 3GPP identifiers (`5G-GUTI`, `S-NSSAI`, `Npcf_SMPolicyControl`), and acronyms (`AMF`, `UPF`, `SMF`, `5QI`).
- **Reciprocal Rank Fusion (RRF)**: Combines dense and lexical ranks ($k=60$) to ensure high candidate variety.

### Fix #2: Specification-Aware Routing
- Detects explicit specification mentions (e.g., `"in TS 28.535"`) and technical domain keywords (e.g., `"Closed control loop"` $\rightarrow$ TS 28.535, `"NG-RAN"` $\rightarrow$ TS 38.300, `"NAS"` $\rightarrow$ TS 24.501).
- Filters candidates to target specifications while falling back gracefully to full-corpus search when unscoped.

### Fix #3: Structural Metadata-Aware Retrieval Refinement
Resolves semantic dilution in broad queries by deterministically re-ranking candidates using document structure signals:
- **Expanded Candidate Pool**: Retrieves $4 \times \text{top\_k}$ candidates before re-ranking.
- **Clause Title Matching (1.30x)**: Boosts chunks whose clause title tokens match key query keywords.
- **Definition Intent (1.45x)**: Boosts Clause 3 / 3.1 ("Terms and Definitions") when queries ask for definitions or abbreviations.
- **Procedure Intent (1.35x)**: Prioritizes TS 23.502 Stage-2 procedure flows when queries ask for procedural execution steps.
- **Description Intent (1.25x)**: Prioritizes overview and functional description clauses for architectural questions.

---

## 5. Grounded Generation, Verification & Safe Abstention

### Constrained Generation (Qwen2.5:1.5b)
- Prompts enforce strict JSON output schema containing atomic claims mapped directly to numbered evidence IDs (`E1`, `E2`, etc.).
- Temperature set to `0.0` for deterministic, factual outputs.

### Citation Validation Gate
- Validates that every citation refers to an evidence chunk provided in the prompt context.
- Confirms specification name, clause number, clause title, and optional table IDs.

### Deterministic Claim-Support Verifier
- Evaluates substantive technical terminology in each claim against the cited evidence text.
- Rejects ungrounded claims with zero tolerance for hallucination.

### Safe Abstention Engine
The system safely abstains (`status: "abstain"`, `answer: null`) under any of the following conditions:
1. Retrieval returns no evidence or evidence below sufficiency thresholds.
2. The question is explicitly unanswerable from the in-corpus specifications.
3. The question is out-of-corpus (e.g., IEEE, Kubernetes, CNCF).
4. The question contains false or adversarial premises (e.g., "7G holographic teleportation").
5. LLM inference times out or produces malformed JSON.

---

## 6. REST API Reference (FastAPI)

The REST API exposes the full RAG pipeline with interactive Swagger documentation available at `/docs`.

### Endpoints

#### `GET /health`
Returns readiness and status of vector store, BM25 index, and embedding/LLM backends.
```json
{
  "status": "ok",
  "service": "mavenir-3gpp-rag",
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

#### `GET /metadata`
Returns loaded specification metadata, chunk breakdowns, and pipeline parameters.

#### `POST /ask`
Submit technical question for grounded question-answering.

**Request:**
```json
{
  "question": "What is the NG User Plane (NG-U) interface defined between in NG-RAN?",
  "top_k": 5
}
```

**Response (Answered):**
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
  "evidence": [...],
  "reason": null,
  "latency_breakdown": {
    "retrieval_ms": 2263.13,
    "generation_ms": 53409.55,
    "total_ms": 55672.94
  }
}
```

**Response (Safe Abstention):**
```json
{
  "status": "abstain",
  "answer": null,
  "citations": [],
  "evidence": [...],
  "reason": "The requested information could not be supported by the provided 3GPP evidence.",
  "latency_breakdown": {
    "retrieval_ms": 2314.04,
    "generation_ms": 63878.34,
    "total_ms": 66192.57
  }
}
```

---

## 7. Setup & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- [Ollama](https://ollama.ai/) installed and running locally

### 1. Install Ollama Models
```bash
ollama pull nomic-embed-text:latest
ollama pull qwen2.5:1.5b
```

### 2. Setup Virtual Environment
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` (optional, defaults point to local Ollama on port 11434):
```bash
cp .env.example .env
```

### 4. Run FastAPI Server
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser for the interactive Swagger UI.

### 5. Run Streamlit UI Demonstration
```bash
streamlit run streamlit_app.py
```
Open [http://localhost:8501](http://localhost:8501) for the interactive 3GPP RAG visual demonstration interface.

---

## 8. Testing & Evaluation

### Run Test Suite (90 Tests)
```bash
pytest -v
```

### Run Retrieval Evaluation
```bash
python evaluation/retrieval/run_retrieval_evaluation.py
```

### Run Generation Evaluation
```bash
python evaluation/generation/run_generation_evaluation.py
```

---

## 9. Known Limitations

1. **CPU Inference Latency**: Local execution of `qwen2.5:1.5b` on CPU produces an average generation latency of ~60–110 seconds per query. This is an expected artifact of local CPU-bound transformer decoding and not a retrieval bottleneck.
2. **Safe Abstentions under Token Constraints**: When complex multi-phase procedural queries exceed local token budgets or generation timeouts, the system safely abstains rather than producing speculative, ungrounded responses.


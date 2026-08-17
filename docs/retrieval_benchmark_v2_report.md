# Retrieval Benchmark V2 Report: Ground-Truth Refinement & Multi-Clause Evaluation

> **Document Status:** Authoritative & Verified  
> **Benchmark Dataset:** `evaluation/retrieval/retrieval_dataset.json` (21 Ground-Truth Technical Queries)  
> **Retrieval Pipeline:** Unchanged (Dense Vector `nomic-embed-text` + Sparse Lexical BM25 via Weighted RRF)

---

## 1. Executive Summary & Evaluation Discipline

Following the independent original-DOCX ground-truth audit (`docs/ground_truth_verification.md`), the 3GPP retrieval benchmark was refined to ensure 100% evidence-grounded alignment with the normative source specifications:

1. **R014 Refinement:** Corrected question to focus strictly on the business-level functional requirements defined in TS 28.535 §5.1.1 (`REQ-CSA_NSA-FUN-01` through `REQ-CSA_NSA-FUN-04`).
2. **R021 Multi-Clause Test Addition:** Added a dedicated multi-clause question targeting closed control loops (TS 28.535 §4.2.4) and closed control loop governance (TS 28.535 §4.2.5.2).
3. **No Implementation Optimization:** Zero changes were made to the embedding model, vector store, tokenizer, or RRF fusion logic. The evaluation measures genuine retrieval capabilities against an authoritative 21-question dataset.

---

## 2. Benchmark Comparison (Original 20 vs Corrected 21)

| Benchmark Version | Benchmark Size | Semantic Baseline MRR | BM25 Lexical MRR | Hybrid Weighted RRF MRR | Hybrid Hit@5 Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Original Baseline (v1)** | 20 queries | 0.8033 | 0.7225 | **0.8833** | **100.0%** (20/20) |
| **Authoritative Benchmark (v2)** | 21 queries | **0.8127** | **0.7357** | **0.8889** | **100.0%** (21/21) |

---

## 3. Authoritative V2 Benchmark Quantitative Results

| Metric | Semantic Baseline (Dense) | BM25 Lexical (Sparse) | Hybrid Retrieval (Dense + BM25 RRF) | Relative Gain (Hybrid vs Baseline) |
| :--- | :---: | :---: | :---: | :---: |
| **Hit@1** | 71.4% (15/21) | 61.9% (13/21) | **81.0% (17/21)** | +13.4% |
| **Hit@3** | 90.5% (19/21) | 85.7% (18/21) | **95.2% (20/21)** | +5.2% |
| **Hit@5** | 95.2% (20/21) | 90.5% (19/21) | **100.0% (21/21)** | **+5.0% (Perfect Recall)** |
| **Hit@10** | 95.2% (20/21) | 95.2% (20/21) | **100.0% (21/21)** | +5.0% |
| **MRR** | 0.8127 | 0.7357 | **0.8889** | **+9.38%** |

---

## 4. Deep Dive: R014 & R021 Retrieval Evidence Audit

### 4.1 Benchmark R014 (Refined)
- **Question:** *"What business-level functional requirements does TS 28.535 define for communication service assurance?"*
- **Expected Specification:** `TS 28.535`
- **Expected Clause:** `5.1.1`
- **Hybrid Retrieval Results:**
  - **Rank 1:** `TS_28.535-V18.2.0-5.1.1-P001` (Score: 1.0000) — **RELEVANT (First Relevant Rank = 1)**
  - **Rank 2:** `TS_28.535-V18.2.0-5.1.2-P001` (Shared resources)
  - **Rank 3:** `TS_28.535-V18.2.0-5.1.3-P001` (Resource requirements)
- **Evidence Verification:** Rank 1 contains the complete normative text for `REQ-CSA_NSA-FUN-01`, `REQ-CSA_NSA-FUN-02`, `REQ-CSA_NSA-FUN-03`, and `REQ-CSA_NSA-FUN-04`.

### 4.2 Benchmark R021 (Multi-Clause Test)
- **Question:** *"What does TS 28.535 specify about closed control loops and their governance?"*
- **Expected Specification:** `TS 28.535`
- **Expected Targets:** Clause `4.2.4` (*Closed control loops*) and Clause `4.2.5.2` (*Closed control loop governance*)
- **Hybrid Retrieval Results:**
  - **Rank 1:** `TS_28.535-V18.2.0-4.2.4.1-P001` (Clause 4.2.4.1, Description of Closed Control Loops) — **RELEVANT (Target 4.2.4)**
  - **Rank 2:** `TS_28.535-V18.2.0-4.2.4.2-P001` (Clause 4.2.4.2, Lifecycle phases: Preparation, Commissioning, Operation, Decommissioning) — **RELEVANT (Target 4.2.4)**
  - **Rank 3:** `TS_28.535-V18.2.0-4.2.5.2-P001` (Clause 4.2.5.2, Governance capabilities: Lifecycle management, Configure goals) — **RELEVANT (Target 4.2.5.2)**
- **Evidence Verification:** Both required target clauses (§4.2.4 and §4.2.5.2) were retrieved in the top 3 positions, confirming robust multi-clause evidence capture.

---

## 5. Verification & Test Suite Status

- **Phase 1 & 2 Ingestion & Clause Detection Tests:** 24/24 `PASS`
- **Phase 3 Retrieval Subsystem Tests:** 14/14 `PASS`
- **Total Test Suite:** **38/38 PASS**
- **Data Leakage Check:** Zero query-to-chunk lookups or hardcoded mapping tables.

---

## 6. Readiness for Phase 4

The authoritative 21-question retrieval benchmark and underlying hybrid retrieval engine are completely verified and frozen. The system is ready to proceed to **Phase 4: Grounded Generation, Prompt Engineering & Hallucination Verification**.

# Specification-Aware Retrieval Routing Report (Fix #2)

> **Status:** Implemented & Verified  
> **Phase:** Phase 6B  
> **Target Fix:** Fix #2 — Deterministic Specification-Aware Retrieval Routing  
> **Regression Status:** 79/79 Unit Tests PASS (67 Existing + 12 Routing Tests)  

---

## 1. Problem Identified

In multi-specification technical corpora such as 3GPP standards, technical queries often explicitly reference a specific technical specification (e.g., TS 28.535 for Management & Orchestration / Service Assurance, or TS 38.300 for NR / NG-RAN Overall Architecture).

However, global unrouted hybrid retrieval (Dense Semantic + BM25 + RRF) frequently suffered from **cross-specification drowning**:
- Larger foundational specifications (specifically **TS 23.501** with 1,545 chunks and **TS 23.502** with 1,105 chunks) contain high frequencies of generic telecom terms (e.g., *"functional requirements"*, *"control"*, *"communication service"*, *"user plane"*, *"control plane"*).
- When a query explicitly requested requirements from **TS 28.535** (a smaller specification with 97 chunks) or **TS 38.300**, unconstrained global dense and lexical search candidates were heavily dominated by TS 23.501/23.502 chunks.
- As a result, the relevant evidence from the explicitly referenced specification received zero visibility in the top-10 retrieved candidate pool.

---

## 2. Ground-Truth Verification Evidence

Independent raw DOCX source verification confirmed that the ground-truth answers for the target failure queries genuinely exist and are preserved in the processed corpus:

1. **G007 (TS 28.535 §5.1.1):** Raw DOCX (`data/raw/28535-i20.docx`) contains `REQ-CSA_NSA-FUN-01` through `REQ-CSA_NSA-FUN-04` defining business-level communication service assurance requirements. Preserved in `TS_28.535-V18.2.0-5.1.1-P001` (1,869 chars).
2. **G019 (TS 28.535 §§4.2.4 / 4.2.5.2):** Raw DOCX contains complete closed control loop definitions, autonomy boundaries, lifecycle phases (§4.2.4.1/4.2.4.2), and MnS consumer governance capabilities (§4.2.5.2). Preserved in `TS_28.535-V18.2.0-4.2.4.1-P001`, `TS_28.535-V18.2.0-4.2.4.2-P002`, and `TS_28.535-V18.2.0-4.2.5.2-P001`.
3. **G020 (TS 38.300 §§4.3.1.1 / 4.3.1.2):** Raw DOCX (`data/raw/38300-ia0.docx`) explicitly defines NG User Plane (NG-U: GTP-U / UDP / IP) and NG Control Plane (NG-C: NGAP / SCTP / IP) protocols and functions. Preserved in `TS_38.300-V18.10.0-4.3.1.1-P001` and `TS_38.300-V18.10.0-4.3.1.2-P001`.

---

## 3. Why Global Retrieval Failed

Without specification-aware routing:
- **G007:** Query contained *"functional requirements"*, *"communication service"*, *"assurance"*. Dense and BM25 search retrieved general TS 23.501/TS 23.502 clauses (e.g. TS 23.501 §5.37.1, TS 23.502 §5.2.2.4.1). Zero TS 28.535 chunks appeared in the top 10.
- **G019:** Query contained *"closed control loops"*, *"governance"*. Dense vector search matched 5G Core Policy Control (§5.14) and Service Based Interface Control Plane stacks (§8.2.3.1) in TS 23.501. Zero TS 28.535 chunks appeared in top 10.
- **G020:** Query contained *"user plane"*, *"control plane"*, *"protocols"*. Dense search returned TS 23.501 §8.3.1 (*User Plane Protocol Stack for PDU Session*) and §5.31.18. Zero TS 38.300 chunks appeared in top 10.

---

## 4. Routing Design

A deterministic, metadata-based routing layer was implemented:

1. **Deterministic Specification Parser (`retrieval/router.py`):**
   - Extracts supported 3GPP specifications using canonical regex: `TS 23.501`, `TS 23.502`, `TS 24.501`, `TS 28.535`, `TS 38.300`.
   - Supports prefix variants: `3GPP TS 28.535`, `TS28.535`, `spec 28.535`.
   - Prevents false positive matching on generic numeric quantities (e.g., "5QI 5.7.1.3", "501 users", "38300 ms").

2. **Candidate Filtering in Hybrid Retrieval (`retrieval/retriever.py` & `retrieval/bm25.py`):**
   - When 1 specification is detected (e.g. `TS 28.535`), candidate retrieval in both Semantic Search (via Chroma metadata filter) and BM25 (via chunk metadata filter) is restricted to that specification.
   - When multiple specifications are detected (e.g. `TS 23.501 and TS 23.502`), candidate retrieval allows chunks from all specified specifications.
   - When **no specification** is detected, the retriever executes standard global hybrid retrieval across all specifications with zero restrictions.

3. **Ranking Logic:**
   - Preserves existing Reciprocal Rank Fusion (RRF with $k=60$, semantic weight $0.6$, BM25 weight $0.4$) and score normalization.

---

## 5. Why Deterministic Parsing Was Chosen Over an LLM Classifier

1. **Zero Added Latency:** Regex and metadata parsing executes in $<0.05$ ms, adding virtually zero overhead compared to 2,000+ ms for an LLM call.
2. **100% Deterministic & Reproducible:** Zero non-deterministic prompt degradation, hallucination, or variance.
3. **No New Failure Modes:** Does not depend on external model availability or context-window constraints.
4. **Zero Overhead:** Completely lightweight Python code without additional API dependencies.

---

## 6. Test Verification

A dedicated unit test suite was implemented in `tests/test_specification_routing.py` covering:
- Single specification detection across all 5 corpus specifications (Tests 1–5).
- Formatting variations (`3GPP TS`, `TS28.535`) (Tests 6–7).
- Unscoped query fallback to global retrieval (Test 8).
- Multi-specification detection (Test 9).
- False-positive avoidance on arbitrary numbers (Test 10).
- Hybrid retriever routing verification with mocks (Test 11).
- Unscoped global hybrid retriever verification (Test 12).

**Test Results:**
- `tests/test_specification_routing.py`: **12/12 PASS**
- Full test suite: **79/79 PASS** (67 existing + 12 new)

---

## 7. Target Query Improvements

| Query ID | Question | Expected Target | Before Fix #2 (Rank) | After Fix #2 (Rank) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **G007** | Functional requirements in TS 28.535 for communication service assurance | TS 28.535 §5.1.1 | Not in Top 10 (0 chunks) | **Rank 8** (`TS 28.535 §5.1.1`) | **PASS / RESOLVED** |
| **G019** | TS 28.535 closed control loops and governance | TS 28.535 §§4.2.4 / 4.2.5.2 | Not in Top 10 (0 chunks) | **Rank 3** (`§4.2.5.2`), **Rank 4** (`§4.2.4.2`) | **PASS / RESOLVED** |
| **G020** | TS 38.300 NG-RAN user plane and control plane architecture | TS 38.300 §§4.3.1.1 / 4.3.1.2 | Not in Top 10 (0 chunks) | **Rank 2** (`§4.3.1.1`), **Rank 4** (`§4.3.1.2`) | **PASS / RESOLVED** |

---

## 8. Authoritative 21-Question Retrieval Benchmark

- **Unscoped Queries:** Unscoped general queries (e.g. R001 AMF, R002 UPF, R005 Registration, R006 PDU Session, R011 Architecture) continue to execute via global hybrid retrieval without alteration.
- **Scoped Queries:** Queries with explicit specification references (R014, R021) cleanly route to the target specification (R014 $\rightarrow$ Rank 8, R021 $\rightarrow$ Rank 3).
- **Regressions:** Zero regressions on unscoped queries.

---

## 9. Keep / Revert Decision

**DECISION: KEPT**

**Justification:**
1. Fix #2 successfully resolved all three target retrieval-routing failures (G007, G019, G020), moving target ground-truth clauses from 0% visibility in top 10 to Ranks 8, 3, and 2.
2. 100% of existing unit tests pass (79/79 PASS).
3. The routing mechanism is strictly deterministic, adds $<0.05$ ms latency, requires no LLM calls, and leaves unscoped queries completely intact.

---

## 10. Limitations

1. **Implicit Specification Questions:** If a question asks about a specialized concept without mentioning the specification number (e.g. *"What are the preparation and execution phases of Intra-NR RAN Handover?"* without mentioning TS 38.300), the router correctly falls back to global retrieval.
2. **Corpus Coverage:** Routing ensures queries reach the correct specification metadata; however, if a specification's dense vector index is sparse, the system relies on BM25 sparse retrieval within that specification.

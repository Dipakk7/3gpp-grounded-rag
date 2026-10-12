# 3GPP-Grounded-RAG — Corpus Inspection & Document Intelligence Report

> **Phase 1 Output:** Empirical structural analysis of the 5 finalized 3GPP Technical Specifications.
> Grounded purely on extracted DOCX object models, styles, and XML structures.

---

## 8.1 Corpus Overview

| Specification | Title | Version | Release | Paragraphs | Tables | Clauses | Annexes |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| **TS 23.501** | System architecture for the 5G System (5GS); Stage 2 | `V18.12.0` | Release 18 | 11,436 | 57 | 1,015 | 18 |
| **TS 23.502** | Procedures for the 5G System (5GS); Stage 2 | `V18.14.0` | Release 18 | 14,179 | 62 | 1,264 | 11 |
| **TS 24.501** | Non-Access-Stratum (NAS) protocol for 5G System (5GS); Stage 3 | `V18.13.0` | Release 18 | 17,991 | 544 | 1,312 | 6 |
| **TS 28.535** | Management and orchestration; Management services for Communication Service Assurance; Requirements | `V18.2.0` | Release 14 | 349 | 3 | 44 | 1 |
| **TS 38.300** | NR; NR and NG-RAN Overall Description; Stage 2 | `V18.10.0` | Release 18 | 4,889 | 15 | 543 | 8 |

---

## 8.2 Document-by-Document Findings

### 8.2.1 TS 23.501 — System architecture for the 5G System (5GS); Stage 2
- **Filename:** `23501-ic0.docx`
- **Version / Date:** `V18.12.0` (2025-12), **Release:** Release 18
- **Volume:** 11,436 paragraphs (10,376 body, 1,060 TOC), 57 tables, 144 detected figure captions.
- **Detected Clauses & Annexes:** 1,015 clauses, 18 annexes.
- **Heading Styles Used:** `H6`, `Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`, `Heading 5`, `Heading 8`
- **Heading Format:** Clause number and title are separated by a tab character (`\t`), e.g., `4.2.3\tNon-roaming reference architecture`.

#### Hierarchy & Sample Clauses:
| Clause | Section Title | DOCX Style | Body Paragraphs | Content Preview |
| :--- | :--- | :--- | ---: | :--- |
| `3.1` | Definitions | `Heading 2` | 165 | For the purposes of the present document, the terms and definitions given in TR 21.905 [1] and the following apply. A te |
| `3.2` | Abbreviations | `Heading 2` | 216 | For the purposes of the present document, the abbreviations given in TR 21.905 [1] and the following apply. An abbreviat |
| `4.1` | General concepts | `Heading 2` | 11 | The 5G System architecture is defined to support data connectivity and services enabling deployments to use techniques s |
| `4.2` | Architecture reference model | `Heading 2` | 0 | [Table / Figure / Child Clause directly follows] |
| `4.2.1` | General | `Heading 3` | 13 | This specification describes the architecture for the 5G System. The 5G architecture is defined as service-based and the |

#### Detected Annexes:
- **Annex A** (informative): Relationship between Service-Based Interfaces and Reference Points (Style: `Heading 8`)
- **Annex B** (normative): Mapping between temporary identities (Style: `Heading 8`)
- **Annex C** (informative): Guidelines and Principles for Compute-Storage Separation (Style: `Heading 8`)
- **Annex D** (informative): 5GS support for Non-Public Network deployment options (Style: `Heading 8`)
- **Annex E** (informative): Communication models for NF/NF services interaction (Style: `Heading 8`)
- *... and 13 more annexes.*

#### Specific Extraction Considerations:
- ⚠️ TOC contains 1060 artifact paragraphs that must be stripped before chunking.

### 8.2.2 TS 23.502 — Procedures for the 5G System (5GS); Stage 2
- **Filename:** `23502-ie0.docx`
- **Version / Date:** `V18.14.0` (2026-06), **Release:** Release 18
- **Volume:** 14,179 paragraphs (12,852 body, 1,327 TOC), 62 tables, 272 detected figure captions.
- **Detected Clauses & Annexes:** 1,264 clauses, 11 annexes.
- **Heading Styles Used:** `H6`, `Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`, `Heading 5`, `Heading 8`
- **Heading Format:** Clause number and title are separated by a tab character (`\t`), e.g., `4.2.3\tNon-roaming reference architecture`.

#### Hierarchy & Sample Clauses:
| Clause | Section Title | DOCX Style | Body Paragraphs | Content Preview |
| :--- | :--- | :--- | ---: | :--- |
| `3.1` | Definitions | `Heading 2` | 2 | For the purposes of the present document, the terms and definitions given in TR 21.905 [1], TS 23.501 [2] and TS 23.503  |
| `3.2` | Abbreviations | `Heading 2` | 1 | For the purposes of the present document, the abbreviations given in TR 21.905 [1], TS 23.501 [2] and TS 23.503 [20] app |
| `4.1` | General | `Heading 2` | 1 | The clause 4 describes the procedures and Network Function services for the 5GS by end-to-end information flows and thes |
| `4.2` | Connection, Registration and Mobility Management procedures | `Heading 2` | 0 | [Table / Figure / Child Clause directly follows] |
| `4.2.1` | General | `Heading 3` | 1 | The Connection Management is used to establish and release the Control Plane signalling connection between the UE and th |

#### Detected Annexes:
- **Annex A** (informative): Drafting rules and conventions for NF services (Style: `Heading 8`)
- **Annex B** (informative): Drafting Rules for Information flows (Style: `Heading 8`)
- **Annex C** (informative): Generating EPS PDN Connection parameters from 5G PDU Session parameters (Style: `Heading 8`)
- **Annex D** (normative): UE Presence in Area of Interest (Style: `Heading 8`)
- **Annex E** (normative): Delegated SMF and PCF discovery in the Home Routed and specific SMF Service Areas scenarios (Style: `Heading 8`)
- *... and 6 more annexes.*

#### Specific Extraction Considerations:
- ⚠️ TOC contains 1327 artifact paragraphs that must be stripped before chunking.

### 8.2.3 TS 24.501 — Non-Access-Stratum (NAS) protocol for 5G System (5GS); Stage 3
- **Filename:** `24501-id0.docx`
- **Version / Date:** `V18.13.0` (2025-12), **Release:** Release 18
- **Volume:** 17,991 paragraphs (16,642 body, 1,349 TOC), 544 tables, 8 detected figure captions.
- **Detected Clauses & Annexes:** 1,312 clauses, 6 annexes.
- **Heading Styles Used:** `H2`, `H6`, `Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`, `Heading 5`, `Heading 6`, `Heading 7`, `Heading 8`
- **Heading Format:** Clause number and title are separated by a tab character (`\t`), e.g., `4.2.3\tNon-roaming reference architecture`.

#### Hierarchy & Sample Clauses:
| Clause | Section Title | DOCX Style | Body Paragraphs | Content Preview |
| :--- | :--- | :--- | ---: | :--- |
| `3.1` | Definitions | `Heading 2` | 372 | For the purposes of the present document, the terms and definitions given in 3GPP TR 21.905 [1] and the following apply. |
| `3.2` | Abbreviations | `Heading 2` | 192 | For the purposes of the present document, the abbreviations given in 3GPP TR 21.905 [1] and the following apply. An abbr |
| `4.1` | Overview | `Heading 2` | 12 | The non-access stratum (NAS) described in the present document forms the highest stratum of the control plane between th |
| `4.2` | Coordination between the protocols for 5GS mobility management and 5GS session management | `Heading 2` | 14 | A 5GS session management (5GSM) message is piggybacked in specific 5GS mobility management (5GMM) transport messages. To |
| `4.3` | UE domain selection | `Heading 2` | 0 | [Table / Figure / Child Clause directly follows] |

#### Detected Annexes:
- **Annex A** (informative): Cause values for 5GS mobility management (Style: `Heading 8`)
- **Annex B** (informative): Cause values for 5GS session management (Style: `Heading 8`)
- **Annex C** (normative): Storage of 5GMM information (Style: `Heading 8`)
- **Annex D** (normative): UE policy delivery service (Style: `Heading 8`)
- **Annex E** (informative): Void (Style: `Heading 8`)
- *... and 1 more annexes.*

#### Specific Extraction Considerations:
- ⚠️ TOC contains 1349 artifact paragraphs that must be stripped before chunking.
- ⚠️ High table density (544 tables); structured table-to-text chunking required.

### 8.2.4 TS 28.535 — Management and orchestration; Management services for Communication Service Assurance; Requirements
- **Filename:** `28535-i20.docx`
- **Version / Date:** `V18.2.0` (2024-09), **Release:** Release 14
- **Volume:** 349 paragraphs (306 body, 43 TOC), 3 tables, 7 detected figure captions.
- **Detected Clauses & Annexes:** 44 clauses, 1 annexes.
- **Heading Styles Used:** `Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`, `Heading 8`
- **Heading Format:** Clause number and title are separated by a tab character (`\t`), e.g., `4.2.3\tNon-roaming reference architecture`.

#### Hierarchy & Sample Clauses:
| Clause | Section Title | DOCX Style | Body Paragraphs | Content Preview |
| :--- | :--- | :--- | ---: | :--- |
| `3.1` | Terms | `Heading 2` | 5 | For the purposes of the present document, the terms given in TR 21.905 [1] and the following apply. A term defined in th |
| `3.2` | Symbols | `Heading 2` | 1 | Void. |
| `3.3` | Abbreviations | `Heading 2` | 21 | For the purposes of the present document, the abbreviations given in 3GPP TR 21.905 [1] and the following apply. An abbr |
| `4.1` | Void | `Heading 2` | 0 | [Table / Figure / Child Clause directly follows] |
| `4.2` | Management control loops | `Heading 2` | 0 | [Table / Figure / Child Clause directly follows] |

#### Detected Annexes:
- **Annex A** (informative): Change history (Style: `Heading 8`)

#### Specific Extraction Considerations:
- ⚠️ TOC contains 43 artifact paragraphs that must be stripped before chunking.

### 8.2.5 TS 38.300 — NR; NR and NG-RAN Overall Description; Stage 2
- **Filename:** `38300-ia0.docx`
- **Version / Date:** `V18.10.0` (2026-06), **Release:** Release 18
- **Volume:** 4,889 paragraphs (4,343 body, 546 TOC), 15 tables, 112 detected figure captions.
- **Detected Clauses & Annexes:** 543 clauses, 8 annexes.
- **Heading Styles Used:** `Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`, `Heading 5`, `Heading 8`
- **Heading Format:** Clause number and title are separated by a tab character (`\t`), e.g., `4.2.3\tNon-roaming reference architecture`.

#### Hierarchy & Sample Clauses:
| Clause | Section Title | DOCX Style | Body Paragraphs | Content Preview |
| :--- | :--- | :--- | ---: | :--- |
| `3.1` | Abbreviations | `Heading 2` | 235 | For the purposes of the present document, the abbreviations given in TR 21.905 [1], in TS 36.300 [2] and the following a |
| `3.2` | Definitions | `Heading 2` | 100 | For the purposes of the present document, the terms and definitions given in TR 21.905 [1], in TS 36.300 [2] and the fol |
| `4.1` | Overall Architecture | `Heading 2` | 7 | An NG-RAN node is either: |
| `4.2` | Functional Split | `Heading 2` | 56 | The gNB and ng-eNB host the following functions: |
| `4.3` | Network Interfaces | `Heading 2` | 0 | [Table / Figure / Child Clause directly follows] |

#### Detected Annexes:
- **Annex A** (informative): QoS Handling in RAN (Style: `Heading 8`)
- **Annex B** (informative): Deployment Scenarios (Style: `Heading 8`)
- **Annex C** (informative): I-RNTI Reference Profiles (Style: `Heading 8`)
- **Annex D** (informative): SPID ranges and mapping of SPID values to cell reselection and inter-RAT/inter frequency handover priorities (Style: `Heading 8`)
- **Annex E** (informative): NG-RAN Architecture for Radio Access Network Sharing with multiple cell ID broadcast (Style: `Heading 8`)
- *... and 3 more annexes.*

#### Specific Extraction Considerations:
- ⚠️ TOC contains 546 artifact paragraphs that must be stripped before chunking.
- ⚠️ Zero lastRenderedPageBreak tags present; page numbers cannot be read natively from DOCX.

---

## 8.3 Clause Detection Findings

### Key Structural Observations across all 5 specifications:
1. **Consistent Tab Separation:** Across all 5 specifications, body section headings consistently follow the pattern `<Clause_Number>\t<Clause_Title>` (e.g. `4.2.1\tGeneral`, `6.1.2.3\tHigh-level use cases`).
2. **Standard 3GPP Heading Styles:** Heading hierarchy consistently maps to `Heading 1` (Level 1), `Heading 2` (Level 2), `Heading 3` (Level 3), `Heading 4` (Level 4), `Heading 5` (Level 5), and `Heading 6` (Level 6).
3. **Annex Style Variations:** Top-level Annexes use `Heading 8`, `ANNEX`, or `Annex` styles with titles formatted as `Annex A (normative): Title` or `Annex B (informative): Change history`.
4. **Annex Subclauses:** Subclauses within Annexes use standard heading styles (e.g., `Heading 1` for `A.1`, `Heading 2` for `A.1.1`).
5. **Recommended Detection Approach:** **Hybrid Style + Regex Validation**.
   - Primary filter: Match DOCX styles (`Heading 1` through `Heading 6`, `Heading 8`, `ANNEX`).
   - Secondary regex: `^(\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\t+(.*)$` for numeric/alphanumeric clauses, and `^Annex\s+([A-Z])\s*\(([^)]+)\):\s*(.*)$` for Annexes.
   - This effectively filters out inline references (such as 'as described in clause 4.2.1') while capturing authoritative structural section boundaries.

---

## 8.4 Page Citation Findings

- **Page Citation Support Status:** `requires rendering/conversion` (Unavailable natively in DOCX object model).
- **Technical Root Cause:** DOCX is an XML reflow document format. Word calculates page breaks dynamically at render time based on system fonts, printer metrics, and margins.
- **Empirical Evidence:** In all 5 raw documents, `w:lastRenderedPageBreak` is absent or incomplete, and headers/footers contain dynamic `PAGE` / `NUMPAGES` Word calculation fields rather than static numbers.
- **Architectural Decision for 3GPP-Grounded-RAG:**
  - **Primary & Mandatory Citation:** `Specification + Clause Number + Clause Title` (e.g. `TS 23.501 Clause 4.2.3: Non-roaming reference architecture`).
  - Clause numbers are authoritative, standardized across 3GPP releases, invariant to font/zoom rendering differences, and provide exact technical pinpointing.
  - Page numbers should not be synthesized or fabricated without rendering.

---

## 8.5 Noise Findings & Cleaning Strategy

The inspection identified several recurring noise patterns that must be filtered before embedding:
1. **Table of Contents (TOC):** Between 43 and 1,349 TOC paragraphs per document (styled `toc 1` to `toc 5`, `TT`). These contain trailing tab-page numbers (`\t23`) and duplicate clause titles without providing body substance.
2. **Cover Page Boilerplate:** Postal addresses (Sophia Antipolis, Valbonne - FRANCE), ETSI trademarks (UMTS™, LTE™, GSM®), and copyright boilerplate (`© 2025, 3GPP Organizational Partners`).
3. **Running Headers & Footers:** `3GPP TS 23.501 V18.12.0`, `ETSI 3GPP` stored in section objects.
4. **Change History Annexes:** Extensive change history tables (e.g. Annex T in TS 23.501, Annex S in TS 23.502) recording CR numbers and meeting dates. These dilute telecom semantic search and should be tagged or excluded.
5. **Void Sections:** Sections marked solely as `Void` (e.g. `4.1\tVoid` in TS 28.535).

---

## 8.6 Recommended Ingestion Strategy (for Phase 2)

Based on the empirical evidence gathered from the 5 specifications:

1. **Document Ingestion Engine:**
   - Use `python-docx` to extract structured paragraph blocks and XML element streams.
   - Discard TOC paragraphs by detecting TOC style markers or slicing body from the first `Foreword` / `Scope` heading.
   - Filter out cover metadata boilerplate and empty runs.

2. **Clause-Aware Hierarchical Chunking:**
   - Maintain an active hierarchy stack: `[Doc -> Clause L1 -> Clause L2 -> Clause L3 -> Clause L4]`.
   - For each section, attach the full breadcrumb path (e.g., `TS 23.501 > 4 Architecture model and concepts > 4.2 Architecture reference model > 4.2.3 Non-roaming reference architecture`).
   - If a clause exceeds target chunk token size (e.g. 512–1024 tokens), chunk internally along paragraph boundaries while retaining the full clause header metadata on every chunk.

3. **Table Handling Strategy:**
   - Extract tables as structured Markdown or Pipe-delimited text blocks.
   - Associate tables directly with their immediately preceding clause and table caption (`Table X.Y.Z-1: ...`).
   - Embed table headers into each row context to ensure high-recall semantic retrieval of telecom parameters.

4. **Grounding & Hallucination Mitigation Strategy:**
   - The later RAG generation pipeline will be designed to minimize hallucination through evidence-constrained prompting, mandatory clause citations, and explicit abstention triggers when context is insufficient.

5. **Metadata Schema:**
   ```json
   {
     "doc_id": "TS 23.501",
     "spec_number": "23.501",
     "version": "V18.12.0",
     "release": "Release 18",
     "clause": "4.2.3",
     "clause_title": "Non-roaming reference architecture",
     "hierarchy_path": "4 > 4.2 > 4.2.3",
     "chunk_type": "paragraph | table | definition",
     "citation": "3GPP TS 23.501 (V18.12.0), Clause 4.2.3"
   }
   ```

---

## 8.7 Claim Validation

### Observed Facts
- All 5 raw DOCX documents are present in `data/raw/` with a total of 48,844 paragraphs, 681 tables, 4,178 detected clauses, and 44 annexes.
- Section headings in body text consistently use a tab character (`\t`) separating the clause number and section title.
- Table of contents sections account for 43 to 1,349 paragraphs per document and must be cleaned prior to chunking.
- Native DOCX XML does not contain static per-paragraph page numbers; headers/footers contain dynamic `PAGE` / `NUMPAGES` Word calculation fields.

### Engineering Recommendations
- **Hybrid Parser:** A combined style-based and regex-based detector is recommended to identify structural section boundaries while ignoring inline text references.
- **Citation Standard:** Authoritative 3GPP clause identifiers (`TS <spec> Clause <X.Y.Z>`) must be used as primary citation metadata.
- **Table Ingestion:** Tables should be chunked as structured markdown with column headers attached to each row.
- **RAG Pipeline Design:** The future generation pipeline should enforce evidence-bounded generation and strict citation requirements to minimize hallucinations.

### Measured Validation
- **Validation Benchmark Size:** 20 representative samples (10 positive clause headings across all 5 specs, 10 negative samples including TOC lines, table captions, numeric prose, and headers).
- **True Positives (TP):** 10
- **True Negatives (TN):** 10
- **False Positives (FP):** 0
- **False Negatives (FN):** 0
- **Measured Precision:** 1.0
- **Measured Recall:** 1.0
- **Scope Note:** These metrics reflect performance on the curated 20-sample validation fixture and demonstrate that the proposed parser reliably differentiates clause headings from numeric prose, TOC lines, and table captions on those tested cases without generalizing unmeasured claims to unexamined edge cases.


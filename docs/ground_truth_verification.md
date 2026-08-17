# Ground Truth Evidence Verification

> **Document Status:** Complete & Audited  
> **Authoritative Source:** Original Raw DOCX Files in `data/raw/`  
> **Validation Tool:** `scripts/verify_ground_truth.py`

---

## 1. Purpose

This quality audit independently verifies whether selected ground-truth clauses extracted directly from the **original DOCX specifications** in `data/raw/` genuinely contain sufficient, authoritative evidence to answer the corresponding retrieval benchmark questions in `evaluation/retrieval/retrieval_dataset.json`.

---

## 2. Verification Results Summary

| Benchmark ID | Spec | Requested Clause | Evidence Status | Target Section / Table | Processed JSONL Match |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **R001** | TS 23.501 | `6.2.1` | **SUPPORTED** | Clause 6.2.1 (AMF Functional Description) | **PASS** |
| **R017** | TS 23.501 | `5.6.1` | **SUPPORTED** | Table 5.6.1-1 (Attributes of a PDU Session) | **PASS** |
| **R005** | TS 23.502 | `4.2.2.2.2` | **SUPPORTED** | Clause 4.2.2.2.2 (General Registration Steps 1–25) | **PASS** |
| **R013** | TS 24.501 | `4.4.2` | **SUPPORTED** | Clause 4.4.2 & Subclauses 4.4.2.1–4.4.2.6 (NAS Security) | **PASS** |
| **R014** | TS 28.535 | `5.1.1` | **PARTIALLY_SUPPORTED** | Clause 5.1.1 (`REQ-CSA_NSA-FUN-01`..`04` & Clause 4.2.4) | **PASS** |

---

## 3. Detailed Verification

### 3.1 Lookup 1: Benchmark R001

- **Filename:** `23501-ic0.docx`
- **Question:** *"What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?"*
- **Expected Clause:** `TS 23.501 §6.2.1`
- **Exact Heading:** `6.2.1	AMF`
- **Evidence Status:** **SUPPORTED**
- **Relevant Source Section:** Clause 6.2.1 (Paragraphs 1–2, bullet list of 25+ primary responsibilities including N2 termination, N1 NAS termination/ciphering/integrity, Registration management, Connection management, Reachability management, Mobility management, Lawful intercept, SM transport, SEAF, and SCM).
- **Reason:** The original DOCX contains the complete, authoritative list of AMF responsibilities explicitly enumerated with zero external dependencies required.
- **Processed Corpus Match:** **PASS** (Present across chunks `TS_23.501-V18.12.0-6.2.1-P001` through `P003`).

---

### 3.2 Lookup 2: Benchmark R017

- **Filename:** `23501-ic0.docx`
- **Question:** *"What attributes of a PDU Session are defined in the overview table of data transport and session management?"*
- **Expected Clause:** `TS 23.501 §5.6.1`
- **Exact Heading:** `5.6.1	Overview`
- **Evidence Status:** **SUPPORTED**
- **Relevant Source Section:** Table 5.6.1-1 (*Attributes of a PDU Session*), listing:
  - S-NSSAI of the HPLMN
  - S-NSSAI of the Serving PLMN
  - DNN (Data Network Name)
  - PDU Session Type
  - SSC mode
  - PDU Session Id
  - User Plane Security Enforcement information
  - Multi-access PDU Connectivity Service
- **Reason:** Table 5.6.1-1 directly defines all PDU Session attributes, their modification rules, and normative reference notes.
- **Processed Corpus Match:** **PASS** (Preserved verbatim as structured Markdown table chunk `TS_23.501-V18.12.0-5.6.1-TS23501-T001`).

---

### 3.3 Lookup 3: Benchmark R005

- **Filename:** `23502-ie0.docx`
- **Question:** *"What are the procedural steps for General Registration in the 5G System?"*
- **Expected Clause:** `TS 23.502 §4.2.2.2.2`
- **Exact Heading:** `4.2.2.2.2	General Registration`
- **Evidence Status:** **SUPPORTED**
- **Relevant Source Section:** Clause 4.2.2.2.2 (Complete multi-step procedure from Step 1 Registration Request via (R)AN, AUSF/UDM authentication, SMF context transfer, AM Policy Association, PCF interaction, down to Step 21/22 Registration Accept/Complete).
- **Reason:** The raw DOCX provides exhaustive, normative call-flow steps and message sequences for the 5GS General Registration procedure.
- **Processed Corpus Match:** **PASS** (Segmented cleanly across 44 sequential chunks `TS_23.502-V18.14.0-4.2.2.2.2-P001` through `P044` with intact document ordering).

---

### 3.4 Lookup 4: Benchmark R013

- **Filename:** `24501-id0.docx`
- **Question:** *"What requirements govern the handling and establishment of 5G NAS security contexts?"*
- **Expected Clause:** `TS 24.501 §4.4.2`
- **Exact Heading:** `4.4.2	Handling of security contexts`
- **Evidence Status:** **SUPPORTED**
- **Relevant Source Section:** Clause 4.4.2 and subclauses:
  - `4.4.2.1` (General)
  - `4.4.2.1.1` (Establishment of 5G NAS security context)
  - `4.4.2.2` (Handling of keys)
  - `4.4.2.3` (Handling of security contexts during inter-system change)
  - `4.4.2.4` (Handling of security contexts during N1 mode to N1 mode handover)
  - `4.4.2.5` (Establishment of 5G NAS security context after inter-system change)
  - `4.4.2.6` (Change of security keys)
- **Reason:** Subclauses 4.4.2.1.1 through 4.4.2.6 provide detailed protocol rules governing native/mapped NAS security context establishment, ngKSI handling, and ciphering/integrity activation.
- **Processed Corpus Match:** **PASS** (Preserved across 19 chunks `TS_24.501-V18.13.0-4.4.2.1.1-P001` to `TS_24.501-V18.13.0-4.4.2.6-P001`).

---

### 3.5 Lookup 5: Benchmark R014

- **Filename:** `28535-i20.docx`
- **Question:** *"What business-level requirements exist for closed control loop concept in communication service assurance?"*
- **Expected Clause:** `TS 28.535 §5.1.1`
- **Exact Heading:** `5.1.1	Communication service assurance`
- **Evidence Status:** **PARTIALLY_SUPPORTED**
- **Relevant Source Section:** Clause 5.1.1 defines the business requirements for service quality assurance and automation (`REQ-CSA_NSA-FUN-01` through `REQ-CSA_NSA-FUN-04`):
  - `REQ-CSA_NSA-FUN-01`: Receive communication service requirements from consumers.
  - `REQ-CSA_NSA-FUN-02`: Monitor and report degree of fulfilment of committed requirements.
  - `REQ-CSA_NSA-FUN-03`: Take actions to adjust 5GS to meet service requirements.
  - `REQ-CSA_NSA-FUN-04`: Act to fulfil service quality requirements.
- **Reason:** While Clause 5.1.1 details the high-level business goals of automation and service adjustments for communication service assurance, the explicit technical architectural descriptions and governance requirements for the "Closed control loop" concept itself are located in Clause 4.2.4 (*Closed control loops*) and Clause 4.2.5.2 (*Closed control loop governance*).
- **Processed Corpus Match:** **PASS** (Verbatim text in `TS_28.535-V18.2.0-5.1.1-P001`).
- **Benchmark Mapping Note:** `Benchmark mapping requires review.`

---

## 4. Issues & Discrepancies

1. **Benchmark Ground-Truth Refinement for R014:**
   - **Observation:** `R014` in `evaluation/retrieval/retrieval_dataset.json` specifies `clause_number: "5.1.1"`. In TS 28.535, Clause 5.1.1 covers general business requirements for service assurance automation (`REQ-CSA_NSA-FUN`), while the dedicated closed control loop concepts and governance requirements reside in Clause 4.2.4 and Clause 4.2.5.2.
   - **Action:** In accordance with strict audit instructions, no benchmark changes were made automatically. Reported as `Benchmark mapping requires review.`
2. **Zero Textual Discrepancies:**
   - All 5 lookups in the processed JSONL files retain 100% substantive fidelity with the original `.docx` source files in `data/raw/`.

---

## 5. Conclusion

The raw DOCX documents in `data/raw/` are verified as the authentic, authoritative truth. Lookups 1–4 are **SUPPORTED** with exhaustive, self-contained evidence. Lookup 5 is **PARTIALLY_SUPPORTED** (business assurance requirements present in 5.1.1, loop concept descriptions in 4.2.4). The processed corpus faithfully mirrors the original DOCX source files.

---

## 6. Phase 7D Authoritative Benchmark Ground-Truth Corrections

Following the comprehensive Phase 7C direct source DOCX verification audit, four ground-truth target clause mappings in `evaluation/retrieval/retrieval_dataset.json` were corrected to match the exact normative clauses in the authentic specifications:

| Benchmark ID | Question Text | Source DOCX | Old Incorrect Clause | Corrected Ground-Truth Clause(s) | Verification Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R004** | *"What factors and criteria are used for UPF selection during PDU session management?"* | `23501-ic0.docx` | `TS 23.501 §5.8.2.1` | **`TS 23.501 §6.3.3.3`** | §5.8.2.1 is titled *"General"* under UPF functional execution. Normative UPF selection parameters and criteria are explicitly specified in §6.3.3.3 (*"Selection of an UPF for a particular PDU Session"*). |
| **R007** | *"What are the preparation and execution phases of Intra-NR RAN Handover?"* | `38300-ia0.docx`<br>`23502-ie0.docx` | `TS 38.300 §9.2.1` | **`TS 38.300 §9.2.3.2.1`**<br>**`TS 23.502 §4.9.1.3.2`**<br>**`TS 23.502 §4.9.1.3.3`** | TS 38.300 §9.2.1 is titled *"Mobility in RRC_IDLE"* (Cell Selection/Reselection). Intra-NR handover preparation/execution is defined in TS 38.300 §9.2.3.2.1 and TS 23.502 §§4.9.1.3.2 / 4.9.1.3.3. |
| **R009** | *"What are the standardized 5QI characteristics and QoS packet delay budgets defined in 5GS?"* | `23501-ic0.docx` | `TS 23.501 §5.7.1.3` | **`TS 23.501 §5.7.3.4`**<br>**`TS 23.501 §5.7.4`** | §5.7.1.3 is titled *"Control of QoS Flows"* (QFI/ARP signaling). Normative Packet Delay Budget is defined in §5.7.3.4 and 5QI mapping in §5.7.4 (Table 5.7.4-1). |
| **R020** | *"What 5GSM sublayer states in the UE are defined in the state description table?"* | `24501-id0.docx` | `TS 24.501 §6.4.1.3` | **`TS 24.501 §6.1.3.2`** (and §§6.1.3.2.1–6.1.3.2.8) | §6.4.1.3 covers procedure acceptance. 5GSM sublayer states in the UE are defined in §6.1.3.2 (*"5GSM sublayer states in the UE"* and Table/Figure 6.1.3.2.1.1). |


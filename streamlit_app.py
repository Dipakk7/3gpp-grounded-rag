"""
3GPP RAG Assistant — Streamlit Demonstration UI
Grounded question answering over 3GPP technical specifications.
Communicates strictly via REST API with the FastAPI backend.
"""

import os
import time
import requests
import streamlit as st
from typing import Dict, Any, Optional

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="3GPP RAG Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished telecom engineering interface
st.markdown(
    """
    <style>
    /* Main Layout & Typography */
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.15rem;
        letter-spacing: -0.02em;
    }
    .subtitle {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.25rem;
    }
    
    /* Status Badges */
    .status-badge-answered {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.85rem;
        border-radius: 0.375rem;
        background-color: #ECFDF5;
        color: #065F46;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid #A7F3D0;
        margin-bottom: 0.75rem;
    }
    .status-badge-abstained {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.85rem;
        border-radius: 0.375rem;
        background-color: #FFFBEB;
        color: #92400E;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid #FDE68A;
        margin-bottom: 0.75rem;
    }
    
    /* Content Containers */
    .answer-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 0.5rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        font-size: 1.0rem;
        line-height: 1.6;
        color: #1E293B;
    }
    .citation-card {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        margin-bottom: 0.6rem;
        font-size: 0.95rem;
    }
    .citation-tag {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 0.15rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.4rem;
        border: 1px solid #DBEAFE;
    }
    .empty-state-card {
        background-color: #F8FAFC;
        border: 1px dashed #CBD5E1;
        border-radius: 0.6rem;
        padding: 1.5rem;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding-bottom: 0.75rem;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .sidebar-brand-title {
        font-weight: 800;
        font-size: 1.15rem;
        color: #0F172A;
        line-height: 1.1;
    }
    .sidebar-brand-sub {
        font-size: 0.72rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .info-pill {
        display: inline-block;
        background-color: #F1F5F9;
        color: #334155;
        padding: 0.2rem 0.55rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-right: 0.4rem;
        border: 1px solid #E2E8F0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Helper: Backend Health Check ---
def check_backend_health() -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

# --- Helper: Send Query to FastAPI Backend ---
def query_rag_api(question: str, top_k: int = 5) -> Dict[str, Any]:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/ask",
            json={"question": question, "top_k": top_k},
            timeout=180.0,
        )
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        elif resp.status_code == 422:
            detail = resp.json().get("detail", "Invalid request parameters.")
            return {"success": False, "error": f"Validation Error (422): {detail}"}
        else:
            detail = resp.json().get("detail", f"HTTP {resp.status_code} error from API.")
            return {"success": False, "error": f"API Error ({resp.status_code}): {detail}"}
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Connection Error: Could not reach FastAPI backend at {API_BASE_URL}. Ensure the API server is running.",
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout Error: The request exceeded the server timeout threshold. CPU inference may be busy.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected Error: {str(e)}",
        }


# --- Sidebar: System Info & Specifications ---
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <span style="font-size: 1.8rem;">📡</span>
            <div>
                <div class="sidebar-brand-title">3GPP RAG Assistant</div>
                <div class="sidebar-brand-sub">Release 18 Technical Specifications</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Live Health Indicator
    health_info = check_backend_health()
    if health_info and health_info.get("status") == "ok":
        chunk_count = health_info.get("details", {}).get("vector_store_chunk_count", 6737)
        st.success(f"🟢 API Online ({chunk_count:,} vectors)")
    else:
        st.warning("🔴 API Offline or Initializing...")
        st.caption(f"Target: `{API_BASE_URL}`")

    st.markdown("### 📚 Indexed Specifications")
    st.markdown(
        """
        - **TS 23.501** (V18.12.0) — *5GS Architecture*
        - **TS 23.502** (V18.14.0) — *5GS Procedures*
        - **TS 24.501** (V18.13.0) — *5GS NAS Protocol*
        - **TS 28.535** (V18.2.0) — *Control Loop Assurance*
        - **TS 38.300** (V18.10.0) — *NR & NG-RAN Architecture*
        """
    )

    st.markdown("### ⚙️ Pipeline Features")
    st.markdown(
        """
        - **6,737** Authoritative Chunks
        - **Hybrid Retrieval**: Dense (768d) + BM25 + RRF
        - **Fix #2**: Specification-Aware Routing
        - **Fix #3**: Structural Metadata Refinement
        - **Generation**: Grounded Qwen2.5:1.5b
        - **Verification**: Deterministic Citation & Claim Validation
        - **Guardrails**: Zero-Hallucination Safe Abstention
        """
    )
    
    st.markdown("---")
    top_k_val = st.slider("Evidence Top-K (chunks)", min_value=1, max_value=10, value=5, step=1)


# --- Main Application Area ---
st.markdown('<div class="main-title">3GPP RAG Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Grounded Question Answering over 3GPP Technical Specifications with Authoritative Citations</div>', unsafe_allow_html=True)

# Sample query quick-selection
SAMPLE_QUERIES = [
    "-- Select a sample technical query --",
    "What is the NG User Plane (NG-U) interface defined between in NG-RAN?",
    "What are the procedural steps for General Registration in the 5G System?",
    "What behavior is specified in the table for change of UE usage setting in single-registration mode?",
    "What does TS 28.535 specify about closed control loops and their governance?",
    "What is the exact battery life specification in hours for 5G RedCap devices in TS 38.300?",
    "What is the standardized 5QI value for 7G holographic teleportation defined in Table 5.7.1.3-1 of TS 23.501?",
]

selected_sample = st.selectbox("💡 Sample Benchmark Questions:", SAMPLE_QUERIES, index=0)

# Manage text input state
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

if selected_sample != SAMPLE_QUERIES[0]:
    st.session_state.query_text = selected_sample

question_input = st.text_area(
    "Enter your 3GPP technical question:",
    value=st.session_state.query_text,
    height=100,
    placeholder="e.g., What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?",
    key="main_question_input",
)

col_ask, col_clear, col_spacer = st.columns([1.2, 0.8, 5.0])
with col_ask:
    ask_button = st.button("🚀 Ask Assistant", type="primary", use_container_width=True)
with col_clear:
    if st.button("🧹 Clear", use_container_width=True):
        st.session_state.query_text = ""
        st.rerun()

# --- Query Execution or Empty State Display ---
if ask_button:
    clean_query = question_input.strip()
    if not clean_query:
        st.warning("⚠️ Please enter a question before submitting.")
    else:
        with st.spinner("🔍 Retrieving 3GPP specification evidence and generating grounded response..."):
            t_start = time.time()
            api_result = query_rag_api(question=clean_query, top_k=top_k_val)
            total_elapsed = (time.time() - t_start) * 1000

        if not api_result["success"]:
            st.error(f"❌ {api_result['error']}")
        else:
            response_data = api_result["data"]
            status = response_data.get("status")
            answer = response_data.get("answer")
            citations = response_data.get("citations", [])
            evidence = response_data.get("evidence", [])
            reason = response_data.get("reason")
            latencies = response_data.get("latency_breakdown") or {}

            st.markdown("---")

            # --- Status Header & Answer Rendering ---
            if status == "answered":
                st.markdown(
                    '<div class="status-badge-answered">✅ Grounded Answer (Verified & Cited)</div>',
                    unsafe_allow_html=True,
                )
                
                # Main Answer Display
                st.markdown("### Answer")
                st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

                # Citations Section
                if citations:
                    st.markdown("### 📑 Technical Citations")
                    for i, cit in enumerate(citations, 1):
                        spec = cit.get("specification", "")
                        ver = cit.get("version", "")
                        clause_num = cit.get("clause_number", "")
                        clause_title = cit.get("clause_title", "")
                        table_id = cit.get("table_id")
                        table_cap = cit.get("table_caption")
                        formatted = cit.get("formatted_citation") or f"[{spec}, Clause {clause_num} — {clause_title}]"

                        table_str = f" | Table: <code>{table_id}</code> ({table_cap})" if table_id else ""
                        ver_str = f" <code>{ver}</code>" if ver else ""

                        st.markdown(
                            f"""
                            <div class="citation-card">
                                <span class="citation-tag">{spec} §{clause_num}</span> <strong>{formatted}</strong><br/>
                                <span style="color: #475569; font-size: 0.88rem;">Specification: {spec}{ver_str} | Clause Title: <em>{clause_title}</em>{table_str}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            elif status == "abstain":
                st.markdown(
                    '<div class="status-badge-abstained">🛡️ Safely Abstained (Zero-Hallucination Guardrail)</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("### Status Notice")
                st.info("ℹ️ Unable to provide a grounded answer from the available 3GPP evidence.")
                if reason:
                    st.markdown(f"**Abstention Reason:** `{reason}`")
                st.caption(
                    "The system safely abstains whenever questions are unanswerable, out-of-corpus, or unsupported by retrieved technical specifications."
                )

            # --- Retrieved Evidence Expandable Section ---
            if evidence:
                with st.expander(f"📚 Retrieved Evidence Chunks ({len(evidence)} items)"):
                    for ev in evidence:
                        ev_id = ev.get("evidence_id", "")
                        chunk_id = ev.get("chunk_id", "")
                        spec = ev.get("specification", "")
                        clause = ev.get("clause_number", "")
                        title = ev.get("clause_title", "")
                        table_id = ev.get("table_id")
                        
                        table_tag = f" [Table: {table_id}]" if table_id else ""
                        st.markdown(f"**[{ev_id}] {spec} §{clause} — {title}{table_tag}** (`{chunk_id}`)")

            # --- Latency & Execution Breakdown Footer ---
            st.markdown("---")
            ret_ms = latencies.get("retrieval_ms", 0.0)
            gen_ms = latencies.get("generation_ms", 0.0)
            st.markdown(
                f"""
                <div style="font-size: 0.85rem; color: #64748B;">
                    <span class="info-pill">Retrieval: {ret_ms:.1f} ms</span>
                    <span class="info-pill">Generation: {gen_ms / 1000:.1f} s</span>
                    <span class="info-pill">Total UI Latency: {total_elapsed / 1000:.1f} s</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    # --- Polished Empty State Display ---
    st.markdown(
        """
        <div class="empty-state-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.4rem;">📖 <strong>3GPP Technical Knowledge Base</strong></div>
            <div style="color: #475569; font-size: 0.95rem; max-width: 600px; margin: 0 auto 1rem auto;">
                Ask architectural, procedural, or protocol questions across 3GPP Release 18 specifications. Answers are strictly grounded with verifiable clause citations.
            </div>
            <div style="display: flex; justify-content: center; gap: 0.75rem; flex-wrap: wrap;">
                <span class="info-pill">🏗️ TS 23.501 (Architecture)</span>
                <span class="info-pill">🔄 TS 23.502 (Procedures)</span>
                <span class="info-pill">🔒 TS 24.501 (NAS Protocol)</span>
                <span class="info-pill">🎯 TS 28.535 (Assurance)</span>
                <span class="info-pill">📡 TS 38.300 (NG-RAN)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

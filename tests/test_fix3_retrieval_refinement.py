"""
Unit tests for Fix #3: Structural Metadata-Aware Hybrid Retrieval Refinement.
"""

import pytest
from unittest.mock import MagicMock
from retrieval.models import RetrievedChunk
from retrieval.retriever import HybridRetriever, SemanticRetriever
from retrieval.bm25 import BM25Index


def create_mock_chunk(chunk_id, spec, clause_num, title, text, rank=1, score=0.8):
    return RetrievedChunk(
        chunk_id=chunk_id,
        specification=spec,
        document_title=f"{spec} Tech Spec",
        version="V18.0.0",
        release="Rel-18",
        source_filename=f"{spec}.docx",
        clause_number=clause_num,
        clause_title=title,
        breadcrumb=[f"{clause_num} {title}"],
        source_type="prose",
        document_order=1,
        text=text,
        content_hash="hash123",
        score=score,
        rank=rank,
        table_id=None,
        table_caption=None,
        retrieval_method="hybrid (dense+bm25)",
    )


@pytest.fixture
def mock_retrievers():
    mock_sem = MagicMock(spec=SemanticRetriever)
    mock_bm25 = MagicMock(spec=BM25Index)
    hybrid = HybridRetriever(semantic_retriever=mock_sem, bm25_index=mock_bm25)
    return hybrid, mock_sem, mock_bm25


def test_fix3_definition_intent_boost(mock_retrievers):
    hybrid, mock_sem, mock_bm25 = mock_retrievers
    query = "What definitions are provided for terms like Closed Control Loop and SLA in service assurance?"

    c_def = create_mock_chunk("TS_28.535-3.1", "TS 28.535", "3.1", "Terms", "Definitions of Closed Control Loop and SLA")
    c_proc = create_mock_chunk("TS_28.535-4.3", "TS 28.535", "4.3", "Assurance Service", "Communication service assurance operational details")

    mock_sem.retrieve.return_value = [c_proc, c_def]
    mock_bm25.query.return_value = [c_proc, c_def]

    results = hybrid.retrieve(query, top_k=2)
    assert len(results) == 2
    # Clause 3.1 should be boosted to Rank 1 for definition intent
    assert results[0].clause_number == "3.1"


def test_fix3_system_procedure_intent_boost(mock_retrievers):
    hybrid, mock_sem, mock_bm25 = mock_retrievers
    query = "What are the procedural steps for General Registration in the 5G System?"

    c_nas = create_mock_chunk("TS_24.501-5.5.1.2.2", "TS 24.501", "5.5.1.2.2", "Initial registration initiation", "NAS registration details")
    c_sys = create_mock_chunk("TS_23.502-4.2.2.2.2", "TS 23.502", "4.2.2.2.2", "General Registration", "5GS General Registration call flow steps 1 to 22")

    mock_sem.retrieve.return_value = [c_nas, c_sys]
    mock_bm25.query.return_value = [c_nas, c_sys]

    results = hybrid.retrieve(query, top_k=2)
    assert len(results) == 2
    # TS 23.502 General Registration should be boosted to Rank 1
    assert results[0].specification == "TS 23.502"
    assert results[0].clause_number == "4.2.2.2.2"


def test_fix3_description_intent_boost(mock_retrievers):
    hybrid, mock_sem, mock_bm25 = mock_retrievers
    query = "How is a closed control loop defined and described in communication service assurance?"

    c_op = create_mock_chunk("TS_28.535-6.1.6", "TS 28.535", "6.1.6", "Limiting actions", "Operational actions")
    c_desc = create_mock_chunk("TS_28.535-4.2.4.1", "TS 28.535", "4.2.4.1", "Description", "Description of closed control loop architecture")

    mock_sem.retrieve.return_value = [c_op, c_desc]
    mock_bm25.query.return_value = [c_op, c_desc]

    results = hybrid.retrieve(query, top_k=2)
    assert len(results) == 2
    assert results[0].clause_number == "4.2.4.1"


def test_fix3_unscoped_general_query_preservation(mock_retrievers):
    hybrid, mock_sem, mock_bm25 = mock_retrievers
    query = "What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?"

    c_amf = create_mock_chunk("TS_23.501-6.2.1", "TS 23.501", "6.2.1", "AMF", "AMF responsibilities")
    c_other = create_mock_chunk("TS_23.501-6.2.2", "TS 23.501", "6.2.2", "SMF", "SMF responsibilities")

    mock_sem.retrieve.return_value = [c_amf, c_other]
    mock_bm25.query.return_value = [c_amf, c_other]

    results = hybrid.retrieve(query, top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "TS_23.501-6.2.1"


def test_fix3_scoped_query_preservation(mock_retrievers):
    hybrid, mock_sem, mock_bm25 = mock_retrievers
    query = "What does TS 28.535 specify about closed control loops and their governance?"

    c_gov = create_mock_chunk("TS_28.535-4.2.5.2", "TS 28.535", "4.2.5.2", "Closed control loop governance", "Governance details")
    c_other = create_mock_chunk("TS_28.535-4.2.5.1", "TS 28.535", "4.2.5.1", "Overview", "Overview details")

    mock_sem.retrieve.return_value = [c_gov, c_other]
    mock_bm25.query.return_value = [c_gov, c_other]

    results = hybrid.retrieve(query, top_k=2)
    assert len(results) == 2
    assert results[0].specification == "TS 28.535"

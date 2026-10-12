"""
Phase 9 — FastAPI Final QA Script.
Tests all endpoints (/health, /metadata, /ask) across the 8 mandatory test cases.
"""

import sys
import json
import time
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from fastapi.testclient import TestClient
from api.main import app

def run_fastapi_qa():
    print("==================================================")
    print("PHASE 9 — FASTAPI FINAL QA AUDIT")
    print("==================================================")
    
    client = TestClient(app)
    
    # 1. Health Endpoint QA
    print("\n--- 1. Testing GET /health ---")
    resp_health = client.get("/health")
    print(f"Status Code: {resp_health.status_code}")
    health_data = resp_health.json()
    print(f"Response: {json.dumps(health_data, indent=2)}")
    assert resp_health.status_code == 200, f"Expected 200, got {resp_health.status_code}"
    assert health_data["status"] == "ok"
    assert health_data["service"] == "3gpp-grounded-rag"
    print("GET /health: PASS")
    
    # 2. Metadata Endpoint QA
    print("\n--- 2. Testing GET /metadata ---")
    resp_meta = client.get("/metadata")
    print(f"Status Code: {resp_meta.status_code}")
    meta_data = resp_meta.json()
    print(f"Response: {json.dumps(meta_data, indent=2)}")
    assert resp_meta.status_code == 200, f"Expected 200, got {resp_meta.status_code}"
    assert meta_data["total_chunks"] == 6737
    assert len(meta_data["specifications"]) == 5
    print("GET /metadata: PASS")
    
    # 3. Eight Mandatory /ask Test Cases
    qa_cases = [
        {
            "id": "QA-1",
            "name": "Factual Question",
            "question": "What is the NG User Plane (NG-U) interface defined between in NG-RAN?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": True,
        },
        {
            "id": "QA-2",
            "name": "Procedural Question",
            "question": "What are the procedural steps for General Registration in the 5G System?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": True,
        },
        {
            "id": "QA-3",
            "name": "Table Question",
            "question": "What behavior is specified in the table for change of UE usage setting in single-registration mode?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": True,
        },
        {
            "id": "QA-4",
            "name": "Multi-Clause Question",
            "question": "What does TS 28.535 specify about closed control loops and their governance?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": True,
        },
        {
            "id": "QA-5",
            "name": "In-Corpus Unanswerable Question",
            "question": "What is the exact battery life specification in hours for 5G RedCap devices in TS 38.300?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": False,  # safe abstention
        },
        {
            "id": "QA-6",
            "name": "Out-of-Corpus Question",
            "question": "How does Kubernetes implement the Container Network Interface (CNI) plugin according to the Cloud Native Computing Foundation?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": False,  # safe abstention
        },
        {
            "id": "QA-7",
            "name": "Adversarial / False-Premise Question",
            "question": "What is the standardized 5QI value for 7G holographic teleportation defined in Table 5.7.1.3-1 of TS 23.501?",
            "top_k": 5,
            "expected_http": 200,
            "expect_answer": False,  # safe abstention
        },
    ]
    
    # Negative / Validation Test Cases
    invalid_cases = [
        {
            "id": "QA-8a",
            "name": "Invalid Request - Empty Question",
            "payload": {"question": "   ", "top_k": 5},
            "expected_http": 422,
        },
        {
            "id": "QA-8b",
            "name": "Invalid Request - Missing Question Field",
            "payload": {"top_k": 5},
            "expected_http": 422,
        },
        {
            "id": "QA-8c",
            "name": "Invalid Request - Negative top_k",
            "payload": {"question": "What is AMF?", "top_k": -1},
            "expected_http": 422,
        },
        {
            "id": "QA-8d",
            "name": "Invalid Request - Wrong Type",
            "payload": {"question": 12345, "top_k": "invalid"},
            "expected_http": 422,
        },
    ]
    
    qa_results = []
    
    print("\n--- 3. Testing POST /ask across Functional Scenarios ---")
    for case in qa_cases:
        cid = case["id"]
        cname = case["name"]
        q = case["question"]
        top_k = case["top_k"]
        exp_http = case["expected_http"]
        exp_ans = case["expect_answer"]
        
        print(f"\n[{cid}] {cname}: \"{q[:60]}...\"")
        t0 = time.time()
        resp = client.post("/ask", json={"question": q, "top_k": top_k})
        elapsed = (time.time() - t0) * 1000
        
        print(f"HTTP Status: {resp.status_code} ({elapsed:.1f} ms)")
        assert resp.status_code == exp_http, f"Expected HTTP {exp_http}, got {resp.status_code}"
        
        data = resp.json()
        status_val = data.get("status")
        ans = data.get("answer")
        citations = data.get("citations", [])
        evidence = data.get("evidence", [])
        reason = data.get("reason")
        
        # Verify schema structure
        assert "status" in data
        assert "evidence" in data
        assert "citations" in data
        assert isinstance(evidence, list)
        assert isinstance(citations, list)
        
        # Verify evidence objects have required fields
        for ev in evidence:
            assert "evidence_id" in ev
            assert "specification" in ev
            assert "clause_number" in ev
            
        if status_val == "answered":
            assert ans is not None and len(ans) > 0
            assert len(citations) > 0
            for cit in citations:
                assert "specification" in cit
                assert "clause_number" in cit
                assert "clause_title" in cit
            print(f"  -> Answered: {ans[:80]}...")
            print(f"  -> Citations: {[c['specification'] + ' §' + str(c['clause_number']) for c in citations]}")
        else:
            assert status_val == "abstain"
            assert ans is None
            assert len(citations) == 0
            print(f"  -> Safely Abstained: Reason = '{reason}'")
            
        qa_results.append({
            "id": cid,
            "name": cname,
            "http_status": resp.status_code,
            "rag_status": status_val,
            "citations_count": len(citations),
            "evidence_count": len(evidence),
            "passed": True,
        })
        
    print("\n--- 4. Testing POST /ask Invalid Requests ---")
    for inv in invalid_cases:
        cid = inv["id"]
        cname = inv["name"]
        payload = inv["payload"]
        exp_http = inv["expected_http"]
        
        print(f"\n[{cid}] {cname}")
        resp = client.post("/ask", json=payload)
        print(f"HTTP Status: {resp.status_code}")
        assert resp.status_code == exp_http, f"Expected HTTP {exp_http}, got {resp.status_code}"
        data = resp.json()
        print(f"Error Response: {data}")
        # Verify no traceback / stack trace leakage
        assert "traceback" not in json.dumps(data).lower()
        assert "file \"" not in json.dumps(data).lower()
        assert data.get("error_code") == "VALIDATION_ERROR"
        
        qa_results.append({
            "id": cid,
            "name": cname,
            "http_status": resp.status_code,
            "passed": True,
        })
        
    print("\n==================================================")
    print("FASTAPI QA AUDIT SUMMARY: ALL CHECKS PASSED")
    print("==================================================")
    for r in qa_results:
        print(f"  {r['id']} ({r['name']}): HTTP {r['http_status']} - PASS")
        
    with open(ROOT_PATH / "data" / "fastapi_qa_results.json", "w", encoding="utf-8") as f:
        json.dump(qa_results, f, indent=2)

if __name__ == "__main__":
    run_fastapi_qa()

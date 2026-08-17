"""
Live Smoke Test Script for Phase 5 FastAPI Integration.
Runs the 5 representative questions directly against the live RAG pipeline via TestClient.
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

QUESTIONS = [
    {
        "id": "A",
        "category": "Factual",
        "question": "What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?",
        "expected": "answer",
    },
    {
        "id": "B",
        "category": "Table",
        "question": "What attributes of a PDU Session are defined in the overview table?",
        "expected": "answer",
    },
    {
        "id": "C",
        "category": "Procedural",
        "question": "What are the procedural steps for General Registration in the 5G System?",
        "expected": "answer",
    },
    {
        "id": "D",
        "category": "Unanswerable",
        "question": "What is the exact battery life specification in hours for 5G RedCap?",
        "expected": "abstain",
    },
    {
        "id": "E",
        "category": "Adversarial",
        "question": "What is the standardized 5QI value for 7G holographic teleportation?",
        "expected": "abstain",
    },
]


def run_smoke_tests():
    print("=== Initializing TestClient against Live RAG FastAPI Service ===")
    client = TestClient(app)

    # 1. Health check
    t0 = time.time()
    health_resp = client.get("/health")
    health_time = (time.time() - t0) * 1000
    print(f"GET /health -> status={health_resp.status_code}, time={health_time:.1f}ms")
    print(f"Health Response: {json.dumps(health_resp.json(), indent=2)}")

    # 2. Metadata check
    meta_resp = client.get("/metadata")
    print(f"GET /metadata -> status={meta_resp.status_code}")
    print(f"Metadata Response: {json.dumps(meta_resp.json(), indent=2)}")

    print("\n=== Running 5 Representative Smoke Test Questions ===")
    results = {}
    for item in QUESTIONS:
        qid = item["id"]
        cat = item["category"]
        q = item["question"]
        expected = item["expected"]

        print(f"\n--- [{qid}] {cat}: {q} ---")
        t_start = time.time()
        resp = client.post("/ask", json={"question": q, "top_k": 5})
        lat = (time.time() - t_start) * 1000

        print(f"HTTP Status: {resp.status_code} ({lat:.1f}ms)")
        if resp.status_code == 200:
            data = resp.json()
            status_val = data.get("status")
            ans = data.get("answer")
            citations = data.get("citations", [])
            evidence = data.get("evidence", [])
            reason = data.get("reason")
            latencies = data.get("latency_breakdown", {})

            print(f"RAG Status: {status_val}")
            print(f"Answer: {ans[:200] if ans else 'None'}")
            print(f"Citations ({len(citations)}): {[c.get('formatted_citation') or c.get('clause_number') for c in citations]}")
            print(f"Evidence count: {len(evidence)}")
            print(f"Abstention reason: {reason}")
            print(f"Latency breakdown: {latencies}")

            # Check if behavior matches expectation
            passed = (status_val == expected)
            results[cat] = "PASS" if passed else f"WARN (got {status_val}, expected {expected})"
        else:
            print(f"FAILED with HTTP {resp.status_code}: {resp.text}")
            results[cat] = f"FAIL (HTTP {resp.status_code})"

    print("\n=== Smoke Test Summary ===")
    for cat, outcome in results.items():
        print(f"  {cat}: {outcome}")

    with open(ROOT_PATH / "data" / "smoke_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    run_smoke_tests()

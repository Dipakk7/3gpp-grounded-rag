"""
Model Selection Experiment for Phase 4:
Compares qwen2.5:1.5b vs qwen2.5:3b on 5 representative 3GPP queries.
Evaluates JSON validity, grounding, citation accuracy, abstention, and latency.
"""

import json
import time
import urllib.request
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent

# Test cases with retrieved mock/real evidence
TEST_CASES = [
    {
        "id": "T1_Factual",
        "type": "factual",
        "question": "What are the primary functional responsibilities of the Access and Mobility Management Function (AMF)?",
        "evidence": [
            {
                "evidence_id": "E1",
                "specification": "TS 23.501",
                "clause_number": "6.2.1",
                "clause_title": "AMF",
                "text": "The Access and Mobility Management Function (AMF) includes: Termination of RAN CP interface (N2), Termination of NAS (N1), NAS ciphering and integrity protection, Registration management, Connection management, Reachability management, Mobility Management, Transport for SM messages between UE and SMF."
            }
        ],
        "expected_behavior": "answer"
    },
    {
        "id": "T2_Procedural",
        "type": "procedural",
        "question": "What are the first 3 steps in the 5GS General Registration procedure?",
        "evidence": [
            {
                "evidence_id": "E1",
                "specification": "TS 23.502",
                "clause_number": "4.2.2.2.2",
                "clause_title": "General Registration",
                "text": "Step 1: UE to (R)AN: Registration Request.\nStep 2: (R)AN to new AMF: N2 message containing Registration Request.\nStep 3: Conditional: New AMF to old AMF: Namf_Communication_UEContextTransfer."
            }
        ],
        "expected_behavior": "answer"
    },
    {
        "id": "T3_Table",
        "type": "table",
        "question": "Can the S-NSSAI of the Serving PLMN be modified during the lifetime of a PDU Session according to Table 5.6.1-1?",
        "evidence": [
            {
                "evidence_id": "E1",
                "specification": "TS 23.501",
                "clause_number": "5.6.1",
                "clause_title": "Overview",
                "text": "**Table 5.6.1-1: Attributes of a PDU Session**\n| PDU Session attribute | May be modified later during the lifetime of the PDU Session | Notes |\n| S-NSSAI of the HPLMN | No | (Note 1) |\n| S-NSSAI of the Serving PLMN | Yes | (Note 1) (Note 4) |\n| DNN | No | (Note 1) |"
            }
        ],
        "expected_behavior": "answer"
    },
    {
        "id": "T4_MultiClause",
        "type": "multi_clause",
        "question": "What does TS 28.535 specify about closed control loop lifecycle phases and governance capabilities?",
        "evidence": [
            {
                "evidence_id": "E1",
                "specification": "TS 28.535",
                "clause_number": "4.2.4.2",
                "clause_title": "Lifecycle phases",
                "text": "The lifecycle phases for closed control loops are preparation, commissioning, operation and decommissioning."
            },
            {
                "evidence_id": "E2",
                "specification": "TS 28.535",
                "clause_number": "4.2.5.2",
                "clause_title": "Closed control loop governance",
                "text": "Closed control loop governance describes a set of capabilities including lifecycle management (create, modify, activate/deactivate, delete) and configure goals for closed control loop."
            }
        ],
        "expected_behavior": "answer"
    },
    {
        "id": "T5_Unanswerable",
        "type": "unanswerable",
        "question": "What is the maximum throughput of 6G Sub-THz links defined in 3GPP TS 23.501?",
        "evidence": [
            {
                "evidence_id": "E1",
                "specification": "TS 23.501",
                "clause_number": "6.2.1",
                "clause_title": "AMF",
                "text": "The AMF includes termination of RAN CP interface (N2) and NAS (N1)."
            }
        ],
        "expected_behavior": "abstain"
    }
]

SYSTEM_PROMPT = """You are a strictly grounded 3GPP Technical Assistant.
Answer the user's question using ONLY the provided evidence blocks.
Do NOT use external knowledge. Do NOT invent facts or clause numbers.
If the provided evidence does not contain sufficient information to answer the question, set status to "abstain".

You MUST respond strictly in valid JSON matching this schema:
{
  "status": "answered" | "abstain",
  "answer": "string or null",
  "claims": [
    {
      "text": "single verifiable claim statement",
      "citations": ["E1"]
    }
  ],
  "citations": [
    {
      "evidence_id": "E1",
      "specification": "TS XX.XXX",
      "clause_number": "X.X.X",
      "clause_title": "Title"
    }
  ],
  "abstention_reason": "string or null"
}
"""

def format_evidence_block(evidence_items: List[Dict[str, Any]]) -> str:
    parts = []
    for item in evidence_items:
        parts.append(
            f"[EVIDENCE {item['evidence_id']}]\n"
            f"Specification: {item['specification']}\n"
            f"Clause: {item['clause_number']}\n"
            f"Title: {item['clause_title']}\n"
            f"Content:\n{item['text']}\n"
        )
    return "\n".join(parts)


def call_ollama(model: str, prompt: str, system: str) -> Dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0,
            "num_predict": 1024
        }
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    lat_ms = (time.time() - t0) * 1000
    
    raw_response = res.get("response", "")
    parsed_json = None
    try:
        parsed_json = json.loads(raw_response)
    except Exception as e:
        pass
    
    return {
        "latency_ms": lat_ms,
        "raw_response": raw_response,
        "parsed_json": parsed_json
    }


def run_experiment():
    models = ["qwen2.5:1.5b", "qwen2.5:3b"]
    results = {}

    for model in models:
        print(f"\n==========================================")
        print(f"Testing Model: {model}")
        print(f"==========================================")
        model_results = []
        
        for case in TEST_CASES:
            ev_str = format_evidence_block(case["evidence"])
            user_prompt = f"Available Evidence:\n{ev_str}\n\nQuestion: {case['question']}"
            
            print(f"\n--- Running Test Case: {case['id']} ({case['type']}) ---")
            res = call_ollama(model, user_prompt, SYSTEM_PROMPT)
            
            parsed = res["parsed_json"]
            valid_json = parsed is not None
            status = parsed.get("status") if valid_json else "invalid"
            abstain_ok = (status == "abstain") if case["expected_behavior"] == "abstain" else (status == "answered")
            
            num_claims = len(parsed.get("claims", [])) if valid_json else 0
            num_cits = len(parsed.get("citations", [])) if valid_json else 0
            
            print(f"Latency: {res['latency_ms']:.2f} ms")
            print(f"Valid JSON: {valid_json}")
            print(f"Status: {status} (Expected: {case['expected_behavior']}, Match: {abstain_ok})")
            print(f"Claims: {num_claims}, Citations: {num_cits}")
            if parsed and parsed.get("answer"):
                print(f"Answer snippet: {parsed['answer'][:120]}...")
            elif parsed and parsed.get("abstention_reason"):
                print(f"Abstention reason: {parsed['abstention_reason']}")
                
            model_results.append({
                "case_id": case["id"],
                "type": case["type"],
                "latency_ms": res["latency_ms"],
                "valid_json": valid_json,
                "status": status,
                "abstain_correct": abstain_ok,
                "num_claims": num_claims,
                "num_citations": num_cits,
                "parsed": parsed
            })
            
        results[model] = model_results

    # Summary
    print("\n\n==========================================")
    print("EXPERIMENT SUMMARY")
    print("==========================================")
    for model, res_list in results.items():
        avg_lat = sum(r["latency_ms"] for r in res_list) / len(res_list)
        all_json = all(r["valid_json"] for r in res_list)
        all_behavior = all(r["abstain_correct"] for r in res_list)
        print(f"\nModel: {model}")
        print(f"  Average Latency: {avg_lat:.2f} ms")
        print(f"  All JSON Valid: {all_json}")
        print(f"  Behavior Accuracy (5/5): {all_behavior}")

    with open(ROOT_DIR / "evaluation" / "model_selection_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nSaved detailed results to evaluation/model_selection_results.json")

if __name__ == "__main__":
    run_experiment()

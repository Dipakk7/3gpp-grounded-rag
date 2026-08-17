"""
Generation Benchmark Evaluation Runner:
Executes full Grounded Generation Pipeline across 30 benchmark questions.
Computes answer correctness, citation validity, claim support rate, abstention accuracy, and latencies.
"""

import json
import time
import sys
import statistics
from pathlib import Path
from typing import Dict, Any, List

ROOT_PATH = Path(__file__).resolve().parent.parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.index_corpus import load_all_chunks
from generation.models import GenerationResult
from generation.pipeline import GroundedGenerationPipeline


def run_generation_evaluation() -> Dict[str, Any]:
    print("=== Loading 3GPP Corpus & Retrieval Foundation for Generation Benchmark ===")
    dataset_file = ROOT_PATH / "evaluation" / "generation" / "generation_dataset.json"
    with open(dataset_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} generation benchmark questions from {dataset_file}")

    chunks = load_all_chunks()
    embedder = OllamaEmbedder()
    vector_store = ChromaVectorStore()
    bm25 = BM25Index()
    bm25.fit(chunks)

    semantic_retriever = SemanticRetriever(embedder=embedder, vector_store=vector_store)
    hybrid_retriever = HybridRetriever(semantic_retriever=semantic_retriever, bm25_index=bm25)

    pipeline = GroundedGenerationPipeline(
        retriever=hybrid_retriever,
    )

    print("\n=== Executing Grounded Generation Benchmark (30 Questions) ===")
    results_list = []
    
    total_questions = len(dataset)
    answerable_count = sum(1 for q in dataset if q["expected_behavior"] == "answer")
    unanswerable_count = sum(1 for q in dataset if q["expected_behavior"] == "abstain")

    correct_answers = 0
    correct_abstentions = 0
    false_answers = 0

    total_citations = 0
    valid_citations = 0

    total_claims = 0
    supported_claims = 0
    unsupported_claims = 0
    uncertain_claims = 0

    lat_retrieval_list = []
    lat_gen_list = []
    lat_ver_list = []
    lat_total_list = []

    for idx, item in enumerate(dataset, start=1):
        qid = item["id"]
        cat = item["category"]
        question = item["question"]
        expected_behavior = item["expected_behavior"]

        print(f"\n[{idx:02d}/{total_questions}] Starting {qid} [{cat}] {question[:65]}...", flush=True)
        t0 = time.time()
        res: GenerationResult = pipeline.process(question, top_k=5)
        dt = (time.time() - t0) * 1000

        lat_breakdown = res.latency_breakdown
        lat_retrieval_list.append(lat_breakdown.get("retrieval_ms", 0.0))
        lat_gen_list.append(lat_breakdown.get("generation_ms", 0.0))
        lat_ver_list.append(lat_breakdown.get("verification_ms", 0.0))
        lat_total_list.append(lat_breakdown.get("total_ms", dt))

        # Behavior check
        is_behavior_correct = (res.status == expected_behavior)
        if expected_behavior == "abstain":
            if res.status == "abstain":
                correct_abstentions += 1
            else:
                false_answers += 1
        elif expected_behavior == "answer":
            if res.status == "answered" and res.citation_valid and len(res.claims) > 0:
                # Check if all claims supported
                all_supp = all(v.verdict == "SUPPORTED" for v in res.claim_verifications)
                if all_supp:
                    correct_answers += 1

        # Citations stats
        for cit in res.citations:
            total_citations += 1
            if res.citation_valid:
                valid_citations += 1

        # Claims stats
        for c in res.claims:
            total_claims += 1

        for v in res.claim_verifications:
            if v.verdict == "SUPPORTED":
                supported_claims += 1
            elif v.verdict == "UNSUPPORTED":
                unsupported_claims += 1
            elif v.verdict == "UNCERTAIN":
                uncertain_claims += 1

        print(f"[{idx:02d}/{total_questions}] {qid} completed — {dt/1000:.1f}s | Status: {res.status} (Expected: {expected_behavior})", flush=True)
        if res.status == "answered":
            print(f"  Answer: {res.answer[:100] if res.answer else ''}...", flush=True)
            print(f"  Claims: {len(res.claims)}, Citations: {len(res.citations)}, Citations Valid: {res.citation_valid}", flush=True)
        else:
            print(f"  Abstention Reason: {res.abstention_reason}", flush=True)


        results_list.append({
            "id": qid,
            "category": cat,
            "question": question,
            "expected_behavior": expected_behavior,
            "actual_status": res.status,
            "behavior_correct": is_behavior_correct,
            "answer": res.answer,
            "abstention_reason": res.abstention_reason,
            "claims": [c.to_dict() for c in res.claims],
            "citations": [cit.to_dict() for cit in res.citations],
            "claim_verifications": [v.to_dict() for v in res.claim_verifications],
            "citation_valid": res.citation_valid,
            "citation_errors": res.citation_validation_errors,
            "gate_passed": res.gate_passed,
            "gate_reason": res.gate_reason,
            "latency_breakdown": res.latency_breakdown,
        })

    # Summary calculations
    answer_correctness_pct = (correct_answers / answerable_count) * 100 if answerable_count else 0
    abstention_accuracy_pct = (correct_abstentions / unanswerable_count) * 100 if unanswerable_count else 0
    false_answer_pct = (false_answers / unanswerable_count) * 100 if unanswerable_count else 0
    citation_validity_pct = (valid_citations / total_citations) * 100 if total_citations else 100.0
    citation_completeness_pct = 100.0 if all(len(c["citations"]) > 0 for r in results_list for c in r["claims"]) else 0.0
    claim_support_pct = (supported_claims / total_claims) * 100 if total_claims else 0.0
    unsupported_claim_pct = (unsupported_claims / total_claims) * 100 if total_claims else 0.0

    mean_total_lat = statistics.mean(lat_total_list)
    median_total_lat = statistics.median(lat_total_list)
    p95_total_lat = sorted(lat_total_list)[int(0.95 * len(lat_total_list))]

    metrics = {
        "benchmark_total_questions": total_questions,
        "answerable_questions": answerable_count,
        "unanswerable_questions": unanswerable_count,
        "answer_correctness_rate": round(answer_correctness_pct, 2),
        "citation_validity_rate": round(citation_validity_pct, 2),
        "citation_completeness_rate": round(citation_completeness_pct, 2),
        "claim_support_rate": round(claim_support_pct, 2),
        "unsupported_claim_rate": round(unsupported_claim_pct, 2),
        "abstention_accuracy": round(abstention_accuracy_pct, 2),
        "false_answer_rate": round(false_answer_pct, 2),
        "latencies_ms": {
            "retrieval_mean_ms": round(statistics.mean(lat_retrieval_list), 2),
            "generation_mean_ms": round(statistics.mean(lat_gen_list), 2),
            "verification_mean_ms": round(statistics.mean(lat_ver_list), 2),
            "total_mean_ms": round(mean_total_lat, 2),
            "total_median_ms": round(median_total_lat, 2),
            "total_p95_ms": round(p95_total_lat, 2),
        },
        "detailed_results": results_list,
    }

    out_path = ROOT_PATH / "evaluation" / "generation" / "generation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n==========================================", flush=True)
    print(f"GENERATION BENCHMARK RESULTS", flush=True)
    print(f"==========================================", flush=True)
    print(f"Answer Correctness:       {answer_correctness_pct:.1f}% ({correct_answers}/{answerable_count})", flush=True)
    print(f"Citation Validity:        {citation_validity_pct:.1f}% ({valid_citations}/{total_citations})", flush=True)
    print(f"Citation Completeness:    {citation_completeness_pct:.1f}%", flush=True)
    print(f"Claim Support Rate:       {claim_support_pct:.1f}% ({supported_claims}/{total_claims})", flush=True)
    print(f"Unsupported Claim Rate:   {unsupported_claim_pct:.1f}% ({unsupported_claims}/{total_claims})", flush=True)
    print(f"Abstention Accuracy:      {abstention_accuracy_pct:.1f}% ({correct_abstentions}/{unanswerable_count})", flush=True)
    print(f"False Answer Rate:        {false_answer_pct:.1f}% ({false_answers}/{unanswerable_count})", flush=True)
    print(f"Mean Latency:             {mean_total_lat:.2f} ms (P95: {p95_total_lat:.2f} ms)", flush=True)
    print(f"Saved results to {out_path}", flush=True)

    return metrics


if __name__ == "__main__":
    run_generation_evaluation()


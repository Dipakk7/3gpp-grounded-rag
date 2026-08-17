"""
Retrieval Benchmark Evaluation Engine.
Evaluates any retriever against ground-truth queries using standard IR metrics:
Hit@1, Hit@3, Hit@5, Hit@10, and MRR.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from retrieval.models import RetrievedChunk, EvaluationMetrics

DEFAULT_BENCHMARK_PATH = Path("evaluation/retrieval/retrieval_dataset.json")


def is_relevant_chunk(retrieved: RetrievedChunk, expected_targets: List[Dict[str, Any]]) -> bool:
    """
    Evidence matching rule:
    A retrieved chunk is relevant if:
    1. specification matches expected specification AND
    2. clause is the expected clause or valid child clause (or vice-versa for parent-child relationship)
    OR
    3. table_id matches expected table_id if specified.
    """
    for target in expected_targets:
        exp_spec = target["specification"]
        exp_clause = target["clause_number"]
        exp_table = target.get("table_id")

        if retrieved.specification != exp_spec:
            continue

        ret_clause = retrieved.clause_number

        # Exact clause match
        if ret_clause == exp_clause:
            return True

        # Child clause match (e.g., retrieved 4.2.2.2.2 matches expected 4.2.2)
        if ret_clause.startswith(f"{exp_clause}."):
            return True

        # Parent clause match (e.g., retrieved 4.4.2 matches expected 4.4.2.1)
        if exp_clause.startswith(f"{ret_clause}."):
            return True

        # Table match
        if exp_table and retrieved.table_id == exp_table:
            return True

    return False


class RetrievalBenchmark:
    """Evaluates retrievers against standard benchmark dataset."""

    def __init__(self, dataset_path: Path = DEFAULT_BENCHMARK_PATH):
        self.dataset_path = Path(dataset_path)
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            self.queries = json.load(f)

    def evaluate(
        self,
        retriever_fn,
        top_k: int = 10,
    ) -> EvaluationMetrics:
        """
        Run evaluation across all benchmark queries.
        retriever_fn is a callable: (query_text, top_k) -> List[RetrievedChunk]
        """
        total = len(self.queries)
        hit_1 = 0
        hit_3 = 0
        hit_5 = 0
        hit_10 = 0
        rr_sum = 0.0
        detailed_results = []

        for q in self.queries:
            qid = q["id"]
            question = q["question"]
            expected = q["expected"]
            category = q.get("category", "General")

            retrieved_chunks = retriever_fn(question, top_k)

            first_rank: Optional[int] = None
            for rank, chunk in enumerate(retrieved_chunks, start=1):
                if is_relevant_chunk(chunk, expected):
                    first_rank = rank
                    break

            is_hit_1 = first_rank == 1
            is_hit_3 = first_rank is not None and first_rank <= 3
            is_hit_5 = first_rank is not None and first_rank <= 5
            is_hit_10 = first_rank is not None and first_rank <= 10
            rr = (1.0 / first_rank) if first_rank is not None else 0.0

            if is_hit_1: hit_1 += 1
            if is_hit_3: hit_3 += 1
            if is_hit_5: hit_5 += 1
            if is_hit_10: hit_10 += 1
            rr_sum += rr

            top_evidence_preview = [
                {
                    "rank": c.rank,
                    "chunk_id": c.chunk_id,
                    "specification": c.specification,
                    "clause_number": c.clause_number,
                    "clause_title": c.clause_title,
                    "score": round(c.score, 4),
                    "method": c.retrieval_method,
                }
                for c in retrieved_chunks[:3]
            ]

            detailed_results.append({
                "id": qid,
                "category": category,
                "question": question,
                "expected": expected,
                "first_relevant_rank": first_rank,
                "hit@1": is_hit_1,
                "hit@3": is_hit_3,
                "hit@5": is_hit_5,
                "hit@10": is_hit_10,
                "reciprocal_rank": round(rr, 4),
                "top_retrieved": top_evidence_preview,
            })

        return EvaluationMetrics(
            total_queries=total,
            hit_at_1=hit_1 / total if total else 0.0,
            hit_at_3=hit_3 / total if total else 0.0,
            hit_at_5=hit_5 / total if total else 0.0,
            hit_at_10=hit_10 / total if total else 0.0,
            mrr=rr_sum / total if total else 0.0,
            detailed_results=detailed_results,
        )

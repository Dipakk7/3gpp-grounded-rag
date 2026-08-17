import sys
import json
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.embedding import OllamaEmbedder
from retrieval.vector_store import ChromaVectorStore
from retrieval.bm25 import BM25Index
from retrieval.retriever import SemanticRetriever, HybridRetriever
from retrieval.benchmark import is_relevant_chunk, DEFAULT_BENCHMARK_PATH
from retrieval.index_corpus import load_all_chunks

def evaluate():
    chunks = load_all_chunks()
    emb = OllamaEmbedder()
    vs = ChromaVectorStore()
    bm = BM25Index()
    bm.fit(chunks)
    sem = SemanticRetriever(emb, vs)
    hyb = HybridRetriever(sem, bm)

    with open(DEFAULT_BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    print(f"Total benchmark queries: {len(benchmark)}")
    for q in benchmark:
        qid = q["id"]
        qtext = q["question"]
        expected = q["expected"]
        results = hyb.retrieve(qtext, top_k=10)
        matches = []
        for rank, r in enumerate(results, start=1):
            if is_relevant_chunk(r, expected):
                matches.append((rank, r.specification, r.clause_number, r.clause_title))
        if matches:
            print(f"PASS | {qid}: First rank {matches[0][0]} -> {matches[0][1]} Clause {matches[0][2]} ('{matches[0][3]}')")
        else:
            print(f"FAIL | {qid}: No match in top 10 for question: '{qtext}'")

if __name__ == "__main__":
    evaluate()

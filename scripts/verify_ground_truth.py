"""
Ground-truth verification script for Phase 6.
Checks original raw DOCX and cross-checks data/processed JSONL preservation.
"""

import json
import re
import sys
import docx
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

DATA_RAW = ROOT_PATH / "data" / "raw"
DATA_PROC = ROOT_PATH / "data" / "processed"

def verify_all():
    print("=================================================================")
    print("PHASE 6 GROUND-TRUTH AND PRESERVATION VERIFICATION")
    print("=================================================================")

    # 1. Check G007
    print("\n--- G007: TS 28.535 Clause 5.1.1 ---")
    doc28 = docx.Document(DATA_RAW / "28535-i20.docx")
    clause_511_text = []
    capture = False
    for p in doc28.paragraphs:
        t = p.text.strip()
        if re.match(r"^5\.1\.1\b", t):
            capture = True
        elif capture and re.match(r"^5\.\d", t) and not t.startswith("5.1.1"):
            capture = False
        if capture and t:
            clause_511_text.append(t)
    print("DOCX Content for 5.1.1:")
    for line in clause_511_text:
        print("  ", line)

    # 2. Check G019
    print("\n--- G019: TS 28.535 Clauses 4.2.4 & 4.2.5.2 ---")
    clause_424_text = []
    clause_4252_text = []
    capture_424 = False
    capture_4252 = False
    for p in doc28.paragraphs:
        t = p.text.strip()
        if re.match(r"^4\.2\.4\b", t):
            capture_424 = True
        elif capture_424 and re.match(r"^4\.2\.[5-9]", t):
            capture_424 = False
        if capture_424 and t:
            clause_424_text.append(t)

        if re.match(r"^4\.2\.5\.2\b", t):
            capture_4252 = True
        elif capture_4252 and (re.match(r"^4\.2\.5\.[3-9]", t) or re.match(r"^4\.2\.[6-9]", t) or re.match(r"^4\.3", t)):
            capture_4252 = False
        if capture_4252 and t:
            clause_4252_text.append(t)

    print("DOCX Content for 4.2.4 (first 8 lines):")
    for line in clause_424_text[:8]:
        print("  ", line)
    print("DOCX Content for 4.2.5.2:")
    for line in clause_4252_text:
        print("  ", line)

    # 3. Check G020
    print("\n--- G020: TS 38.300 Clauses 4.3.1.1 & 4.3.1.2 ---")
    doc38 = docx.Document(DATA_RAW / "38300-ia0.docx")
    clause_4311_text = []
    clause_4312_text = []
    capture_4311 = False
    capture_4312 = False
    for p in doc38.paragraphs:
        t = p.text.strip()
        if re.match(r"^4\.3\.1\.1\b", t):
            capture_4311 = True
        elif capture_4311 and re.match(r"^4\.3\.1\.2\b", t):
            capture_4311 = False
        if capture_4311 and t:
            clause_4311_text.append(t)

        if re.match(r"^4\.3\.1\.2\b", t):
            capture_4312 = True
        elif capture_4312 and (re.match(r"^4\.3\.1\.[3-9]", t) or re.match(r"^4\.3\.2", t) or re.match(r"^4\.4", t)):
            capture_4312 = False
        if capture_4312 and t:
            clause_4312_text.append(t)

    print("DOCX Content for 4.3.1.1:")
    for line in clause_4311_text:
        print("  ", line)
    print("DOCX Content for 4.3.1.2:")
    for line in clause_4312_text:
        print("  ", line)

    # 4. Check processed corpus preservation
    print("\n=================================================================")
    print("PROCESSED CORPUS PRESERVATION CHECK")
    print("=================================================================")
    def check_jsonl(fpath, target_clauses):
        found = {}
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                cnum = c.get("clause_number", "")
                for tc in target_clauses:
                    if cnum == tc or cnum.startswith(tc + "."):
                        found[cnum] = c
        for tc in target_clauses:
            matches = [k for k in found if k == tc or k.startswith(tc + ".")]
            if matches:
                for m in matches:
                    chunk = found[m]
                    print(f"PRESERVED: {fpath.name} | Clause {m} | ID: {chunk.get('chunk_id')} | Title: '{chunk.get('clause_title')}' | Chars: {len(chunk.get('text', ''))}")
            else:
                print(f"FAILED: {fpath.name} | Clause {tc} NOT found!")

    check_jsonl(DATA_PROC / "TS_28_535_chunks.jsonl", ["5.1.1", "4.2.4", "4.2.5.2"])
    check_jsonl(DATA_PROC / "TS_38_300_chunks.jsonl", ["4.3.1.1", "4.3.1.2"])

    # 5. Diagnostic retrieval trace for the 3 questions
    print("\n=================================================================")
    print("DIAGNOSTIC RETRIEVAL TRACE (Top-5 Retrieved per Query)")
    print("=================================================================")
    from retrieval.embedding import OllamaEmbedder
    from retrieval.vector_store import ChromaVectorStore
    from retrieval.bm25 import BM25Index
    from retrieval.retriever import SemanticRetriever, HybridRetriever
    from retrieval.index_corpus import load_all_chunks

    chunks = load_all_chunks()
    embedder = OllamaEmbedder()
    vector_store = ChromaVectorStore()
    bm25 = BM25Index()
    bm25.fit(chunks)
    sem = SemanticRetriever(embedder=embedder, vector_store=vector_store)
    hybrid = HybridRetriever(semantic_retriever=sem, bm25_index=bm25)

    queries = [
        ("G007", "What business-level functional requirements does TS 28.535 define for communication service assurance?", "TS 28.535", ["5.1.1"]),
        ("G019", "What does TS 28.535 specify about closed control loops and their governance?", "TS 28.535", ["4.2.4", "4.2.4.1", "4.2.4.2", "4.2.5.2"]),
        ("G020", "How are NG-RAN architecture and NG interface protocols structured across user plane and control plane in TS 38.300?", "TS 38.300", ["4.3.1.1", "4.3.1.2"]),
    ]

    for qid, qtext, exp_spec, exp_clauses in queries:
        print(f"\n--- Diagnostic Trace for {qid} ---")
        print(f"Query: '{qtext}'")
        print(f"Target Specification: {exp_spec} | Expected Clause(s): {exp_clauses}")
        results = hybrid.retrieve(qtext, top_k=10)
        found_target = False
        highest_rank = None
        for rank, r in enumerate(results, start=1):
            is_match = (r.specification == exp_spec and any(c in r.clause_number for c in exp_clauses))
            match_str = " [CORRECT TARGET EVIDENCE]" if is_match else ""
            if is_match and highest_rank is None:
                highest_rank = rank
                found_target = True
            print(f"  Rank {rank}: [{r.specification}] Clause {r.clause_number} — '{r.clause_title}' (method: {r.retrieval_method}){match_str}")
        print(f"Target Found in Top 10: {found_target} | Highest Target Rank: {highest_rank}")

if __name__ == "__main__":
    verify_all()

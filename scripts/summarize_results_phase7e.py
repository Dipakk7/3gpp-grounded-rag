import json
import sys
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.router import parse_query_specifications

with open('evaluation/retrieval/retrieval_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hybrid = data['hybrid_rrf']
print(f"Hybrid RRF Metrics:")
print(f"Hit@1:  {hybrid['hit@1']*100:.1f}%")
print(f"Hit@3:  {hybrid['hit@3']*100:.1f}%")
print(f"Hit@5:  {hybrid['hit@5']*100:.1f}%")
print(f"Hit@10: {hybrid['hit@10']*100:.1f}%")
print(f"MRR:    {hybrid['mrr']:.4f}")

print("\n--- Per-Query Detailed Results ---")
for q in hybrid['detailed_results']:
    qid = q['id']
    rank = q['first_relevant_rank']
    h1 = q['hit@1']
    h3 = q['hit@3']
    h5 = q['hit@5']
    h10 = q['hit@10']
    exp = q['expected']
    qtext = q['question']
    
    # Check routing
    detected = parse_query_specifications(qtext)
    routed = len(detected) > 0
    
    specs = [e['specification'] for e in exp]
    clauses = [e['clause_number'] for e in exp]
    
    print(f"{qid:<5} | Rank: {str(rank):<5} | H@1:{str(h1):<5} H@3:{str(h3):<5} H@5:{str(h5):<5} H@10:{str(h10):<5} | Specs: {specs} | Clauses: {clauses} | Routed: {routed} (det: {detected})")

import json

with open('evaluation/retrieval/retrieval_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hybrid = data['hybrid_rrf']
print(f"Total queries: {hybrid['total_queries']}")
print(f"Hit@1: {hybrid['hit@1']*100:.1f}%")
print(f"Hit@3: {hybrid['hit@3']*100:.1f}%")
print(f"Hit@5: {hybrid['hit@5']*100:.1f}%")
print(f"Hit@10: {hybrid['hit@10']*100:.1f}%")
print(f"MRR: {hybrid['mrr']:.4f}")

print("\n--- Per-Query Details ---")
for r in hybrid['detailed_results']:
    qid = r['id']
    rank = r['first_relevant_rank']
    hit5 = r['hit@5']
    q = r['question']
    exp = r['expected']
    print(f"{qid:<5} | Rank: {str(rank):<5} | Hit@5: {str(hit5):<5} | Q: {q[:50]}... | Expected: {exp}")

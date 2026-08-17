import json

def validate():
    with open('evaluation/retrieval/retrieval_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print(f"Total queries: {len(dataset)}")
    assert len(dataset) == 21, f"Expected 21 queries, found {len(dataset)}"

    q_ids = [q['id'] for q in dataset]
    expected_qids = [f"R{i:03d}" for i in range(1, 22)]
    assert q_ids == expected_qids, f"QIDs mismatch: {q_ids}"

    changed_keys = ["R004", "R007", "R009", "R020"]

    for q in dataset:
        assert 'id' in q
        assert 'question' in q
        assert 'category' in q
        assert 'expected' in q
        assert isinstance(q['expected'], list)
        for exp in q['expected']:
            assert 'specification' in exp
            assert 'clause_number' in exp
        ch_mark = " [CORRECTED]" if q['id'] in changed_keys else ""
        print(f"{q['id']}: {q['expected']}{ch_mark}")

    print("\nJSON and schema validation: 100% PASS")

if __name__ == "__main__":
    validate()

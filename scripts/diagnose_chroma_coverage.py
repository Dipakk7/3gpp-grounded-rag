import sys
import json
from pathlib import Path
from collections import Counter

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from retrieval.vector_store import ChromaVectorStore, DEFAULT_VECTORSTORE_PATH, COLLECTION_NAME
from ingestion.config import PROCESSED_DATA_DIR

def run_coverage_diagnostic():
    print("=================================================================")
    print("PHASE 6E DIAGNOSTIC: CHROMA SPECIFICATION INDEX COVERAGE")
    print("=================================================================")

    vs = ChromaVectorStore()
    total_vectors = vs.count()
    print(f"Chroma Collection Name: {COLLECTION_NAME}")
    print(f"Persisted Index Path: {DEFAULT_VECTORSTORE_PATH}")
    print(f"Total Chroma Vectors: {total_vectors}")

    # Read all metadatas from Chroma
    all_chroma_data = vs.collection.get(limit=10000, include=["metadatas"])
    metadatas = all_chroma_data.get("metadatas", [])
    print(f"Retrieved {len(metadatas)} metadatas from Chroma")

    # Analyze specification field in Chroma metadatas
    spec_counts = Counter()
    missing_spec = 0
    all_spec_values = set()

    for m in metadatas:
        if "specification" in m:
            val = m["specification"]
            spec_counts[val] += 1
            all_spec_values.add(val)
        else:
            missing_spec += 1

    print(f"\nUnique specification values in Chroma: {all_spec_values}")
    print(f"Counts by specification value in Chroma:")
    for k, v in spec_counts.items():
        print(f"  '{k}': {v}")
    print(f"Missing specification field count: {missing_spec}")

    # Inspect JSONL chunks per specification
    jsonl_files = {
        "TS 23.501": PROCESSED_DATA_DIR / "TS_23_501_chunks.jsonl",
        "TS 23.502": PROCESSED_DATA_DIR / "TS_23_502_chunks.jsonl",
        "TS 24.501": PROCESSED_DATA_DIR / "TS_24_501_chunks.jsonl",
        "TS 28.535": PROCESSED_DATA_DIR / "TS_28_535_chunks.jsonl",
        "TS 38.300": PROCESSED_DATA_DIR / "TS_38_300_chunks.jsonl",
    }

    jsonl_counts = {}
    jsonl_sample_metas = {}
    total_jsonl = 0

    for spec_name, fpath in jsonl_files.items():
        count = 0
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
                    if spec_name not in jsonl_sample_metas:
                        jsonl_sample_metas[spec_name] = json.loads(line)
        jsonl_counts[spec_name] = count
        total_jsonl += count

    print(f"\nTotal JSONL chunks across 5 specifications: {total_jsonl}")

    print("\n-----------------------------------------------------------------")
    print(f"{'Specification':<12} | {'JSONL Chunks':<14} | {'Chroma Vectors':<14} | {'Missing from Chroma'}")
    print("-----------------------------------------------------------------")
    specs_to_check = ["TS 23.501", "TS 23.502", "TS 24.501", "TS 28.535", "TS 38.300"]
    for s in specs_to_check:
        j_count = jsonl_counts.get(s, 0)
        c_count = spec_counts.get(s, 0)
        missing = j_count - c_count
        print(f"{s:<12} | {j_count:<14} | {c_count:<14} | {missing}")
    print("-----------------------------------------------------------------")

    # Test Chroma query filtering for each spec
    print("\nTesting Chroma Query Filtering (where={'specification': '<SPEC>'}):")
    for s in specs_to_check:
        res = vs.collection.get(where={"specification": s})
        matched_count = len(res["ids"]) if res and res.get("ids") else 0
        print(f"  where={{'specification': '{s}'}} -> {matched_count} matching vectors")

    # Check sample metadata from JSONL vs Chroma
    print("\nJSONL Stored Specification Values:")
    for s in specs_to_check:
        sample = jsonl_sample_metas.get(s, {})
        print(f"  {s} JSONL sample specification field: '{sample.get('specification')}' (type: {type(sample.get('specification')).__name__})")

    # Check sample metadata from Chroma
    print("\nChroma Stored Metadatas Sample:")
    for s in ["TS 23.501", "TS 23.502"]:
        res = vs.collection.get(where={"specification": s}, limit=1)
        if res and res.get("metadatas"):
            print(f"  {s} Chroma sample: {res['metadatas'][0]}")

if __name__ == "__main__":
    run_coverage_diagnostic()

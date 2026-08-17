"""
Source DOCX Direct Verification Script for Phase 7C
Directly parses the original raw DOCX files using python-docx to verify exact clause headings and content.
"""

import docx
from pathlib import Path

RAW_DIR = Path("data/raw")

def extract_docx_clauses(docx_path: Path, target_clauses: list):
    doc = docx.Document(docx_path)
    found = {c: [] for c in target_clauses}
    current_clause = None

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        
        # Check if paragraph starts with a target clause or is a heading
        for c in target_clauses:
            # Match exact clause prefix at start of paragraph e.g. "5.8.2.1 ", "6.3.3.3\t", etc.
            if text.startswith(f"{c} ") or text.startswith(f"{c}\t") or text == c:
                current_clause = c
                break
        
        if current_clause and current_clause in target_clauses:
            found[current_clause].append(text)
            # Stop collecting if next top-level or sibling clause begins
            if len(found[current_clause]) > 1:
                # check if a new clause started
                words = text.split()
                if len(words) > 1 and words[0][0].isdigit() and words[0] != current_clause and not words[0].startswith(f"{current_clause}."):
                    # Check if it looks like a clause number
                    first = words[0].rstrip(".\t")
                    parts = first.split(".")
                    if all(p.isdigit() for p in parts) and len(parts) >= 2:
                        current_clause = None

    # Also search tables in docx
    table_matches = {c: [] for c in target_clauses}
    for t_idx, table in enumerate(doc.tables):
        for row in table.rows:
            row_text = " | ".join(cell.text.strip().replace("\n", " ") for cell in row.cells if cell.text.strip())
            for c in target_clauses:
                if c in row_text:
                    table_matches[c].append(f"Table {t_idx+1}: {row_text[:200]}")

    return found, table_matches


def run_source_verification():
    print("=================================================================")
    print("PHASE 7C — DIRECT SOURCE DOCX GROUND-TRUTH AUDIT")
    print("=================================================================")

    # 1. R004: TS 23.501 (23501-ic0.docx)
    f23501 = RAW_DIR / "23501-ic0.docx"
    print(f"\n>>> 1. AUDITING R004 in {f23501.name}")
    found_23501, _ = extract_docx_clauses(f23501, ["5.8.2.1", "6.3.3", "6.3.3.1", "6.3.3.3"])
    
    for c in ["5.8.2.1", "6.3.3", "6.3.3.1", "6.3.3.3"]:
        lines = found_23501.get(c, [])
        print(f"\n--- Clause {c} ---")
        if lines:
            print(f"Heading / First Line: {lines[0]}")
            for l in lines[1:10]:
                print(f"  {l[:150]}...")
        else:
            print("  NOT FOUND as distinct paragraph start, searching text occurrences...")

    # 2. R007: TS 38.300 (38300-ia0.docx) & TS 23.502 (23502-ie0.docx)
    f38300 = RAW_DIR / "38300-ia0.docx"
    print(f"\n>>> 2. AUDITING R007 in {f38300.name}")
    found_38300, _ = extract_docx_clauses(f38300, ["9.2.1", "9.2.1.1", "9.2.3", "9.2.3.1", "9.2.3.2", "9.2.3.2.1"])
    for c in ["9.2.1", "9.2.1.1", "9.2.3", "9.2.3.1", "9.2.3.2", "9.2.3.2.1"]:
        lines = found_38300.get(c, [])
        print(f"\n--- TS 38.300 Clause {c} ---")
        if lines:
            print(f"Heading / First Line: {lines[0]}")
            for l in lines[1:6]:
                print(f"  {l[:150]}...")

    f23502 = RAW_DIR / "23502-ie0.docx"
    print(f"\n>>> AUDITING Handover Phases in {f23502.name}")
    found_23502, _ = extract_docx_clauses(f23502, ["4.9.1.2.1", "4.9.1.3.1", "4.9.1.3.2", "4.9.1.3.3"])
    for c in ["4.9.1.2.1", "4.9.1.3.1", "4.9.1.3.2", "4.9.1.3.3"]:
        lines = found_23502.get(c, [])
        print(f"\n--- TS 23.502 Clause {c} ---")
        if lines:
            print(f"Heading / First Line: {lines[0]}")
            for l in lines[1:4]:
                print(f"  {l[:150]}...")

    # 3. R009: TS 23.501 (23501-ic0.docx)
    print(f"\n>>> 3. AUDITING R009 in {f23501.name}")
    found_23501_r9, _ = extract_docx_clauses(f23501, ["5.7.1.3", "5.7.3.4", "5.7.4"])
    for c in ["5.7.1.3", "5.7.3.4", "5.7.4"]:
        lines = found_23501_r9.get(c, [])
        print(f"\n--- Clause {c} ---")
        if lines:
            print(f"Heading / First Line: {lines[0]}")
            for l in lines[1:8]:
                print(f"  {l[:150]}...")

    # 4. R020: TS 24.501 (24501-id0.docx)
    f24501 = RAW_DIR / "24501-id0.docx"
    print(f"\n>>> 4. AUDITING R020 in {f24501.name}")
    found_24501, tables_24501 = extract_docx_clauses(f24501, ["6.1.3.2", "6.1.3.2.1", "6.4.1.3"])
    for c in ["6.1.3.2", "6.1.3.2.1", "6.4.1.3"]:
        lines = found_24501.get(c, [])
        print(f"\n--- TS 24.501 Clause {c} ---")
        if lines:
            print(f"Heading / First Line: {lines[0]}")
            for l in lines[1:8]:
                print(f"  {l[:150]}...")
        if tables_24501.get(c):
            print(f"  Tables referencing {c}: {tables_24501[c][:2]}")


if __name__ == "__main__":
    run_source_verification()

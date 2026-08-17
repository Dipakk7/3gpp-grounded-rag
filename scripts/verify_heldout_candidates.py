import docx
from pathlib import Path

DATA_RAW = Path("data/raw")

def inspect_clause_in_docx(filename, target_heading_prefix):
    doc_path = DATA_RAW / filename
    doc = docx.Document(doc_path)
    found = []
    capture = False
    captured_text = []
    
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        if text.startswith(target_heading_prefix):
            capture = True
            found.append(text)
            continue
        if capture:
            if p.style and p.style.name.startswith("Heading") and not text.startswith(target_heading_prefix):
                break
            captured_text.append(text)
            if len(captured_text) >= 5:
                break
    return found, captured_text[:5]

# Let's verify our candidates:
# Category A:
# 1. H001: TS 23.501 §3.1 "Definitions" - Definition of "5G System" / "Network Slice" / "PDU Session"
# 2. H002: TS 38.300 §3.1 "Definitions" - Definition of "gNB" / "ng-eNB" / "En-gNB"

# Category B:
# 3. H003: TS 23.502 §4.2.2.3.2 "UE-initiated Deregistration" (procedural steps for UE-initiated deregistration in 5G System)
# 4. H004: TS 23.502 §4.2.3.2 "UE Triggered Service Request" (procedural steps for Service Request procedure in 5G System)

# Category C:
# 5. H005: TS 23.501 §5.2 "Architecture Reference Model" / §5.2.1 "General description" (or §5.3.2 "5GS mobility management states overview")
# 6. H006: TS 38.300 §6.1 "User Plane Protocol Stack Description" (or §6.1.1 "User Plane")

for fn, h in [
    ("23501-ic0.docx", "3.1\tDefinitions"),
    ("38300-ia0.docx", "3.1\tDefinitions"),
    ("23502-ie0.docx", "4.2.2.3.2\tUE-initiated Deregistration"),
    ("23502-ie0.docx", "4.2.3.2\tUE Triggered Service Request"),
    ("23501-ic0.docx", "5.3.2\t5GS Mobility Management states"),
    ("38300-ia0.docx", "6.1\tUser Plane"),
]:
    h_found, lines = inspect_clause_in_docx(fn, h.split("\t")[0])
    print(f"File: {fn} | Target: {h}")
    print(f"  Headings: {h_found}")
    print(f"  Sample: {lines[:2]}")
    print("-" * 50)

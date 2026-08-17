"""
Document metadata extraction logic for 3GPP specifications.
Extracts specification number, version, release, title, and publication date from DOCX structure.
"""

import re
from pathlib import Path
import docx
from ingestion.models import DocumentMetadata
from ingestion.config import KNOWN_SPEC_TITLES


def extract_document_metadata(doc: docx.Document, doc_path: Path) -> DocumentMetadata:
    """
    Extracts specification number, version, release, date, and title from cover text and properties.
    """
    filename = doc_path.name

    # 1. Search cover paragraphs (first 30)
    cover_paragraphs = [p for p in doc.paragraphs[:30] if p.text.strip()]
    cover_text = "\n".join([p.text.strip() for p in cover_paragraphs])

    # Match: "3GPP TS 23.501 V18.12.0 (2024-12)"
    spec_match = re.search(
        r"3GPP\s+TS\s+([\d\.]+)\s+V([\d\.]+)\s*(?:\(([\d\-]+)\))?",
        cover_text,
        re.IGNORECASE,
    )

    if spec_match:
        spec_num = f"TS {spec_match.group(1)}"
        spec_ver = f"V{spec_match.group(2)}"
        spec_date = spec_match.group(3) if spec_match.group(3) else "Unknown"
    else:
        # Fallback to headers
        header_text = ""
        for s in doc.sections:
            header_text += " " + " ".join([p.text for p in s.header.paragraphs])
        spec_match = re.search(
            r"3GPP\s+TS\s+([\d\.]+)\s+V([\d\.]+)\s*(?:\(([\d\-]+)\))?",
            header_text,
            re.IGNORECASE,
        )
        if spec_match:
            spec_num = f"TS {spec_match.group(1)}"
            spec_ver = f"V{spec_match.group(2)}"
            spec_date = spec_match.group(3) if spec_match.group(3) else "Unknown"
        else:
            # Infer from filename if needed (e.g. 23501-ic0.docx -> TS 23.501)
            fn_match = re.match(r"^(\d{2})(\d{3})", filename)
            if fn_match:
                spec_num = f"TS {fn_match.group(1)}.{fn_match.group(2)}"
            else:
                spec_num = "Unknown"
            spec_ver = "Unknown"
            spec_date = "Unknown"

    # 2. Release extraction
    rel_match = re.search(r"Release\s+(\d+)", cover_text, re.IGNORECASE)
    if not rel_match and doc.core_properties.subject:
        rel_match = re.search(r"Release\s+(\d+)", doc.core_properties.subject, re.IGNORECASE)
    spec_rel = f"Release {rel_match.group(1)}" if rel_match else "Release 18"

    # 3. Canonical or extracted title
    title = KNOWN_SPEC_TITLES.get(spec_num)
    if not title:
        for p in cover_paragraphs:
            if p.style.name in ["Cover_main_title", "ZT", "Title"] and len(p.text.strip()) > 10:
                lines = [l.strip() for l in p.text.strip().split("\n") if l.strip()]
                meaningful = [
                    l for l in lines
                    if not any(k in l for k in ["3rd Generation", "Technical Specification Group", "Stage", "Release", "3GPP"])
                ]
                if meaningful:
                    title = "; ".join(meaningful)
                    break
        if not title:
            title = doc.core_properties.title or "Unknown 3GPP Specification"

    return DocumentMetadata(
        specification=spec_num,
        version=spec_ver,
        release=spec_rel,
        date=spec_date,
        title=title,
        source_filename=filename,
    )

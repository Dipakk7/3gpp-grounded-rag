"""
Configuration settings and constants for 3GPP document ingestion.
"""

from pathlib import Path
import re

# Directory Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DOCS_DIR = ROOT_DIR / "docs"

# Expected Corpus Files
EXPECTED_FILES = [
    "23501-ic0.docx",
    "23502-ie0.docx",
    "24501-id0.docx",
    "28535-i20.docx",
    "38300-ia0.docx",
]

# Canonical 3GPP Specification Titles
KNOWN_SPEC_TITLES = {
    "TS 23.501": "System architecture for the 5G System (5GS); Stage 2",
    "TS 23.502": "Procedures for the 5G System (5GS); Stage 2",
    "TS 24.501": "Non-Access-Stratum (NAS) protocol for 5G System (5GS); Stage 3",
    "TS 28.535": "Management and orchestration; Management services for Communication Service Assurance; Requirements",
    "TS 38.300": "NR; NR and NG-RAN Overall Description; Stage 2",
}

# Regular Expression Patterns for 3GPP Clauses & Annexes
# Headings in body text use tab separation: <Clause_Number>\t<Clause_Title>
CLAUSE_REGEX = re.compile(r"^(\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\t+(.*)$")
ANNEX_REGEX = re.compile(r"^Annex\s+([A-Z])\s*\(([^)]+)\):\s*(.*)$", re.IGNORECASE)

# Table and Figure Caption Regexes
TABLE_CAPTION_REGEX = re.compile(r"^Table\s+([\d\.\-A-Za-z]+)\s*[:：]\s*(.*)$", re.IGNORECASE)
FIGURE_CAPTION_REGEX = re.compile(r"^Figure\s+([\d\.\-A-Za-z]+)\s*[:：]\s*(.*)$", re.IGNORECASE)

# Chunking Thresholds (derived from corpus empirical character distribution)
# Median clause length is ~1,300 chars; 75th percentile is ~3,000 chars.
MAX_CHUNK_CHARS = 2400
MIN_SPLIT_CHARS = 1200
TARGET_CHUNK_CHARS = 1800

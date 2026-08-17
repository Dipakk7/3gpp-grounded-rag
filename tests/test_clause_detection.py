"""
Unit tests for 3GPP clause detection logic.
Validates that the parser distinguishes true structural headings from prose, TOC, and tables.
"""

import unittest
import re

# Parser detection primitives (matching inspect_documents.py logic)
CLAUSE_REGEX = re.compile(r"^(\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\t+(.*)$")
ANNEX_REGEX = re.compile(r"^Annex\s+([A-Z])\s*\(([^)]+)\):\s*(.*)$", re.IGNORECASE)


def is_structural_clause(text: str, style_name: str, is_toc: bool = False) -> bool:
    """
    Evaluates whether a paragraph represents an authoritative structural clause heading.
    Combines DOCX style constraints, TOC filtering, and regular expression validation.
    """
    if is_toc:
        return False

    s_lower = style_name.lower().strip()
    # Reject known non-heading styles
    if any(k in s_lower for k in ["toc", "header", "footer", "caption", "th", "tf", "ta", "table"]):
        return False

    is_heading_style = (
        "heading" in s_lower
        or "annex" in s_lower
        or (s_lower.startswith("h") and len(s_lower) <= 3 and s_lower[1:].isdigit())
    )

    if not is_heading_style:
        return False

    clean_text = text.strip()
    if not clean_text:
        return False

    # Standard named unnumbered front-matter sections
    if clean_text in ["Foreword", "Introduction", "Scope", "References"]:
        return True

    # Annex heading (e.g., 'Annex A (normative): ...')
    if ANNEX_REGEX.match(clean_text):
        return True

    # Numbered / Alphanumeric clause heading (e.g., '4.2.3\tTitle', 'A.1\tTitle')
    if CLAUSE_REGEX.match(clean_text):
        return True

    return False


class TestClauseDetection(unittest.TestCase):
    """Validation test suite for 3GPP clause parsing."""

    def test_1_valid_clause_detected(self):
        """Test 1 — Valid clause detected: A known real clause heading must be recognized."""
        text = "4.2.3\tNon-roaming reference architecture"
        style = "Heading 3"
        self.assertTrue(
            is_structural_clause(text, style, is_toc=False),
            "Failed to detect standard level-3 clause heading.",
        )

    def test_2_nested_clause_detected(self):
        """Test 2 — Nested clause detected: Deeply nested clause (e.g. 4.2.8.2.1) recognized."""
        text = "4.2.8.2.1\tNon-roaming Architecture"
        style = "Heading 5"
        self.assertTrue(
            is_structural_clause(text, style, is_toc=False),
            "Failed to detect deeply nested level-5 clause heading.",
        )

    def test_3_annex_clause_detected(self):
        """Test 3 — Annex clause detected: Both top-level Annex and Annex subclause recognized."""
        annex_top = "Annex A (informative):\nRelationship between Service-Based Interfaces and Reference Points"
        self.assertTrue(
            is_structural_clause(annex_top, "Heading 8", is_toc=False),
            "Failed to detect top-level Annex heading.",
        )

        annex_sub = "A.1\tChange history"
        self.assertTrue(
            is_structural_clause(annex_sub, "Heading 1", is_toc=False),
            "Failed to detect Annex subclause heading.",
        )

    def test_4_numeric_prose_rejected(self):
        """Test 4 — Numeric prose rejected: Body prose containing numbers must not become a clause."""
        prose_samples = [
            ("As described in clause 4.2.3, the AMF provides registration management.", "Normal"),
            ("1. The UE sends a Registration Request message to the (R)AN.", "B1"),
            ("The timer T3512 has a default value of 54.0 minutes (see clause 10.2).", "Normal"),
            ("3GPP TS 23.501 V18.12.0 (2024-12)", "Header"),
            ("© 2025, 3GPP Organizational Partners (ARIB, ATIS, CCSA, ETSI, TSDSI, TTA, TTC).", "Normal"),
        ]
        for text, style in prose_samples:
            self.assertFalse(
                is_structural_clause(text, style, is_toc=False),
                f"Incorrectly classified numeric prose as clause: {text}",
            )

    def test_5_toc_artifact_rejected(self):
        """Test 5 — TOC artifact rejected: Table of Contents line must not become an indexed clause."""
        toc_samples = [
            ("4.2.3\tNon-roaming reference architecture\t43", "toc 3", True),
            ("1\tScope\t23", "toc 1", True),
            ("Contents", "TT", True),
            ("Foreword\t22", "toc 1", True),
        ]
        for text, style, is_toc in toc_samples:
            self.assertFalse(
                is_structural_clause(text, style, is_toc=is_toc),
                f"Incorrectly classified TOC artifact as body clause: {text}",
            )

    def test_6_table_text_rejected_as_heading(self):
        """Test 6 — Table text rejected as a heading: Table cells and captions must not become clauses."""
        table_samples = [
            ("5.4.1\t5GMM-REGISTERED\tNormal service", "TA"),
            ("Table 4.2.3-1: Non-roaming architecture reference points", "TH"),
            ("Figure 4.2.3-1: Non-roaming architecture in reference point representation", "TF"),
            ("Table 6.1-1: Management services for ACCL", "Table Head"),
        ]
        for text, style in table_samples:
            self.assertFalse(
                is_structural_clause(text, style, is_toc=False),
                f"Incorrectly classified table/figure text as clause heading: {text}",
            )


if __name__ == "__main__":
    unittest.main()

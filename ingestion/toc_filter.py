"""
Table of Contents (TOC) filtering logic for 3GPP specifications.
Strips pre-body TOC structures while preserving all valid technical body sections and paragraphs.
"""

import re
from typing import Tuple


def is_toc_marker(text: str, style_name: str, index: int) -> bool:
    """
    Checks if a paragraph represents the start of the Table of Contents block.
    """
    clean = text.strip().lower()
    s_lower = style_name.lower().strip()
    return clean == "contents" and (
        "tt" in s_lower or "heading" in s_lower or "normal" in s_lower or index < 35
    )


class TOCFilter:
    """
    Stateful filter that detects the TOC boundary and filters out TOC artifact paragraphs.
    """

    def __init__(self):
        self.in_toc: bool = False
        self.toc_ended: bool = False
        self.toc_paragraph_count: int = 0

    def process_paragraph(self, text: str, style_name: str, index: int) -> Tuple[bool, bool]:
        """
        Evaluates a paragraph during sequential traversal.
        Returns:
            (is_toc_item: bool, is_body_active: bool)
        """
        clean = text.strip()
        s_lower = style_name.lower().strip()

        # Check for TOC start
        if not self.in_toc and not self.toc_ended:
            if is_toc_marker(clean, style_name, index):
                self.in_toc = True
                self.toc_paragraph_count += 1
                return True, False

        # While inside TOC block
        if self.in_toc and not self.toc_ended:
            # TOC entry characteristics:
            # 1. Style is 'toc 1'..'toc 5'
            # 2. Text is 'Contents'
            # 3. Contains tab followed by page digits at end (e.g. '1\tScope\t23')
            is_toc_style = s_lower.startswith("toc") or s_lower == "tt"
            has_trailing_page = bool(re.search(r"\t\d+$", clean))

            if is_toc_style or clean.lower() == "contents" or has_trailing_page:
                self.toc_paragraph_count += 1
                return True, False
            else:
                # First non-TOC paragraph indicates TOC has ended
                if clean:
                    self.in_toc = False
                    self.toc_ended = True
                    return False, True
                else:
                    # Empty paragraph in TOC region
                    return True, False

        # If TOC has already ended or index past front-matter, it's body content
        if not self.toc_ended and index > 50:
            self.toc_ended = True

        return False, True

"""
Clause detection and section hierarchy reconstruction logic for 3GPP specifications.
Maintains a hierarchical breadcrumb stack during sequential document traversal.
"""

from typing import List, Optional, Tuple
from ingestion.models import ClauseInfo, BreadcrumbItem
from ingestion.config import CLAUSE_REGEX, ANNEX_REGEX


class HierarchyTracker:
    """
    Tracks and updates the active section hierarchy and breadcrumb path during parsing.
    """

    def __init__(self):
        # Stack of (level: int, BreadcrumbItem)
        self.stack: List[Tuple[int, BreadcrumbItem]] = []
        self.current_clause: Optional[ClauseInfo] = None

    def update(self, clause_info: ClauseInfo) -> List[BreadcrumbItem]:
        """
        Updates the active hierarchy stack with the new clause.
        Pops shallower or equal levels and appends the new level.
        Returns the full current breadcrumb list.
        """
        new_level = clause_info.level
        new_item = BreadcrumbItem(number=clause_info.clause_number, title=clause_info.clause_title)

        # Pop any items from the stack that are at the same or deeper level
        while self.stack and self.stack[-1][0] >= new_level:
            self.stack.pop()

        # Compute parent clause number from top of remaining stack
        if self.stack:
            clause_info.parent_clause = self.stack[-1][1].number
        else:
            clause_info.parent_clause = None

        self.stack.append((new_level, new_item))
        clause_info.breadcrumb = [item for _, item in self.stack]
        self.current_clause = clause_info
        return clause_info.breadcrumb


class ClauseParser:
    """
    Detects 3GPP clause boundaries by combining DOCX heading styles and regular expressions.
    """

    def __init__(self):
        self.hierarchy = HierarchyTracker()

    def parse_heading(self, text: str, style_name: str, is_toc: bool = False) -> Optional[ClauseInfo]:
        """
        Evaluates a paragraph to determine if it marks an authoritative clause boundary.
        If yes, returns ClauseInfo and updates hierarchy. Otherwise returns None.
        """
        if is_toc:
            return None

        s_lower = style_name.lower().strip()
        # Reject non-heading styles immediately
        if any(k in s_lower for k in ["toc", "header", "footer", "caption", "th", "tf", "ta", "table", "b1", "b2", "normal"]):
            return None

        is_heading_style = (
            "heading" in s_lower
            or "annex" in s_lower
            or (s_lower.startswith("h") and len(s_lower) <= 3 and s_lower[1:].isdigit())
        )

        if not is_heading_style:
            return None

        clean_text = text.strip()
        if not clean_text:
            return None

        # 1. Top-Level Annex match: "Annex A (normative): Mapping between..."
        match_annex = ANNEX_REGEX.match(clean_text)
        if match_annex or (clean_text.lower().startswith("annex ") and ":" in clean_text):
            if match_annex:
                letter = match_annex.group(1).upper()
                normative_type = match_annex.group(2).strip().lower()
                annex_title = match_annex.group(3).strip().replace("\n", " ")
            else:
                parts = clean_text.split(":", 1)
                letter = parts[0].split()[1].upper() if len(parts[0].split()) > 1 else "A"
                normative_type = "informative" if "informative" in parts[0].lower() else "normative"
                annex_title = parts[1].strip().replace("\n", " ") if len(parts) > 1 else clean_text

            clause_num = f"Annex {letter}"
            clause_info = ClauseInfo(
                clause_number=clause_num,
                clause_title=annex_title,
                level=1,
                style_name=style_name,
                is_annex=True,
                annex_type=normative_type,
            )
            self.hierarchy.update(clause_info)
            return clause_info

        # 2. Numbered / Alphanumeric Clause match: "4.2.3\tNon-roaming reference architecture"
        match_clause = CLAUSE_REGEX.match(clean_text)
        if match_clause:
            c_num = match_clause.group(1)
            c_title = match_clause.group(2).strip().replace("\n", " ")
            level = len(c_num.split("."))
            is_annex_sub = c_num[0].isalpha()

            clause_info = ClauseInfo(
                clause_number=c_num,
                clause_title=c_title,
                level=level,
                style_name=style_name,
                is_annex=is_annex_sub,
                annex_type=None,
            )
            self.hierarchy.update(clause_info)
            return clause_info

        # 3. Unnumbered Standard Front-Matter Headings
        if clean_text in ["Foreword", "Introduction", "Scope", "References"]:
            clause_info = ClauseInfo(
                clause_number=clean_text,
                clause_title=clean_text,
                level=1,
                style_name=style_name,
                is_annex=False,
                annex_type=None,
            )
            self.hierarchy.update(clause_info)
            return clause_info

        return None

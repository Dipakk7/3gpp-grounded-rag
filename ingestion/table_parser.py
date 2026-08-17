"""
Table parsing and markdown formatting logic for 3GPP specifications.
Preserves structured tabular data, captions, rows, columns, and generates deterministic table IDs.
"""

from typing import List, Optional, Tuple
import re
import docx.table
from ingestion.config import TABLE_CAPTION_REGEX


def clean_cell_text(text: str) -> str:
    """Cleans cell content for markdown table rendering, replacing newlines and escaping pipes."""
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n") if line.strip()]
    joined = " <br> ".join(lines)
    return joined.replace("|", "\\|").strip()


def table_to_markdown(table: docx.table.Table) -> Tuple[str, Optional[str]]:
    """
    Converts a docx Table object into a clean GitHub-flavored Markdown table.
    Also detects if the first row is an embedded title/caption row.
    """
    rows_data: List[List[str]] = []
    embedded_caption: Optional[str] = None

    for row_idx, row in enumerate(table.rows):
        row_cells = [clean_cell_text(cell.text) for cell in row.cells]
        # De-duplicate consecutive identical cells from merged columns
        deduped_cells = []
        for c in row_cells:
            if not deduped_cells or c != deduped_cells[-1]:
                deduped_cells.append(c)

        if not any(deduped_cells):
            continue

        # Check if first row is a merged caption row (e.g. "Table 4.2.3-1: ...")
        if row_idx == 0 and len(deduped_cells) == 1:
            first_cell = deduped_cells[0].replace(" <br> ", " ").strip()
            if TABLE_CAPTION_REGEX.match(first_cell) or first_cell.startswith("Table "):
                embedded_caption = first_cell
                continue

        rows_data.append(row_cells)

    if not rows_data:
        return "", embedded_caption

    num_cols = max(len(r) for r in rows_data)
    normalized_rows = []
    for r in rows_data:
        if len(r) < num_cols:
            r = r + [""] * (num_cols - len(r))
        normalized_rows.append(r)

    # First remaining row as header
    header = normalized_rows[0]
    md_lines = []
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join([":---"] * num_cols) + " |")

    for r in normalized_rows[1:]:
        md_lines.append("| " + " | ".join(r) + " |")

    return "\n".join(md_lines), embedded_caption


def generate_table_id(spec_num: str, table_index: int) -> str:
    """
    Generates a unique, deterministic table ID.
    Example: TS 23.501, index 1 -> 'TS23501-T001'
    """
    clean_spec = spec_num.replace(" ", "").replace(".", "")
    return f"{clean_spec}-T{table_index:03d}"


class TableParser:
    """
    Extracts tables, formats them to markdown, and links captions and table IDs.
    """

    def __init__(self, spec_num: str):
        self.spec_num = spec_num
        self.table_counter: int = 0

    def parse(self, table: docx.table.Table, caption: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
        """
        Parses a table into (table_id, table_markdown, table_caption).
        """
        self.table_counter += 1
        table_id = generate_table_id(self.spec_num, self.table_counter)
        md_text, embedded_caption = table_to_markdown(table)

        final_caption = caption or embedded_caption
        if final_caption:
            clean_cap = final_caption.strip()
            full_text = f"**{clean_cap}**\n\n{md_text}"
        else:
            clean_cap = None
            full_text = md_text

        return table_id, full_text, clean_cap

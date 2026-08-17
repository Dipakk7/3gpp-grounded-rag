"""
Specification-Aware Retrieval Router:
Deterministic parser that extracts and canonicalizes 3GPP specification identifiers from user queries.
"""

import re
from typing import List, Set

# Canonical supported 3GPP specifications
SUPPORTED_SPECS = {
    "23.501": "TS 23.501",
    "23.502": "TS 23.502",
    "24.501": "TS 24.501",
    "28.535": "TS 28.535",
    "38.300": "TS 38.300",
}

# Regex pattern matching 3GPP specifications with optional "3GPP", optional "TS", and supported spec number
# Examples matched: "TS 23.501", "TS23.501", "3GPP TS 23.501", "3GPP TS28.535", "TS 38.300", "28.535" (when preceded by TS or spec context)
SPEC_PATTERN = re.compile(
    r"(?:3GPP\s+)?(?:TS\s*|spec(?:ification)?\s+)?(23\.501|23\.502|24\.501|28\.535|38\.300)\b",
    re.IGNORECASE
)


def parse_query_specifications(query: str) -> List[str]:
    """
    Deterministically extracts and canonicalizes all supported 3GPP specification identifiers from query text.
    Returns a sorted list of unique canonical identifiers, e.g. ['TS 28.535'] or ['TS 23.501', 'TS 23.502'].
    If no supported specification is detected, returns an empty list.
    """
    if not query or not query.strip():
        return []

    matches = SPEC_PATTERN.findall(query)
    found_specs: Set[str] = set()

    for match in matches:
        match_clean = match.strip()
        if match_clean in SUPPORTED_SPECS:
            found_specs.add(SUPPORTED_SPECS[match_clean])

    return sorted(list(found_specs))

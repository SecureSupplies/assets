"""Product classification helper.

This module contains a simple heuristic classifier that assigns each
record to a product category in the taxonomy based on keywords.  In a
production system this would likely use a machine‑learning model or
rules engine informed by NAICS/PSC/NIGP codes.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import Record
from .log import get_logger

logger = get_logger(__name__)


# A simple keyword map for demonstration.  Real implementation would
# parse NAICS/PSC codes and use ML classifiers.
KEYWORD_MAP: dict[str, str] = {
    r"\bdiesel\b": "diesel",
    r"\bdef\b": "def",
    r"\bhydrogen\b": "hydrogen",
    r"\bnitrogen\b": "nitrogen",
    r"\boxygen\b": "oxygen",
    r"\bpropane\b": "propane",
    r"\bjet fuel\b": "jet",
}


def classify_record(record: Record) -> str:
    """Classify the record and assign a taxonomy ID.

    Args:
        record: Normalized record.

    Returns:
        The taxonomy ID assigned to the record.  If no keywords are
        matched the value ``other`` is returned.
    """
    text = f"{record.title} {record.description or ''}".lower()
    for pattern, category in KEYWORD_MAP.items():
        if re.search(pattern, text):
            record.taxonomy = category
            logger.debug("Classified record %s as %s", record.id, category)
            return category
    record.taxonomy = "other"
    logger.debug("Classified record %s as other", record.id)
    return "other"

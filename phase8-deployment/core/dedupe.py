"""Deduplication utilities.

This module provides a naive deduplicator that filters out records
with identical source and ID combinations.  In a production system
you would maintain a hash registry to track duplicates across runs.
"""

from __future__ import annotations

from typing import Iterable, List, Set

from .models import Record
from .log import get_logger

logger = get_logger(__name__)


def dedupe_records(records: Iterable[Record]) -> List[Record]:
    """Remove duplicate records based on (source, id) pair.

    Args:
        records: Iterable of records to deduplicate.

    Returns:
        List of unique records preserving original order.
    """
    seen: Set[tuple[str, str]] = set()
    unique: List[Record] = []
    for rec in records:
        key = (rec.source, rec.id)
        if key not in seen:
            seen.add(key)
            unique.append(rec)
        else:
            logger.debug("Dropping duplicate record %s from source %s", rec.id, rec.source)
    return unique

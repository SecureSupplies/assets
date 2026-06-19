"""Opportunity scoring logic.

This module scores the overall potential of an opportunity based on
estimated value, buyer reputation and relevance to core product lines.
For simplicity this stub assigns points based on the presence of
product keywords and mentions of repeat buyers.
"""

from __future__ import annotations

from .models import Record
from .log import get_logger

logger = get_logger(__name__)


def score_opportunity(record: Record) -> int:
    """Compute an opportunity score from 0‑100.

    Args:
        record: Normalized record.

    Returns:
        Integer score where higher values indicate more attractive long‑cycle opportunities.
    """
    score = 0

    # Award more points for core products (these align with our taxonomy)
    product_weights = {
        "diesel": 20,
        "def": 15,
        "lng": 10,
        "cng": 10,
        "hydrogen": 25,
        "oxygen": 5,
        "nitrogen": 5,
        "propane": 10,
    }
    if record.taxonomy in product_weights:
        score += product_weights[record.taxonomy]
        logger.debug(
            "Product taxonomy '%s' adds %s points to record %s",
            record.taxonomy,
            product_weights[record.taxonomy],
            record.id,
        )

    # Detect repeat buyer signals in description
    repeat_keywords = ["renewal", "extension", "multi‑year", "incumbent"]
    text = f"{record.title} {record.description or ''}".lower()
    for kw in repeat_keywords:
        if kw in text:
            score += 20
            logger.debug("Repeat buyer keyword '%s' found in record %s", kw, record.id)
            break

    record.opportunity_score = min(score, 100)
    return record.opportunity_score

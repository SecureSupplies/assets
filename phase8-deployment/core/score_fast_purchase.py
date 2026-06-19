"""Fast purchase scoring logic.

This module provides a simplistic scoring algorithm for determining the
urgency of an opportunity.  The real system uses more complex
heuristics and economic signals; this stub scores based on keyword
triggers and deadlines encoded in the record description.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

from .models import Record
from .log import get_logger

logger = get_logger(__name__)


DEADLINE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")  # ISO date in description


def score_fast_purchase(record: Record) -> int:
    """Compute a fast‑purchase score from 0–100.

    Args:
        record: Normalized record.

    Returns:
        Integer score where values ≥70 are routed to fast purchase posts.
    """
    score = 0

    # Basic keyword triggers indicating urgency
    urgent_keywords = ["immediate delivery", "emergency", "asap", "urgent"]
    text = f"{record.title} {record.description or ''}".lower()
    for kw in urgent_keywords:
        if kw in text:
            score += 30
            logger.debug("Fast purchase keyword '%s' found in record %s", kw, record.id)

    # Detect deadlines in description and score based on proximity
    match = DEADLINE_PATTERN.search(text)
    if match:
        try:
            deadline = datetime.fromisoformat(match.group(1))
            days_until = (deadline - datetime.utcnow()).days
            if days_until <= 1:
                score += 40
            elif days_until <= 3:
                score += 20
            elif days_until <= 7:
                score += 10
            logger.debug(
                "Deadline %s for record %s yields %s additional points",
                deadline.date(),
                record.id,
                score,
            )
        except ValueError:
            pass

    record.fast_purchase_score = min(score, 100)
    return record.fast_purchase_score

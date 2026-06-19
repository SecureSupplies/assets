"""Core modules for Phase 8 Government Biz.

This package contains configuration helpers, logging setup, data models,
classification and scoring utilities used across the ingestion pipeline.
"""

from .config import get_settings
from .log import get_logger
from .models import Record
from .classify_products import classify_record
from .score_fast_purchase import score_fast_purchase
from .score_opportunities import score_opportunity
from .dedupe import dedupe_records

__all__ = [
    "get_settings",
    "get_logger",
    "Record",
    "classify_record",
    "score_fast_purchase",
    "score_opportunity",
    "dedupe_records",
]

#!/usr/bin/env python
"""Test mode for Phase 8 Government Biz.

This script pulls a limited number of records from each configured
source adapter, normalizes, dedupes, classifies and scores them, and
prints a CSV summary to STDOUT.  It is intended for local testing
without writing to the CRM.
"""

from __future__ import annotations

import argparse
import csv
import sys

from ..core import (
    classify_record,
    score_fast_purchase,
    score_opportunity,
    dedupe_records,
    get_logger,
)
from ..adapters import SamAdapter, UsaSpendingAdapter


logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase8 test mode")
    parser.add_argument(
        "--source",
        dest="source",
        choices=["sam", "usaspending", "gsa", "eia", "state_csv"],
        help="Single source to fetch (optional)",
    )
    parser.add_argument("--limit", dest="limit", type=int, default=20, help="Max records per source")
    args = parser.parse_args()

    records = []
    # Determine sources to fetch
    sources = [args.source] if args.source else ["sam", "usaspending"]
    for src in sources:
        if src == "sam":
            adapter = SamAdapter()
        elif src == "usaspending":
            adapter = UsaSpendingAdapter()
        else:
            logger.warning("Source %s is not implemented in test mode", src)
            continue
        fetched = adapter.fetch(limit=args.limit)
        records.extend(fetched)

    # Deduplicate
    records = dedupe_records(records)

    # Classify and score
    for rec in records:
        classify_record(rec)
        score_fast_purchase(rec)
        score_opportunity(rec)

    # Output CSV summary
    writer = csv.writer(sys.stdout)
    writer.writerow(["source", "id", "title", "taxonomy", "fast_purchase_score", "opportunity_score"])
    for rec in records:
        writer.writerow([
            rec.source,
            rec.id,
            rec.title,
            rec.taxonomy,
            rec.fast_purchase_score,
            rec.opportunity_score,
        ])


if __name__ == "__main__":
    main()

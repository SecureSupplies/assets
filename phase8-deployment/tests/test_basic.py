"""Basic unit tests for Phase 8 Government Biz.

These tests exercise the classifier and scoring functions using simple
fixtures.  Extend these tests as the business logic becomes more
sophisticated.
"""

from phase8_government_biz.core import (
    Record,
    classify_record,
    score_fast_purchase,
    score_opportunity,
)


def test_classification_and_scoring():
    record = Record(
        source="sam",
        id="123",
        title="Emergency diesel delivery",
        description="Need diesel ASAP for backup generators by 2026-06-18",
    )
    classify_record(record)
    assert record.taxonomy == "diesel"
    score_fast_purchase(record)
    score_opportunity(record)
    # Fast purchase score should be high due to 'ASAP' and near deadline
    assert record.fast_purchase_score >= 70
    # Opportunity score should include points for diesel taxonomy
    assert record.opportunity_score >= 20

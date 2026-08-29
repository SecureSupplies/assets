from __future__ import annotations

from datetime import datetime, timedelta, timezone

import run_pipeline
from adapters.samples import SampleAdapter
from core.classify_products import classify_record, classify_records
from core.config import Settings
from core.dedupe import dedupe_records
from core.route_records import route_record, route_records
from core.schemas import NormalizedRecord
from core.score_opportunities import days_until, score_record, score_records
from crm.zoho_modules import EXTERNAL_ID_LABEL, field_payload, infer_type
from crm.zoho_tasks import task_payload_for_record
from crm.zoho_upsert import ZohoUpsertClient, chunks, record_to_labels, source_health_to_labels


def records():
    return route_records(score_records(classify_records(SampleAdapter(Settings()).fetch().records)))


def future_date(days: int) -> str:
    return (datetime.now(timezone.utc).date() + timedelta(days=days)).isoformat()


def test_fast_purchase():
    item = records()[0]
    assert item.fast_purchase_score >= 70
    assert item.recommended_module == "GOV FAST PURCHASE POSTS"


def test_auction_route():
    assert any(record.recommended_module == "GOV AUCTIONS" for record in records())


def test_dedupe():
    raw = SampleAdapter(Settings()).fetch().records
    assert len(dedupe_records(raw + [raw[0]])) == len(raw)


def test_due_today_is_not_expired():
    assert days_until(future_date(0)) == 0


def test_expired_notice_never_reaches_money_queue():
    record = NormalizedRecord(
        source_platform="test",
        source_type="opportunity",
        source_record_id="expired-1",
        source_url="https://example.invalid/expired-1",
        title="Urgent RFQ bulk diesel delivery",
        description="Emergency public works fuel delivery with direct purchase order.",
        due_date=future_date(-1),
        estimated_value=250000,
        agency_name="County Public Works",
        state="FL",
    ).finalize()
    record = route_record(score_record(classify_record(record)))
    assert record.fast_purchase_score == 0
    assert record.priority_score <= 59
    assert record.recommended_module == "GOV WATCHLIST"
    assert record.recommended_action.startswith("Expired")


def test_contact_information_alone_does_not_create_fast_path_score():
    record = NormalizedRecord(
        source_platform="test",
        source_type="buyer",
        source_record_id="buyer-1",
        source_url="https://example.invalid/buyer-1",
        title="Annual bulk diesel market research",
        description="General supplier research for a future fleet program.",
        buyer_email="buyer@example.invalid",
        due_date=future_date(30),
        estimated_value=10000,
    ).finalize()
    record = score_record(classify_record(record))
    assert record.fast_purchase_score < 70


def test_external_id_field_payload_is_unique_and_external():
    payload = field_payload("GOV FAST PURCHASE POSTS", EXTERNAL_ID_LABEL)
    assert payload["data_type"] == "text"
    assert payload["unique"] == {"case_sensitive": False}
    assert payload["external"] == {"type": "org", "show": True}


def test_compliance_and_purchase_need_are_textareas():
    assert infer_type("GOV FAST PURCHASE POSTS", "Compliance Needed") == "textarea"
    assert infer_type("GOV DIRECT PO", "Likely Purchase Need") == "textarea"
    payload = field_payload("GOV FAST PURCHASE POSTS", "Compliance Needed")
    assert payload["textarea"] == {"type": "large"}
    assert payload["length"] == 32000


def test_zoho_batch_limit_is_100():
    batches = list(chunks(list(range(205))))
    assert [len(batch) for batch in batches] == [100, 100, 5]


def test_record_mapping_preserves_human_owned_fields():
    record = records()[0]
    labels = record_to_labels(record)
    assert "Status" not in labels
    assert "Owner" not in labels
    assert "Notes" not in labels
    assert "Unit of Measure" in labels


def test_source_health_does_not_write_owner_lookup():
    health = SampleAdapter(Settings()).fetch().health
    assert "Owner" not in source_health_to_labels(health)


def test_auction_task_precedes_generic_quote_task():
    record = NormalizedRecord(
        source_platform="test",
        source_type="auction",
        source_record_id="auction-1",
        source_url="https://example.invalid/auction-1",
        title="Fuel tank auction",
        due_date=future_date(2),
        recommended_module="GOV AUCTIONS",
        fast_purchase_score=90,
        priority_score=90,
        priority_label="A1",
    ).finalize()
    payload = task_payload_for_record(record)
    assert payload is not None
    assert payload["Subject"] == "Evaluate Asset Buy"


def test_expired_record_has_no_task():
    record = NormalizedRecord(
        source_platform="test",
        source_type="opportunity",
        source_record_id="task-expired",
        source_url="https://example.invalid/task-expired",
        title="Expired RFQ",
        due_date=future_date(-1),
        recommended_module="GOV FAST PURCHASE POSTS",
        fast_purchase_score=100,
        priority_score=100,
        priority_label="A1",
    ).finalize()
    assert task_payload_for_record(record) is None


def test_upsert_uses_body_duplicate_fields_and_returns_insert_action(monkeypatch):
    client = ZohoUpsertClient("https://www.zohoapis.com", {"Authorization": "test"}, dry_run=False)
    captured = {}

    monkeypatch.setattr(
        client,
        "_prepare_rows",
        lambda module_name, rows: ("Custom_Module", "Phase8_External_ID", [{"Phase8_External_ID": "x:1", "Name": "One"}], ["x:1"]),
    )

    class Response:
        status_code = 201
        text = ""

        @staticmethod
        def json():
            return {
                "data": [
                    {
                        "status": "success",
                        "action": "insert",
                        "details": {"id": "123"},
                    }
                ]
            }

    def fake_request(method, path, **kwargs):
        captured.update({"method": method, "path": path, **kwargs})
        return Response()

    monkeypatch.setattr(client, "_request", fake_request)
    result = client._upsert_label_rows("GOV FAST PURCHASE POSTS", [{EXTERNAL_ID_LABEL: "x:1"}])
    assert captured["json"]["duplicate_check_fields"] == ["Phase8_External_ID"]
    assert "params" not in captured
    assert result["record_links"]["x:1"]["action"] == "insert"


def test_test_mode_does_not_call_live_adapters(monkeypatch):
    class LiveAdapter:
        source_name = "Must Not Run"

        def __init__(self, settings):
            raise AssertionError("live adapter instantiated in isolated test mode")

    monkeypatch.setattr(run_pipeline, "ADAPTERS", [LiveAdapter])
    monkeypatch.setattr(run_pipeline, "TEST_ADAPTERS", [SampleAdapter])
    fetched, health = run_pipeline.fetch_records(
        Settings(),
        mode="test",
        include_samples=False,
        include_live_sources=False,
        limit_per_source=5,
    )
    assert len(fetched) == 5
    assert health[0].source_name == "Phase 8 Sample Data"

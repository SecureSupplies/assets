from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Sequence

import requests

from core.schemas import NormalizedRecord
from core.score_opportunities import days_until
from .zoho_upsert import phase8_external_id


MAX_ZOHO_BATCH = 100


def chunks(values: Sequence[object], size: int = MAX_ZOHO_BATCH):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def task_payload_for_record(
    record: NormalizedRecord,
    related_record: Mapping[str, object] | None = None,
) -> Dict[str, object] | None:
    days = days_until(record.due_date)
    if days is not None and days < 0:
        return None

    if record.recommended_module == "GOV AUCTIONS" and record.fast_purchase_score >= 80:
        subject = "Evaluate Asset Buy"
    elif record.recommended_module == "GOV FAST PURCHASE POSTS" and record.fast_purchase_score >= 85:
        subject = "CALL BUYER NOW / QUOTE SAME DAY"
    elif record.recommended_module == "GOV FAST PURCHASE POSTS" and days is not None and days <= 3:
        subject = "QUOTE NOW - DUE WITHIN 72 HOURS"
    elif record.fast_purchase_score >= 70:
        subject = "QUOTE NOW - GOVERNMENT FAST PURCHASE"
    elif record.priority_score >= 80:
        subject = "BID/NO-BID REVIEW - HIGH PRIORITY GOV LEAD"
    else:
        return None

    payload: Dict[str, object] = {
        "Subject": subject,
        "Status": "Not Started",
        "Priority": "High" if record.priority_label in {"A1", "A2"} else "Normal",
        "Description": (
            f"{record.recommended_action}: {record.title}\n"
            f"Buyer: {record.agency_name}\n"
            f"Product: {record.product_category}\n"
            f"Fast/Priority Score: {record.fast_purchase_score}/{record.priority_score}\n"
            f"Source: {record.source_url}"
        ),
    }
    if record.due_date and (days is None or days >= 0):
        payload["Due_Date"] = record.due_date[:10]
    if related_record and related_record.get("id") and related_record.get("module_api_name"):
        payload["What_Id"] = {"id": str(related_record["id"])}
        payload["$se_module"] = str(related_record["module_api_name"])
    return payload


class ZohoTaskClient:
    def __init__(
        self,
        api_domain: str,
        headers: Dict[str, str],
        dry_run: bool = True,
        timeout: int = 30,
        batch_size: int = MAX_ZOHO_BATCH,
    ):
        self.api_domain = api_domain.rstrip("/")
        self.headers = headers
        self.dry_run = dry_run
        self.timeout = timeout
        self.batch_size = max(1, min(MAX_ZOHO_BATCH, batch_size))
        self.session = requests.Session()
        self.session.headers.update(headers)

    def create_tasks(
        self,
        records: Iterable[NormalizedRecord],
        record_links: Mapping[str, Mapping[str, object]] | None = None,
    ) -> Dict[str, object]:
        links = record_links or {}
        tasks: List[Dict[str, object]] = []
        skipped_updates = 0
        skipped_unlinked = 0

        for record in records:
            link = links.get(phase8_external_id(record))
            if not self.dry_run:
                if not link:
                    skipped_unlinked += 1
                    continue
                if link.get("action") == "update":
                    skipped_updates += 1
                    continue
            payload = task_payload_for_record(record, link)
            if payload:
                tasks.append(payload)

        if self.dry_run:
            return {
                "action": "dry_run_tasks",
                "count": len(tasks),
                "tasks": tasks[:20],
                "skipped_updates": skipped_updates,
                "skipped_unlinked": skipped_unlinked,
            }
        if not tasks:
            return {
                "action": "no_tasks",
                "count": 0,
                "skipped_updates": skipped_updates,
                "skipped_unlinked": skipped_unlinked,
            }

        result: Dict[str, object] = {
            "action": "created",
            "created": 0,
            "failed": 0,
            "skipped_updates": skipped_updates,
            "skipped_unlinked": skipped_unlinked,
            "batches": [],
        }
        for batch in chunks(tasks, self.batch_size):
            response = self.session.post(
                f"{self.api_domain}/crm/v8/Tasks",
                json={"data": list(batch), "trigger": ["workflow"]},
                timeout=self.timeout,
            )
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text[:2000]}
            rows = payload.get("data", []) if isinstance(payload, dict) else []
            result["batches"].append(
                {"status_code": response.status_code, "count": len(batch), "response": payload}
            )
            if response.status_code >= 400 and response.status_code != 207:
                result["failed"] += len(batch)
                continue
            for item in rows:
                if item.get("status") == "success":
                    result["created"] += 1
                else:
                    result["failed"] += 1
            if len(rows) < len(batch):
                result["failed"] += len(batch) - len(rows)
        result["count"] = result["created"]
        return result

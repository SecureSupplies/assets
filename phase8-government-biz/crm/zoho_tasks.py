from __future__ import annotations
from typing import Dict, Iterable
import requests
from core.schemas import NormalizedRecord


def task_payload_for_record(record: NormalizedRecord) -> Dict[str, object] | None:
    if record.recommended_module == "GOV FAST PURCHASE POSTS" and record.fast_purchase_score >= 85:
        subject = "CALL BUYER NOW / QUOTE SAME DAY"
    elif record.fast_purchase_score >= 70:
        subject = "QUOTE NOW - GOVERNMENT FAST PURCHASE"
    elif record.priority_score >= 80:
        subject = "BID/NO-BID REVIEW - HIGH PRIORITY GOV LEAD"
    elif record.recommended_module == "GOV AUCTIONS" and record.fast_purchase_score >= 80:
        subject = "Evaluate Asset Buy"
    else:
        return None
    return {"Subject":subject,"Status":"Not Started","Priority":"High" if record.priority_label in {"A1","A2"} else "Normal","Due_Date":record.due_date,"Description":f"{record.recommended_action}: {record.title}\nBuyer: {record.agency_name}\nProduct: {record.product_category}\nScore: {record.fast_purchase_score}/{record.priority_score}\nSource: {record.source_url}"}

class ZohoTaskClient:
    def __init__(self, api_domain: str, headers: Dict[str, str], dry_run: bool = True):
        self.api_domain = api_domain.rstrip("/"); self.headers = headers; self.dry_run = dry_run
    def create_tasks(self, records: Iterable[NormalizedRecord]) -> Dict[str, object]:
        tasks = [p for r in records if (p := task_payload_for_record(r))]
        if self.dry_run:
            return {"action":"dry_run_tasks","count":len(tasks),"tasks":tasks[:20]}
        if not tasks:
            return {"action":"no_tasks","count":0}
        resp = requests.post(f"{self.api_domain}/crm/v8/Tasks", headers=self.headers, json={"data":tasks}, timeout=60)
        if resp.status_code >= 400:
            return {"action":"failed","status_code":resp.status_code,"body":resp.text[:2000]}
        return {"action":"created","count":len(tasks),"body":resp.json()}

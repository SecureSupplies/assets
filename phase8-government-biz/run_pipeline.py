from __future__ import annotations
import argparse, csv, json, logging
from pathlib import Path
from typing import Iterable, List, Tuple
from adapters import ADAPTERS, TEST_ADAPTERS
from core.classify_products import classify_records
from core.config import load_settings
from core.dedupe import dedupe_records
from core.logging import configure_logging
from core.normalize import records_to_rows
from core.notify import notify_records
from core.raw_audit import raw_audit_rows
from core.route_records import route_records, sales_output
from core.schemas import NormalizedRecord, SourceHealth
from core.score_opportunities import score_records
from crm.zoho_auth import ZohoAuth
from crm.zoho_modules import write_deployment_plan
from crm.zoho_tasks import ZohoTaskClient
from crm.zoho_upsert import ZohoUpsertClient

log = logging.getLogger("phase8.pipeline")

def fetch_records(settings, mode: str, include_samples: bool, limit_per_source: int) -> Tuple[List[NormalizedRecord], List[SourceHealth]]:
    classes = []
    if include_samples or mode == "test": classes.extend(TEST_ADAPTERS)
    if mode != "test" or not include_samples: classes.extend(ADAPTERS)
    records: List[NormalizedRecord] = []; health: List[SourceHealth] = []
    for cls in classes:
        result = cls(settings).fetch(limit=limit_per_source)
        records.extend(result.records); health.append(result.health)
        log.info("source=%s status=%s pulled=%s", result.health.source_name, result.health.status, result.health.records_pulled)
    return records, health

def write_csv(path: Path, records: Iterable[NormalizedRecord]) -> None:
    rows = records_to_rows(records)
    if not rows:
        path.write_text(""); return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)

def build_report(records: List[NormalizedRecord], health: List[SourceHealth], crm_result: dict, task_result: dict, email_outcomes: list) -> dict:
    top_fast = sorted(records, key=lambda r: r.fast_purchase_score, reverse=True)[:10]
    top_priority = sorted(records, key=lambda r: r.priority_score, reverse=True)[:10]
    return {"records_total": len(records), "module_counts": {m: sum(1 for r in records if r.recommended_module == m) for m in sorted({r.recommended_module for r in records})}, "top_10_highest_scoring_opportunities": [r.to_dict() for r in top_priority], "top_10_fast_purchase_posts": [r.to_dict() for r in top_fast], "top_10_direct_po_buyer_targets": [r.to_dict() for r in top_priority if r.recommended_module in {"GOV DIRECT PO", "GOV FAST PURCHASE POSTS"}][:10], "top_10_auction_assets": [r.to_dict() for r in records if r.recommended_module == "GOV AUCTIONS"][:10], "sales_outputs": [sales_output(r) for r in top_fast], "source_health": [h.to_dict() for h in health], "crm_result": crm_result, "task_result": task_result, "email_outcomes": email_outcomes}

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Secure Supplies Phase 8 Government Biz pipeline")
    parser.add_argument("--mode", choices=["test", "production"], default="test")
    parser.add_argument("--include-samples", action="store_true")
    parser.add_argument("--limit-per-source", type=int, default=50)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    configure_logging(args.log_level)
    settings = load_settings(); settings.output_dir.mkdir(parents=True, exist_ok=True)
    write_deployment_plan(settings.output_dir)
    records, health = fetch_records(settings, args.mode, args.include_samples, args.limit_per_source)
    records = dedupe_records(route_records(score_records(classify_records(records))))
    write_csv(settings.output_dir / "phase8_normalized_records.csv", records)
    (settings.output_dir / "phase8_records.json").write_text(json.dumps([r.to_dict() for r in records], indent=2, default=str))
    (settings.output_dir / "phase8_source_health.json").write_text(json.dumps([h.to_dict() for h in health], indent=2, default=str))
    (settings.output_dir / "phase8_raw_audit.json").write_text(json.dumps(raw_audit_rows(records), indent=2, default=str))
    email_outcomes = notify_records(records, settings)
    (settings.output_dir / "phase8_email_outcomes.json").write_text(json.dumps(email_outcomes, indent=2, default=str))
    crm_result = {"action": "skipped", "reason": "dry run or missing Zoho variables"}
    task_result = {"action": "skipped", "reason": "dry run or missing Zoho variables"}
    if args.mode == "production" and settings.zoho_ready():
        token = ZohoAuth(settings).refresh_access_token()
        headers = {"Authorization": ("Zoho-" + "oauthtoken ") + token.access_token}
        crm_result = ZohoUpsertClient(token.api_domain, headers, dry_run=settings.dry_run).upsert_records(records)
        task_result = ZohoTaskClient(token.api_domain, headers, dry_run=settings.dry_run).create_tasks(records)
    elif args.mode == "production":
        crm_result = {"action": "blocked", "reason": "Zoho variables missing from terminal environment"}
        task_result = {"action": "blocked", "reason": "Zoho variables missing from terminal environment"}
    (settings.output_dir / "phase8_crm_result.json").write_text(json.dumps(crm_result, indent=2, default=str))
    (settings.output_dir / "phase8_task_result.json").write_text(json.dumps(task_result, indent=2, default=str))
    report = build_report(records, health, crm_result, task_result, email_outcomes)
    (settings.output_dir / "phase8_deployment_report.json").write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()

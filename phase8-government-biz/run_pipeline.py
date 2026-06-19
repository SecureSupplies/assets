from __future__ import annotations

import argparse
import csv
import json
import logging
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
from core.runtime_safety import (
    crm_write_blockers,
    crm_writes_allowed,
    notification_blockers,
    notifications_allowed,
)
from core.schemas import NormalizedRecord, SourceHealth
from core.score_opportunities import score_records
from crm.zoho_auth import ZohoAuth
from crm.zoho_modules import ZohoModuleDeployer, write_deployment_plan
from crm.zoho_tasks import ZohoTaskClient
from crm.zoho_upsert import ZohoUpsertClient, phase8_external_id


log = logging.getLogger("phase8.pipeline")


def fetch_records(
    settings,
    mode: str,
    include_samples: bool,
    include_live_sources: bool,
    limit_per_source: int,
) -> Tuple[List[NormalizedRecord], List[SourceHealth]]:
    if mode == "test":
        classes = list(TEST_ADAPTERS)
        if include_live_sources:
            classes.extend(ADAPTERS)
    else:
        classes = list(ADAPTERS)
        if include_samples:
            classes = list(TEST_ADAPTERS) + classes

    records: List[NormalizedRecord] = []
    health: List[SourceHealth] = []
    for adapter_class in classes:
        try:
            result = adapter_class(settings).fetch(limit=limit_per_source)
            records.extend(result.records)
            health.append(result.health)
            log.info(
                "source=%s status=%s pulled=%s",
                result.health.source_name,
                result.health.status,
                result.health.records_pulled,
            )
        except Exception as exc:
            failed = SourceHealth(
                source_name=getattr(adapter_class, "source_name", adapter_class.__name__),
                source_type=getattr(adapter_class, "source_type", "api"),
                source_url=getattr(adapter_class, "source_url", ""),
                access_method=getattr(adapter_class, "access_method", "API"),
                free_or_paid=getattr(adapter_class, "free_or_paid", "Free"),
                credential_required=getattr(adapter_class, "credential_required", False),
            ).fail(str(exc))
            health.append(failed)
            log.exception("source=%s failed", failed.source_name)
    return records, health


def write_csv(path: Path, records: Iterable[NormalizedRecord]) -> None:
    rows = records_to_rows(records)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def update_health_from_crm(
    records: Iterable[NormalizedRecord],
    health: Iterable[SourceHealth],
    crm_result: dict,
    live_write: bool,
) -> None:
    if not live_write:
        return
    by_source = {row.source_name: row for row in health}
    links = crm_result.get("record_links", {}) if isinstance(crm_result, dict) else {}
    for record in records:
        source = by_source.get(record.source_platform)
        if not source:
            continue
        link = links.get(phase8_external_id(record))
        if not link:
            source.records_failed += 1
            continue
        if link.get("action") == "update":
            source.records_updated += 1
        else:
            source.records_inserted += 1


def build_report(
    records: List[NormalizedRecord],
    health: List[SourceHealth],
    crm_result: dict,
    task_result: dict,
    email_outcomes: list,
) -> dict:
    active = [record for record in records if not record.recommended_action.lower().startswith("expired")]
    top_fast = sorted(
        [record for record in active if record.recommended_module == "GOV FAST PURCHASE POSTS" and record.fast_purchase_score > 0],
        key=lambda record: record.fast_purchase_score,
        reverse=True,
    )[:10]
    top_priority = sorted(active, key=lambda record: record.priority_score, reverse=True)[:10]
    return {
        "records_total": len(records),
        "module_counts": {
            module: sum(1 for record in records if record.recommended_module == module)
            for module in sorted({record.recommended_module for record in records})
        },
        "top_10_highest_scoring_opportunities": [record.to_dict() for record in top_priority],
        "top_10_fast_purchase_posts": [record.to_dict() for record in top_fast],
        "top_10_direct_po_buyer_targets": [
            record.to_dict()
            for record in top_priority
            if record.recommended_module in {"GOV DIRECT PO", "GOV FAST PURCHASE POSTS"}
        ][:10],
        "top_10_auction_assets": [
            record.to_dict()
            for record in records
            if record.recommended_module == "GOV AUCTIONS" and "closed" not in record.recommended_action.lower()
        ][:10],
        "sales_outputs": [sales_output(record) for record in top_fast],
        "source_health": [row.to_dict() for row in health],
        "crm_result": crm_result,
        "task_result": task_result,
        "email_outcomes": email_outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Secure Supplies Phase 8 Government Biz pipeline")
    parser.add_argument("--mode", choices=["test", "production"], default="test")
    parser.add_argument("--include-samples", action="store_true", help="Include samples in production; test mode already uses them")
    parser.add_argument("--include-live-sources", action="store_true", help="Also call live adapters while in test mode")
    parser.add_argument("--deploy-fields", action="store_true", help="Audit module shells and create missing fields when live-write gates pass")
    parser.add_argument("--limit-per-source", type=int, default=50)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    configure_logging(args.log_level)
    settings = load_settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    write_deployment_plan(settings.output_dir)

    records, health = fetch_records(
        settings,
        args.mode,
        args.include_samples,
        args.include_live_sources,
        args.limit_per_source,
    )
    records = dedupe_records(route_records(score_records(classify_records(records))))

    write_csv(settings.output_dir / "phase8_normalized_records.csv", records)
    (settings.output_dir / "phase8_records.json").write_text(
        json.dumps([record.to_dict() for record in records], indent=2, default=str)
    )
    (settings.output_dir / "phase8_source_health.json").write_text(
        json.dumps([row.to_dict() for row in health], indent=2, default=str)
    )
    (settings.output_dir / "phase8_raw_audit.json").write_text(
        json.dumps(raw_audit_rows(records), indent=2, default=str)
    )

    crm_result: dict = {"action": "skipped", "reason": "test mode"}
    task_result: dict = {"action": "skipped", "reason": "test mode"}

    if args.mode == "production":
        write_blockers = crm_write_blockers(settings)
        requested_live = crm_writes_allowed(settings)
        crm_result = {
            "action": "blocked",
            "live_write_requested": requested_live,
            "write_blockers": write_blockers,
        }

        if settings.zoho_ready():
            deployer = ZohoModuleDeployer(settings)
            backup_path = deployer.backup_metadata(settings.output_dir)
            module_audit = deployer.audit_module_shells()
            field_result = None
            if args.deploy_fields:
                field_result = deployer.apply_fields_to_existing_modules(
                    dry_run=not requested_live,
                    output_dir=settings.output_dir,
                )

            schema_ready = module_audit.get("missing_count", 0) == 0
            if field_result is not None:
                schema_ready = schema_ready and bool(field_result.get("ready_for_records"))
            effective_live = requested_live and schema_ready

            token = ZohoAuth(settings).refresh_access_token()
            headers = {"Authorization": f"Zoho-oauthtoken {token.access_token}"}
            client = ZohoUpsertClient(
                token.api_domain,
                headers,
                dry_run=not effective_live,
                timeout=settings.request_timeout_seconds,
            )
            business_result = client.upsert_records(records)
            update_health_from_crm(records, health, business_result, effective_live)
            source_health_result = client.upsert_source_health(health)
            raw_audit_result = client.upsert_raw_audit(records)

            task_client = ZohoTaskClient(
                token.api_domain,
                headers,
                dry_run=not effective_live,
                timeout=settings.request_timeout_seconds,
            )
            task_result = task_client.create_tasks(
                records,
                record_links=business_result.get("record_links", {}),
            )
            crm_result = {
                "action": "completed" if effective_live else "dry_run_or_blocked",
                "live_write_allowed": effective_live,
                "write_blockers": write_blockers,
                "schema_ready": schema_ready,
                "metadata_backup": str(backup_path),
                "module_audit": module_audit,
                "field_deployment": field_result,
                "business_records": business_result,
                "source_health": source_health_result,
                "raw_audit": raw_audit_result,
            }

    if args.mode == "production" and notifications_allowed(settings):
        email_outcomes = notify_records(records, settings)
    else:
        reason = "test mode" if args.mode != "production" else "; ".join(notification_blockers(settings))
        email_outcomes = [{"action": "suppressed", "reason": reason}]

    (settings.output_dir / "phase8_email_outcomes.json").write_text(
        json.dumps(email_outcomes, indent=2, default=str)
    )
    (settings.output_dir / "phase8_crm_result.json").write_text(
        json.dumps(crm_result, indent=2, default=str)
    )
    (settings.output_dir / "phase8_task_result.json").write_text(
        json.dumps(task_result, indent=2, default=str)
    )
    (settings.output_dir / "phase8_source_health.json").write_text(
        json.dumps([row.to_dict() for row in health], indent=2, default=str)
    )

    report = build_report(records, health, crm_result, task_result, email_outcomes)
    (settings.output_dir / "phase8_deployment_report.json").write_text(
        json.dumps(report, indent=2, default=str)
    )
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()

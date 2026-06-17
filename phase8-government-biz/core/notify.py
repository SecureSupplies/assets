from __future__ import annotations
from email.message import EmailMessage
import json, smtplib
from typing import Iterable, List, Dict
from .config import Settings
from .route_records import sales_output
from .schemas import NormalizedRecord, utc_now_iso


def eligible_for_email(record: NormalizedRecord, settings: Settings) -> bool:
    return record.fast_purchase_score >= settings.min_fast_score_to_email or record.priority_score >= settings.min_priority_score_to_email or record.priority_label in {"A1", "A2"}


def build_email_body(record: NormalizedRecord) -> str:
    so = sales_output(record)
    return "\n".join([
        f"Phase 8 Government Biz alert generated at {utc_now_iso()}",
        "",
        f"Action: {so['action']}",
        f"Priority: {record.priority_label}",
        f"Fast Score: {record.fast_purchase_score}",
        f"Priority Score: {record.priority_score}",
        f"Module: {record.recommended_module}",
        f"Buyer: {so['buyer']}",
        f"Product: {so['product']}",
        f"Need: {so['need']}",
        f"Due: {record.due_date or 'Not specified'}",
        f"Source: {record.source_platform} / {record.source_url}",
        "",
        f"Sales Script: {so['sales_script']}",
        f"Email Subject: {so['email_subject']}",
        f"Short Outreach Email: {so['short_email']}",
        f"Pricing Basis Needed: {so['pricing_basis_needed']}",
        f"Supplier/Logistics Requirement: {so['supplier_need']}",
        f"Compliance Requirement: {so['compliance_requirement']}",
        f"Bid/No-Bid: {so['bid_no_bid_recommendation']}",
        "",
        json.dumps(record.to_dict(), indent=2, default=str)[:6000]
    ])


def send_record_email(record: NormalizedRecord, settings: Settings) -> Dict[str, object]:
    out = {"source_record_id": record.source_record_id, "sent": False, "dry_run": settings.dry_run, "to": settings.notification_to, "error": ""}
    if not eligible_for_email(record, settings):
        out["error"] = "Below threshold"
        return out
    if settings.dry_run:
        out["error"] = "Dry run; email suppressed"
        return out
    if not settings.smtp_ready():
        out["error"] = "SMTP environment variables missing"
        return out
    so = sales_output(record)
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = settings.notification_to
    msg["Subject"] = f"{record.priority_label or 'Gov'} {record.fast_purchase_score}/100 - {so['email_subject']}"
    msg.set_content(build_email_body(record))
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_secret_value)
            smtp.send_message(msg)
        out["sent"] = True
    except Exception as exc:
        out["error"] = str(exc)[:1000]
    return out


def notify_records(records: Iterable[NormalizedRecord], settings: Settings) -> List[Dict[str, object]]:
    return [send_record_email(record, settings) for record in records if eligible_for_email(record, settings)]

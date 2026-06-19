from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from .schemas import NormalizedRecord

HIGH_FIT_LANES = {
    "Diesel / ULSD / clear diesel", "Red diesel / off-road diesel", "Emergency generator fuel", "DEF / AdBlue / AUS32", "Jet A / Jet A-1 / aviation fuel", "Avgas", "Marine diesel / MGO / bunkering", "Propane / LPG", "CNG / LNG / RNG / natural gas", "Hydrogen / H2", "Oxygen / O2 / LOX", "Nitrogen / N2 / LIN", "CO2 / carbon dioxide", "Helium / He", "Argon / specialty gases", "Ammonia / urea / UAN / NPK / fertilizers", "Water / wastewater chemicals", "Fuel tanks / DEF tanks / water tanks / gas tanks", "Tank rentals", "Pumps / dispensers / fuel management / telemetry", "Auction assets", "Data center fuel / backup power fuel", "Emergency response fuel"
}
FAST_PATH_WORDS = ["rfq", "quote", "purchase order", "p-card", "credit card", "direct purchase", "emergency", "urgent", "same day", "next day", "spot buy", "small purchase", "simplified acquisition"]
REPEAT_BUYER_WORDS = ["public works", "fleet", "school", "airport", "port", "utility", "wastewater", "hospital", "fire", "police", "emergency management", "correction", "transit", "parks"]
ROUTE_WORDS = ["delivery", "terminal", "route", "fuel delivery", "bulk", "tank", "fleet", "airport", "port", "yard"]


def parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y", "%m/%d/%Y %H:%M"):
        try:
            dt = datetime.strptime(value.replace("+00:00", "Z"), fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_until(value: str) -> Optional[int]:
    dt = parse_date(value)
    return None if not dt else (dt - datetime.now(timezone.utc)).days


def score_record(record: NormalizedRecord) -> NormalizedRecord:
    text = f" {record.title} {record.description} {record.notice_type} {record.purchase_path} {record.agency_name} {record.buying_office} ".lower()
    product_fit = 25 if record.product_category in HIGH_FIT_LANES else (12 if record.product_keywords_matched else 0)
    if record.estimated_value and record.estimated_value >= 250000:
        value_score = 20
    elif record.estimated_value and record.estimated_value >= 50000:
        value_score = 16
    elif record.estimated_value and record.estimated_value >= 10000:
        value_score = 10
    elif record.estimated_volume and record.estimated_volume >= 5000:
        value_score = 16
    elif any(word in text for word in ["annual", "blanket", "recurring", "term contract", "requirements contract", "idiq"]):
        value_score = 16
    else:
        value_score = 7 if record.product_category else 0
    d = days_until(record.due_date)
    if d is not None and d <= 3:
        urgency_score = 15
    elif d is not None and d <= 10:
        urgency_score = 12
    elif d is not None and d <= 30:
        urgency_score = 8
    elif any(word in text for word in ["urgent", "emergency", "same day", "next day"]):
        urgency_score = 15
    else:
        urgency_score = 3
    repeat_score = 15 if any(word in text for word in REPEAT_BUYER_WORDS) or record.incumbent_vendor or record.awarded_vendor else 5
    route_score = 10 if any(word in text for word in ROUTE_WORDS) or record.state else 4
    direct_score = 10 if record.direct_po_eligible or any(word in text for word in FAST_PATH_WORDS) or record.buyer_email or record.buyer_phone else 0
    emergency_score = 5 if record.emergency_trigger else 0
    record.priority_score = min(100, product_fit + value_score + urgency_score + repeat_score + route_score + direct_score + emergency_score)
    record.fast_purchase_score = min(100, (30 if direct_score else 0) + product_fit + min(20, value_score) + route_score + min(10, repeat_score) + emergency_score)
    if record.priority_score >= 85:
        record.priority_label = "A1"
    elif record.fast_purchase_score >= 70 or record.direct_po_eligible:
        record.priority_label = "A2"
    elif repeat_score >= 15:
        record.priority_label = "B1"
    elif record.supplier_fit == "Unknown":
        record.priority_label = "B2"
    elif record.priority_score >= 45:
        record.priority_label = "C1"
    else:
        record.priority_label = "C2"
    if record.fast_purchase_score >= 85:
        record.recommended_action = "Call Now"
    elif record.fast_purchase_score >= 70:
        record.recommended_action = "Quote Now"
    elif record.fast_purchase_score >= 55:
        record.recommended_action = "Procurement Review"
    elif record.priority_label in {"A1", "A2"}:
        record.recommended_action = "Bid/No-Bid Review"
    else:
        record.recommended_action = "Watch or No-Bid"
    return record


def score_records(records: Iterable[NormalizedRecord]) -> List[NormalizedRecord]:
    return [score_record(record) for record in records]

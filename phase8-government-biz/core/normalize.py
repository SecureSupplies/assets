from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional
import re
from .schemas import NormalizedRecord, make_hash

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
STATE_RE = re.compile(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|PR|GU|VI|AS|MP)\b")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def coerce_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def extract_email(text: str) -> str:
    match = EMAIL_RE.search(text or "")
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = PHONE_RE.search(text or "")
    return match.group(0) if match else ""


def extract_state(text: str) -> str:
    match = STATE_RE.search(text or "")
    return match.group(1) if match else ""


def listify(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [clean_text(x) for x in value if clean_text(x)]
    return [clean_text(value)]


def normalize_generic(raw: Dict[str, Any], *, source_platform: str, source_type: str, source_url: str) -> NormalizedRecord:
    title = clean_text(raw.get("title") or raw.get("subject") or raw.get("name") or raw.get("description") or "Untitled Government Record")
    description = clean_text(raw.get("description") or raw.get("body") or raw.get("synopsis") or raw.get("summary") or raw.get("lot_description") or "")
    combined = f"{title} {description} {raw}"
    rid = clean_text(raw.get("id") or raw.get("notice_id") or raw.get("noticeId") or raw.get("solicitation_number") or raw.get("solicitationNumber") or raw.get("auction_id") or raw.get("award_id") or make_hash(raw)[:20])
    return NormalizedRecord(
        source_platform=source_platform,
        source_type=source_type,
        source_record_id=rid,
        source_url=clean_text(raw.get("source_url") or raw.get("url") or raw.get("uiLink") or source_url),
        title=title,
        description=description,
        notice_type=clean_text(raw.get("notice_type") or raw.get("noticeType") or raw.get("type") or raw.get("award_type")),
        government_level=clean_text(raw.get("government_level") or raw.get("level") or "Federal"),
        jurisdiction=clean_text(raw.get("jurisdiction") or raw.get("state") or raw.get("placeOfPerformance") or raw.get("place_of_performance")),
        agency_name=clean_text(raw.get("agency") or raw.get("agency_name") or raw.get("department") or raw.get("awarding_agency") or raw.get("subTier") or raw.get("sub_tier")),
        buying_office=clean_text(raw.get("office") or raw.get("buying_office") or raw.get("officeAddress") or raw.get("funding_office")),
        buyer_contact=clean_text(raw.get("contact") or raw.get("buyer_contact") or raw.get("pointOfContact") or raw.get("poc")),
        buyer_email=clean_text(raw.get("email") or raw.get("buyer_email") or extract_email(combined)),
        buyer_phone=clean_text(raw.get("phone") or raw.get("buyer_phone") or extract_phone(combined)),
        naics=listify(raw.get("naics")),
        psc_fsc=listify(raw.get("psc_fsc") or raw.get("psc") or raw.get("classificationCode")),
        nigp=listify(raw.get("nigp")),
        unspsc=listify(raw.get("unspsc")),
        posted_date=clean_text(raw.get("posted_date") or raw.get("postedDate") or raw.get("posted")),
        due_date=clean_text(raw.get("due_date") or raw.get("responseDeadLine") or raw.get("response_deadline") or raw.get("close_date") or raw.get("auction_close_date")),
        award_date=clean_text(raw.get("award_date") or raw.get("awardDate") or raw.get("action_date")),
        estimated_value=coerce_float(raw.get("estimated_value") or raw.get("award_amount") or raw.get("current_bid") or raw.get("baseAndAllOptionsValue")),
        estimated_volume=coerce_float(raw.get("estimated_volume") or raw.get("quantity") or raw.get("gallons")),
        unit_of_measure=clean_text(raw.get("unit_of_measure") or raw.get("uom")),
        place_of_performance=clean_text(raw.get("place_of_performance") or raw.get("placeOfPerformance") or raw.get("location") or raw.get("delivery_location")),
        state=clean_text(raw.get("state") or extract_state(combined)),
        territory=clean_text(raw.get("territory")),
        county=clean_text(raw.get("county")),
        city=clean_text(raw.get("city")),
        set_aside=clean_text(raw.get("set_aside") or raw.get("setAside") or raw.get("typeOfSetAsideDescription")),
        incumbent_vendor=clean_text(raw.get("incumbent_vendor") or raw.get("recipient_name")),
        awarded_vendor=clean_text(raw.get("awarded_vendor") or raw.get("recipient_name") or raw.get("awardee")),
        contract_vehicle=clean_text(raw.get("contract_vehicle") or raw.get("award_id_piid") or raw.get("contractAwardNumber")),
        purchase_path=clean_text(raw.get("purchase_path") or raw.get("procurement_type") or raw.get("notice_type") or raw.get("noticeType")),
        raw_payload=raw,
    ).finalize()


def records_to_rows(records: Iterable[NormalizedRecord]) -> List[Dict[str, Any]]:
    rows = []
    for record in records:
        row = record.to_dict()
        for key, value in list(row.items()):
            if isinstance(value, list):
                row[key] = "; ".join(map(str, value))
            elif isinstance(value, dict):
                row[key] = str(value)
        rows.append(row)
    return rows

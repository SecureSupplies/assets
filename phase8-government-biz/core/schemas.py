from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib, json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class NormalizedRecord:
    source_platform: str
    source_type: str
    source_record_id: str
    source_url: str
    title: str
    description: str = ""
    notice_type: str = ""
    government_level: str = ""
    jurisdiction: str = ""
    agency_name: str = ""
    buying_office: str = ""
    buyer_contact: str = ""
    buyer_email: str = ""
    buyer_phone: str = ""
    product_category: str = ""
    product_interest: str = ""
    product_keywords_matched: List[str] = field(default_factory=list)
    naics: List[str] = field(default_factory=list)
    psc_fsc: List[str] = field(default_factory=list)
    nigp: List[str] = field(default_factory=list)
    unspsc: List[str] = field(default_factory=list)
    posted_date: str = ""
    due_date: str = ""
    award_date: str = ""
    estimated_value: Optional[float] = None
    estimated_volume: Optional[float] = None
    unit_of_measure: str = ""
    place_of_performance: str = ""
    state: str = ""
    territory: str = ""
    county: str = ""
    city: str = ""
    set_aside: str = ""
    incumbent_vendor: str = ""
    awarded_vendor: str = ""
    contract_vehicle: str = ""
    purchase_path: str = ""
    direct_po_eligible: bool = False
    emergency_trigger: bool = False
    route_fit: str = "Unknown"
    supplier_fit: str = "Unknown"
    priority_score: int = 0
    fast_purchase_score: int = 0
    priority_label: str = ""
    fast_lane_tags: List[str] = field(default_factory=list)
    recommended_module: str = "LEADS GOV"
    recommended_action: str = "Review"
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    record_hash: str = ""
    pulled_at: str = field(default_factory=utc_now_iso)

    def finalize(self) -> "NormalizedRecord":
        if not self.record_hash:
            self.record_hash = make_hash(self.raw_payload or self.title)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SourceHealth:
    source_name: str
    source_type: str
    source_url: str
    access_method: str
    free_or_paid: str = "Free"
    credential_required: bool = False
    last_sync_time: str = field(default_factory=utc_now_iso)
    last_success_time: str = ""
    records_pulled: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: str = ""
    status: str = "Not Run"
    owner: str = "Revenue Ops"

    def ok(self, count: int) -> "SourceHealth":
        self.records_pulled = count
        self.last_success_time = utc_now_iso()
        self.status = "Success"
        return self

    def fail(self, message: str) -> "SourceHealth":
        self.error_message = str(message)[:1000]
        self.status = "Failed"
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

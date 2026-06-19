from __future__ import annotations

import json
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import requests

from core.compliance import compliance_notes
from core.schemas import NormalizedRecord, SourceHealth
from .module_definitions import MODULE_ORDER
from .zoho_modules import EXTERNAL_ID_LABEL, normalize_label, primary_field_label


MAX_ZOHO_BATCH = 100


def chunks(values: Sequence[object], size: int = MAX_ZOHO_BATCH) -> Iterable[Sequence[object]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def phase8_external_id(record: NormalizedRecord) -> str:
    return f"{record.source_platform}:{record.source_record_id}"[:255]


def quantity_signal(record: NormalizedRecord) -> str:
    if record.estimated_volume is None:
        return ""
    value = f"{record.estimated_volume:g}"
    return f"{value} {record.unit_of_measure or 'Needs Confirmation'}"


def record_to_labels(record: NormalizedRecord) -> Dict[str, object]:
    data: Dict[str, object] = {
        EXTERNAL_ID_LABEL: phase8_external_id(record),
        "Source Platform": record.source_platform,
        "Source Record ID": record.source_record_id,
        "Source URL": record.source_url,
        "Raw Payload JSON": json.dumps(record.raw_payload, default=str),
    }

    if record.recommended_module == "GOV FAST PURCHASE POSTS":
        data.update(
            {
                "Fast Purchase Name": record.title,
                "Buyer / Agency": record.agency_name,
                "Government Level": record.government_level,
                "Jurisdiction": record.jurisdiction,
                "State / Territory": record.state or record.territory,
                "County / City": ", ".join(item for item in (record.county, record.city) if item),
                "Buyer Contact": record.buyer_contact,
                "Buyer Email": record.buyer_email,
                "Buyer Phone": record.buyer_phone,
                "Product Category": record.product_category,
                "Product Interest": record.product_interest,
                "Product Keywords Matched": ", ".join(record.product_keywords_matched),
                "Quantity / Volume Signal": quantity_signal(record),
                "Unit of Measure": record.unit_of_measure or "Needs Confirmation",
                "Estimated Value": record.estimated_value,
                "Purchase Path": record.purchase_path,
                "Purchase Urgency": record.recommended_action,
                "Posted Date": record.posted_date,
                "Due Date": record.due_date,
                "Response Deadline": record.due_date,
                "Delivery Location": record.place_of_performance,
                "Route / Terminal Fit": record.route_fit,
                "Supplier Fit": record.supplier_fit,
                "Compliance Needed": compliance_notes(record),
                "Direct PO Eligible": record.direct_po_eligible,
                "Purchase Card Possible": record.direct_po_eligible,
                "Emergency Trigger": record.emergency_trigger,
                "Fast Purchase Score": record.fast_purchase_score,
                "Margin Potential": "High" if record.priority_label in {"A1", "A2"} else "Review",
            }
        )
    elif record.recommended_module == "LEADS GOV":
        data.update(
            {
                "Gov Lead Name": record.title,
                "Notice Type": record.notice_type,
                "Government Level": record.government_level,
                "Jurisdiction": record.jurisdiction,
                "Agency Name": record.agency_name,
                "Buying Office": record.buying_office,
                "Buyer Contact": record.buyer_contact,
                "Buyer Email": record.buyer_email,
                "Buyer Phone": record.buyer_phone,
                "Product Category": record.product_category,
                "Product Interest": record.product_interest,
                "NAICS": ", ".join(record.naics),
                "PSC / FSC": ", ".join(record.psc_fsc),
                "NIGP": ", ".join(record.nigp),
                "UNSPSC": ", ".join(record.unspsc),
                "Posted Date": record.posted_date,
                "Due Date": record.due_date,
                "Award Date": record.award_date,
                "Estimated Value": record.estimated_value,
                "Estimated Gallons / Units": record.estimated_volume,
                "Unit of Measure": record.unit_of_measure or "Needs Confirmation",
                "Place of Performance": record.place_of_performance,
                "State / Territory": record.state or record.territory,
                "Route / Terminal Fit": record.route_fit,
                "Set-Aside": record.set_aside,
                "Contract Vehicle": record.contract_vehicle,
                "Direct PO Eligible": record.direct_po_eligible,
                "Emergency Trigger": record.emergency_trigger,
                "Priority Score": record.priority_score,
                "Compliance Notes": compliance_notes(record),
            }
        )
    elif record.recommended_module == "GOV AUCTIONS":
        data.update(
            {
                "Auction Asset Name": record.title,
                "Asset Type": record.product_category,
                "Asset Category": record.product_interest,
                "Location": record.place_of_performance,
                "State / Territory": record.state or record.territory,
                "Current Bid": record.estimated_value,
                "Auction Close Date": record.due_date,
                "Margin Score": record.fast_purchase_score,
                "Buy / Pass Recommendation": "Evaluate" if record.fast_purchase_score >= 70 else "Watch",
            }
        )
    elif record.recommended_module == "GOV AWARDS":
        data.update(
            {
                "Award Name": record.title,
                "Awarding Agency": record.agency_name,
                "Recipient / Vendor": record.awarded_vendor or record.incumbent_vendor,
                "Product Category": record.product_category,
                "Product Keywords": ", ".join(record.product_keywords_matched),
                "NAICS": ", ".join(record.naics),
                "PSC / FSC": ", ".join(record.psc_fsc),
                "NIGP": ", ".join(record.nigp),
                "Award Amount": record.estimated_value,
                "Award Date": record.award_date,
                "Place of Performance": record.place_of_performance,
                "State / Territory": record.state or record.territory,
                "Contract Vehicle": record.contract_vehicle,
                "Award Type": record.notice_type,
                "Incumbent Renewal Watch": True,
            }
        )
    elif record.recommended_module == "GOV DIRECT PO":
        data.update(
            {
                "Direct PO Target Name": record.title,
                "Buyer / Agency": record.agency_name,
                "Buyer Type": record.buying_office,
                "Government Level": record.government_level,
                "Jurisdiction": record.jurisdiction,
                "Product Fit": record.product_category,
                "Likely Purchase Need": record.description,
                "Estimated Recurring Value": record.estimated_value,
                "Contact Name": record.buyer_contact,
                "Contact Email": record.buyer_email,
                "Contact Phone": record.buyer_phone,
                "Procurement Portal": record.source_url,
                "Credit Card / P-Card Possible": record.direct_po_eligible,
                "Emergency Supplier Need": record.emergency_trigger,
                "Route Fit": record.route_fit,
                "Next Call Date": record.due_date,
            }
        )
    else:
        data.update(
            {
                "Watchlist Name": record.title,
                "Buyer / Agency": record.agency_name,
                "Product Category": record.product_category,
                "Current Incumbent": record.incumbent_vendor,
                "Trigger Source": record.source_platform,
                "Next Review Date": record.due_date,
            }
        )

    # Human-owned fields such as Status, Owner, Notes, strategy, and action plan are intentionally omitted.
    return {key: value for key, value in data.items() if value not in (None, "", [], {})}


def source_health_to_labels(health: SourceHealth) -> Dict[str, object]:
    return {
        EXTERNAL_ID_LABEL: f"source-health:{health.source_name}"[:255],
        "Source Name": health.source_name,
        "Source Type": health.source_type,
        "Source URL": health.source_url,
        "API / Portal / RSS / CSV / Email": health.access_method,
        "Free or Paid": health.free_or_paid,
        "Credential Required": health.credential_required,
        "Last Sync Time": health.last_sync_time,
        "Last Success Time": health.last_success_time,
        "Records Pulled": health.records_pulled,
        "Records Inserted": health.records_inserted,
        "Records Updated": health.records_updated,
        "Records Failed": health.records_failed,
        "Error Message": health.error_message,
        "Status": health.status,
    }


def raw_audit_to_labels(record: NormalizedRecord) -> Dict[str, object]:
    return {
        EXTERNAL_ID_LABEL: f"raw:{phase8_external_id(record)}:{record.record_hash[:16]}"[:255],
        "Raw Record Name": f"{record.source_platform} - {record.source_record_id}"[:255],
        "Source Platform": record.source_platform,
        "Source Record ID": record.source_record_id,
        "Source URL": record.source_url,
        "Pulled At": record.pulled_at,
        "Normalized Record ID": phase8_external_id(record),
        "Target Module": record.recommended_module,
        "Hash": record.record_hash,
        "Raw Payload JSON": json.dumps(record.raw_payload, default=str),
        "Processing Status": "Normalized and routed",
        "Error Details": "",
    }


class ZohoUpsertClient:
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
        self._modules: Dict[str, Dict[str, object]] | None = None
        self._fields: Dict[str, List[Dict[str, object]]] = {}

    def _request(self, method: str, path: str, **kwargs: object) -> requests.Response:
        return self.session.request(
            method,
            f"{self.api_domain}/crm/v8/{path.lstrip('/')}",
            timeout=self.timeout,
            **kwargs,
        )

    @staticmethod
    def _module_aliases(module: Mapping[str, object]) -> set[str]:
        keys = ["api_name", "module_name", "plural_label", "singular_label", "actual_plural_label", "actual_singular_label"]
        return {normalize_label(module.get(key)) for key in keys if module.get(key)}

    def _load_modules(self) -> Dict[str, Dict[str, object]]:
        if self._modules is not None:
            return self._modules
        response = self._request("GET", "settings/modules")
        response.raise_for_status()
        payload = response.json()
        resolved: Dict[str, Dict[str, object]] = {}
        for desired in MODULE_ORDER:
            wanted = normalize_label(desired)
            for module in payload.get("modules", []):
                if wanted in self._module_aliases(module):
                    resolved[desired] = dict(module)
                    break
        self._modules = resolved
        return resolved

    def _load_fields(self, module_api_name: str) -> List[Dict[str, object]]:
        if module_api_name in self._fields:
            return self._fields[module_api_name]
        response = self._request("GET", "settings/fields", params={"module": module_api_name})
        response.raise_for_status()
        fields = [dict(field) for field in response.json().get("fields", [])]
        self._fields[module_api_name] = fields
        return fields

    @staticmethod
    def _coerce_value(value: object, field: Mapping[str, object]) -> object:
        data_type = str(field.get("data_type") or "text")
        if data_type == "boolean":
            return bool(value)
        if data_type in {"integer", "bigint"}:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return value
        if data_type in {"currency", "double", "percent"}:
            try:
                return float(value)
            except (TypeError, ValueError):
                return value
        if data_type == "date":
            return str(value)[:10]
        if data_type in {"text", "email", "phone", "website", "textarea", "picklist"}:
            text = str(value)
            length = field.get("length")
            if isinstance(length, int) and length > 0:
                return text[:length]
            return text
        return value

    def _prepare_rows(self, module_name: str, label_rows: Sequence[Dict[str, object]]) -> Tuple[str, str, List[Dict[str, object]], List[str]]:
        modules = self._load_modules()
        module = modules.get(module_name)
        if not module:
            raise RuntimeError(f"Missing Zoho module shell: {module_name}")
        module_api_name = str(module.get("api_name"))
        fields = self._load_fields(module_api_name)
        by_label = {normalize_label(field.get("field_label")): field for field in fields if field.get("api_name")}
        external_field = by_label.get(normalize_label(EXTERNAL_ID_LABEL))
        if not external_field:
            raise RuntimeError(f"{module_name} is missing required unique field '{EXTERNAL_ID_LABEL}'")
        external_api_name = str(external_field.get("api_name"))

        desired_primary = primary_field_label(module_name)
        primary_field = by_label.get(normalize_label(desired_primary))
        fallback_name = next(
            (
                field
                for field in fields
                if field.get("api_name") == "Name" and field.get("data_type") in {"text", "textarea"}
            ),
            None,
        )

        prepared: List[Dict[str, object]] = []
        external_values: List[str] = []
        for label_row in label_rows:
            row: Dict[str, object] = {}
            for label, value in label_row.items():
                field = by_label.get(normalize_label(label))
                if not field or not field.get("api_name"):
                    continue
                if str(field.get("data_type") or "") in {"ownerlookup", "userlookup"} and not isinstance(value, dict):
                    continue
                row[str(field["api_name"])] = self._coerce_value(value, field)

            title = str(label_row.get(desired_primary) or label_row.get("Raw Record Name") or label_row.get("Source Name") or "Phase 8 Record")
            if primary_field and primary_field.get("api_name"):
                row.setdefault(str(primary_field["api_name"]), self._coerce_value(title, primary_field))
            if fallback_name and fallback_name.get("api_name"):
                row.setdefault(str(fallback_name["api_name"]), self._coerce_value(title, fallback_name))

            external_value = str(label_row.get(EXTERNAL_ID_LABEL) or "")
            if not external_value:
                raise RuntimeError(f"A {module_name} row is missing {EXTERNAL_ID_LABEL}")
            row[external_api_name] = self._coerce_value(external_value, external_field)
            prepared.append(row)
            external_values.append(external_value)
        return module_api_name, external_api_name, prepared, external_values

    def _upsert_label_rows(self, module_name: str, label_rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
        if not label_rows:
            return {"action": "no_records", "inserted": 0, "updated": 0, "failed": 0, "record_links": {}}

        try:
            module_api_name, external_api_name, prepared, external_values = self._prepare_rows(module_name, label_rows)
        except Exception as exc:
            return {
                "action": "blocked",
                "inserted": 0,
                "updated": 0,
                "failed": len(label_rows),
                "error": str(exc),
                "record_links": {},
            }

        if self.dry_run:
            return {
                "action": "dry_run_upsert",
                "module_api_name": module_api_name,
                "count": len(prepared),
                "inserted": 0,
                "updated": 0,
                "failed": 0,
                "duplicate_check_fields": [external_api_name],
                "sample": prepared[:2],
                "record_links": {},
            }

        result: Dict[str, object] = {
            "action": "upserted",
            "module_api_name": module_api_name,
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "batches": [],
            "record_links": {},
        }
        offset = 0
        for batch in chunks(prepared, self.batch_size):
            batch_values = external_values[offset : offset + len(batch)]
            offset += len(batch)
            body = {
                "data": list(batch),
                "duplicate_check_fields": [external_api_name],
                "trigger": ["workflow"],
            }
            response = self._request("POST", f"{module_api_name}/upsert", json=body)
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text[:2000]}
            response_rows = payload.get("data", []) if isinstance(payload, dict) else []
            batch_result = {"status_code": response.status_code, "count": len(batch), "response": payload}
            result["batches"].append(batch_result)

            if response.status_code >= 400 and response.status_code != 207:
                result["failed"] += len(batch)
                continue

            for index, external_value in enumerate(batch_values):
                item = response_rows[index] if index < len(response_rows) else {}
                if item.get("status") == "success":
                    action = str(item.get("action") or "insert").lower()
                    if action == "update":
                        result["updated"] += 1
                    else:
                        action = "insert"
                        result["inserted"] += 1
                    record_id = str((item.get("details") or {}).get("id") or "")
                    if record_id:
                        result["record_links"][external_value] = {
                            "id": record_id,
                            "module_api_name": module_api_name,
                            "module_name": module_name,
                            "action": action,
                        }
                else:
                    result["failed"] += 1
        return result

    def upsert_records(self, records: Iterable[NormalizedRecord]) -> Dict[str, object]:
        grouped: Dict[str, List[Dict[str, object]]] = {}
        for record in records:
            grouped.setdefault(record.recommended_module, []).append(record_to_labels(record))

        result: Dict[str, object] = {
            "inserted": 0,
            "updated": 0,
            "created_or_updated": 0,
            "failed": 0,
            "modules": {},
            "record_links": {},
        }
        for module_name, rows in grouped.items():
            module_result = self._upsert_label_rows(module_name, rows)
            result["modules"][module_name] = module_result
            result["inserted"] += int(module_result.get("inserted", 0))
            result["updated"] += int(module_result.get("updated", 0))
            result["failed"] += int(module_result.get("failed", 0))
            result["record_links"].update(module_result.get("record_links", {}))
        result["created_or_updated"] = result["inserted"] + result["updated"]
        return result

    def upsert_source_health(self, health_rows: Iterable[SourceHealth]) -> Dict[str, object]:
        return self._upsert_label_rows("GOV SOURCE HEALTH", [source_health_to_labels(row) for row in health_rows])

    def upsert_raw_audit(self, records: Iterable[NormalizedRecord]) -> Dict[str, object]:
        return self._upsert_label_rows("GOV RAW DATA AUDIT", [raw_audit_to_labels(record) for record in records])

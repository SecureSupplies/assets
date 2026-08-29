from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import requests

from core.config import Settings
from .module_definitions import (
    DASHBOARDS,
    MODULE_FIELDS,
    MODULE_ORDER,
    STATUS_FAST,
    STATUS_LEAD,
    VIEWS,
)
from .zoho_auth import ZohoAuth


EXTERNAL_ID_LABEL = "Phase8 External ID"
EXTRA_FIELDS = {
    "GOV FAST PURCHASE POSTS": ["Unit of Measure"],
    "LEADS GOV": ["Unit of Measure"],
    "GOV OPPORTUNITIES": ["Unit of Measure"],
    "GOV PRICE INTEL": ["Unit of Measure"],
    "GOV SUPPLIER CAPACITY": ["Unit of Measure"],
}
GENERIC_STATUS = ["New", "Active", "Review", "Submitted", "Won", "Lost", "Closed", "Watch", "Inactive"]
TEXTAREA_HINTS = ["Notes", "JSON", "Strategy", "Script", "Instructions", "Documents", "Requirement", "Action Plan", "Compliance", "Payload", "Description", "Error Details", "Error Message", "Likely Purchase Need"]
BOOLEAN_EXACT = {"Direct PO Eligible", "Purchase Card Possible", "Emergency Trigger", "Credit Card / P-Card Possible", "Emergency Supplier Need", "Incumbent Renewal Watch", "Credential Required", "Emergency Availability"}
BOOLEAN_HINTS = ["Eligible", "Possible", "Trigger", "Required", "Available", "Availability"]
CURRENCY_HINTS = ["Estimated Value", "Recurring Value", "Award Amount", "Obligation Amount", "Current Bid", "Market Value", "Repair Cost", "Resale Value", "Rental Value", "Logistics Cost", "Index Price", "Supplier Price", "Freight Estimate", "Delivered Price", "Margin Target", "Last Award Amount", "Historical Spend"]
INTEGER_HINTS = ["Score", "Probability", "Records Pulled", "Records Inserted", "Records Updated", "Records Failed"]
DATETIME_LABELS = {"Last Sync Time", "Last Success Time", "Pulled At"}
DOUBLE_LABELS = {"Estimated Gallons / Units", "Estimated Volume"}


def normalize_label(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def chunks(values: Sequence[object], size: int) -> Iterable[Sequence[object]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def primary_field_label(module_name: str) -> str:
    return MODULE_FIELDS[module_name][0]


def desired_fields(module_name: str) -> List[str]:
    fields = list(MODULE_FIELDS[module_name])
    if EXTERNAL_ID_LABEL not in fields:
        fields.insert(1, EXTERNAL_ID_LABEL)
    for label in EXTRA_FIELDS.get(module_name, []):
        if label not in fields:
            fields.append(label)
    return fields


def picklist_values(module_name: str, label: str) -> List[str]:
    if module_name == "GOV FAST PURCHASE POSTS" and label == "Status":
        return STATUS_FAST
    if module_name == "LEADS GOV" and label == "Bid Status":
        return STATUS_LEAD
    if label == "Status":
        return GENERIC_STATUS
    if label == "Free or Paid":
        return ["Free", "Paid"]
    if label == "Buy / Pass Recommendation":
        return ["Buy", "Evaluate", "Pass", "Watch"]
    if label == "Margin Potential":
        return ["High", "Medium", "Low", "Review"]
    if label == "Purchase Urgency":
        return ["Call Now", "Quote Now", "Procurement Review", "Standard", "Expired"]
    return []


def infer_type(module_name: str, label: str) -> str:
    if picklist_values(module_name, label):
        return "picklist"
    if label in DATETIME_LABELS or label.endswith(" Time"):
        return "datetime"
    if label.endswith(" Date") or label in {"Posted Date", "Due Date", "Award Date", "Response Deadline", "Expiration Date", "Auction Close Date", "Contract Start", "Contract End", "Expected Close Date", "Bid / Quote Due Date", "Period of Performance Start", "Period of Performance End", "Effective Date", "Expected Renewal Window", "Renewal Window", "Next Review Date", "Next Call Date", "Next Action Due"}:
        return "date"
    if label in DOUBLE_LABELS:
        return "double"
    if any(hint in label for hint in INTEGER_HINTS):
        return "integer"
    if any(hint in label for hint in CURRENCY_HINTS):
        return "currency"
    if "Email" in label:
        return "email"
    if "Phone" in label:
        return "phone"
    if "URL" in label or label in {"Website", "Procurement Portal"}:
        return "website"
    if any(hint in label for hint in TEXTAREA_HINTS):
        return "textarea"
    if label in BOOLEAN_EXACT or any(hint in label for hint in BOOLEAN_HINTS):
        return "boolean"
    return "text"


def field_payload(module_name: str, label: str) -> Dict[str, object]:
    data_type = infer_type(module_name, label)
    payload: Dict[str, object] = {"field_label": label, "data_type": data_type}

    if data_type == "text":
        payload["length"] = 255
    elif data_type == "email":
        payload["length"] = 100
    elif data_type == "phone":
        payload["length"] = 50
    elif data_type == "website":
        payload["length"] = 450
    elif data_type == "textarea":
        payload["length"] = 32000
        payload["textarea"] = {"type": "large"}
    elif data_type == "integer":
        payload["length"] = 9
        payload["separator"] = True
    elif data_type == "double":
        payload["length"] = 16
        payload["decimal_place"] = 4
        payload["separator"] = True
    elif data_type == "currency":
        payload["length"] = 16
        payload["decimal_place"] = 4
        payload["currency"] = {"rounding_option": "normal", "precision": 2}
    elif data_type == "picklist":
        payload["pick_list_values"] = [
            {"display_value": value, "actual_value": value} for value in picklist_values(module_name, label)
        ]
        payload["pick_list_values_sorted_lexically"] = False

    if label == EXTERNAL_ID_LABEL:
        payload["unique"] = {"case_sensitive": False}
        payload["external"] = {"type": "org", "show": True}
    return payload


def deployment_plan() -> Dict[str, object]:
    return {
        "tab_group": "Phase 8 Government Biz",
        "tab_group_status": "User reports the menu/tab group already exists",
        "module_shell_creation": "Zoho CRM REST v8 exposes module metadata retrieval, not custom-module shell creation. Create any missing shells in the Zoho UI.",
        "placement": "Inside the existing Phase 8 Government Biz menu/tab group, with GOV FAST PURCHASE POSTS first.",
        "modules_ordered": MODULE_ORDER,
        "primary_field_labels": {name: primary_field_label(name) for name in MODULE_ORDER},
        "views": VIEWS,
        "dashboards": DASHBOARDS,
        "fields": {name: desired_fields(name) for name in MODULE_ORDER},
    }


def write_deployment_plan(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "zoho_phase8_deployment_plan.json"
    path.write_text(json.dumps(deployment_plan(), indent=2, default=str))
    return path


class ZohoModuleDeployer:
    def __init__(self, settings: Settings):
        self.settings = settings
        token = ZohoAuth(settings).refresh_access_token()
        self.api_domain = token.api_domain.rstrip("/")
        self.headers = {"Authorization": f"Zoho-oauthtoken {token.access_token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _request(self, method: str, path: str, **kwargs: object) -> requests.Response:
        return self.session.request(
            method,
            f"{self.api_domain}/crm/v8/{path.lstrip('/')}",
            timeout=self.settings.request_timeout_seconds,
            **kwargs,
        )

    def get_modules(self) -> Dict[str, object]:
        response = self._request("GET", "settings/modules")
        response.raise_for_status()
        return response.json()

    def get_fields(self, module_api_name: str) -> Dict[str, object]:
        response = self._request("GET", "settings/fields", params={"module": module_api_name})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _module_aliases(module: Mapping[str, object]) -> set[str]:
        keys = ["api_name", "module_name", "plural_label", "singular_label", "actual_plural_label", "actual_singular_label"]
        return {normalize_label(module.get(key)) for key in keys if module.get(key)}

    def resolve_modules(self, modules_payload: Dict[str, object] | None = None) -> Dict[str, Dict[str, object]]:
        payload = modules_payload or self.get_modules()
        modules = payload.get("modules", [])
        resolved: Dict[str, Dict[str, object]] = {}
        for desired in MODULE_ORDER:
            wanted = normalize_label(desired)
            for module in modules:
                if wanted in self._module_aliases(module):
                    resolved[desired] = dict(module)
                    break
        return resolved

    def audit_module_shells(self, modules_payload: Dict[str, object] | None = None) -> Dict[str, object]:
        payload = modules_payload or self.get_modules()
        resolved = self.resolve_modules(payload)
        modules: Dict[str, object] = {}
        for position, desired in enumerate(MODULE_ORDER, start=1):
            module = resolved.get(desired)
            if not module:
                modules[desired] = {
                    "position": position,
                    "status": "missing_module_shell",
                    "primary_field_label": primary_field_label(desired),
                }
            else:
                modules[desired] = {
                    "position": position,
                    "status": "found",
                    "api_name": module.get("api_name"),
                    "module_id": module.get("id"),
                    "generated_type": module.get("generated_type"),
                    "visible": module.get("visible"),
                    "sequence_number": module.get("sequence_number"),
                    "primary_field_label": primary_field_label(desired),
                }
        missing = [name for name, result in modules.items() if result["status"] != "found"]
        return {
            "tab_group": "Phase 8 Government Biz",
            "required_count": len(MODULE_ORDER),
            "found_count": len(MODULE_ORDER) - len(missing),
            "missing_count": len(missing),
            "missing_modules": missing,
            "modules": modules,
        }

    def backup_metadata(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        modules_payload = self.get_modules()
        resolved = self.resolve_modules(modules_payload)
        fields: Dict[str, object] = {}
        for desired, module in resolved.items():
            api_name = str(module.get("api_name") or "")
            if api_name:
                fields[desired] = self.get_fields(api_name)
        data = {
            "modules": modules_payload,
            "phase8_module_audit": self.audit_module_shells(modules_payload),
            "phase8_fields": fields,
        }
        path = output_dir / "zoho_metadata_backup.json"
        path.write_text(json.dumps(data, indent=2, default=str))
        return path

    @staticmethod
    def _field_map(fields_payload: Dict[str, object]) -> Dict[str, Dict[str, object]]:
        return {
            normalize_label(field.get("field_label")): dict(field)
            for field in fields_payload.get("fields", [])
            if field.get("field_label") and field.get("api_name")
        }

    @staticmethod
    def _mandatory_fields(fields_payload: Dict[str, object]) -> List[Dict[str, object]]:
        return [
            dict(field)
            for field in fields_payload.get("fields", [])
            if field.get("system_mandatory") and field.get("api_name")
        ]

    def apply_fields_to_existing_modules(self, dry_run: bool = True, output_dir: Path | None = None) -> Dict[str, object]:
        modules_payload = self.get_modules()
        resolved = self.resolve_modules(modules_payload)
        audit = self.audit_module_shells(modules_payload)
        results: Dict[str, object] = {
            "dry_run": dry_run,
            "module_audit": audit,
            "modules": {},
            "ready_for_records": audit["missing_count"] == 0,
        }

        for module_name in MODULE_ORDER:
            module = resolved.get(module_name)
            if not module:
                results["modules"][module_name] = {
                    "status": "missing_module_shell",
                    "next_action": f"Create the custom module in Zoho UI with primary field '{primary_field_label(module_name)}'.",
                }
                continue

            api_name = str(module.get("api_name"))
            fields_payload = self.get_fields(api_name)
            existing = self._field_map(fields_payload)
            missing_labels = [label for label in desired_fields(module_name) if normalize_label(label) not in existing]
            field_actions: List[Dict[str, object]] = []

            for label in desired_fields(module_name):
                field = existing.get(normalize_label(label))
                if field:
                    field_actions.append({"field": label, "action": "exists", "api_name": field.get("api_name")})

            for batch in chunks(missing_labels, 5):
                body = {"fields": [field_payload(module_name, str(label)) for label in batch]}
                if dry_run:
                    field_actions.extend(
                        {"field": label, "action": "dry_run_create", "payload": field_payload(module_name, str(label))}
                        for label in batch
                    )
                    continue

                response = self._request("POST", "settings/fields", params={"module": api_name}, json=body)
                try:
                    payload = response.json()
                except ValueError:
                    payload = {"raw": response.text[:2000]}
                response_rows = payload.get("fields", []) if isinstance(payload, dict) else []
                for index, label in enumerate(batch):
                    item = response_rows[index] if index < len(response_rows) else {}
                    succeeded = response.status_code < 400 and item.get("status") == "success"
                    field_actions.append(
                        {
                            "field": label,
                            "action": "created" if succeeded else "failed",
                            "status_code": response.status_code,
                            "response": item or payload,
                        }
                    )
                    if not succeeded:
                        results["ready_for_records"] = False

            refreshed = self.get_fields(api_name) if not dry_run and missing_labels else fields_payload
            refreshed_map = self._field_map(refreshed)
            desired_map = {
                label: refreshed_map.get(normalize_label(label), {}).get("api_name")
                for label in desired_fields(module_name)
            }
            mandatory = [
                {"field_label": field.get("field_label"), "api_name": field.get("api_name"), "data_type": field.get("data_type")}
                for field in self._mandatory_fields(refreshed)
            ]
            primary_exact = bool(desired_map.get(primary_field_label(module_name)))
            if not primary_exact:
                results["ready_for_records"] = False

            results["modules"][module_name] = {
                "status": "fields_processed",
                "api_name": api_name,
                "module_id": module.get("id"),
                "primary_field_exact": primary_exact,
                "mandatory_fields": mandatory,
                "field_map": desired_map,
                "field_actions": field_actions,
            }

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "zoho_phase8_field_map.json").write_text(json.dumps(results, indent=2, default=str))
        return results

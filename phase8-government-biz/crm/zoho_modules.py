from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
import requests
from core.config import Settings
from .module_definitions import MODULE_ORDER, MODULE_API_NAMES, MODULE_FIELDS, VIEWS, DASHBOARDS, field_api_name
from .zoho_auth import ZohoAuth

TEXTAREA_HINTS = ["Notes", "JSON", "Strategy", "Script", "Instructions", "Documents", "Requirement", "Action Plan", "Compliance", "Payload"]
DATE_HINTS = ["Date", "Expiration"]
BOOL_HINTS = ["Eligible", "Possible", "Trigger", "Watch", "Required", "Available", "Availability", "Need"]
NUMBER_HINTS = ["Score", "Probability", "Records"]
MONEY_HINTS = ["Value", "Amount", "Price", "Cost", "Margin", "Bid", "Estimate", "Spend"]

def infer_type(label: str) -> str:
    if any(x in label for x in MONEY_HINTS): return "currency"
    if any(x in label for x in NUMBER_HINTS): return "integer"
    if any(x in label for x in BOOL_HINTS): return "boolean"
    if "Email" in label: return "email"
    if "Phone" in label: return "phone"
    if "URL" in label or "Website" in label or "Portal" in label: return "website"
    if any(x in label for x in DATE_HINTS): return "date"
    if any(x in label for x in TEXTAREA_HINTS): return "textarea"
    return "text"

def deployment_plan() -> Dict[str, object]:
    return {"tab_group":"Phase 8 Government Biz","placement":"Under or immediately after Phase 7 where Zoho UI/API supports it; otherwise adjacent tab group.","limitation":"If custom module or tab-group creation is not exposed by the active Zoho CRM API scope/edition, create module shells in the UI and run this deployer for fields, sync, tasks, and data.","modules_ordered":MODULE_ORDER,"module_api_names":MODULE_API_NAMES,"views":VIEWS,"dashboards":DASHBOARDS,"fields":MODULE_FIELDS}

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
    def get_modules(self) -> Dict[str, object]:
        r = requests.get(f"{self.api_domain}/crm/v8/settings/modules", headers=self.headers, timeout=30); r.raise_for_status(); return r.json()
    def get_fields(self, module_api_name: str) -> Dict[str, object]:
        r = requests.get(f"{self.api_domain}/crm/v8/settings/fields", headers=self.headers, params={"module": module_api_name}, timeout=30); r.raise_for_status(); return r.json()
    def backup_metadata(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        data = {"modules": self.get_modules()}
        path = output_dir / "zoho_metadata_backup.json"
        path.write_text(json.dumps(data, indent=2, default=str))
        return path
    def field_payload(self, label: str) -> Dict[str, object]:
        payload = {"field_label": label, "data_type": infer_type(label)}
        if label == "Source Record ID": payload["unique"] = {"casesensitive": False}
        if payload["data_type"] == "textarea": payload["length"] = 32000
        return payload
    def apply_fields_to_existing_modules(self, dry_run: bool = True) -> Dict[str, object]:
        modules = self.get_modules().get("modules", [])
        existing_modules = {m.get("api_name"): m for m in modules}
        results: Dict[str, object] = {"tab_group": "Phase 8 Government Biz", "modules": {}}
        for module_name in MODULE_ORDER:
            api_name = MODULE_API_NAMES[module_name]
            if api_name not in existing_modules:
                results["modules"][module_name] = {"status":"missing_module_shell","api_name":api_name,"note":"Create this module shell in Zoho UI if API cannot create custom modules."}
                continue
            existing_fields = {f.get("field_label") for f in self.get_fields(api_name).get("fields", [])}
            field_results = []
            for label in MODULE_FIELDS[module_name]:
                if label in existing_fields:
                    field_results.append({"field":label,"action":"exists"}); continue
                body = {"fields":[self.field_payload(label)]}
                if dry_run:
                    field_results.append({"field":label,"action":"dry_run_create","payload":body}); continue
                r = requests.post(f"{self.api_domain}/crm/v8/settings/fields", headers=self.headers, params={"module":api_name}, json=body, timeout=30)
                field_results.append({"field":label,"action":"created" if r.status_code < 400 else "failed","status_code":r.status_code,"body":r.text[:800]})
            results["modules"][module_name] = {"status":"fields_processed","api_name":api_name,"field_results":field_results}
        return results

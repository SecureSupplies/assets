from __future__ import annotations
import json
from pathlib import Path
from .base import AdapterResult, BaseAdapter
from core.normalize import normalize_generic

class StatePortalRegistryAdapter(BaseAdapter):
    source_name = "State/Territory Procurement Registry"
    source_type = "direct_po_registry"
    source_url = "https://www.naspo.org/states/"
    access_method = "Registry"
    credential_required = False
    def fetch(self, limit: int = 100) -> AdapterResult:
        health = self.health()
        try:
            path = Path(__file__).resolve().parents[1] / "data" / "state_registry.json"
            rows = json.loads(path.read_text())
            records = []
            for row in rows[:limit]:
                raw = {"id":row.get("code"),"title":f"{row.get('name')} procurement direct PO target registry","description":"State/local procurement portal monitoring seed for public works, fleets, airports, ports, utilities, schools, hospitals, emergency management, and water/wastewater buyers.","government_level":"State/Territory","agency":f"{row.get('name')} Procurement","state":row.get("code"),"notice_type":"Direct PO Registry","source_url":self.source_url}
                records.append(normalize_generic(raw, source_platform=self.source_name, source_type=self.source_type, source_url=self.source_url))
            return AdapterResult(records, health.ok(len(records)))
        except Exception as exc:
            return AdapterResult([], health.fail(str(exc)))

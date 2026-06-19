from __future__ import annotations
from .base import AdapterResult, BaseAdapter
from core.normalize import normalize_generic

class EiaAdapter(BaseAdapter):
    source_name = "EIA Open Data"
    source_type = "price_intel"
    source_url = "https://www.eia.gov/opendata/"
    access_method = "API"
    credential_required = True
    def fetch(self, limit: int = 50) -> AdapterResult:
        health = self.health()
        if not self.settings.eia_api_key:
            return AdapterResult([], health.fail("EIA_API_KEY missing; price intel sync disabled"))
        try:
            data = self.get_json("https://api.eia.gov/v2/petroleum/pri/gnd/data/", params={"api_key":self.settings.eia_api_key,"frequency":"weekly","data[0]":"value","facets[series][]":"EMD_EPD2D_PTE_NUS_DPG","sort[0][column]":"period","sort[0][direction]":"desc","length":min(limit,10)})
            rows = data.get("response", {}).get("data", []) if isinstance(data, dict) else []
            records = []
            for row in rows:
                raw = {"id": f"EIA-{row.get('series')}-{row.get('period')}", "title": "EIA diesel market price signal", "description": str(row), "estimated_value": row.get("value"), "notice_type": "Price Intel", "source_url": self.source_url}
                records.append(normalize_generic(raw, source_platform=self.source_name, source_type=self.source_type, source_url=self.source_url))
            return AdapterResult(records, health.ok(len(records)))
        except Exception as exc:
            return AdapterResult([], health.fail(str(exc)))

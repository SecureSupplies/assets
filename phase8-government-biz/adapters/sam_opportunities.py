from __future__ import annotations
from datetime import datetime, timedelta
from .base import AdapterResult, BaseAdapter
from core.normalize import normalize_generic

class SamOpportunitiesAdapter(BaseAdapter):
    source_name = "SAM.gov Contract Opportunities"
    source_type = "opportunity"
    source_url = "https://open.gsa.gov/api/get-opportunities-public-api/"
    access_method = "API"
    credential_required = True
    def fetch(self, limit: int = 50) -> AdapterResult:
        health = self.health()
        if not self.settings.sam_api_key:
            return AdapterResult([], health.fail("SAM_API_KEY missing; source marked Missing Credentials"))
        try:
            params = {"api_key": self.settings.sam_api_key, "postedFrom": (datetime.utcnow()-timedelta(days=14)).strftime("%m/%d/%Y"), "postedTo": datetime.utcnow().strftime("%m/%d/%Y"), "limit": min(limit, 100), "ptype": "o,k,p,r,s"}
            data = self.get_json("https://api.sam.gov/opportunities/v2/search", params=params)
            items = data.get("opportunitiesData", []) if isinstance(data, dict) else []
            records = [normalize_generic(item, source_platform=self.source_name, source_type=self.source_type, source_url=self.source_url) for item in items]
            return AdapterResult(records, health.ok(len(records)))
        except Exception as exc:
            return AdapterResult([], health.fail(str(exc)))

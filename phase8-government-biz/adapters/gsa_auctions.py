from __future__ import annotations
from .base import AdapterResult, BaseAdapter
from core.normalize import normalize_generic

class GsaAuctionsAdapter(BaseAdapter):
    source_name = "GSA Auctions"
    source_type = "auction"
    source_url = "https://gsa.github.io/auctions_api/"
    access_method = "Public API"
    credential_required = False
    def fetch(self, limit: int = 50) -> AdapterResult:
        health = self.health()
        try:
            data = self.get_json("https://api.gsa.gov/technology/gsaauctions/v1/auctions", params={"format":"json"})
            items = data.get("Results") or data.get("auctions") or data.get("results") or [] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            records = [normalize_generic(item, source_platform=self.source_name, source_type=self.source_type, source_url=self.source_url) for item in items[:limit]]
            return AdapterResult(records, health.ok(len(records)))
        except Exception as exc:
            return AdapterResult([], health.fail(str(exc)))

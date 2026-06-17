from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List
import requests
from core.config import Settings
from core.normalize import normalize_generic
from core.schemas import NormalizedRecord, SourceHealth

@dataclass
class AdapterResult:
    records: List[NormalizedRecord]
    health: SourceHealth

class BaseAdapter:
    source_name = "Unknown"
    source_type = "api"
    source_url = ""
    access_method = "API"
    free_or_paid = "Free"
    credential_required = False

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent, "Accept": "application/json"})

    def health(self) -> SourceHealth:
        return SourceHealth(self.source_name, self.source_type, self.source_url, self.access_method, self.free_or_paid, self.credential_required)

    def fetch(self, limit: int = 50) -> AdapterResult:
        raise NotImplementedError

    def get_json(self, url: str, params: Dict[str, object] | None = None) -> object:
        response = self.session.get(url, params=params or {}, timeout=self.settings.request_timeout_seconds)
        response.raise_for_status()
        return response.json()

    def sample_result(self, raws: Iterable[Dict[str, object]], source_type: str | None = None) -> AdapterResult:
        records = [normalize_generic(raw, source_platform=self.source_name, source_type=source_type or self.source_type, source_url=self.source_url) for raw in raws]
        return AdapterResult(records, self.health().ok(len(records)))

from __future__ import annotations
from .base import AdapterResult, BaseAdapter
from core.normalize import normalize_generic

class OpenFemaAdapter(BaseAdapter):
    source_name = "OpenFEMA Disaster Declarations"
    source_type = "disaster_signal"
    source_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
    access_method = "API"
    credential_required = False
    def fetch(self, limit: int = 50) -> AdapterResult:
        health = self.health()
        try:
            data = self.get_json(self.source_url, params={"$top":min(limit,100),"$orderby":"declarationDate desc"})
            rows = data.get("DisasterDeclarationsSummaries", []) if isinstance(data, dict) else []
            records = []
            for row in rows:
                raw = {"id":row.get("disasterNumber"),"title":f"FEMA disaster declaration {row.get('disasterNumber')} {row.get('incidentType')}","description":str(row),"agency":"FEMA","state":row.get("state"),"notice_type":"Disaster Declaration","source_url":self.source_url}
                records.append(normalize_generic(raw, source_platform=self.source_name, source_type=self.source_type, source_url=self.source_url))
            return AdapterResult(records, health.ok(len(records)))
        except Exception as exc:
            return AdapterResult([], health.fail(str(exc)))

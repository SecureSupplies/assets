from __future__ import annotations
from .base import AdapterResult, BaseAdapter

class UsaSpendingAdapter(BaseAdapter):
    source_name = "USAspending"
    source_type = "award"
    source_url = "https://api.usaspending.gov/docs/endpoints"
    access_method = "API"
    credential_required = False
    def fetch(self, limit: int = 50) -> AdapterResult:
        return AdapterResult([], self.health().fail("USAspending live adapter pending endpoint payload validation in production terminal; sample awards still validate routing."))

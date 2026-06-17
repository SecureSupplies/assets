"""SAM.gov Contract Opportunities adapter.

This adapter calls the SAM.gov API to retrieve contracting
opportunities.  It requires a valid API key configured in the
environment.  Only a stub implementation is provided here for
illustration; a full implementation would handle pagination, filters
and error handling.
"""

from __future__ import annotations

import requests
from typing import Iterable, Dict

from ..core.models import Record
from ..core.config import get_settings
from ..core.log import get_logger


logger = get_logger(__name__)


class SamAdapter:
    """Fetch records from SAM.gov Contract Opportunities."""

    BASE_URL = "https://api.sam.gov/prod/opportunities/v2/search"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.sam_api_key
        if not self.api_key:
            logger.warning("SAM_API_KEY is not set; SAM adapter will not return results")

    def fetch(self, limit: int = 20) -> Iterable[Record]:
        """Fetch a limited number of opportunities from SAM.gov.

        Args:
            limit: Maximum number of records to return.

        Yields:
            Record instances for each opportunity retrieved.
        """
        if not self.api_key:
            return []
        params: Dict[str, str | int] = {
            "api_key": self.api_key,
            "limit": limit,
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Error fetching SAM data: %s", exc)
            return []

        records: list[Record] = []
        for item in data.get("opportunitiesData", [])[:limit]:
            record = Record(
                source="sam",
                id=str(item.get("noticeId")),
                title=item.get("title", ""),
                description=item.get("description", ""),
                raw=item,
            )
            records.append(record)
        return records

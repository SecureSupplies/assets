"""USAspending Awards adapter.

Fetches award search results from the USAspending API.  The endpoint
does not require an API key but may enforce rate limits.  Only a
simplified stub is provided.
"""

from __future__ import annotations

import requests
from typing import Iterable, Dict, Any

from ..core.models import Record
from ..core.log import get_logger

logger = get_logger(__name__)


class UsaSpendingAdapter:
    """Fetch records from USAspending award search API."""

    BASE_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    def fetch(self, limit: int = 50) -> Iterable[Record]:
        """Fetch a limited number of award records.

        Args:
            limit: Maximum number of awards to return.

        Yields:
            Record instances for each award.
        """
        payload: Dict[str, Any] = {
            "fields": ["Award ID", "Award Description"],
            "limit": limit,
            "page": 1,
            "query": "fuel",  # simple query for demonstration
        }
        try:
            resp = requests.post(self.BASE_URL, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Error fetching USAspending data: %s", exc)
            return []

        awards = data.get("results", [])
        records: list[Record] = []
        for item in awards[:limit]:
            record = Record(
                source="usaspending",
                id=str(item.get("Award ID")),
                title=item.get("Award Description", ""),
                description=item.get("Award Description", ""),
                raw=item,
            )
            records.append(record)
        return records

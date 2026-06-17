"""Zoho CRM client stub.

This class demonstrates the structure of a Zoho client using OAuth
tokens.  In production the client would handle token refresh,
module/field creation, data upsert and error handling.  Here we
provide only basic scaffolding.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable

import requests

from ..core.config import get_settings
from ..core.log import get_logger
from ..core.models import Record


logger = get_logger(__name__)


class ZohoClient:
    """Minimal Zoho CRM REST client with OAuth token support."""

    BASE_URL = "https://www.zohoapis.com/crm/v4"

    def __init__(self) -> None:
        settings = get_settings()
        self.client_id = settings.zoho_client_id
        self.client_secret = settings.zoho_client_secret
        self.refresh_token = settings.zoho_refresh_token
        self.access_token: str | None = None

    def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not (self.client_id and self.client_secret and self.refresh_token):
            raise RuntimeError("Zoho OAuth credentials are not configured")
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        payload = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        try:
            resp = requests.post(token_url, data=payload, timeout=10)
            resp.raise_for_status()
            token_data = resp.json()
            self.access_token = token_data.get("access_token")
            logger.info("Obtained new Zoho access token")
        except Exception as exc:
            logger.error("Failed to refresh Zoho access token: %s", exc)
            raise

    def _ensure_token(self) -> None:
        if not self.access_token:
            self._refresh_access_token()

    def create_module(self, module_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom module in Zoho CRM.

        Args:
            module_definition: JSON definition of the module per Zoho API.

        Returns:
            API response JSON.
        """
        self._ensure_token()
        url = f"{self.BASE_URL}/settings/modules"
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        try:
            resp = requests.post(url, json=module_definition, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Error creating module: %s", exc)
            raise

    def upsert_records(self, module_api_name: str, records: Iterable[Record]) -> Dict[str, Any]:
        """Upsert records into a Zoho module.

        Args:
            module_api_name: API name of the module.
            records: Iterable of Record objects to upsert.

        Returns:
            API response JSON.
        """
        self._ensure_token()
        url = f"{self.BASE_URL}/{module_api_name}/upsert"
        payload = {
            "data": [self._record_to_dict(r) for r in records]
        }
        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Error upserting records: %s", exc)
            raise

    def _record_to_dict(self, record: Record) -> Dict[str, Any]:
        """Map our Record object into the structure expected by Zoho."""
        return {
            "External_Id": record.id,
            "Name": record.title,
            "Description": record.description,
            "Taxonomy": record.taxonomy,
            "Fast_Purchase_Score": record.fast_purchase_score,
            "Opportunity_Score": record.opportunity_score,
        }

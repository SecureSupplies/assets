from __future__ import annotations
from dataclasses import dataclass
import requests
from core.config import Settings

@dataclass
class ZohoToken:
    access_token: str
    api_domain: str

class ZohoAuth:
    def __init__(self, settings: Settings):
        self.settings = settings
    def refresh_access_token(self) -> ZohoToken:
        if not self.settings.zoho_ready():
            raise RuntimeError("Zoho OAuth variables missing in terminal environment")
        url = f"{self.settings.zoho_accounts_domain}/oauth/v2/token"
        data = {"refresh_token": self.settings.zoho_refresh_token_value, "client_id": self.settings.zoho_client_id, "client_secret": self.settings.zoho_client_secret_value, "grant_type": "refresh_token"}
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise RuntimeError("Zoho token refresh did not return access token")
        return ZohoToken(token, payload.get("api_domain") or self.settings.zoho_api_domain)

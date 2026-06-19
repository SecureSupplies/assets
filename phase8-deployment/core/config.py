"""Configuration loader for Phase 8 Government Biz.

This module centralizes the loading of environment variables and other
runtime configuration.  It reads from a `.env` file when present
and falls back to the environment.  Consumers should use
``get_settings`` to obtain a mapping of configuration values.
"""

import os
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python‑dotenv is not installed or .env is not present
    pass


class Settings:
    """Simple settings object with attribute access."""

    def __init__(self) -> None:
        self.sam_api_key: str | None = os.getenv("SAM_API_KEY")
        self.gsa_api_key: str | None = os.getenv("GSA_API_KEY")
        self.eia_api_key: str | None = os.getenv("EIA_API_KEY")
        self.nws_user_agent: str | None = os.getenv("NWS_USER_AGENT")
        self.fema_api_key: str | None = os.getenv("FEMA_API_KEY")
        self.zoho_client_id: str | None = os.getenv("ZOHO_CLIENT_ID")
        self.zoho_client_secret: str | None = os.getenv("ZOHO_CLIENT_SECRET")
        self.zoho_refresh_token: str | None = os.getenv("ZOHO_REFRESH_TOKEN")
        self.enable_crm_writes: bool = os.getenv("PHASE8_ENABLE_CRM_WRITES", "false").lower() == "true"

    def __repr__(self) -> str:  # pragma: no cover
        return f"Settings(sam_api_key={self.sam_api_key!r}, enable_crm_writes={self.enable_crm_writes})"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object.  Use lru_cache to avoid re‑parsing environment each time."""
    return Settings()

from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "y", "on"}


def int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    dry_run: bool = bool_env("PHASE8_DRY_RUN", True)
    output_dir: Path = Path(os.getenv("PHASE8_OUTPUT_DIR", "out"))
    notification_to: str = os.getenv("PHASE8_NOTIFICATION_TO", "fuels@securesupplies.us")
    min_fast_score_to_email: int = int_env("PHASE8_MIN_FAST_SCORE_TO_EMAIL", 70)
    min_priority_score_to_email: int = int_env("PHASE8_MIN_PRIORITY_SCORE_TO_EMAIL", 80)
    request_timeout_seconds: int = int_env("PHASE8_REQUEST_TIMEOUT_SECONDS", 30)
    user_agent: str = os.getenv("PHASE8_USER_AGENT", "SecureSupplies-Phase8-GovBiz/1.0 ops@securesupplies.us")
    zoho_api_domain: str = os.getenv("ZOHO_API_DOMAIN", "https://www.zohoapis.com")
    zoho_accounts_domain: str = os.getenv("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com")
    zoho_client_id: str = os.getenv("ZOHO_CLIENT_ID", "")
    zoho_client_secret_value: str = os.getenv("ZOHO_CLIENT_SECRET_VALUE") or os.getenv("ZOHO_CLIENT_SECRET", "")
    zoho_refresh_token_value: str = os.getenv("ZOHO_REFRESH_TOKEN_VALUE") or os.getenv("ZOHO_REFRESH_TOKEN", "")
    sam_api_key: str = os.getenv("SAM_API_KEY", "")
    eia_api_key: str = os.getenv("EIA_API_KEY", "")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int_env("SMTP_PORT", 587)
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_secret_value: str = os.getenv("SMTP_SECRET_VALUE", "")
    smtp_from: str = os.getenv("SMTP_FROM", "alerts@securesupplies.us")
    smtp_use_tls: bool = bool_env("SMTP_USE_TLS", True)

    def zoho_ready(self) -> bool:
        return all([self.zoho_client_id, self.zoho_client_secret_value, self.zoho_refresh_token_value])

    def smtp_ready(self) -> bool:
        return all([self.smtp_host, self.smtp_username, self.smtp_secret_value, self.smtp_from])


def load_settings() -> Settings:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    return settings

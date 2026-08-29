from __future__ import annotations

import os
from typing import List

from .config import Settings


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "y", "on"}


def crm_write_blockers(settings: Settings) -> List[str]:
    blockers: List[str] = []
    if settings.dry_run:
        blockers.append("PHASE8_DRY_RUN is true")
    if not bool_env("PHASE8_ENABLE_CRM_WRITES", False):
        blockers.append("PHASE8_ENABLE_CRM_WRITES is not true")
    if os.getenv("PHASE8_DEPLOY_CONFIRMATION", "").strip() != "DEPLOY_PHASE8":
        blockers.append("PHASE8_DEPLOY_CONFIRMATION must equal DEPLOY_PHASE8")
    if not settings.zoho_ready():
        blockers.append("Zoho OAuth variables are incomplete")
    return blockers


def crm_writes_allowed(settings: Settings) -> bool:
    return not crm_write_blockers(settings)


def notification_blockers(settings: Settings) -> List[str]:
    blockers: List[str] = []
    if settings.dry_run:
        blockers.append("PHASE8_DRY_RUN is true")
    if not bool_env("PHASE8_ENABLE_NOTIFICATIONS", False):
        blockers.append("PHASE8_ENABLE_NOTIFICATIONS is not true")
    if not settings.smtp_ready():
        blockers.append("SMTP variables are incomplete")
    return blockers


def notifications_allowed(settings: Settings) -> bool:
    return not notification_blockers(settings)

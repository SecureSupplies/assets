#!/usr/bin/env python
"""Deploy Phase 8 Government Biz modules and fields to Zoho CRM.

This script reads the deployment plan from local data and, if run with
the `--production` flag and the `PHASE8_ENABLE_CRM_WRITES` environment
variable set to true, calls the Zoho API to create custom modules,
fields and dashboards.  In dry‑run mode it prints a summary of the
actions that would be taken without making any API calls.  The
implementation here is deliberately skeletal; full error handling and
backup/restore logic should be added in a production system.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ..core import get_logger, get_settings
from ..crm import ZohoClient

logger = get_logger(__name__)


def build_module_definitions() -> list[dict[str, object]]:
    """Return a list of module definitions to create in Zoho.

    Each entry is a minimal module definition.  In reality these
    definitions would include fields, layouts, permissions and other
    metadata derived from our data schema.
    """
    module_names = [
        "GOV FAST PURCHASE POSTS",
        "LEADS GOV",
        "GOV DIRECT PO",
        "GOV OPPORTUNITIES",
        "GOV BUYERS",
        "GOV AWARDS",
        "GOV INCUMBENTS",
        "GOV AUCTIONS",
        "GOV PRICE INTEL",
        "GOV ROUTES",
        "GOV SUPPLIER CAPACITY",
        "GOV COMPLIANCE",
        "GOV WATCHLIST",
        "GOV SOURCE HEALTH",
        "GOV RAW DATA AUDIT",
    ]
    modules = []
    for name in module_names:
        api_name = name.replace(" ", "_").replace("-", "_").upper()
        modules.append({
            "api_name": api_name,
            "module_name": name,
            "plural_label": name,
            "singular_label": name[:-1] if name.endswith('S') else name,
            "owner": None,
        })
    return modules


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy Phase8 modules to Zoho")
    parser.add_argument("--production", action="store_true", help="Perform live writes to Zoho")
    args = parser.parse_args()

    settings = get_settings()
    do_writes = args.production and settings.enable_crm_writes
    if args.production and not settings.enable_crm_writes:
        logger.error("Production flag set but PHASE8_ENABLE_CRM_WRITES is not true; aborting")
        return

    modules = build_module_definitions()

    # Dry run: print JSON plan to stdout
    if not do_writes:
        logger.info("Dry run: printing module definitions")
        print(json.dumps(modules, indent=2))
        return

    # Production: create modules via Zoho API
    client = ZohoClient()
    for module_def in modules:
        try:
            resp = client.create_module({"modules": [module_def]})
            logger.info("Created module %s", module_def["module_name"])
        except Exception as exc:
            logger.error("Failed to create module %s: %s", module_def["module_name"], exc)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json

from core.config import load_settings
from core.runtime_safety import crm_write_blockers, crm_writes_allowed
from .zoho_modules import ZohoModuleDeployer, write_deployment_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and deploy Secure Supplies Phase 8 Zoho CRM fields")
    parser.add_argument("--audit", action="store_true", help="Read Zoho metadata and report module-shell readiness")
    parser.add_argument("--apply", action="store_true", help="Create missing fields on module shells that already exist")
    parser.add_argument("--dry-run", action="store_true", help="Show field payloads without creating fields")
    args = parser.parse_args()

    settings = load_settings()
    plan_path = write_deployment_plan(settings.output_dir)
    result: dict[str, object] = {
        "deployment_plan": str(plan_path),
        "requested": {"audit": args.audit, "apply": args.apply, "dry_run": args.dry_run},
    }

    if not (args.audit or args.apply):
        result["status"] = "plan_only"
        result["next_command"] = "python -m crm.deploy_phase8 --audit"
    elif not settings.zoho_ready():
        result["status"] = "blocked"
        result["blockers"] = ["Zoho OAuth variables are incomplete"]
    else:
        deployer = ZohoModuleDeployer(settings)
        backup = deployer.backup_metadata(settings.output_dir)
        result["metadata_backup"] = str(backup)
        result["module_audit"] = deployer.audit_module_shells()

        if args.apply:
            live_allowed = crm_writes_allowed(settings) and not args.dry_run
            result["live_write_allowed"] = live_allowed
            result["write_blockers"] = [] if live_allowed else crm_write_blockers(settings)
            result["field_apply"] = deployer.apply_fields_to_existing_modules(
                dry_run=not live_allowed,
                output_dir=settings.output_dir,
            )
            result["status"] = "applied" if live_allowed else "dry_run_complete"
        else:
            result["status"] = "audit_complete"

    output = settings.output_dir / "zoho_phase8_deploy_result.json"
    output.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()

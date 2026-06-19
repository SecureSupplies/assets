from __future__ import annotations
import argparse, json
from core.config import load_settings
from .zoho_modules import write_deployment_plan, ZohoModuleDeployer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()
    settings = load_settings()
    plan_path = write_deployment_plan(settings.output_dir)
    result = {"deployment_plan": str(plan_path)}
    if args.apply:
        deployer = ZohoModuleDeployer(settings)
        backup = deployer.backup_metadata(settings.output_dir)
        result["metadata_backup"] = str(backup)
        result["field_apply"] = deployer.apply_fields_to_existing_modules(dry_run=args.dry_run or settings.dry_run)
    output = settings.output_dir / "zoho_phase8_deploy_result.json"
    output.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()

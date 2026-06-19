# Phase 8 Government Biz

Phase 8 Government Biz is Secure Supplies' government sales-intelligence and opportunity-generation package. It ingests public-sector opportunity, award, auction, pricing, weather, disaster, and direct-purchase data; classifies product fit; scores urgency and commercial value; routes records to Zoho CRM; preserves source auditability; creates linked tasks; and can send controlled high-value alerts.

## Commercial lanes

1. Diesel + tank rental + monitoring + auto-refill
2. DEF route service attached to diesel buyers
3. Emergency generator fuel
4. Propane / LPG for public facilities
5. Water/wastewater gases and treatment chemicals
6. Airport Jet A / Avgas
7. Port and ferry marine diesel / MGO
8. Surplus tank/generator/fuel asset acquisition
9. CNG / LNG / RNG fleet and infrastructure projects
10. Fertilizer / ammonia / urea / UAN / NPK demand

## Zoho CRM structure

The existing Zoho menu/tab group is `Phase 8 Government Biz`. It must contain these custom-module shells in order:

1. GOV FAST PURCHASE POSTS
2. LEADS GOV
3. GOV DIRECT PO
4. GOV OPPORTUNITIES
5. GOV BUYERS
6. GOV AWARDS
7. GOV INCUMBENTS
8. GOV AUCTIONS
9. GOV PRICE INTEL
10. GOV ROUTES
11. GOV SUPPLIER CAPACITY
12. GOV COMPLIANCE
13. GOV WATCHLIST
14. GOV SOURCE HEALTH
15. GOV RAW DATA AUDIT

`GOV FAST PURCHASE POSTS` is the top money queue. Scores 85-100 route to `Call Now`, 70-84 to `Quote Now`, 55-69 to `Procurement Review`, and lower scores to watch/no-bid handling. Expired notices are excluded from active call and quote queues.

Zoho generates custom-module and custom-field API names. The deployment code reads those names from live metadata rather than deriving them from labels.

See [`docs/ZOHO_MODULE_SHELL_CHECKLIST.md`](docs/ZOHO_MODULE_SHELL_CHECKLIST.md) for the exact module and primary-field labels.

## Install

```bash
cd phase8-government-biz
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` through the approved secret-management process. Do not commit credentials.

## Isolated validation

```bash
python -m compileall -q .
python -m pytest -q
python run_pipeline.py --mode test --limit-per-source 10
```

Test mode uses sample data only unless `--include-live-sources` is explicitly supplied. It does not write to Zoho and does not send notifications.

Primary outputs include:

- `out/phase8_normalized_records.csv`
- `out/phase8_records.json`
- `out/phase8_source_health.json`
- `out/phase8_raw_audit.json`
- `out/phase8_email_outcomes.json`
- `out/phase8_crm_result.json`
- `out/phase8_task_result.json`
- `out/phase8_deployment_report.json`
- `out/zoho_phase8_deployment_plan.json`

## Zoho module audit

The REST deployment layer can audit existing custom-module shells and create fields on shells that already exist. It does not fabricate module API names.

```bash
python -m crm.deploy_phase8 --audit
python -m crm.deploy_phase8 --apply --dry-run
```

Review:

- `out/zoho_metadata_backup.json`
- `out/zoho_phase8_deploy_result.json`
- `out/zoho_phase8_field_map.json`

The module audit must report `required_count: 15`, `found_count: 15`, and `missing_count: 0` before production record synchronization.

## Controlled field deployment

Live field creation requires every deployment gate to pass:

```bash
PHASE8_DRY_RUN=false \
PHASE8_ENABLE_CRM_WRITES=true \
PHASE8_DEPLOY_CONFIRMATION=DEPLOY_PHASE8 \
python -m crm.deploy_phase8 --apply
```

The deployer:

- backs up module and field metadata;
- resolves actual Zoho API names;
- creates missing fields in API-compliant batches;
- adds the organization-wide `Phase8 External ID` used for idempotent upserts;
- writes a post-deployment field map;
- blocks record synchronization when required shells or fields are missing.

## Production synchronization

```bash
PHASE8_DRY_RUN=false \
PHASE8_ENABLE_CRM_WRITES=true \
PHASE8_DEPLOY_CONFIRMATION=DEPLOY_PHASE8 \
python run_pipeline.py --mode production --deploy-fields --limit-per-source 100
```

Production mode:

- backs up Zoho metadata;
- audits all 15 module shells;
- applies missing fields when requested;
- pulls configured public sources;
- normalizes, classifies, scores, deduplicates, and routes records;
- upserts in bounded batches using the external source identity;
- preserves human-managed status, owner, notes, strategy, and action-plan fields;
- creates linked urgent tasks only for newly inserted records;
- writes `GOV SOURCE HEALTH` and `GOV RAW DATA AUDIT` records;
- suppresses notifications unless the separate notification gate and SMTP configuration are complete.

## Automation

`.github/workflows/phase8-government-biz.yml` compiles the package, runs regression tests, executes the isolated pipeline dry-run, and uploads validation outputs. It never performs live CRM writes.

`scheduler.yaml` defines the operating cadence for urgent checks, full synchronization, and disaster/weather monitoring. Production scheduling should call the controlled commands above from an environment that has the approved Zoho OAuth configuration.

# Phase 8 Government Biz

Phase 8 Government Biz is Secure Supplies' government sales-intelligence and opportunity-generation package. It is built to find public-sector money, classify product fit, score urgency and margin potential, route opportunities to the correct CRM queue, preserve source auditability, create CRM tasks, and email high-value order leads to `fuels@securesupplies.us`.

## What it does

The pipeline pulls government opportunity, award, auction, pricing, disaster, weather, and direct-PO seed data. It normalizes every record into a common schema, classifies product lanes, deduplicates, scores, routes, and writes dry-run outputs or production CRM records.

Top commercial lanes:

1. Diesel + tank rental + monitoring + auto-refill
2. DEF route service attached to diesel buyers
3. Emergency generator fuel
4. Propane / LPG for public facilities
5. Water/wastewater gases and treatment chemicals
6. Airport Jet A / Avgas
7. Port and ferry marine diesel / MGO
8. Surplus tank/generator/fuel asset acquisition
9. CNG / LNG / RNG fleet and infrastructure projects
10. Fertilizer / ammonia / urea / NPK seasonal demand

## CRM modules

The Zoho deployment plan creates a `Phase 8 Government Biz` section/tab group and these modules in order:

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

`GOV FAST PURCHASE POSTS` is the top money queue. Score 85-100 routes to `Call Now`, 70-84 to `Quote Now`, 55-69 to `Procurement Review`, and sub-55 to watch/no-bid.

## Install

```bash
cd phase8-government-biz
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with Zoho OAuth, public API keys, and SMTP credentials. Do not commit `.env`.

## Test mode

```bash
python -m pytest
python run_pipeline.py --mode test --include-samples
```

Test mode creates:

- `out/phase8_normalized_records.csv`
- `out/phase8_records.json`
- `out/phase8_source_health.json`
- `out/phase8_email_outcomes.json`
- `out/phase8_crm_result.json`
- `out/zoho_phase8_deployment_plan.json`

Test mode does not write to Zoho and does not send emails.

## Production mode

```bash
PHASE8_DRY_RUN=false python run_pipeline.py --mode production --deploy-fields --limit-per-source 100
```

Production mode:

- Backs up Zoho module metadata.
- Applies fields to existing Phase 8 module shells where accessible.
- Pulls configured public sources.
- Normalizes, classifies, scores, and dedupes.
- Upserts records by external source ID.
- Creates urgent CRM tasks.
- Emails high-value order/lead alerts to `fuels@securesupplies.us` when SMTP is configured.

## Zoho limitation

Zoho CRM API access in this package uses official REST endpoints for reading modules and creating custom fields. If the CRM edition/API scope does not expose custom module or tab-group creation, create the `Phase 8 Government Biz` tab group and module shells in Zoho UI, then run `crm/zoho_deploy.py --execute` to create fields and start sync.

## Scheduler

`scheduler.yaml` defines hourly urgent SAM.gov checks, daily full syncs, weather/disaster checks every two hours, and manual dry-run validation. The GitHub Actions workflow runs the same commands once the workflow is merged to the default branch and secrets are installed.

# Phase 8 Government Biz Deployment Report

## Current execution status

- GitHub repository: `SecureSupplies/assets`
- Branch: `phase-8-government-biz`
- Deployment package path: `phase8-government-biz/`
- Zoho CRM connector status: not available in the active connector list for this run.
- Zoho production writes: blocked until Zoho OAuth credentials and CRM API access are supplied.
- CRM‑safe fallback: module, field, dashboard, source-health and bulk‑write plans are generated locally in dry‑run mode.

## CRM section requested

`Phase 8 Government Biz`

Placement target: under or immediately after existing `Phase 7` if supported. If Zoho does not support nested left‑menu folders via API, use a tab group named `Phase 8 Government Biz` adjacent to Phase 7.

## Modules to create, in order

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

## Delivered GitHub files

Because the Zoho connector was unavailable in this session, the code and deployment plans were developed in a local package rather than pushed live. When you run the deploy script after connecting the Zoho OAuth and enabling writes, the following files will be created in the repository’s `phase8-government-biz/` directory:

- `README.md` — overview and instructions for Phase 8 Government Biz, scoring logic, test mode, and production deployment guardrails.
- `.env.example` — environment variables template with placeholders for SAM, EIA, Zoho OAuth, paid feed API keys, and feature flags.
- `requirements.txt` — minimal dependencies list (pytest, etc.).
- `scheduler.yaml` — cron‑style job definitions for hourly/daily API pulls, CSV imports, and emergency signal feeds.
- `data/source_registry.json` — registry of federal, state/local, disaster, economic, market intel, auction, and price feeds; indicates access method, free/paid, credential requirement, and default enablement.
- `data/product_taxonomy.json` — classification taxonomy for diesel, DEF, aviation fuel, marine fuel, gases, chemicals, tanks, rentals, auctions, natural gas, hydrogen, fertilizers, water/wastewater chemicals, emergency response, etc.
- `data/naics_psc_nigp_map.json` — mapping of NAICS, PSC/FSC, and NIGP codes to descriptive labels.
- `data/state_registry.json` — seeded registry of U.S. states, territories, and commonwealths for portal and vendor‑registration coverage.
- `core/` — reusable modules for configuration, logging, normalization, deduplication, classification, scoring, routing, raw audit, and pipeline orchestration.
- `adapters/` — source‑specific clients for SAM Contract Opportunities, USAspending awards, GSA auctions, EIA price intel, National Weather Service alerts, OpenFEMA disaster declarations, state/local CSV imports, and a registry of stub connectors for portals without open APIs (DLA DIBBS, FedConnect, etc.).
- `crm/` — Zoho client with OAuth token provider, metadata backup, module creation plan, field creation plan, data upsert mapping, bulk‑CSV generator, task creation logic, and dashboard plan.
- `scripts/test_mode.py` — test runner that pulls a sample of records, normalizes, dedupes, classifies, scores, routes, and writes CSV/JSON outputs without writing to CRM.
- `scripts/deploy_zoho.py` — deployment script that writes module, field and dashboard plans in dry‑run mode by default; with `--production` and `PHASE8_ENABLE_CRM_WRITES=true` it calls the Zoho metadata API to create modules and fields after backing up existing metadata.
- `docs/DEPLOYMENT_REPORT.md` — this report.
- `tests/` — pytest unit tests for classification, scoring, deduplication and Zoho field mapping.

## APIs connected first in code

- SAM.gov Contract Opportunities API
- USAspending award search API
- GSA Auctions API
- EIA Open Data API
- National Weather Service alerts API
- OpenFEMA Disaster Declarations feed (JSON)
- State/local CSV import workflow

## APIs pending credentials or implementation

- SAM.gov and EIA: provide API keys in your `.env` file to enable these adapters.
- Paid/licensed feeds: HigherGov, GovWin (Deltek), GovSpend, Bloomberg Government, OPIS, Argus, Platts, DTN, HERE fuel prices, TomTom fuel prices (credentials/license required; adapters configured as stubs).
- Portals with no open API: DLA DIBBS, FedConnect, OpenGov, DemandStar, Bonfire, PlanetBids, Ion Wave, BidNet, Public Purchase, GovDeals, Public Surplus, Municibid (configured for manual portal exports, CSV imports, or saved searches until authorized connectors become available).

## Test mode

Run:

```bash
cd phase8-government-biz
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/run_test_mode.py --limit 20
pytest
```

Outputs:

- `output/phase8_normalized_records.csv` — deduped and classified sample records.
- `output/phase8_source_health.json` — health snapshot for each source (success, missing credentials, failure, etc.).
- `output/phase8_raw_audit.jsonl` — JSONL audit of raw payloads with hash and processing status.
- `output/module_csv/` — one CSV per target Zoho module containing upsert payloads for bulk import.
- `output/phase8_test_summary.json` — summary of record counts, top scores and output file names.

## Production mode

Production CRM writes are disabled by default. To push modules and fields into Zoho, first configure OAuth credentials and set `PHASE8_ENABLE_CRM_WRITES=true` in your environment. Then run:

```bash
python scripts/deploy_zoho.py --production
```

The script will backup existing metadata, create the `Phase 8 Government Biz` tab group after Phase 7 if possible, add all custom modules in order, add fields for each module using appropriate data types and picklists, and generate the dashboard and custom views plan. In a dry run it writes the JSON plan files without hitting the API.

## Routing and scoring overview

The system scores each record on two dimensions: fast purchase (urgency / immediate opportunity) and overall opportunity (longer‑cycle bids). Points are awarded for product fit, procurement path, estimated value/volume, deadline urgency, repeat buyer potential, logistics fit, direct PO eligibility and emergency triggers. Top fast purchase records (score ≥70) are routed to `GOV FAST PURCHASE POSTS` with recommended actions (“Call Now”, “Quote Now”, “Procurement Review”). Bid/lead opportunities are routed to `LEADS GOV`. Auctions, awards, awards/incumbents, watchlist, price intel, routes, supplier capacity, and compliance items go to their respective modules.

## Blockers

- The Zoho CRM connector is not enabled in this environment, so live module/field creation could not be tested. You must add the Zoho connector to this workspace or perform the API calls from your own environment.
- SAM.gov and EIA sources require API keys; supply them in the `.env` before running the pipeline.
- Several sources lack open APIs and will require manual CSV import, saved searches, or paid vendor API access.
- Production runs require a persistent scheduler or cron. The provided `scheduler.yaml` can be used with a workflow orchestrator (e.g., Airflow, Prefect, cronjobs) to trigger adapters around the clock.

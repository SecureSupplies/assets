# Phase 8 Government Biz

This package contains the Phase 8 Government Biz pipeline used by Secure Supplies to ingest, normalize, classify, score and route government sourcing data into the Zoho CRM.  It is structured as a Python package with clear separation between configuration, core processing logic, data adapters and CRM integration.

## Overview

The pipeline pulls data from a registry of federal, state and local feeds including SAM.gov Contract Opportunities, USAspending, GSA Auctions, EIA price data, National Weather Service alerts, OpenFEMA Disaster Declarations and other CSV imports.  Each record is normalized, deduped, classified into a product taxonomy (diesel, DEF, natural gas, propane, hydrogen, industrial gases, chemicals, rentals, auctions, emergency response, etc.), scored on both fast‑purchase urgency and long‑cycle opportunity potential, then routed to the appropriate Zoho CRM module.

## Structure

```
phase8-government-biz/
├── README.md                – this file
├── .env.example             – template for API keys and feature flags
├── requirements.txt         – Python dependencies
├── scheduler.yaml           – cron‑style job definitions
├── data/                    – JSON registries for sources, taxonomy and codes
├── core/                    – common processing modules
├── adapters/                – source‑specific clients
├── crm/                     – Zoho CRM integration
├── scripts/                 – command‑line entry points
├── docs/                    – documentation including deployment report
└── tests/                   – pytest unit tests
```

## Getting started

1.  Copy `.env.example` to `.env` and provide your API keys (SAM.gov, EIA, etc.) and Zoho OAuth credentials.  Set `PHASE8_ENABLE_CRM_WRITES=true` when you are ready to perform live CRM writes.
2.  Create a virtual environment and install dependencies:

    ```bash
    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  Run the test mode to pull a sample of records, classify, score, route and output CSVs without writing to CRM:

    ```bash
    python scripts/run_test_mode.py --limit 20
    ```

4.  When ready to push modules and fields into Zoho, run the deployment script in production mode:

    ```bash
    python scripts/deploy_zoho.py --production
    ```

See `docs/DEPLOYMENT_REPORT.md` for a complete description of the modules and deployment plan.

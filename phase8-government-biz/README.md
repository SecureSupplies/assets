# Phase 8 Government Biz

This directory contains the code, configuration, and data pipeline for Secure Supplies' Phase 8 Government Business initiative. The goal is to build a government sales intelligence and opportunity-generation system that captures, normalizes, scores, and routes government procurement data into Zoho CRM.

The pipeline connects to federal, state, local, tribal, and territorial data sources, including SAM.gov, USAspending, GSA auctions, state procurement portals, weather and disaster feeds, and pricing feeds. It classifies each record into product lanes (diesel, DEF, aviation fuel, marine fuel, gases, chemicals, tanks, rentals, auctions, etc.), scores opportunities, and maps them to custom Zoho CRM modules (GOV FAST PURCHASE POSTS, LEADS GOV, GOV DIRECT PO, GOV OPPORTUNITIES, etc.).

This codebase is organized into the following packages:

- **adapters/**: source-specific clients that fetch data from external APIs and feeds.
- **core/**: shared utilities for configuration, logging, normalization, deduplication, classification, scoring, routing, and error handling.
- **crm/**: integrations with Zoho CRM, including authentication, metadata inspection, module and field creation, upserts, bulk writes, and task creation.
- **data/**: static files such as state registries, product taxonomies, and code mappings.
- **tests/**: unit tests for normalization, deduplication, classification, scoring, and CRM mapping.

The top-level `.env.example` lists the environment variables needed to authenticate against Zoho and external APIs. Copy it to `.env` and populate the secrets before running any ingestion scripts.

See the deployment instructions in this README and the Phase 8 deployment plan for more details on creating Zoho CRM modules and running the data pipeline.

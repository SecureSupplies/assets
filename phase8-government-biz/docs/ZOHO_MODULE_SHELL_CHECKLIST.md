# Zoho Phase 8 Government Biz Module Shell Checklist

The **Phase 8 Government Biz** menu/tab group already exists. Create any missing custom-module shells inside that group in the exact order below. The field deployer resolves Zoho-generated API names from metadata, so the visible module and primary-field labels must match exactly.

| Order | Custom module label | Primary field label |
|---:|---|---|
| 1 | GOV FAST PURCHASE POSTS | Fast Purchase Name |
| 2 | LEADS GOV | Gov Lead Name |
| 3 | GOV DIRECT PO | Direct PO Target Name |
| 4 | GOV OPPORTUNITIES | Opportunity Name |
| 5 | GOV BUYERS | Buyer Name |
| 6 | GOV AWARDS | Award Name |
| 7 | GOV INCUMBENTS | Incumbent Vendor |
| 8 | GOV AUCTIONS | Auction Asset Name |
| 9 | GOV PRICE INTEL | Price Intel Name |
| 10 | GOV ROUTES | Route Name |
| 11 | GOV SUPPLIER CAPACITY | Supplier / Carrier Name |
| 12 | GOV COMPLIANCE | Compliance Item |
| 13 | GOV WATCHLIST | Watchlist Name |
| 14 | GOV SOURCE HEALTH | Source Name |
| 15 | GOV RAW DATA AUDIT | Raw Record Name |

## Required shell settings

- Module type: custom module.
- Visibility: enabled for the operating profiles that will use Phase 8.
- Menu/tab group: `Phase 8 Government Biz`.
- Sequence: use the order above; `GOV FAST PURCHASE POSTS` must be first.
- Primary field: single-line text using the exact label above.
- Do not manually invent module API names. Zoho generates them; the deployer retrieves them through module metadata.

## Audit and field deployment

From `phase8-government-biz/`:

```bash
python -m crm.deploy_phase8 --audit
python -m crm.deploy_phase8 --apply --dry-run
```

The audit must report:

```text
required_count: 15
found_count: 15
missing_count: 0
```

After reviewing `out/zoho_metadata_backup.json`, `out/zoho_phase8_deploy_result.json`, and `out/zoho_phase8_field_map.json`, execute the controlled field deployment:

```bash
PHASE8_DRY_RUN=false \
PHASE8_ENABLE_CRM_WRITES=true \
PHASE8_DEPLOY_CONFIRMATION=DEPLOY_PHASE8 \
python -m crm.deploy_phase8 --apply
```

Then run the production synchronization:

```bash
PHASE8_DRY_RUN=false \
PHASE8_ENABLE_CRM_WRITES=true \
PHASE8_DEPLOY_CONFIRMATION=DEPLOY_PHASE8 \
python run_pipeline.py --mode production --deploy-fields --limit-per-source 100
```

A live run remains blocked unless every write gate passes and the Zoho OAuth configuration is complete.

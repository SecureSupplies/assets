# CRM Market Workspaces & Sales Hotlists Feature Specification

This document serves as a detailed functional and technical specification for building a unified Market Workspaces and Sales Hotlists system within the Secure Supplies sales platform. The goal is to empower sales reps to access prospects by vertical market (e.g. Data Centers, Fleets) and operational state (e.g. Hot Prospects, New Prospects) without duplicating underlying CRM records. 

## 1. Objective

Implement a universal market-classification picker and dynamic workspaces that make existing Leads, Accounts, Contacts and Sites appear in the correct sales hotlists. Provide dedicated “My Market” views (My Fleets, My Data Centers, etc.) and operational queues (Hot Prospects, New Prospects, Active RFQs, No Next Action, Stale, Contract Renewals) for rapid execution.

## 2. Scope and Deliverables

1. **Audit & Architecture:**
   * Inspect the existing codebase to identify the framework, ORM and models for Leads, Accounts, Contacts and Sites.
   * Determine the authentication and permission model, existing grid/list components, card/detail components, lead-conversion workflow and any Zoho CRM integrations. Confirm the system of record (custom database vs. Zoho).

2. **Data Model Changes:**
   * Introduce a `market_verticals` table (or model) with stable slugs and parent relationships.
   * Introduce an `entity_market_memberships` table linking entity_type (lead/account/contact/site) to `market_vertical_id` with audit fields. Enforce uniqueness on entity_type + entity_id + market_vertical_id.
   * Add fields on Leads, Accounts, Contacts and Sites: `primary_market_id`, `prospect_lifecycle` (new/working/qualified/nurture/customer/disqualified), `prospect_heat` (cold/warm/hot/critical), `buyer_fit_score` (0–100), `owner_id`, `last_activity_at`, `next_action_at`, `last_verified_at`, `target_products`, `estimated_demand`, `demand_unit`, `buying_trigger`, `buying_deadline`, `contract_expiration`.

3. **Controlled Taxonomy:**
   * Seed 16 core markets: Fleets & Logistics, Data Centers, Factories & Manufacturing, Maritime & Ports, Government & Military, Power Plants, Cold Chain, Agriculture & Farms, Medical & Healthcare, Rail & Intermodal, Aviation & Airports, Mining & Quarry, Education & Institutional, Hospitality & Entertainment, Pharma & Biotech, Telecom & Digital Infrastructure.
   * Seed six additional priority markets: Construction & Equipment Rental, Utilities/Water & Wastewater, Waste & Environmental, Food Processing & Beverage, Oil/Gas/Pipeline, Transit & Bus.
   * Provide stable slugs for each market (e.g. `data-centers`), group them under parents where applicable and allow subverticals for further segmentation.

4. **Universal Picker Component:**
   * Build a reusable `MarketPicker` available on Lead, Account, Contact and Site cards.
   * Support selecting one Primary Market and multiple Additional Markets. The component should be searchable, grouped by parent, keyboard navigable and autosave using existing mutation patterns.
   * Provide a bulk-assignment UI so users can select multiple records in a grid to assign markets, set lifecycle or heat, assign owners and set next actions.

5. **Market Workspaces & Hotlists:**
   * Build a reusable `MarketWorkspace` component with dynamic routes such as `/sales/markets/:marketSlug` and hotlist routes `/sales/hotlists/hot`, `/sales/hotlists/new`, `/sales/hotlists/active-rfqs`, `/sales/hotlists/urgent`, `/sales/hotlists/no-next-action`, `/sales/hotlists/stale`, `/sales/hotlists/renewals`, `/sales/hotlists/unassigned`.
   * Support My/Team/All scope, record-type toggles (Leads/Accounts/Contacts/Sites), search, server-side filtering, sorting, pagination, saved filters, column preferences, export (when authorized) and side-drawer row opening.
   * Include columns for Primary Market, Additional Markets (badges), Prospect Heat, Prospect Lifecycle, Buyer Fit Score, Owner, Last Activity, Next Action and Last Verified.

6. **Sales Hotlist Rules:**
   * **New Prospects:** `prospect_lifecycle = new` and no completed outbound sales activity.
   * **Hot Prospects:** `prospect_heat ∈ {hot, critical}` or active RFQ, buying deadline, outage, incumbent failure or other triggers.
   * **Urgent Prospects:** Active emergency, storm, outage or commissioning triggers.
   * **No Next Action:** Active prospect with `next_action_at` null.
   * **Stale Prospects:** Active prospect with `last_activity_at` older than the configured threshold.
   * **Contract Renewals:** Based on `contract_expiration` approaching renewal threshold.
   * Hotlists should be independent from market classification; prospects can appear in multiple hotlists simultaneously.

7. **Lead Conversion Mapping:**
   * Preserve Primary Market, Additional Markets, Heat, Lifecycle, Buyer Fit Score, Owner, Product Fit, Estimated Demand and other metadata on lead conversion.
   * If a Site model exists, support inheritance of market memberships from Account/Site to Contacts and vice versa.

8. **Permissions & Audit:**
   * Respect existing row-level permissions; reps can only modify records they own or are authorized to edit.
   * Provide My/Team/All views based on role.
   * Admins manage taxonomy values and can inactivate markets (soft-delete). Taxonomy changes should be audited.
   * Audit all changes to market memberships, heat and lifecycle with timestamp and user.

9. **Migration Plan:**
   * Create reversible schema migrations to add the new tables and fields.
   * Map existing `Industry` or category values into the new taxonomy and generate an unmapped-value report for data cleanup.
   * Preserve existing IDs, ownership and activity history during migration.
   * Backfill market membership entries and run the migration idempotently. Roll out under a feature flag.

10. **Testing & Validation:**
   * Implement unit tests for new models, API endpoints, permissions, hotlist rules, lead-conversion mapping and migrations.
   * Add end-to-end tests covering: assigning markets to a lead, verifying appearance in multiple markets and hotlists, converting the lead and confirming classification preservation and removal behavior.

11. **Documentation & Guides:**
   * Provide configuration instructions, taxonomy-management steps and user guides for sales reps and administrators.
   * Document migration and rollback instructions.
   * Outline known limitations and recommended next enhancements (e.g. AI-driven buyer-fit scoring, marketing-automation integration).

## 3. Delivery & Acceptance Criteria

A successful implementation will:

1. Avoid creating duplicate Lead, Account, Contact or Site records.
2. Allow users to assign markets to leads/accounts/contacts/sites via the universal picker.
3. Display selected markets in grid columns and dynamic workspaces.
4. Present records in the appropriate Market workspace and Hotlists immediately after classification.
5. Preserve classifications during lead conversion.
6. Keep Hot and New hotlists independent of market selection.
7. Respect permissions and audit changes.
8. Ensure migrations are reversible and idempotent.
9. Pass all automated tests.

## 4. Next Steps

1. **Audit the existing repository:** Identify actual code structure, database schema and CRM integrations. Do not assume frameworks or technologies until verified. Produce an implementation plan based on the audit.
2. **Implement data models and migrations:** Following the data model section, add the new tables and fields with proper constraints and indexes.
3. **Implement the universal picker and market workspaces:** Build reusable front-end components using the project’s existing framework and patterns.
4. **Implement hotlist rules and automation:** Ensure proper filtering and classification logic for New, Hot, Urgent, No Next Action, Stale, Contract Renewals and other queues.
5. **Write tests and documentation:** Cover all critical scenarios and provide guidance for users and administrators.

This specification provides the detailed blueprint for the unified Market Workspaces and Sales Hotlists feature in Secure Supplies’ CRM platform.

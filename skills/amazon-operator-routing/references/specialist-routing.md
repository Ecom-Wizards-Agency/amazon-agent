# Specialist Routing

Use one main Amazon operator with specialist skills. The specialist is usually a skill, not a permanent subagent. Spawn temporary subagents only for parallel research, independent QA, or large multi-part work.

## Dispatch Table

| User intent | Specialist skill | Search priority |
| --- | --- | --- |
| Error, suppression, blocked workflow, Account Health | `amazon-troubleshooting` | Exact UI/error text in first-party docs, then internal notes, then MAG |
| Listing SEO, keyword workbook, Ranking Juice, Rufus | `amazon-seo` | Knowledge-base SEO skills, then Amazon rules, then MAG SEO SOPs |
| Variation, parentage, flat file, catalog contribution | `amazon-catalog` | Amazon Seller Help, then internal notes, then MAG catalog SOPs |
| Ads Console, campaigns, bids, budgets, Creator Connections | `amazon-ads` | Advertising Help After Login, Amazon Ads Help, internal strategy, MAG |
| Reports, SQP, business reports, dashboards, workbooks | `amazon-reporting` | Internal analytics skills for workbook logic, Amazon docs for report definitions, MAG |
| Weekly FBA Inventory Overview, reshipment planning | `amazon-inventory-planning` | Inventory planning skill reference, local planner code, Amazon report docs |
| Product Opportunity Explorer, OEI/POE, Niche Scout exports, image strategy, product strategy | `amazon-opportunity-explorer` | Knowledge-base `amazon-image-strategy` / `oei-product-strategy`, extractor workflow, Amazon docs, MAG |
| SOP bug report, SOP draft, or verified SOP correction | `amazon-sop-maintenance` | Source SOP/help file, current first-party docs/UI evidence, pCloud visual archive when visual proof is needed, `sop-updates/` for synced correction notes |
| FBA shipments, removals, AWD, inventory operations | `amazon-logistics` | Amazon Seller Help, internal notes, MAG logistics/catalog SOPs |
| Support case, buyer message, creator reply | `amazon-communications` | Amazon communication rules, Ads/Seller Help UI docs, internal templates, MAG |

## Efficient Search Rule

1. Classify the task.
2. Search the relevant index/helper with 1-3 targeted queries.
3. Open only the top 2-5 relevant files.
4. Search exact UI labels, error text, report names, ASIN/SKU/campaign IDs, or workflow terms before broader synonyms.
5. Record the files used in the final operator note.

## Source Ladder

For current Amazon rules, UI, policies, eligibility, error text, and report definitions:

1. Amazon first-party docs.
2. Ecom Wizards/client context.
3. MAG SOPs.

For Ecom Wizards methodology or generated outputs:

1. Knowledge-base skills and client notes.
2. Amazon first-party docs for constraints and compliance.
3. MAG SOPs for practical execution.

For explicit MAG procedure requests:

1. MAG SOPs.
2. Amazon first-party docs to verify anything current or risky.
3. Client/internal notes when relevant.

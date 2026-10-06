# Symptom routing

Use this table after capturing the exact error text. It names where the answer most likely lives, which skill owns the fix, and which libraries to search in order: the knowledge topic first, then the first-party library, then the MAG SOP category.

Knowledge topics are the folders under `knowledge/`. MAG SOP categories are the folders under `MAG SOPs/` plus the title prefix used in `MAG SOPs/_index/sop-index.json`.

| Symptom family | Knowledge topic | Owning skill | First-party library | MAG SOP category |
|---|---|---|---|---|
| Listing suppressed or removed | catalog; compliance when a policy is cited | `amazon-catalog`; `amazon-regulated-product-appeals` for serious regulated-product suppressions | Amazon Seller Help | `catalog/` Troubleshooting SOP (search suppression), Catalog SOP (suppressed listing report) |
| Compliance document request | compliance | `amazon-catalog` for a routine upload; `amazon-regulated-product-appeals` for an appeal pack | Amazon Seller Help | `catalog/` Catalog SOP (product document upload, letter of compliance) |
| Hazmat or SDS | compliance; logistics when it blocks an inbound | `amazon-catalog`; `amazon-logistics` for blocked shipments | Amazon Seller Help | `catalog/` Troubleshooting SOP (SDS upload and hazmat issues) |
| Inbound shipment defect | logistics | `amazon-logistics` | Amazon Seller Help | `catalog/` Logistics SOP and Catalog SOP (shipment reconciliation, inbound performance) |
| Stranded or reserved inventory | logistics | `amazon-logistics` | Amazon Seller Help | `catalog/` Troubleshooting SOP (stranded inventory), Logistics SOP (reserved inventory) |
| Capacity limit | logistics | `amazon-fba-inventory-planning`; `amazon-logistics` to act | Amazon Seller Help | `catalog/` Catalog SOP (FBA storage capacity limits) |
| Removal or disposal | logistics | `amazon-logistics` | Amazon Seller Help | `catalog/` Catalog SOP and Logistics SOP (removal orders and reports) |
| Variation or parentage | catalog | `amazon-catalog` | Amazon Seller Help | `catalog/` Catalog SOP (variations, parentage) |
| Brand Registry role or error | brand-registry | `amazon-catalog` | Amazon Seller Help | `catalog/` Brand Registry SOP |
| Hijacker | brand-registry | `amazon-catalog`; `amazon-communications` for the case | Amazon Seller Help | `catalog/` Catalog SOP (remove unauthorized sellers) |
| Flat file error | catalog | `amazon-catalog`; `amazon-flatfilepro` for FlatFilePro workbooks | Amazon Seller Help | `catalog/` Catalog SOP (full and partial flat-file updates) |
| Image or A+ rejection | catalog; brand-registry for A+ | `amazon-catalog`; `amazon-image-production` for new artwork | Amazon Seller Help | `catalog/` Catalog SOP (images, A+ eligibility); `design/` |
| Buy Box or pricing health | catalog | `amazon-catalog` | Amazon Seller Help | `catalog/` Catalog SOP (Buy Box percentage, hidden price, pricing rules) |
| FBM settings or late shipment | logistics; account-health when a metric is at risk | `amazon-logistics`; `amazon-account-health-check` for the metric | Amazon Seller Help | `catalog/` Catalog SOP and Logistics SOP (FBM late shipment, shipping templates, handling capacity) |
| Account verification or permissions | account-health | `amazon-troubleshooting`; `amazon-account-health-check` for Account Health rows | Amazon Seller Help | `general/` General SOP |
| Support case or SAS escalation | support-cases | `amazon-communications` | Amazon Seller Help | `catalog/` Troubleshooting SOP and Catalog SOP (case creation, Brand Registry ticket cases) |
| Ads delivery or eligibility | ads | `amazon-ads-console` | Advertising Help After Login, then Amazon Ads Help | `amazon-advertising/` Advertising SOP |
| Ads bulk job | ads | `amazon-sponsored-products-bulk-files` for the file; `amazon-ads-console` for the upload result | Amazon Ads Help, then Advertising Help After Login | `amazon-advertising/` Advertising SOP (bulk operations) |
| Report missing | reporting | `amazon-reporting` | Amazon Seller Help; Advertising Help After Login for ads reports | `catalog/` Catalog SOP (report downloads) |

When no row fits, search `--library all` and classify the symptom with step 3 of the skill.

## Error-text search recipe

1. Search the verbatim notice first, in quotes as one argument: `python3 tools/search_amazon_libraries.py "<verbatim notice or code>" --library kb --limit 5`. Units store notices in `error_text`, and the helper boosts exact hits.
2. Repeat the verbatim search with `--library seller` or `--library ads` for the first-party page.
3. If nothing matches, strip IDs, SKUs, dates and amounts and search three to five simplified keywords, first `--library kb`, then the first-party library, then `--library mag`.
4. Check `--library drafts` last for recent internal learnings.

## Stating the label

Every answer that uses a unit states its label in the reply, for example "Knowledge unit, draft, unverified" or "Knowledge unit, reviewed, verified 14.09.2026 (live-ui)". A draft or unverified unit is a lead to confirm against the first-party page or the live UI, not a rule. When the unit and an Amazon page disagree, say so and follow the authority order in `docs/knowledge-library.md`.

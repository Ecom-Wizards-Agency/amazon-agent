# Data source: AdLabs MCP (managed clients)

Loaded at step 2 when the brand resolves to an AdLabs profile. Every Lens A row must still be
filled from here. "Not available on this path" is only an acceptable answer for margin.


**No downloads. No handoff. Do not ask for exports.** Every metric comes live from the AdLabs
MCP and rank comes from the DataDive MCP. The only external input is human context.

Read the audit methodology once per session: `read_resource(adlabs://guides/account_audit)`.
Read each target profile's `adlabs://profiles/<slug>` resource for profile_id, Target ACOS and
Target Total ACOS.

What is available, verified against the filter schemas:

- **Per-ASIN, query-level SQP is available.** The `search_query` entity exposes `PRODUCT_ASIN`
  and `PRODUCT_PARENT_ASIN` plus `ASIN_IMPRESSION_SHARE`, `ASIN_CLICK_SHARE`,
  `ASIN_CART_ADD_SHARE`, `ASIN_PURCHASE_SHARE`, `ASIN_CTR` and `ASIN_CONVERSION_RATE`, each
  beside its `TOTAL_*` market counterpart. The CTR and CVR gaps against market are therefore
  free. It is weekly, Sunday to Saturday, snapped, and not campaign-linked.
- **The Business Report is available** through the Seller Central SP-API link on the `product`
  entity: sessions `ORGANIC_TRAFFIC` / `TOTAL_CLICKS`, page views `TOTAL_VIEWS`, unit-session
  rate `UPS` / `UPPW`, session CVR `TCVR`, Buy Box `FEATURED_OFFER_PERCENT` / `BUY_BOX_VIEWS`,
  sales `TOTAL_SALES` / `ORGANIC_SALES` / `TOTAL_UNITS`, plus `ACOTS` and `ACOTS_TO_TARGET`.
- **Stock is available and is often the real story**: `out_of_stock_days`, `scarce_stock_days`,
  `days_of_cover`, `fulfillable_units`, `availability_trend`, `best_seller_rank`, and the
  `PRODUCT_HISTORICAL_AVAILABILITY` / `PRODUCT_AVAILABILITY_CHANGE` filters.
- **The one real gap is margin.** `PRODUCT_PROFIT`, `PRODUCT_COGS` and `PRODUCT_PROFIT_MARGIN`
  exist only when profit tracking is enabled on the profile, and never break out FBM against
  FBA fees. For a confirmed break-even ACOS use the client's Sellerboard P&L. Break-even =
  margin % + Real ACOS %, cross-checkable as (net profit + ad spend) / sales.

## Mechanics learned the hard way

**MCP path.** Read the aggregate reference first. `query` is SELECT-only, with no GROUP BY, so use
`group_by_column`, which recalculates derived metrics. Match-type casing differs between audit-summary
labels and row filters, so use `LOWER(col) LIKE` when a literal returns zero rows. Placement modifiers
can multiply a low base bid several-fold, so when a target shows a low bid but a high CPC, fix the
modifier or the base bid, not the symptom. `organic_sales` on the product entity is derived from
`total_sales`; never sum it with ad sales. The `search_query` entity has **no date column**, so a
single range pull aggregates the weeks: pull once per week whenever week-over-week movement is the
point, which is what `/supa` does, and `COMPARE_DATE` is unsupported there. The `campaign` entity
returns only ENABLED and PAUSED, **never ARCHIVED**, so archived spend is invisible: say so rather
than reconciling to it. **Delta conventions differ**: the profile entity returns `*_delta_percent` as
a ratio while the product aggregate returns a true percent. `analyze(brand_spend_leak_detection)`
substring-matches `brand_name`, so it silently misses misspellings that do not contain the root; scan
variants manually before trusting its total. Big Rank Radar payloads overflow, so parse the saved
tool-result file with python.

## Completeness statement

On this path there is no `--validate`, so state the equivalent explicitly: which Lens A rows
produced numbers, which did not, and why.

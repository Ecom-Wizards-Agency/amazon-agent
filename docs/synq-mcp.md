# SYNQ MCP: routing contract

Status: current from 04.11.2026. This file replaces the source contract named by the 02.10 decision, which never reached this repo. Raise any difference from an older local copy with the operator; do not merge it in silently.

## Purpose

SYNQ (`app.wearesynq.com`) is the Amazon Ads data source and the place where PPC changes happen, for every client in SYNQ. AdLabs is retired except for the AdLabs carve-out account (US and CA); see "Which route a client takes". This file says which SYNQ tool answers which question, what SYNQ cannot answer and where that data comes from instead, and how changes are made. Every skill and tool that reads ads data follows it.

- MCP server: `synq`, `https://app.wearesynq.com/mcp`, OAuth sign-in in the MCP client. Never save a SYNQ credential in this repo, notes or chat.
- The MCP is read-only and free: no credits, no approval needed for reads.
- Writes happen only in the SYNQ web app (see Web-app writes).
- Saved responses become consumer files through `tools/synq/convert.py` (`tools/synq/README.md`).

## Which route a client takes

Check in this order:

1. **AdLabs carve-out.** The AdLabs carve-out account is the one brand whose US and CA profiles the AdLabs MCP still lists. The team vault's 03.11.2026 AdLabs decision record (`Decisions/2026-11-03-adlabs-retired-synq-primary.md`) names it. It follows the "AdLabs carve-out only" section below.
2. **SYNQ.** A client that `list_clients` lists, with its catalog confirmed (Start of every run), follows the rest of this file.
3. **Not yet in SYNQ.** A client that `list_clients` does not list is not yet in SYNQ. Four clients were being onboarded on 03.11.2026; the same decision record names them. They follow the "Clients not yet in SYNQ" section below.

Client names stay out of this repo. Resolve them from the decision record and the client profile.

## Start of every run

1. **`list_clients`.** Skip every row with `is_demo: true`. Note `lifecycle_status`. An `offboarding` client is still readable: it is the normal case for `amazon-client-offboarding` and not a normal run for any other workflow. A `purged` client's data is gone; take its ads data from the Ads console and bulk downloads.
2. **Confirm the client.** Match at least one SKU or product title from `get_catalog` against the client profile (`Amazon Ops.md`) or the listing. A SYNQ client name alone does not prove whose seller data it is.
3. **`get_sync_status`** for the client and marketplace. Report `last_sync_status` and `updated_at` in the operator note. Anything other than `success`, or an `updated_at` older than a day, is a data-quality finding stated before any number.
4. Pass the same `client_id` and `marketplace` on every call of the run. `convert.py` refuses inputs that mix clients or marketplaces.

## Tool map

All tools take `client_id`; most take `marketplace`. All cap at `limit` (see Row caps).

| Tool | Answers |
|---|---|
| `list_clients` | Which SYNQ clients exist (`client_id`, `client_name`, `is_demo`, `lifecycle_status`). |
| `get_sync_status` | Whether the client's data synced and when (`last_sync_status`, `updated_at`). |
| `get_metrics` | Ads metrics for a rolling 7d, 14d, 30d or 60d window, per `entity_type`: campaign, ad_group, target, keyword, product_ad, asin, search_term, placement. Impressions, clicks, cost, sales, orders, units, ACOS, CPC, CTR, CVR, `keyword_text`. |
| `get_daily_metrics` | The same metrics for an exact date range, raw daily rows or grouped (`group_by` total, campaign, ad_group, target, asin, date). Keywords appear as `target` rows with `keyword_text`. |
| `get_search_terms` | Search-term rows per day, term and keyword: `campaign_name`, `ad_group_name`, `keyword_id`, `keyword_text`, `match_type`, metrics. Harvest, negate, waste and brand-leak input. |
| `get_spend_pacing` | Month-to-date spend against the monthly target, by ad product, with projected month end. |
| `get_campaign_changes` | Campaign state changes (enabled, paused, archived), also those made outside SYNQ. History from 12.06.2026. |
| `get_ads_change_log` | Changes SYNQ made: `action_type`, `entity_ids`, success and failure counts, `source_module` (BidOptimizer, CampaignManager, change_history_revert, ...), `user_email` (`system@synq.app` is automation), `batch_id`. |
| `get_entity_changes` | Old and new values per entity and attribute (bid, daily_budget, state, placement modifiers), with `source` app or external. History from 20.08.2026. |
| `list_campaigns` | Campaign id, name, ad product, state. No budget, bid strategy or portfolio. |
| `get_organic_ranks` | Organic rank series by keyword (`provider` helium10, soldscope or datadive). Cross-check only. |
| `get_organic_rank_summary` | Rank summary over the same providers. Cross-check only. |
| `get_sqp_data` | Search Query Performance per ASIN or brand, WEEK, MONTH or QUARTER, with the market totals. |
| `get_sqp_alerts` | SYNQ's SQP alerts. Read the tool description for its fields; not captured on 04.11.2026. |
| `get_sales_traffic_daily` | Sales and Traffic per day, ASIN, parent or total: ordered product sales, units, sessions, page views, buy box. |
| `get_inventory` | Current stock and listing state per SKU, or daily history with `history: true` (180-day retention). |
| `get_catalog` | Per SKU: ACOS and TACOS goals, COGS and margin, days of cover (`days_inventory`), velocity, assigned strategy, campaign-role multipliers, FBA stock, bullets. |
| `get_keepa_data` | Keepa price and rank history. Read the tool description; not captured on 04.11.2026. |
| `list_market_intel_groups` | The client's market-intelligence groups. Not captured on 04.11.2026. |
| `get_market_intel_group_members` | The ASINs in one market-intelligence group. Not captured on 04.11.2026. |
| `get_market_intel_alerts` | Alerts raised for a market-intelligence group. Not captured on 04.11.2026. |

Placement metrics: `get_metrics` or `get_daily_metrics` with `entity_type: placement`; one row per campaign and placement, `entity_id` `<campaign_id>::Top of Search on-Amazon` and similar.

## Row caps

- Every tool returns at most `limit` rows (default 50, maximum 2000).
- When rows were cut, the response starts with a note: "ROW LIMIT REACHED" (the limit was hit) or "TRUNCATED" (grouped results, "showing the top N of M"; sums over those rows are not account totals).
- **Save every response with its note:** `{"note": <note text or null>, "rows": [...]}`.
- **Never present a cut list as complete.** Narrow the call, raise the limit, or use `group_by: total` for an exact sum. `get_daily_metrics` narrows only by `entity_type`, `group_by`, the date range and `limit`; it takes no `campaign_id`, so filter campaigns locally after a complete pull. `get_search_terms` also takes `ad_product` and `campaign_id`.
- **Before/after comparisons:** pull each window separately and join by id, so an entity that fell to zero still shows.
- `convert.py` exits 2 on a cut input unless `--allow-truncated` is passed for a knowingly partial look.

## Lag and attribution

- Sales and Traffic (`get_sales_traffic_daily`) runs 2 to 3 days behind the ads data. TACOS and total-sales figures for the last 3 days are provisional; say so or end the window earlier.
- Ads `sales` attribution window is unconfirmed; the question to SYNQ is open. Label it "SYNQ-reported sales" until SYNQ answers.
- Some `get_metrics` rows carry an older `computed_at` (inactive entities). Use `get_daily_metrics` when the exact window matters.

## Gaps and where the data comes from instead

| Gap in the SYNQ MCP | Use instead |
|---|---|
| Top-of-search impression share, current bids and budgets, budget-capped days, runner membership, flags and recommendations | Ads console target report or bulk download, or the SYNQ Bid Optimizer and Exposure pages, read-only in the browser |
| Match type on metric rows | join to `get_search_terms` (`keyword_id`, `match_type`); `convert.py entities` does it |
| Days of cover | `get_catalog.days_inventory` |
| Out-of-stock days | derived from `get_inventory` history; `convert.py stock` does it |
| Margin | `get_catalog.cogs` when set, else Sellerboard |
| Organic rank | the SoldScope rank tracker (`tools/soldscope/ranks.py`) stays primary; `get_organic_ranks` only cross-checks |
| P&L | Sellerboard |
| Current bid or budget of an entity that never changed | `get_entity_changes` covers changed entities only; read the bulk download or console |
| SQP parity | Until one ASIN-week of SYNQ SQP matches the Seller Central download, the Seller Central SQP fetcher stays the fallback |

## Adapters

`tools/synq/convert.py` turns saved responses into the files the consumers read: `sqp` (SUPA SQP CSVs), `search-terms` (SUPA PPC CSVs and the weekly brief's search-term JSON), `stock` (SUPA stock CSVs), `entities` (`run_weekly.py --ads-json` rows) and `totals` (`run_monitor.py --ads-json` figures). Each writes a receipt with input hashes and row counts. Details: `tools/synq/README.md`.

## Web-app writes

The SYNQ MCP cannot write. Every change is made in the SYNQ web app in the attended operator browser: `node tools/browserctl/browserctl.mjs run --session operator -- <command>` (9222). Grimoire and scheduled runs never write; they prepare proposals.

**Modules.**
- **Bid Optimizer runners** own routine bidding: ACOS or TACOS goals set in Catalog Manager, campaign roles, exclusions.
- **Campaign Manager:** one-off bids, budgets, placement modifiers, negative lists.
- **Keyword Harvester** and **Search Term Negator:** harvests and negatives.
- **New campaign builds** stay bulk files through `amazon-sponsored-products-bulk-files` (file only, paused).

**Gate for every change: exact-action approval.** Proposal, then operator approval of that exact action, then snapshot, then the web-app change, then readback.
- The approval names the client, marketplace, exact entities, old and new values, and the expected result. An earlier general approval does not cover a new batch.
- Snapshot and tag the batch first with `tools/amazon-ppc-management/batches.py snapshot` (rows JSON with old and new values, tag, lever, note).
- Read it back after the change with `get_ads_change_log` (record the `batch_id`), `get_entity_changes` (old and new values) and `get_campaign_changes` (state).
- Rollback: `batches.py revert --client <slug> --tag <tag>` gives the old values; the revert itself passes the same gate.
- Procedure: `skills/amazon-ppc-weekly-management/SKILL.md`. Rights: rows `synq.read` and `synq.web-execute` in `docs/rights/README.md`.

**One-writer rule.** A SYNQ runner and any other bid writer (AdLabs optimizer or dayparting, manual pushes) never share a campaign. A one-off bid, budget or placement push goes only to a campaign no runner writes, or to a runner exclusion. Runner membership is a SYNQ MCP gap, so the required check before any one-off bid or budget push on a campaign is a read-only look at the SYNQ Bid Optimizer page in the attended operator browser: the campaign is in no runner, or is excluded from its runner. Record what the page showed in the action log. `get_ads_change_log` with `source_module: BidOptimizer` is supporting evidence only: it has no campaign filter (match the campaign in `entity_ids` yourself), and a runner that changed nothing in the window leaves no row, so an empty result never proves a campaign is outside every runner.

## AdLabs carve-out only

The AdLabs carve-out account (US and CA) stays fully on AdLabs until it moves to SYNQ: optimizer, harvest, opt-groups and live AdLabs dayparting schedules. Every other client is on SYNQ or on the fallback below.

- Reads and writes go through AdLabs, under rows `adlabs.read` and `adlabs.write` in `docs/rights/README.md`. Procedure: `skills/amazon-ppc-weekly-management/references/adlabs-carve-out.md`; audit source: `skills/amazon-audit/references/source-adlabs.md`.
- **Dayparting overwrite trap.** While an AdLabs dayparting schedule is assigned, it multiplies its stored base bid every hour. A bid edited in the Ads console, a bulk file or any tool other than AdLabs on an assigned campaign is overwritten at the next run. Make the carve-out account's bid changes in AdLabs, and read the schedule assignment before proposing any bid change.
- A SYNQ runner never takes a carve-out campaign while an AdLabs optimizer group or dayparting schedule still covers it.
- `tools/amazon-dayparting/` is retired; it stays only for reading old analyses.
- AMC runs only through AdLabs, which now covers only the AdLabs carve-out account; the replacement route is an open decision (03.11.2026).

## Clients not yet in SYNQ

Clients not yet in SYNQ (see "Which route a client takes") are being onboarded. Until a client appears in `list_clients` with its catalog confirmed, its ads data comes from the Ads console, bulk downloads and Seller Central reports. The audit's bulk path (`skills/amazon-audit/references/source-bulk.md`) is allowed for them. Prospects follow the same path. Once a client is in SYNQ, this fallback ends for it.

## Grimoire

Grimoire uses SYNQ read-only: free reads in mention-pass, under the same start-of-run, row-cap and lag rules. It never writes in SYNQ or AdLabs and never drives the SYNQ web app. Its AdLabs MCP entry is disabled, so ads questions about the AdLabs carve-out account go to an attended run. Its rights stay as recorded in `docs/rights/README.md`.

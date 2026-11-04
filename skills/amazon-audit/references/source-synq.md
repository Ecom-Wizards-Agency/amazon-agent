# Data source: SYNQ MCP (managed clients)

Loaded at step 2 for `monthly` and `actions` when the brand resolves to a SYNQ client. Every Lens A
row must still be filled from here or from the named gap source. "Not available on this path" is
only an acceptable answer for margin.

The AdLabs carve-out account (US and CA) loads `references/source-adlabs.md` instead. A client not
yet in SYNQ (`list_clients` does not list it; see `docs/synq-mcp.md`) loads
`references/source-bulk.md`. The source contract for every SYNQ reader is `docs/synq-mcp.md`; this
file adds what the audit needs on top of it.

The SYNQ MCP is read-only and free: no credits, no run approval. This skill never writes, in the
MCP or in the SYNQ web app. Rank comes from the SoldScope rank tracker over the SoldScope MCP.

## Startup

1. `list_clients`. Skip every row with `is_demo: true` and every `lifecycle_status` other than
   `active`. Match the brand to one `client_id`.
2. Confirm the client with `get_catalog(client_id, marketplace, limit: 2000)`: at least one SKU or
   `product_title` must match the brand's known listings. A client name alone does not prove whose
   seller data it is.
3. `get_sync_status(client_id, marketplace)` for every marketplace in scope. Require
   `last_sync_status: success` and an `updated_at` that covers the end of both windows. Otherwise
   stop and report the blocker; a stale sync explains a "drop" before any ad does.

## Windows

- Use completed, equal-length windows and exclude the current day. Default: the last 30 completed
  days against the 30 before them.
- Pull every comparison window with `get_daily_metrics(date_from, date_to)`. The `get_metrics`
  timeframes (`7d`, `14d`, `30d`, `60d`) are rolling and carry no prior window, so use them only for
  a current-state snapshot, never for a before/after claim.
- Sales and Traffic (`get_sales_traffic_daily`) runs 2 to 3 days behind ads data. Any row that
  joins ads to Sales and Traffic (A2, A13) ends both windows at the last Sales and Traffic date.
- Label ads sales "SYNQ-reported attributed sales". The attribution window is not yet confirmed by
  SYNQ, so never call it 7-day or 14-day.

## Row caps

- Every tool caps at `limit` (default 50, max 2000). A cut response starts with a "ROW LIMIT
  REACHED" or "TRUNCATED" note before the JSON.
- Save every response as `{"note": <note text or null>, "rows": [...]}`, so the note travels with
  the rows into the evidence folder.
- A response with a note is not complete. Narrow the call, raise `limit`, or use `group_by: total`
  for an exact sum. `get_daily_metrics` narrows only by `entity_type`, `group_by`, a shorter date
  range and `limit`; it takes no `campaign_id`, so filter campaigns locally after a complete pull.
  `get_search_terms` also takes `ad_product` and `campaign_id`. Sums over truncated grouped rows are
  not account totals.
- Reconcile campaign sums to the `group_by: total` row for the same window before grading. A gap
  means a cut list or a missing channel; resolve it before writing.

## Window join

- Pull each window separately and join by `entity_id` (or `campaign_id`), so an entity that fell to
  zero still shows with its prior value and a current zero.
- Never join two separately capped top-N lists: the entity that dropped out of the current top N
  is exactly the one the diagnosis needs. Pull until neither window carries a note.
- A missing row means no delivery or unknown, never a pause. Confirm state with
  `get_campaign_changes` before writing that anything was paused.

## Sum, then recompute

Sum the base metrics (impressions, clicks, cost, sales, orders, units) and recompute CTR, CPC,
CVR, AOV and ACOS from the sums. Never average a row's `acos`, `ctr` or `cvr`. Unit trap: metric
`acos`, `ctr` and `cvr` are 0-1 ratios, `get_catalog.acos_target` is a percent (45 means 45%), and
`target_tacos` is a ratio (0.2 means 20%).

## Per-step map

| Audit step | SYNQ tool and parameters | Notes |
|---|---|---|
| Stage 2 startup | `list_clients`, `get_catalog`, `get_sync_status` | As in Startup above |
| Section 1 learnings | `get_ads_change_log`, `get_entity_changes`, `get_campaign_changes` over both windows; `get_catalog` goals | Replaces AdLabs apply history and profile memory |
| A1 stock and offline days | `get_inventory(asin, history: true, date_from, date_to)`; current `get_inventory` for `fulfillable_quantity`; `get_catalog.days_inventory` for days of cover | Out-of-stock days are derived, see Stock |
| A2 Buy Box, weekly then daily | `get_sales_traffic_daily(group_by: asin)` per week, then `group_by: date` for the moving week (`buy_box_percentage`, `buy_box_pct_weighted`); `get_inventory` `is_buy_box_winner`, `buy_box_price` against `current_price` | Seller count is not in SYNQ; read the retail offer listing when the Buy Box moved |
| A3 organic rank and cost-per-rank | SoldScope rank tracker (`tools/soldscope/ranks.py`) | `get_organic_ranks(provider: soldscope)` is a cross-check only |
| A4 SQP demand and shares | `get_sqp_data(period_from, period_to, report_period: WEEK, limit: 2000)`, one week per call | See SQP |
| A5 funnel tripwire | the A4 rows: `clicks`, `cart_adds`, `purchases` over `total_clicks`, `total_cart_adds`, `total_purchases` | Same queries, same weeks |
| A6 demand trajectory | SoldScope keyword research plus the weekly `get_sqp_data` series (`search_query_volume`) | |
| A7 channel mix and placement | `get_daily_metrics(entity_type: placement)` per window; `get_daily_metrics(group_by: campaign)` joined to `list_campaigns.ad_product` | Current placement modifiers are a gap |
| A8 search-term waste and harvest | `get_search_terms(date_from, date_to, ad_product, campaign_id, limit: 2000)` per window; `get_daily_metrics(entity_type: target, group_by: target)` | aCTC and CVR benchmarks computed from the account totals |
| A9 structure, enabled and spending | `list_campaigns(state: ENABLED)` plus target metrics per window; match type from `get_search_terms` (`keyword_id`, `match_type`) | Negatives and ad group composition come from the bulk download |
| A10 bid categories and budget caps | `get_spend_pacing` for month pacing | Budgets, current bids and capped days are gaps |
| A11 missing channels | `list_campaigns.ad_product` (SP, SB, SD) | DSP is not visible in SYNQ; say so |
| A12 brand leak | `get_search_terms` plus `get_sqp_data`, matched on brand tokens locally | No built-in leak tool; scan misspellings yourself |
| A13 TACOS | `get_daily_metrics(group_by: total)` cost over `get_sales_traffic_daily(group_by: total)` `ordered_product_sales`, both windows ending at the Sales and Traffic date; per product `entity_type: asin, group_by: asin` against `get_sales_traffic_daily(group_by: asin)` | Grade against `get_catalog.target_tacos` |
| Falling-sales and ACOS branch, step 0 | `get_sync_status` | Freshness before any decomposition |
| Branch, size and shape | `get_daily_metrics(group_by: total)` per window | |
| Branch, timing | `get_daily_metrics(group_by: date)` over both windows | Sustained, single-day, or a base effect |
| Branch, contributors | `get_daily_metrics(group_by: campaign)` per window joined to `list_campaigns`; then `entity_type: target`; `get_search_terms`; `entity_type: placement` | Ranked by absolute delta |
| Branch, step 6 change log | `get_ads_change_log`, `get_entity_changes`, `get_campaign_changes`; Bid Optimizer page read-only | Replaces flags and recommendations |

## SQP

- `get_sqp_data` weeks run Sunday to Saturday (`period_start`, `period_end`). Pull one week per call
  when week-over-week movement matters, and save each week.
- The market columns (`search_query_volume`, `total_*`) repeat on every ASIN row for the same query
  and period. Take them once per query and period; sum only the ASIN columns across ASINs. For brand
  totals use `brand_level: true`.
- There are no comparison columns. Compute every delta from two pulled weeks.
- The Seller Central SQP fetcher stays the cross-check until the SYNQ SQP parity check passes. For the
  SUPA CSV shape, convert saved pages with `tools/synq/convert.py sqp`.

## Stock

- `get_inventory(history: true)` keeps 180 days of daily snapshots.
- SKUs that share an `fnsku` share one stock pool, repeated on each row. Count one row per `fnsku`,
  plus each row without one.
- An ASIN's out-of-stock day is a `snapshot_date` where its `fulfillable_quantity`, summed with
  each `fnsku` pool counted once, is 0. Listing state does not count. This matches SUPA and
  `tools/synq/convert.py stock`.
- Report unbuyable days separately as a listing-health signal: a `snapshot_date` where
  `listing_is_buyable` is false while the pool still has fulfillable stock. They are not
  out-of-stock days.
- Days of cover is `get_catalog.days_inventory`.
- Check units before trusting listing state: a listing can read buyable with nothing fulfillable.

## Change history and runner status

These replace the flag and recommendation reads of other tools. They describe what changed and who
changed it; they never prescribe.

- `get_ads_change_log`: one row per batch, with `action_type`, `source_module` (`BidOptimizer`,
  `CampaignManager`, ...), `user_email` (`system@synq.app` is automation) and `batch_id`. Match a
  batch to `_local/ppc-manage/<client>/batches/<tag>.json` through its tag before attributing a move
  to it.
- `get_entity_changes`: old and new values per entity and attribute (`bid`, `daily_budget`, `state`,
  `PLACEMENT_TOP`, ...). `source: external` marks an edit made outside SYNQ; on a campaign a runner
  owns, that is a one-writer-rule finding. History starts on 20.08.2026.
- `get_campaign_changes`: state transitions, including those made outside SYNQ. History starts on
  12.06.2026.
- Goals and roles: `get_catalog` `acos_target`, `target_tacos`, `assigned_strategy_id` and the
  campaign-role multipliers `rnk_multiplier`, `rsc_multiplier`, `coq_multiplier`.
- Runner membership, overdue runners and role gaps are not in the MCP. Read them from the SYNQ Bid
  Optimizer page in the attended operator browser, read-only, and screenshot the state you cite.

## Gaps and their sources

Gap reads fill the named rows only. They are not a fallback for the posture.

| Gap | Use instead |
|---|---|
| Top-of-search impression share, current bids and budgets, budget-capped days, runner membership, flags and recommendations | Ads console target report or bulk download, or the SYNQ Bid Optimizer and Exposure pages, read-only in the browser |
| Match type on metric rows | join to `get_search_terms` (`keyword_id`, `match_type`) |
| Days of cover | `get_catalog.days_inventory` |
| Out-of-stock days | derived from `get_inventory` history |
| Margin | `get_catalog.cogs` when set, else Sellerboard |
| Organic rank | the SoldScope rank tracker (`tools/soldscope/ranks.py`) stays primary |

## Mechanics learned the hard way

- Placement rows carry `entity_id` `<campaign_id>::Top of Search on-Amazon` (or `::Detail Page
  on-Amazon` and the other placements) and a null `ad_group_id`. Never sum placement rows with target
  rows; they re-slice the same traffic.
- Metric rows carry no campaign name: join `list_campaigns` on `campaign_id`. They carry no match
  type either: join `get_search_terms` on `keyword_id`.
- `get_daily_metrics` with `entity_type: keyword` can return nothing. Use `entity_type: target`,
  whose rows carry `keyword_text`.
- `get_search_terms` returns one row per day per search term per keyword, so a 30-day pull hits the
  cap fast. Split by `campaign_id` or `ad_product`, or shorten the range, then sum locally.
- `cost` carries four decimals. Round only in the deliverable.
- Rows with an old `computed_at` belong to inactive entities; keep them out of current-state reads.
- `get_sales_traffic_daily` has returned a 502 once; retry one time, then report it.

## Completeness statement

On this path there is no `--validate`, so state the equivalent explicitly: which Lens A rows
produced numbers, which came from a gap source and which source, which pulls were truncated and how
each was resolved, and the last ads and Sales and Traffic dates the windows end on.

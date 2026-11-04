# SYNQ adapters

SYNQ is the Amazon Ads data source for every client in SYNQ. The agent calls the `synq` MCP, saves every response in the run folder, and runs `tools/synq/convert.py`. The adapter reads saved files only; it never calls SYNQ. The routing contract (which tool answers what, gaps, writes, the AdLabs carve-out account) is `docs/synq-mcp.md`.

`convert.py` writes the shapes the consumers already read, so a consumer only changes its input path:

| Subcommand | Reads (saved SYNQ responses) | Writes | Consumer |
|---|---|---|---|
| `sqp` | `get_sqp_data`, per-ASIN, `report_period: WEEK` | `sqp_<period_start>.csv` | `tools/sqp-supa/build_supa_workbook.py` (`inputs.sqp_csvs`) |
| `search-terms` | `get_search_terms` | `search_terms_<week_start>.csv` and `searchterms_weekly_<week_end>.json` | SUPA (`inputs.search_term_csvs`); the weekly brief's search-term file |
| `stock` | `get_inventory` with `history: true` | `stock_<week_start>.csv` | SUPA (`inputs.stock_csvs`) |
| `entities` | `get_metrics` or `get_daily_metrics`, `list_campaigns`, optionally `get_search_terms` | one entity-rows JSON | `tools/amazon-ads-monitor/run_weekly.py`, the PPC weekly checker |
| `totals` | `get_daily_metrics` `group_by: total`, optionally `get_sales_traffic_daily` `group_by: total` | one totals JSON | `tools/amazon-ads-monitor/run_monitor.py` cross-check |

Standard library only. Old AdLabs exports stay readable in the consumers; nothing here touches them.

## Start of every run

1. `list_clients`. Skip every row with `is_demo: true`.
2. Confirm the client by SKU or product title from `get_catalog`. A SYNQ client name alone does not prove whose seller data it is.
3. `get_sync_status` for the client and marketplace. A `last_sync_status` other than `success`, or an `updated_at` older than a day, goes into the operator note before any number.

`convert.py` enforces one client and one marketplace per run: rows that name two `client_id` or `marketplace` values exit 2. Pass `--client-id` and `--marketplace` to also check them against the client you confirmed.

## Saving responses

Save each response unchanged, with its note, as:

```
{"note": "<the NOTE text SYNQ put before the JSON, or null>", "rows": [ ...the JSON list... ]}
```

`convert.py` also reads a bare JSON list (a response with no note) and the raw MCP text (a `NOTE ...` block followed by the JSON). A bare list carries no note, so a bare list of exactly 50, 500 or 2000 rows (SYNQ's default limit, a common limit and the maximum) exits 2 unless `--allow-truncated` is passed: save the response with its note wrapper, or raise `limit` and pull again. Name files so the pull is clear, for example `synq/search-terms-2026-10-25_2026-10-31-SP.json`.

## Row-cap rule

Every SYNQ tool returns at most `limit` rows (default 50, maximum 2000). When rows were cut, the response starts with a "ROW LIMIT REACHED" or "TRUNCATED" note. A cut list is never complete.

- `convert.py` exits 2 when any input note says rows were cut, and writes only the receipt. Narrow the pull (shorter date window, one `ad_product`, one `campaign_id`, one ASIN) or raise `limit`, save each narrower pull as its own file, and pass them all.
- `--allow-truncated` runs anyway for a knowingly partial look. Never use it for SUPA, the monitor or a proposal. The output then says it is partial:
  - JSON outputs (`entities`, `totals`, the search-term JSON) are written as `{"note": "PARTIAL: ...", "rows": [...]}` (`totals` puts its one figures object in `rows`). `run_weekly.py` and `run_monitor.py` read the wrapper and print the note in the brief.
  - CSV outputs cannot carry a note: the receipt says `"truncated": true` (top level and on each output) and the run prints a warning naming each CSV to stderr.
- For an exact sum use `group_by: total`; it returns one row.
- Rows with an `id` that appear in two files are counted once. One `id` with two different contents exits 2, because the files mix different pulls.
- For before/after comparisons, pull each window separately and join by id (`entity_id` in the entity rows), so an entity that fell to zero still shows.

## Subcommands

### sqp

```
python3 tools/synq/convert.py sqp --pages SQP.json [SQP.json ...] --out-dir DIR [--asins B0..,B0..]
```

Writes `DIR/sqp_<period_start>.csv` per week with exactly these columns:

```
asin,search_query,total_click_count,asin_click_count,total_purchase_count,asin_purchase_count,
search_query_volume,total_query_impression_count,asin_impression_count,search_query_score
```

- Mapping: `clicks` to `asin_click_count`, `total_clicks` to `total_click_count`, `purchases` to `asin_purchase_count`, `total_purchases` to `total_purchase_count`, `impressions` to `asin_impression_count`, `total_query_impressions` to `total_query_impression_count`; `search_query_volume` and `search_query_score` as they are.
- The market columns (`search_query_volume` and the `total_*` counts) repeat on every ASIN row of a query and week. They are taken once per query and week; if two ASIN rows disagree, the first value is kept and the receipt warns.
- Weeks are keyed by `period_start`, which must be a Sunday with `period_end` the Saturday after. Brand-level rows (no `asin`) and MONTH or QUARTER rows exit 2.
- SYNQ has no comparison columns; SUPA computes week over week from the weekly files.
- Point SUPA's `inputs.sqp_csvs` at the files, keyed by the same Sunday. Until the SQP parity check against a Seller Central SQP download passes, the Seller Central fetcher stays the fallback.

### search-terms

```
python3 tools/synq/convert.py search-terms --pages ST.json [ST.json ...] --out-dir DIR
  [--week-start sunday|monday] [--ad-products SP,SB]
```

- `DIR/search_terms_<week_start>.csv`: `search_term,campaign,ad_group,match_type,impressions,clicks,spend,sales,orders`, one row per term, campaign, ad group and match type for the week (`cost` becomes `spend`). This is SUPA's `inputs.search_term_csvs` file.
- `DIR/searchterms_weekly_<week_end>.json`: `[{term, campaign, "ad group", "match type", impressions, clicks, spend, sales, orders}]`, spend descending. This is the weekly brief's search-term file (`_local/ads-monitor/inbox/<brand>/searchterms_weekly_<week_end>.json`).
- Weeks run Sunday to Saturday by default, from `report_date`. A missing campaign or ad group name falls back to its id.
- The receipt records each week's first and last date and `days_seen`. Fewer than 7 days marks the week `partial` and warns, because a quiet day and a missing pull look the same. Pull exact Sunday to Saturday windows.
- The weekly brief reads SP and SB only: pass `--ad-products SP,SB`.

### stock

```
python3 tools/synq/convert.py stock --history INV_HISTORY.json [...] --out-dir DIR [--week-start sunday] [--asins ...]
```

- Input is `get_inventory` with `history: true` (180-day retention). A row without `snapshot_date` (a current-state pull) exits 2.
- Per ASIN and day, SKUs that share an `fnsku` share one stock pool, so the pool counts once; each SKU without an fnsku is its own pool. A day is out of stock when the pools' `fulfillable_quantity` sums to 0.
- `DIR/stock_<week_start>.csv`: `asin,out_of_stock_days`. Days without a snapshot are not counted. The receipt records `days_observed` and `max_pools_per_day` per ASIN and week and warns below 7 days.
- Days of cover is not here: use `get_catalog.days_inventory`.

### entities

```
python3 tools/synq/convert.py entities --metrics [GRAIN:]METRICS.json [...] --campaigns CAMPAIGNS.json [...]
  [--search-terms ST.json ...] [--entity-type target] --out ENTITIES.json
```

The weekly recipe pulls `get_daily_metrics` for one Sunday to Saturday window twice, once with `group_by: campaign` and once with `group_by: target`, and passes both with a grain prefix:

```
python3 tools/synq/convert.py entities --metrics campaign:CAMPAIGNS_WEEK.json target:TARGETS_WEEK.json --campaigns LIST_CAMPAIGNS.json [--search-terms ST.json ...] --out ENTITIES.json
```

Writes the `run_weekly.py` entity rows (`--ads-json`):

```
[{entity_type, name, campaign_name, campaign_id, category: "Unknown", match_type, impressions, clicks,
  spend, sales, orders, daily_budget: null, budget_capped_days: null, time_in_budget: null,
  entity_id, ad_group_id, ad_product, source: "synq"}]
```

- Metrics come from `get_metrics` (one `timeframe`: 7d, 14d, 30d or 60d) or `get_daily_metrics` (summed over its dates). Mixing timeframes, or `get_metrics` rows with `get_daily_metrics` rows, exits 2 because it would double count. Grouped `get_daily_metrics` files of different grains from the same window are fine. One grain sent both as raw daily rows and as grouped rows, or the same grouped file passed twice, exits 2.
- Grouped `get_daily_metrics` rows carry no `entity_type`. Prefix each file with the `group_by` value used for its pull (`campaign:`, `ad_group:`, `target:` or `keyword:`); only those four count as a prefix. A file without a prefix falls back to `--entity-type`. A prefix that disagrees with a row's own `entity_type` exits 2.
- Campaign rows and target rows of the same campaign can sit in one file. The monitor takes a campaign's total from its campaign row and ignores that campaign's target rows when it rolls targets up, so the spend is not counted twice.
- Campaign, ad group, target and keyword rows are kept; placement, search-term, product-ad and ASIN rows are skipped and counted in the receipt. Keywords appear as targets in SYNQ.
- `name`: the row's `keyword_text`, else the search terms' `keyword_text` for that target id, else the campaign name; ad groups take the ad group name; campaign rows take the campaign name. A row with none of these is named `<entity_type> <entity_id>`.
- `campaign_name` comes from `list_campaigns` by `campaign_id` (pull it without a state filter so paused campaigns resolve), then from the search terms. Unresolved ids are warned in the receipt.
- `match_type` is not on SYNQ metric rows. It is joined from `get_search_terms` (`keyword_id` equals the target `entity_id`), so pass search terms for the same window. No match leaves it null.
- `category: "Unknown"` lets the monitor classify by campaign name. Budgets and budget-capped days are SYNQ gaps (see `docs/synq-mcp.md`); they stay null.

### totals

```
python3 tools/synq/convert.py totals --ads-total ADS_TOTAL.json [--sales-traffic ST_TOTAL.json] --out TOTALS.json
```

- `--ads-total`: `get_daily_metrics` with `group_by: total` for the report day. `--sales-traffic`: `get_sales_traffic_daily` with `group_by: total` for the same day. Each must hold exactly one row, else exit 2.
- Writes `{"ad_spend": cost, "ad_sales": sales, "total_sales": ordered_product_sales or null}` for `run_monitor.py --ads-json`.
- Label the ad sales as SYNQ-reported sales: the attribution window is unconfirmed. Sales and Traffic runs 2 to 3 days behind the ads data, so a recent day's `total_sales` can still grow; the receipt warns.

## Receipts and exit codes

Each run writes a receipt next to its output: `DIR/<subcommand>-receipt.json` for `--out-dir`, `<out name>-receipt.json` for `--out`. It holds `ok`, every input's path, sha256, row count, note and `truncated` flag, rows read and deduplicated, every output with its row count, per-subcommand counts (weeks, days seen, skipped rows), warnings and errors. Read it before using the output.

Exit 0 on success. Exit 2 writes only the receipt, with `ok: false` and the reason.

## Tests

```
python3 -m unittest discover -s tools/synq/test -v
```

Fixtures in `tools/synq/test/fixtures/` are synthetic, built from the captured response shapes. The consumer tests import the SUPA loaders and the monitor's `normalize_entities` and `cross_check` to prove the files parse.

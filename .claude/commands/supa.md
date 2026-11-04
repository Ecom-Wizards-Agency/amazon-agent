---
description: Build the SUPA weekly SQP x PPC workbook for a client (SYNQ-native, per-keyword spend-vs-share diagnosis)
argument-hint: "[client + marketplace] (e.g. 'acme de' or 'bravo us')"
---

# /supa: weekly SQP x PPC monitor

Build the SUPA workbook with `tools/sqp-supa/build_supa_workbook.py`. It joins Amazon SQP shares
(search volume, click share, purchase share) to PPC ad spend and ad sales, per keyword, per
Sunday-Saturday week, per ASIN, and flags the result with deterministic rules.

The question it answers: **did click share fall because ad spend on that keyword quietly fell?**
Nothing else in the toolkit separates a spend-driven share loss from a market-driven one.

The user's target is: **$ARGUMENTS**

Reference: `tools/sqp-supa/README.md`. Data source is the SYNQ MCP (read-only, free reads; contract
in `docs/synq-mcp.md`), converted to the builder's CSVs by `tools/synq/convert.py`. SYNQ SQP parity
against Seller Central is pending: until one ASIN-week has been checked against the Seller Central
SQP CSV, say in the delivery note that SYNQ SQP is unverified. The AdLabs carve-out account (US and CA)
keeps the AdLabs pull (see "AdLabs carve-out only" at the end).

## Steps

1. **Find or create the config.** `tools/sqp-supa/config.<client>-<market>.json`, copied from
   `config.TEMPLATE.json`. These are **gitignored** (client configs are local-only). Existing local configs
   follow the same `config.<client>-<market>.json` naming.

   Fill from SYNQ, never by guessing: `synq_client_id` from `list_clients` (skip `is_demo` clients),
   confirmed by a known SKU or title in `get_catalog`, because a client name alone does not prove
   whose seller data it is. `data_source` stays `SYNQ`. `targets.acos` / `targets.tacos` come from
   `get_catalog` (`acos_target` is a percent, so 45 becomes 0.45; `target_tacos` is already a ratio)
   or the client's strategy; set `currency` to the marketplace currency. `adlabs_team_id` and
   `adlabs_profile_id` are optional legacy keys for the AdLabs carve-out account only. Set `asins` to the ASINs carrying real spend
   (one tab each, so keep it to the meaningful set, not the whole catalog) with short variant labels.

2. **Pick the weeks.** Sunday week-starts, ascending, at least 2 (`len < 2` hard-exits). The last
   entry is the focus week and drives every WoW flag.
   - **Never include the current, incomplete week.** SQP weeks run Sunday to Saturday; a week whose
     Saturday has not passed is partial and reads as a collapse in every WoW comparison.
   - 3-4 complete weeks is the useful default.

3. **Optional but high value: wire organic rank.** For each ASIN tracked in a SoldScope rank
   tracker group on the RIGHT marketplace, build its rank file and add
   `inputs.rank_jsons: {"<ASIN>": "downloads/<client>/reporting/rank_<ASIN>.json"}`. The reads are
   free (no credits):
   - `rank_tracker_list_groups` (filter by marketplace and ASIN) gives the `group_id`;
     `rank_tracker_list_products(group_id)` gives the own `product_id`.
   - `rank_tracker_list_phrases(group_id, product_id, heatmap=true, heatmap_date_from,
     heatmap_date_to, results_type=organic, per_page=100)`, every page, covering the config's
     weeks (at most 92 days). Save each page; large pages overflow context, so read them from the
     saved files rather than inline.
   - `python3 tools/soldscope/ranks.py --organic <pages> --asin <ASIN> --marketplace <code>
     --out downloads/<client>/reporting/rank_<ASIN>.json` writes the series SUPA reads.

   **Check the group's marketplace.** A client can have a group that tracks another country's
   listing of the same product (seen live 2026-07): using it would silently score the wrong
   country. `ranks.py --marketplace` fails on a mismatch.

   Rank is what makes P3 useful: paying over target while rank IMPROVES is rank investment, not
   waste. Without it, P3 can only say "cut". With no `rank_jsons` the column never renders and every
   flag falls back to v1 behaviour, so this is safe to skip.

4. **Pull the data from SYNQ and convert it.** Run `get_sync_status` first; a failed or stale sync
   stops the build. Save every response as `{"note": <note text or null>, "rows": [...]}`. A
   "ROW LIMIT REACHED" or "TRUNCATED" note means rows were cut: narrow the pull or raise `limit`
   (max 2000) until no page carries one, because a cut list is never complete.
   - **SQP, one pull per week:** `get_sqp_data(client_id, marketplace, period_from=<sunday>,
     period_to=<saturday>, report_period="WEEK")`. Then
     `python3 tools/synq/convert.py sqp --pages <SQP pages> --out-dir downloads/<client>/reporting`
     → `sqp_<week>.csv` per Sunday week.
   - **Search terms:** `get_search_terms(client_id, marketplace, date_from=<first sunday>,
     date_to=<last saturday>)`, split by `ad_product`, `campaign_id` or week when it caps. Then
     `python3 tools/synq/convert.py search-terms --pages <pages> --out-dir downloads/<client>/reporting --week-start sunday`
     → `search_terms_<week>.csv`.
   - **Stock (v3, strongly recommended):** `get_inventory(client_id, marketplace, history=true,
     date_from=<first sunday>, date_to=<last saturday>)`. Then
     `python3 tools/synq/convert.py stock --history <pages> --out-dir downloads/<client>/reporting --week-start sunday`
     → `stock_<week>.csv`, wired via `inputs.stock_csvs`. A day counts as out of stock when the
     ASIN's fulfillable quantity is 0 (one pool per FNSKU); a day without a snapshot is not counted.

   Each converter exits 2 on a row-cap note unless `--allow-truncated`, and writes a receipt with
   input hashes and row counts. Check that every configured week has its three CSVs and that no
   week is marked `partial`.

   The SQP reader has **no column fallbacks**: `asin`, `search_query`, `total_click_count`,
   `asin_click_count`, `total_purchase_count`, `asin_purchase_count`, `search_query_volume` must be
   present and exactly named, or it hard-exits. The PPC reader tolerates `search term`/`query` and `cost`.

5. **Build:** `python3 tools/sqp-supa/build_supa_workbook.py --config config.<client>-<market>.json --validate`
   (`--validate` rebuilds first, then checks.) It verifies the tab set, every block's column geometry
   against `asin_layout()`, raw-CSV spot checks, and that no >100% ACOS renders green. Exit 1 on failure.
   The build prints rank and CVR-gap coverage: low coverage is normal (rank tracking covers dozens of keywords,
   SQP carries hundreds), zero coverage where you configured a rank file is not.

6. **Read the output.** Tabs: `① Dashboard` (per-ASIN weekly rollup + account block), one tab per
   ASIN, `Action Plan` (P1/P2/P3 ranked), `Methods & Sources` (provenance, caps, verbatim flag rules,
   match rate). Output lands in `output/<client>/reporting/`.

   Flag rules: **P1** spend-driven share loss · **P2** share loss with spend held · **P3** paying over
   target without traction · **O1** unfunded demand · **O2** converts above its weight · **E1** scaling winner.

   **v2/v3 split those by stock, rank and the conversion gap**, which is where the judgement is.
   **Stock is checked first, because it explains the rest**: Amazon deranks what it cannot ship, so
   an out-of-stock week produces share loss, rank slip and high ACOS that look exactly like a
   bidding failure and are not one.
   - **P3 + out of stock this week** → "STOCK, not bids. Pause until restocked, judge on a clean week"
   - **P3 + rank slipped + stock lost across the span** → "do not read this as a bidding failure"
   - **P3 + rank improving** → flips to Opportunity: "do not cut on ACOS alone, this is buying position"
   - **P3 + rank slipping + CVR below market + stock clean** → "unwinnable at any bid, fix the offer"
   - **P1 + out of stock** → check stock before restoring spend
   - **P2 + rank slipping + stock clean** → outranked organically, a listing problem not a bid problem
   - **O1 + out of stock** → do not buy demand you cannot ship
   - **E1 + out of stock** → it won anyway, so the true ceiling is higher than it looks

   Two stock questions, deliberately separate: **focus-week** OOS drives "pause now"; OOS **across
   the weeks the rank move spans** drives "stock explains that move". A product can be clean this
   week and still have lost its rank to an out-of-stock week a fortnight ago.

7. **Sanity-check the match rate** printed on build. It is the share of SQP queries with ad traffic and
   the share of profile spend that matched. A low rate is not a bug by itself (most spend legitimately
   sits on queries outside the SQP top-100), but a sudden drop means the join is off.

8. **Deliver** to the client's Drive folder (`output.drive_folder` in the config) via the desktop mount
   only when asked. MD5-verify local against Drive.

## Notes

- **Currency is fully wired.** `money()`, `dmoney()` and `sym()` drive value cells, WoW delta cells and
  all flag prose from `cfg["currency"]`. Verified on both a EUR and a USD account.
- SQP shares are **recomputed from raw counts**, never read from the export's share columns.
- Rollups are share-of-sums, never a mean of shares.
- The SQP grid caps at the top 100 queries per ASIN per week; that is Amazon's cap, not ours. Queries
  outside it render grey rather than zero.
- **Stock outranks every other reading** (v3). `thresholds.oos_days_flag` (default 2) is the lost-days
  bar at which stock takes over the verdict. Without `inputs.stock_csvs` the block never renders and
  the flags fall back to v2, which will confidently tell you to cut the bid on a product that was
  simply unavailable. Wire it.
- Ad spend is **profile level** per search term, so siblings sharing a query show an identical spend
  number. The Action Plan therefore anchors each (query, rule) to an ASIN that HAS rank data first,
  score second, since rank is what changes the advice.
- The ASIN tab's column geometry comes from `asin_layout()`, shared with the validator. v1 hardcoded
  it for 3 weeks and silently corrupted any 4-week run; do not reintroduce fixed offsets.
- Read-only. This builds a file. It never touches SYNQ, AdLabs or Amazon.

## AdLabs carve-out only

The AdLabs carve-out account (US and CA) keeps the AdLabs pull until it moves to SYNQ. Set `data_source: "AdLabs"`,
`adlabs_team_id` and `adlabs_profile_id` from the AdLabs profile resource. For each week, with
`DATE >= <sunday>` and `DATE <= <saturday>`:
- `get_entity_data(entity_type="search_query", team_id, profile_id, filters=...)` → `download_data`
  → `downloads/<client>/reporting/sqp_<week>.csv`
- `get_entity_data(entity_type="search_term", ...)` → `download_data`
  → `downloads/<client>/reporting/search_terms_<week>.csv`
- `get_entity_data(entity_type="product", ...)` → `download_data`
  → `downloads/<client>/reporting/stock_<week>.csv`. `out_of_stock_days` is window-scoped, so the
  weeks sum back to the monthly figure; sanity-check that they do. Do NOT read `availability` /
  `days_of_cover` / `fulfillable_units` per week: those are CURRENT snapshots, identical in every
  week's export.

The per-week pull is not optional there. The `search_query` entity has no date column, so a single
range pull silently aggregates the weeks together and destroys the comparison the tool exists to make.

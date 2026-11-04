# SQP x PPC Weekly Monitor (SUPA-style)

Per-keyword SQP shares (search volume, click share, purchase share) joined
with PPC ad spend + ad sales, per Sunday-Saturday week, per ASIN, with
rule-based flags and an Action Plan tab. The diagnostic this exists for:
"click share fell because ad spend on that keyword quietly fell."

**v2** adds organic rank (SoldScope rank tracker, optional) and the conversion gap
to the market (free, from counts already read). **v3** adds days out of stock per
week. Together they split the flags, which is where the judgement lives: paying
over target while rank IMPROVES is rank investment, not waste, and v1 could only
ever say "cut".

**Stock is checked first, because it explains the rest.** Amazon deranks what it
cannot ship, so an out-of-stock week produces share loss, rank slip and a high
ACOS that look exactly like a bidding failure and are not one. On the Acme DE
run (historical DataDive Rank Radar data), "kollagen pulver" reads rank
7 → 24 → 8 → 14 against 1 → 5 → 2 → 1 days out of stock: the collapse and its
cause on one line.

Data source: SYNQ (read-only MCP, free reads; contract in `docs/synq-mcp.md`).
The SYNQ pulls are saved as `{"note", "rows"}` and turned into the CSVs this
builder reads by `tools/synq/convert.py`. SYNQ SQP parity against Seller Central
is pending: until one ASIN-week has been checked against the Seller Central SQP
CSV and the field differences are reported, treat SYNQ SQP as unverified and say
so in the delivery note. The AdLabs carve-out account (US and CA) keeps the AdLabs pull (see
"AdLabs carve-out only" below), whose `search_query` entity was verified
byte-identical to Seller Central SQP on 2026-07-08 (US 3-way + DE 2-way, 13,248
cells, 0 mismatches).

## Workflow (per refresh)

1. **Pull weekly data through the SYNQ MCP** (agent step, no script). Start with
   `list_clients` (skip `is_demo`), confirm the client by SKU or title in
   `get_catalog`, then `get_sync_status`. Save every response as
   `{"note": <note text or null>, "rows": [...]}`; a "ROW LIMIT REACHED" or
   "TRUNCATED" note means the list is cut, so narrow the pull (fewer ASINs,
   one `search_query`, a smaller date range) or raise `limit` (max 2000) until
   no page carries a note.
   - SQP: `get_sqp_data(client_id, marketplace, period_from=<sunday>,
     period_to=<saturday>, report_period=WEEK)`, one pull per Sunday-Saturday
     week. Market columns repeat on every ASIN row; the converter takes them
     once per query and week.
   - PPC: `get_search_terms(client_id, marketplace, date_from=<first sunday>,
     date_to=<last saturday>)`. It returns one row per day per term per
     keyword, so it caps fast: split by `ad_product`, `campaign_id` or week.
   - Stock: `get_inventory(client_id, marketplace, history=true,
     date_from=<first sunday>, date_to=<last saturday>)` (180-day retention).
   - Convert into `downloads/<client>/reporting/`:
     ```bash
     python3 tools/synq/convert.py sqp --pages <SQP pages> --out-dir downloads/<client>/reporting
     python3 tools/synq/convert.py search-terms --pages <search-term pages> --out-dir downloads/<client>/reporting --week-start sunday
     python3 tools/synq/convert.py stock --history <inventory pages> --out-dir downloads/<client>/reporting --week-start sunday
     ```
     They write `sqp_<week>.csv`, `search_terms_<week>.csv` and
     `stock_<week>.csv` per Sunday week, plus a receipt with input hashes and
     row counts. Each exits 2 on a row-cap note unless `--allow-truncated`.
     Check the receipts: every configured week present, and no `partial`
     week in the search terms or stock.
2. **Configure**: copy `config.TEMPLATE.json` to `config.<client>-<market>.json`
   (gitignored), set `synq_client_id` (and `data_source`, default `SYNQ`), list
   weeks ascending and the input maps. `adlabs_team_id` and `adlabs_profile_id`
   are optional legacy keys (AdLabs carve-out only).
   - Optionally add `inputs.rank_jsons: {"<ASIN>": ".../rank_<ASIN>.json"}` holding
     one rank series per ASIN, written by `tools/soldscope/ranks.py` from saved
     SoldScope rank tracker `rank_tracker_list_phrases` pages (free reads; pass
     `--marketplace` so a group from another marketplace fails). **Check the rank
     tracker group's marketplace matches** the config's: a DE config fed an IT
     group scores the wrong country silently.
   - `rank_source` (optional, default `SoldScope rank tracker`) names the rank
     source in the Methods tab and the build summary. Rank files saved from the
     retired DataDive Rank Radar have the same shape and still load; set
     `rank_source` to `DataDive Rank Radar (historical)` when rebuilding from them.
   - Add `inputs.stock_csvs: {"<week>": ".../stock_<week>.csv"}` from
     `convert.py stock`, and `thresholds.oos_days_flag` (default 2).
3. **Build + validate**:
   ```bash
   .venv/bin/python tools/sqp-supa/build_supa_workbook.py \
     --config tools/sqp-supa/config.<client>.json --validate
   ```
4. **Deliver**: copy the XLSX from `output/<client>/reporting/` to the client
   folder on the agency Drive via the desktop mount. MD5-verify local vs Drive.
   It opens directly in Google Sheets.
5. Weekly refresh: append the newest week to `weeks`, pull and convert the new
   week, add its CSVs, rebuild. The file name carries the focus-week Saturday.
   The build summary and the Methods tab name the data source.

## Tabs

Dashboard (per-ASIN weekly rollup + flag) · one tab per ASIN (per-keyword
weekly matrix, now with ORGANIC RANK and CVR/CTR-vs-market columns) · Action
Plan (ranked, rule-based) · Methods & Sources (provenance, caps, join caveat,
verbatim flag rules).

## Flags, and how v2 splits them

Base rules: **P1** spend-driven share loss · **P2** share loss with spend held ·
**P3** paying over target without traction · **O1** unfunded demand · **O2**
converts above its weight · **E1** scaling winner.

Rank and the CVR gap change the advice rather than adding new rules:

**Stock is evaluated before rank and CVR**, since it causes both:

| Rule | + out of stock | + rank improving | + rank slipping, stock clean |
|---|---|---|---|
| **P3** | STOCK, not bids: pause until restocked, judge on a clean week | flips to Opportunity: do not cut on ACOS alone, this is buying position | cut; and if CVR is also below market, stop entirely (unwinnable at any bid) |
| **P1** | check stock before restoring spend | cut was survivable, organic held | URGENT: the cut is costing rank too |
| **P2** | it was stock, not price or competitors | competitor bought the share or the SERP moved | outranked organically: listing/price problem |
| **O1** | do not buy demand you cannot ship | (already ranking) stop paying for traffic organic owns | fund it |
| **E1** | won anyway: true ceiling is higher than it looks | — | — |

Two stock questions, kept separate: **focus-week** OOS drives "pause now"; OOS
**across the weeks the rank move spans** drives "stock explains that move". A
product can be clean this week and still have lost its rank to an out-of-stock
week a fortnight ago.

## Known limits

- Rank coverage is thin by design: rank tracking covers a few dozen keywords while SQP
  carries hundreds, so most rows have no rank and fall back to earlier behaviour.
- Stock is an ASIN-level fact repeated on every keyword row of that ASIN. That
  redundancy is deliberate: a rank slip and its cause belong in the same eyeline.
- SYNQ stock days come from daily inventory snapshots: a day counts when the
  ASIN's fulfillable quantity is 0, counting one stock pool per FNSKU. A day
  without a snapshot is not counted, so a missing snapshot understates the loss;
  the converter's receipt records the days observed.
- SQP = top 100 queries per ASIN per week (Amazon's cap in every source).
  SV totals are floors.
- The PPC join is profile-level. Search terms are campaign-scoped, not
  ASIN-scoped. Never sum ad spend across ASIN tabs. Because of this, siblings
  sharing a query carry an identical spend number, so the Action Plan anchors
  each (query, rule) to an ASIN with rank data first and score second.
- The CVR gap needs >= 5 of our clicks that week; the CTR gap needs >= 100 of our
  impressions AND the optional impression columns in the export. Blank otherwise.
- Validation gates: exact tab set, **per-block column geometry via the shared
  `asin_layout()`**, week headers, group headers, raw-CSV spot checks (shares
  1e-6, spend 0.01), no >100% ratio with a green fill, plus a soft cross-check
  against an export's own comparison columns (AdLabs exports carry them; SYNQ
  rows do not, so it skips). Exit 1 on failure.

## AdLabs carve-out only

The AdLabs carve-out account (US and CA) stays on AdLabs until it moves to SYNQ. Set
`data_source: "AdLabs"`, `adlabs_team_id` and `adlabs_profile_id` in their
config, and pull per Sunday-Saturday week through the AdLabs MCP:

- SQP: `get_entity_data(search_query)` with a DATE filter per week (optionally
  `PRODUCT_ASIN IN (...)`), then `download_data`, saved as
  `downloads/<client>/reporting/sqp_<week-start>.csv`.
- PPC: `get_entity_data(search_term)` with the same DATE filter, then
  `group_by_column(search_term)`, then `download_data`, saved as
  `search_terms_<week-start>.csv`.
- Stock: `get_entity_data(product)`, then `download_data`, saved as
  `stock_<week-start>.csv`. `out_of_stock_days` is window-scoped, so per-week
  pulls sum back to the monthly figure (verified on Acme DE: 1+5+2+1 = 9,
  matching the 30-day pull). `availability`, `days_of_cover` and
  `fulfillable_units` are CURRENT snapshots and come back identical in every
  week's export: never read those per week.

The per-week pull is not optional there: the `search_query` entity has no date
column, so one range pull silently merges the weeks.

## History

- **v3** (2026-07-16): days out of stock per week, checked before rank and CVR.
- **v2** (2026-07-16): organic rank + CVR/CTR gap vs market, splitting the flags.

- **v1 bug, fixed in v2**: the ASIN tab column offsets were hardcoded for 3 weeks.
  Any run with a different week count wrote each metric block on top of the
  previous block's delta, and the validator recomputed the same wrong offsets so
  it agreed with the corruption instead of catching it. Geometry now comes from
  `asin_layout()`, shared by writer and validator.
- **v1 bug, fixed**: currency was hardcoded USD in the delta formats, all flag
  prose and the delta column header. Now driven by `cfg["currency"]` through
  `money()` / `dmoney()` / `sym()`.

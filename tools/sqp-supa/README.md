# SQP x PPC Weekly Monitor (SUPA-style)

Per-keyword SQP shares (search volume, click share, purchase share) joined
with PPC ad spend + ad sales, per Sunday-Saturday week, per ASIN, with
rule-based flags and an Action Plan tab. The diagnostic this exists for:
"click share fell because ad spend on that keyword quietly fell."

**v2** adds organic rank (DataDive Rank Radar, optional) and the conversion gap
to the market (free, from counts already read). **v3** adds days out of stock per
week. Together they split the flags, which is where the judgement lives: paying
over target while rank IMPROVES is rank investment, not waste, and v1 could only
ever say "cut".

**Stock is checked first, because it explains the rest.** Amazon deranks what it
cannot ship, so an out-of-stock week produces share loss, rank slip and a high
ACOS that look exactly like a bidding failure and are not one. On the Sheko DE
run, "kollagen pulver" reads rank 7 → 24 → 8 → 14 against 1 → 5 → 2 → 1 days out
of stock: the collapse and its cause on one line.

Validated basis: the AdLabs MCP `search_query` entity is byte-identical to
Seller Central SQP (verified 2026-07-08, US 3-way + DE 2-way, 13,248 cells,
0 mismatches). See the sqp-adlabs-sc-parity memory note.

## Workflow (per refresh)

1. **Pull weekly CSVs via the AdLabs MCP** (agent step, no script):
   - SQP: `get_entity_data(search_query)` with a DATE filter per Sunday-Saturday
     week (optionally `PRODUCT_ASIN IN (...)`), then `download_data` and save as
     `downloads/<client>/reporting/sqp_<week-start>.csv`.
   - PPC: `get_entity_data(search_term)` with the same DATE filter, then
     `group_by_column(search_term)`, then `download_data`, saved as
     `downloads/<client>/reporting/search_terms_<week-start>.csv`.
2. **Configure**: copy `config.TEMPLATE.json` to `config.<client>-<market>.json`
   (gitignored), list weeks ascending and both input maps.
   - Optionally add `inputs.rank_jsons: {"<ASIN>": ".../rank_<ASIN>.json"}` holding
     `get_rank_radar_data` payloads. **Check the radar's marketplace matches** the
     config's: a DE config fed an IT radar scores the wrong country silently.
   - Add `inputs.stock_csvs: {"<week>": ".../stock_<week>.csv"}` holding one AdLabs
     `product` export per week, and `thresholds.oos_days_flag` (default 2).
3. **Build + validate**:
   ```bash
   .venv/bin/python tools/sqp-supa/build_supa_workbook.py \
     --config tools/sqp-supa/config.<client>.json --validate
   ```
4. **Deliver**: copy the XLSX from `output/<client>/reporting/` to the client
   folder on the agency Drive via the desktop mount. MD5-verify local vs Drive.
   It opens directly in Google Sheets.
5. Weekly refresh: append the newest week to `weeks`, add the two new CSVs,
   rebuild. The file name carries the focus-week Saturday.

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

- Rank coverage is thin by design: radars track a few dozen keywords while SQP
  carries hundreds, so most rows have no rank and fall back to earlier behaviour.
- Stock is an ASIN-level fact repeated on every keyword row of that ASIN. That
  redundancy is deliberate: a rank slip and its cause belong in the same eyeline.
- `out_of_stock_days` is window-scoped, so per-week pulls sum back to the monthly
  figure (verified on Sheko DE: 1+5+2+1 = 9, matching the 30-day pull). But
  `availability`, `days_of_cover` and `fulfillable_units` are CURRENT snapshots and
  come back identical in every week's export: never read those per week.
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
  against AdLabs' own comparison columns. Exit 1 on failure.

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

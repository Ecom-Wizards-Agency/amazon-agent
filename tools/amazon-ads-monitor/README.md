# Amazon Ads Monitor Toolkit

Client-agnostic, read-only Python toolkit that produces a **daily previous-day
Amazon Ads performance report** with trends, % changes, a Sellerboard-vs-AdLabs
data cross-check, and goal-lens-aware flags, plus a compact Slack payload.
Pure stdlib + `requests` (no MCP calls in this toolkit; MCP enrichment --
fetching the Sellerboard feed via firecrawl, pulling AdLabs figures, Notion/
Slack context -- happens at the skill/runtime layer). **Never changes
campaigns.**

## Files

- `datasource.py` -- pluggable data-source interface (`DataSource`) +
  adapters: `MockDataSource` (fully implemented, deterministic synthetic
  data), `SellerboardDataSource` (**PRIMARY** real adapter -- parses the
  Sellerboard "Dashboard Totals" CSV feed from a file path or raw string;
  see `parse_sellerboard_csv`/`_local/ads-monitor/SELLERBOARD-FORMAT.md`),
  `SPAdsApiDataSource` (secondary real adapter, Amazon Ads API v3
  reporting, not live-tested), `AdLabsDataSource` /
  `MarketplaceAdProsDataSource` (documented stubs -- AdLabs is wired at
  the skill layer via its MCP, see `crosscheck.py`). Also defines
  `DailyRow` (raw + derived metrics: CTR, CVR, CPC, ACOS, ROAS, TACOS,
  plus the Sellerboard-only fields real_acos/margin/units/refunds/
  sessions/etc.) and `classify_campaign_category` (Rank/Discovery/
  Profit/Shield, from the EW naming convention).
- `analyze.py` -- pure delta/trend math: value vs prior day and vs
  trailing-7-day average (absolute + %), plus an up/down/flat trend
  classification over the trailing week. Metric set is pluggable
  (`datasource.METRICS` for mock/SP-Ads, `datasource.SELLERBOARD_METRICS`
  for Sellerboard account rows) so the same math covers both.
- `flags.py` -- severity-tagged (info/warn/alert/critical), philosophy-
  aware, **goal-lens-aware** flags (spend spike/collapse, budget-capped
  days, CVR drop with stable clicks, near-zero-impression Rank/SKW
  campaigns, discovery-share-of-spend >20%, ACOS swings, zero-sales
  spend, and an account-level goal-aware TACOS-rise/margin-drop check).
  **Suppresses** the known false alarm (high/volatile ACOS on a Rank/SKW
  campaign -- expected due to last-click attribution per
  `_local/ads-strategy/strategy.md`) into a separate `suppressed` list
  instead of alerting on it. `evaluate(analysis, config, goal=<lens>)`
  takes a brand goal/stage string (`rank-launch`, `scale`,
  `profit-maintain`, `defend`, `liquidate`; see `GOAL_LENSES`) that
  adjusts thresholds, severities, and wording -- unknown/omitted goal
  resolves to the neutral lens (unchanged behavior).
- `pacing.py` -- the month-to-date RUN-RATE GOVERNOR (strategy.md v3):
  `compute_pacing(account_rows, as_of, monthly_budget, lens)` returns the
  pace (MTD spend vs budget-to-date), a status (on_pace / warn / act /
  underpace, thresholds layered defaults -> goal-lens `pacing_overrides`
  -> config), and, when acting, the FIXED cut order (waste -> discovery
  -> profit; Rank last and only by explicit operator decision). Partial
  month coverage is stated in a note and never produces an under-pace
  verdict. `pacing_flag()` folds the read into the flag sections
  (act = ALERT). No budget on file = no pacing section, never a
  fabricated one.
- `crosscheck.py` -- Sellerboard-vs-AdLabs data-quality cross-check.
  `cross_check(sellerboard_figures, adlabs_figures, tolerance=0.07)`
  compares `ad_spend`/`ad_sales`/`total_sales` for the same report day and
  returns a per-figure + headline verdict (`verified`/`mismatch`/
  `no_data`); `render_verdict_line`/`render_verdict_emoji_line` produce
  the "data verified" / "data mismatch (ad spend SB $X vs AdLabs $Y,
  +Z%)" line the report leads with.
- `report.py` -- renders the markdown daily report and a compact Slack
  payload (mrkdwn text + Block Kit `blocks`) from the same analysis +
  flags, including the cross-check verdict line and goal-lens label when
  provided via `meta`. `SELLERBOARD_HEADLINE_METRICS` swaps in the
  Sellerboard account-total headline (total sales, ad sales, ad spend,
  TACOS, Real ACOS, orders, margin) in place of the click-level mock/
  SP-Ads set. No file I/O, no Slack posting.
- `run_monitor.py` -- daily CLI: `--date`, `--source mock|sellerboard|spads`,
  `--csv` (Sellerboard CSV path(s), comma-separate a 7d+30d pair),
  `--goal` (lens name), `--adlabs-json` (same-day AdLabs figures file for
  the cross-check), `--tolerance`, `--accounts`, `--config`, `--out`,
  `--window-days`, `--slack-json`. Mock mode runs end-to-end with no
  credentials.
- `recommendations.py` -- the weekly brief's read-only PROPOSAL engine.
  `build_recommendations(raw_entities, goal, situation, test_candidates,
  signal_items, config)` normalizes AdLabs weekly campaign/target rows
  (`normalize_entities`) and returns a `RecommendationsResult` with three
  goal-aware lists: **push** (scale converting/rank-driving/budget-capped
  targets), **pause_optimize** (zero-sale spend, high-ACOS non-rank,
  discovery bloat, self-competition, stalled campaigns -- a Rank/SKW
  target is never proposed for a cut on ACOS grounds alone), and **tests**
  (`select_tests` filters the vetted `DEFAULT_TEST_BACKLOG` plus any
  parsed external-signal digest items, `parse_signal_digest_markdown`,
  down to what this week's actual signals make pertinent -- empty when
  nothing is, never a fabricated filler test). NEW (strategy.md v3):
  optional `rank_radar` rows (DataDive Rank Radar,
  `normalize_rank_radar`) add a fourth list, **graduate** (organic rank
  1-3 stable 2+ consecutive weeks -> step ToS/bid down toward break-even
  over 2-3 cycles, never cliff-drop), and a data-backed protection: a
  keyword whose organic rank is IMPROVING is never proposed for a cut,
  whatever its category (the read moves to notes). Radar absent with Rank
  entities present = a stated note, not silence. An optional
  `pacing` result adds the cut-order note when the governor says act.
- `run_weekly.py` -- weekly CLI: `--date` (week-end, a fully-completed
  day), `--csv` (Sellerboard CSV path(s), >=14 days), `--account`,
  `--goal`, `--situation`, `--adlabs-json` (normalized weekly AdLabs
  campaign/target rows), `--signal-digest` (a
  `_local/ads-signals/<ISO-year>-W<week>/digest.md` path),
  `--rank-radar-json` (DataDive Rank Radar rows -> GRADUATE list +
  per-keyword rank protection), `--monthly-budget` (enables the run-rate
  pacing section; per-brand amounts live under `monthly_budgets` in
  `_local/ads-monitor/config.json`; needs Sellerboard history back to the
  1st of the month -- raise `--window-days` late in a month), `--out`,
  `--window-days`, `--slack-json`, `--no-daily-flags`. Runs end-to-end
  from a Sellerboard CSV alone (AdLabs-free -> empty Push/Pause-Optimize
  with a note, not an error). Writes
  `output/{account}/ads-monitor/{week_end}_weekly.md`.
- `selftest.py` -- regression suite: synthetic fixtures + the real
  `MockDataSource` scenarios + a full daily CLI dry run + Sellerboard CSV
  parsing (synthetic semicolon-delimiter proof, plus the real gitignored
  sample with expectations recomputed at test time, never hardcoded) +
  cross-check verdicts + goal-lens severity differences + weekly
  aggregation math (`aggregate_week`), goal-differentiated
  Push/Pause-Optimize proposals, Test selection (empty vs signal-driven),
  weekly markdown/Slack rendering, and a full weekly CLI dry run. Run
  after any change.

## Quick start (mock mode, no credentials)

```bash
python3 tools/amazon-ads-monitor/run_monitor.py --source mock --date 2026-07-12 \
  --out output --slack-json output/acme-us/ads-monitor/2026-07-12_slack.json
```

Writes `output/{account}/ads-monitor/{date}_daily.md` for each sample
account (`acme-us`, `globex-us`) and the Slack payload to the given path.
Omit `--date` to default to yesterday; omit `--accounts` to run every
account the source knows about.

## Real Sellerboard CSV (primary)

```bash
python3 tools/amazon-ads-monitor/run_monitor.py --source sellerboard \
  --csv _local/ads-monitor/inbox/acme/dashboardtotals_7d.csv \
  --accounts acme --goal rank-launch --date 2026-07-13 \
  --adlabs-json <path to {"ad_spend":..,"ad_sales":..,"total_sales":..}> \
  --out output --slack-json -
```

The CSV comes from the brand's Sellerboard "Dashboard Totals" feed --
see `_local/ads-monitor/SELLERBOARD-FORMAT.md` for the column mapping and
the `amazon-ads-monitor` skill for the file-first (delivered to
`_local/ads-monitor/inbox/<brand>/`) / firecrawl-fallback flow that
obtains the file. `--goal` and `--adlabs-json` are both optional: omit
`--goal` for the neutral lens; omit `--adlabs-json` to skip the
cross-check (the report just won't show a verdict line). If the CSV is
blank/missing (a just-requested Sellerboard report can come back empty),
`get_account_daily` returns `[]` -- the skill layer should fall back to
AdLabs entirely for that brand/day per `sellerboard-feeds.json`'s
`"fallback": "if_sellerboard_blank_use_adlabs"`.

## Weekly brief (WoW + Push/Pause-Optimize/Test proposals)

```bash
python3 tools/amazon-ads-monitor/run_weekly.py \
  --csv _local/ads-monitor/inbox/acme/dashboardtotals_30d.csv \
  --account acme --goal rank-launch --situation "recurring ACOS spikes" \
  --date 2026-07-13 \
  --adlabs-json <path to a JSON list of normalized weekly AdLabs entities, or omit> \
  --signal-digest _local/ads-signals/2026-W28/digest.md \
  --out output --slack-json -
```

Aggregates this week vs last week (`analyze.aggregate_week`) from the
Sellerboard CSV, runs `recommendations.build_recommendations` over the
(optional) AdLabs weekly entities + (optional) signal digest, and renders
`report.render_weekly_markdown`/`render_weekly_slack`. `--adlabs-json`
and `--signal-digest` are both optional -- omitting either is a valid,
complete run (Push/Pause-Optimize/Test just come back empty with a note
in place of a fabricated result). `--date` must be a fully-completed day
-- Sellerboard's `total_*` columns (and AdLabs figures) can read 0 for
the still-in-progress current day. See the `amazon-ads-monitor` skill's
"Weekly variant" section for the full MCP-enrichment flow (AdLabs
campaign/target pull with its two documented quirks, goal-lens
resolution, Slack delivery).

## Switching to the real Amazon Ads API (secondary path)

1. Complete the credential checklist in `_local/ads-monitor/README.md`.
2. Copy `_local/ads-monitor/config.TEMPLATE.json` -> `_local/ads-monitor/config.json`
   (gitignored) and fill in `lwa` (client_id/client_secret/refresh_token),
   `accounts[]` (one entry per account with its Amazon Ads `profile_id`),
   `region`, `attribution_window`, and any `thresholds` overrides.
3. Run with `--source spads --config _local/ads-monitor/config.json`.

`SPAdsApiDataSource` implements the full documented v3 reporting flow
(async report create -> poll status -> download GZIP_JSON -> parse) with
LWA auth, but **has not been live-tested** (no real credentials exist yet
in this workspace). It is now a secondary path -- use it only for
accounts without Sellerboard/AdLabs access. Every method that talks to
Amazon is marked "NEEDS LIVE-CREDENTIAL TEST" in its docstring. Known
gaps that need a live account to close (documented, not silently
assumed):

- **Campaign name lookup**: v3 reporting returns `campaignId` only; the
  name join is supposed to go through Amazon's Exports API
  (`_fetch_campaign_metadata`, currently a stub returning `{}`). Until
  implemented, campaign category classification degrades to "Unknown"
  for any campaign whose name isn't already known some other way.
- **Budget / budget-capped state**: not part of this reporting report;
  needs a separate Budget Usage or Campaigns-list call. Currently
  `None`/`False`.
- **Report generation latency**: Amazon's docs say generation can take up
  to three hours. The bundled `_poll_report` uses a bounded wait loop
  suited to typical daily volume; a production cron should split
  "request" and "fetch" into two separate scheduled runs instead of
  blocking.
- **TACOS**: needs an external total-sales figure. `total_sales_source`
  in config supports a manual CSV (`date,account,total_sales`) today; a
  Business Reports puller is a documented extension point, not built.

`AdLabsDataSource` is a documented stub in `datasource.py` (it's wired at
the skill layer via the AdLabs MCP, not as a `DataSource` adapter here --
see `crosscheck.py` and the skill's Flow section). As of 2026-07-14 the
operator confirms AdLabs data is current except that **today's** figures
are slightly off and get corrected the next day -- caveat this for the
report date only, not older days. `MarketplaceAdProsDataSource` is a
separate documented stub; the operator's AI Connect plan was expired as
of 2026-07-13, not usable until renewed/reauthorized.

## Testing

```bash
python3 tools/amazon-ads-monitor/selftest.py
```

No network access (the real-sample test reads a local gitignored file if
present; it skips cleanly, not a failure, if it's absent). Exercises:
exact delta/trend arithmetic on a hand-built fixture; every flag rule
(including that the suppressed Rank/SKW ACOS false-alarm does NOT appear
in active flags, only in suppressed, while every real-anomaly rule DOES
fire) on both the hand fixture and the real `MockDataSource`'s scripted
scenarios; markdown + Slack rendering; Sellerboard CSV delimiter
auto-detection (synthetic values) and column mapping against the real
sample `_local/ads-monitor/samples/sample_dashboardtotals_7d.csv` (with
day-over-day deltas recomputed independently at test time -- no real
financial figures are hardcoded in this committed file); Sellerboard-
vs-AdLabs cross-check verdicts; goal-lens severity differences (e.g. a
near-zero-impressions Rank/SKW flag is ALERT under the neutral lens but
CRITICAL under rank-launch; an account-level TACOS-rise/margin-drop read
is suppressed as expected under rank-launch but an active ALERT under
profit-maintain); and a full `--source mock` CLI run that writes real
files with no credentials.

## Rules

- Read-only. Never creates, updates, pauses, or archives anything in a
  live Amazon Ads account. File + Slack output only.
- Secrets (Sellerboard feed URLs/tokens in `sellerboard-feeds.json`; LWA
  client_id/secret/refresh_token, profile IDs in `config.json`) live only
  in gitignored `_local/ads-monitor/`; only `config.TEMPLATE.json` is
  committed. Never echo a full feed URL/token in chat or a commit.
- Dependency-light: stdlib + `requests` (already used elsewhere in this
  repo; no new pip install needed in this environment).
- Extend the toolkit, never hand-edit it per client -- everything
  client-specific belongs in `_local/ads-monitor/` (config, feeds,
  inbox).

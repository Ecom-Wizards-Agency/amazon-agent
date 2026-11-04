# Daily And Weekly Brief Workflows

Mode browser: None; read-only file, MCP, and Slack workflow.

Automated performance surveillance with judgment, not a raw metric dump.
Produces a **daily previous-day** Amazon Ads report (trends + % changes,
a Sellerboard-vs-SYNQ cross-check, goal-aware flags) and posts a
compact summary to Slack. Never touches campaigns -- this skill only
reads and reports; any resulting bid/budget/keyword change is a
separate, operator-confirmed action in `amazon-ads-console` or
`amazon-sponsored-products-bulk-files`.

SYNQ source contract: `docs/synq-mcp.md` (client scoping, row caps, lag,
gaps) and the saved-file adapters in `tools/synq/convert.py`. The AdLabs
carve-out account (US and CA, identified in `docs/synq-mcp.md`) still
pulls from AdLabs; see "AdLabs carve-out only" at the end.

## Source of truth

Before a run, execute `python3 tools/ads_recall.py monitor` and read the returned decision, Playbook, and Research files in order. Continue quietly when it returns no paths. Numeric thresholds belong only in `_local/ads-strategy/strategy.json`; the ownership map is `docs/ads-doctrine-sources.md`.

1. **Toolkit:** `tools/amazon-ads-monitor/` -- `datasource.py` (pluggable
   data-source layer + adapters, incl. `SellerboardDataSource`),
   `analyze.py` (deltas/trends + `aggregate_week` for the weekly WoW
   read), `flags.py` (severity-tagged, philosophy-aware, goal-lens-aware
   flags), `crosscheck.py` (Sellerboard-vs-SYNQ data-quality verdict),
   `recommendations.py` (the weekly Push/Pause-Optimize/Test proposal
   engine), `report.py` (markdown + Slack rendering, daily and weekly),
   `run_monitor.py` (daily CLI), `run_weekly.py` (weekly CLI). See its
   `README.md`.
2. **Data format:** `_local/ads-monitor/SELLERBOARD-FORMAT.md` -- the
   Sellerboard "Dashboard Totals" CSV column-by-column mapping, delimiter
   quirks, and cross-check rules. `_local/ads-monitor/sellerboard-feeds.json`
   -- the 9 brands' feed URLs (SECRET, gitignored, never echo tokens) and
   `_context_rules` (goal-based lenses, Slack/Notion context folding).
3. **Philosophy:** `_local/ads-strategy/strategy.md` -- rank-first, the
   four categories (Rank/Discovery/Profit/Shield), TACOS ~1/3 of
   break-even ACOS, ACOS as an indicator not a decision trigger. Every
   flag in `flags.py` is written to respect this; do not override or
   second-guess the suppression rules below without updating the
   toolkit itself.
4. **Evidence and tested practice:** the ordered Playbook and Research files
   returned by `tools/ads_recall.py`. Research explains likely causes but never
   overrides the tracked skill, local strategy, or approved decision record.

## Data source priority

**Sellerboard's "Dashboard Totals" CSV is the account P&L source**
-- whole-account truth (total sales, ad spend, ad sales, Real ACOS,
margin, units, refunds, sessions), parsed by
`SellerboardDataSource`/`parse_sellerboard_csv` in `datasource.py`.
**SYNQ supplies campaign and target detail and the cross-check.** Its
MCP is read-only and free (no credits). `get_daily_metrics` with exact
date ranges gives campaign, ad group, target, ASIN and placement metrics;
`get_search_terms` gives shopper queries with match type;
`get_spend_pacing` gives month-to-date spend against the SYNQ monthly
target. `crosscheck.py` compares the SYNQ totals with Sellerboard (ad
spend, ad sales, total sales, within +/-7% by default -> "verified", else
"mismatch"). SYNQ sales are SYNQ-reported attributed sales; the
attribution window is not confirmed yet, so never call them total
revenue, and never derive margin or profit from SYNQ (margin comes from
Sellerboard, or `get_catalog.cogs` when it is set).

Amazon Ads API v3 (`SPAdsApiDataSource`) is a **secondary** fallback (not
live-tested) for accounts without Sellerboard/SYNQ access. A client not
yet onboarded into SYNQ runs Sellerboard-only (no `--ads-json`), labelled
"Sellerboard only, not cross-checked"; campaign detail for it comes from
an Ads console report or a bulk download when the operator asks. Mock
(`--source mock`) remains the no-credentials PREVIEW path.

## Start of every SYNQ pull

Every daily and weekly run starts the same way, before any metric read:

1. `list_clients`, skipping every `is_demo` client.
2. `get_catalog(client_id, marketplace)`: confirm the client by a known SKU
   or product title of the brand. A SYNQ client name alone does not prove
   whose seller data it is. On a mismatch, stop for that brand.
3. `get_sync_status(client_id, marketplace)`: `last_sync_status` must be
   `success` and `updated_at` must be after the last day the brief reads.
   Otherwise report the brand as blocked on SYNQ freshness and continue
   with the next brand; never fill the gap with zeros.

Save every SYNQ response as `{"note": <note text or null>, "rows": [...]}`.
Every SYNQ tool caps at `limit` (max 2000) and prefixes a "ROW LIMIT
REACHED" or "TRUNCATED" note when rows were cut. A cut list is never
complete: narrow the filters, raise the limit, or use `group_by: total`
for exact sums. `tools/synq/convert.py` exits 2 on such a note unless
`--allow-truncated` is passed; pass it only when the brief states the cut.

## Getting the Sellerboard CSV: delivered file, then local fetch

Each brand's feed comes from a delivered file first. On a miss, a local
fetcher on this machine downloads it. No third-party service ever sees
the feed URL:

1. **PRIMARY -- delivered file.** Check
   `_local/ads-monitor/inbox/<brand>/` for a CSV already there (Sellerboard
   can email/auto-export the report to a synced folder that lands here),
   and `_local/ads-monitor/inbox/<brand>/fetched/` for one the fetcher
   saved earlier. A file counts as fresh if its date/window covers the
   report date (7d feed for the daily brief). If a fresh file exists, use
   it directly.
2. **FALLBACK -- local fetch, no third party.** If no fresh file exists,
   run from the repo root:

   ```bash
   python3 tools/amazon-ads-monitor/fetch_sellerboard.py --account <brand-slug>
   ```

   It reads the brand's feed URL from
   `_local/ads-monitor/sellerboard-feeds.json` (SECRET), sends one https
   GET to the feed's own host, saves the CSV into
   `_local/ads-monitor/inbox/<brand>/fetched/` with mode 0600 and prints
   the saved path. It never prints the URL or token. Never open the
   manifest yourself, and never pass a feed URL to Firecrawl, Monid, a
   browser, a web-fetch tool or any other third-party fetcher: the URL
   carries the access token. If the fetcher exits non-zero, do not retry
   through another service. Use the SYNQ-only fallback below and say
   so in the operator note. Exit 6 means the brand has no feed URL
   configured; a runtime without shell network access gets exit 4 and
   takes the same SYNQ-only route.
   - A just-requested Sellerboard report can come back **blank** -- that
     is not an error (the fetcher exits 3 and saves nothing;
     `parse_sellerboard_csv` returns `[]` for a blank delivered file); per
     the `fallback` value in `sellerboard-feeds.json` (its legacy value
     `if_sellerboard_blank_use_adlabs` now means the ads source),
     fall back to SYNQ entirely for that brand/day and label the report
     accordingly.

## Flow (per brand)

1. **Obtain the CSV** per the delivered-file/local-fetch rule above.
   If the inbox holds both a delivered
   7d and a 30d export, use the 7d one for the daily brief and the 30d
   one only if the 7d one is missing or blank. The fetcher pulls only the
   one feed URL configured for the slug.

2. **Pull SYNQ ad detail** (for the cross-check + campaign anomalies),
   after the start-of-pull checks above:
   - `get_daily_metrics(client_id, marketplace, date_from=<report date>,
     date_to=<report date>, group_by: total)`, saved as
     `{"note", "rows"}`. Convert it with
     `python3 tools/synq/convert.py totals --ads-total <saved file> --out <totals JSON>`.
     The output is the `{ad_spend, ad_sales, total_sales}` file for
     `--ads-json`. Leave out `--sales-traffic` while Sales and Traffic is
     inside its 2-3 day lag (it nearly always is for the previous day),
     so `total_sales` stays null and that figure reads "not
     cross-checked" rather than a false mismatch.
   - For anomalies: `get_daily_metrics` with `group_by: campaign` for the
     report date and, in a separate call, the prior day; join the two by
     `campaign_id`, so a campaign that fell to zero still shows. Names
     come from `list_campaigns` (no state filter).
   - The newest day of SYNQ ads data can still settle. Treat the report
     date's SYNQ figures as provisional; older days are reliable.

3. **Run the toolkit**:

   ```bash
   python3 tools/amazon-ads-monitor/run_monitor.py \
     --source sellerboard --csv <inbox path>[,<second feed path>] \
     --accounts <brand-slug> --goal <lens from step 4, or omit for neutral> \
     --date <yesterday, or the requested report date> \
     --ads-json <step 2's totals JSON, or omit> \
     --out output --slack-json <path or ->
   ```

   `--ads-source` defaults to `SYNQ`; `--adlabs-json` is a legacy alias of
   `--ads-json`. The cross-check happens inside this call; the rendered
   report/Slack payload already shows "data verified" or "data mismatch
   (ad spend SB $X vs SYNQ $Y, +Z%)" -- don't recompute or restate it
   differently in the write-up.

   If the Sellerboard feed is blank/missing/wrong-type for this
   brand/day, NEVER drop the brand from the report -- build the write-up
   from whatever data IS available, in this order: SYNQ totals for the
   report date (+ prior day for deltas), then any older
   Sellerboard CSV in the inbox for trailing-week context, then
   campaign-level SYNQ detail if something looks off. Label the
   section plainly ("SYNQ-only, not cross-checked" or "Sellerboard
   stale through <date>") -- do not silently present fallback figures as
   if they were cross-checked, and do not reduce the brand to a
   one-line "no data" note when usable numbers exist elsewhere.

4. **Brand context -- RE-DERIVE EVERY RUN (MCP, done here, not in the
   Python toolkit).** Situations change daily (hijackers, listing
   takedowns, buy-box loss, offboarding, launches), so never trust a
   durable profile on its own -- rebuild the brand's current context from
   the live sources every run, in this order:
   - **Seed:** read the brand's lens + situation from its shared team-vault
     `Amazon Ops.md`, then verify/refresh it against the live sources below.
     Lenses: rank-launch, scale, profit-maintain, defend, maintain,
     liquidate, inactive (see
     `flags.py` `GOAL_LENSES`). Unknown -> omit `--goal` (neutral lens).
   - **Team-vault profile + Notion meeting database**: read the brand's
     `Clients/{Name}/Amazon Ops.md` through the client-profile lookup tool
     for goal/stage and its durable situation, then use Notion `search` +
     `fetch` for the brand's most recent meeting notes. Meeting notes carry
     the freshest live context and may predate a profile-field update.
   - **Slack MCP -- read_channel**: read the brand's `#<brand>-ew-amazon`
     channel and `#amazon-check` for the report window plus a few days of
     look-back for launches, promos, price/stock changes, or incidents.
   - **Reconcile:** if the live sources show the lens or situation changed,
     use the live version for this run and flag the proposed durable profile
     update in the operator note. Only a human-supervised session may write
     that update to `Amazon Ops.md`; do not create or update a local context
     cache. Pass the resolved lens as `--goal`. If a flag matches a known
     intentional change from Slack/meeting notes, annotate it in the Slack/markdown
     write-up rather than presenting it as a surprise (don't suppress it in
     the file).
   - This step reads the shared profile, Notion, and Slack. It never posts or
     edits the shared profile, Notion, or Slack during enrichment.
5. **Deliver -- THREADED format (operator feedback 2026-07-15: the
   single-message daily was "messy, hard to read"; use a clean parent
   summary + one threaded reply per brand, mirroring the weekly).**
   - **Parent message** to **#amazon-daily-report** (channel ID from
     `slack_channel_id` in the `_local/ads-monitor/` config; resolve by
     name if unset), starting with `<!here>` (daily; `<!channel>` is
     reserved for the weekly) and the header
     `<!here> *Daily Amazon Ads Report -- <date>*`. Then exactly two
     scannable sections, one line per brand, ordered worst-first:
     - `:rotating_light: *Needs attention*` -- every brand with a
       critical/alert flag or a true data mismatch. Line format:
       `*<Brand>* -- <one clause naming the single most important thing, with its number>`
     - `:white_check_mark: *On track*` -- everything else. Line format:
       `*<Brand>* -- Sales <ccy><n> (<+/-x% vs 7d avg>), TACOS <x>%, margin <x>%`
     - No other prose in the parent. Keep it under ~15 lines.
   - **One threaded reply per brand** (`thread_ts` = parent ts), same
     worst-first order, each with this fixed structure so every brand
     reads identically:
     1. `*<Brand>* (<goal lens>) -- <STATUS>` where STATUS is one of
        `:rotating_light: ALERT` / `:warning: WATCH` / `:white_check_mark: OK`.
     2. A compact metrics table (Slack markdown table): rows = Total
        Sales, Ad Sales, Ad Spend, TACOS, Real ACOS, Orders, Margin;
        columns = Value, vs prior day, vs 7d avg. Use the brand's own
        currency symbol (EUR accounts in EUR -- never re-label as $).
     3. `*Data check:*` the toolkit's cross-check verdict verbatim, plus
        -- when the only gap is ad sales with spend matching -- one
        plain-language line that this is the Sellerboard-vs-SYNQ
        attribution difference (SYNQ's sales attribution window is
        unconfirmed; the figure is SYNQ-reported sales), not lost data.
     4. `*Flags:*` each active flag on its own bullet with its numbers,
        each annotated (not suppressed) when it matches a known
        intentional change from step 4 context.
     5. `*Context:*` 1-2 sentences of live brand situation (from step 4)
        that explain today's numbers.
     6. `*Suggested follow-up:*` one concrete, read-only suggestion for
        the operator, or `none` -- never an executed action.
   - Brands running SYNQ-only (blank/wrong-type Sellerboard feed) get
     the same thread structure with the fallback stated in the STATUS
     line and in *Data check* ("SYNQ-only, not cross-checked"). Brands
     not yet in SYNQ say "Sellerboard only, not cross-checked".
   - Save the markdown report exactly where the toolkit wrote it:
     `output/{brand}/ads-monitor/{date}_daily.md`. Do not duplicate it
     elsewhere.
6. **Finish with a short operator note per brand**: data source used
   (sellerboard file/local fetch/SYNQ-fallback/mock-PREVIEW), the SYNQ
   client confirmed by SKU or title, sync status, any row-cap note, goal
   lens applied, cross-check verdict, report date, critical/alert/warn/info
   counts, what context enrichment changed (if anything), and the Slack
   message link.

## Exact MCP tools this flow uses

- SYNQ (read-only, free): `list_clients`, `get_catalog`, `get_sync_status`,
  `get_daily_metrics`, `list_campaigns`; weekly also `get_search_terms`,
  `get_spend_pacing`, `get_ads_change_log` and `get_entity_changes`. The
  wizard-ads flag and recommendation calls are not used: flags come from
  `flags.py` and the step 6 goal check, proposals from `recommendations.py`.
- SoldScope (weekly rank rows, free reads): the rank-tracker calls in step 5.
- Notion: `search`, `fetch` (meeting-note context).
- Slack: `read_channel` (brand + `#amazon-check` context). An attended run uses
  the supervising operator's verified native Slack MCP `send_message`; a
  scheduled/background Evo run posts through the guarded Wizards AI helper.
  Missing access never falls back across identities.

Sellerboard feeds use no MCP tool; see the local fetcher above.

## Weekly variant

A weekly brief (`{week_end}_weekly.md`) shares the daily brief's data
sources and philosophy but replaces the day-over-day read with a
week-over-week (WoW) read, then adds read-only PROPOSAL lists on top:
**Push**, **Graduate** (organic-rank-driven), **Pause/Optimize**, and
**Test** (only if pertinent), plus a **Run-rate pacing** read when a
monthly budget is on file. It reports what happened, why it moved, and
what the operator should review. It never executes anything -- see Rules
below; execution belongs to `amazon-ppc-weekly-management` (`/ppc-manage`),
which consumes this brief.

### Toolkit

`tools/amazon-ads-monitor/run_weekly.py` is the weekly CLI:
`analyze.aggregate_week` (this-week vs last-week totals + WoW deltas),
`recommendations.py` (the Push/Pause-Optimize/Test engine), and
`report.render_weekly_markdown`/`render_weekly_slack`. See each module's
docstring for exact signatures.

### Method rules

- Sum base metrics (impressions, clicks, spend, sales, orders, units) and
  recompute ratios (CTR, CVR, CPC, CPA, ACOS, ROAS, AOV). Never average
  ratios across entities or days.
- Show missing, provisional, suppressed, partial and truncated data
  explicitly. Never fabricate a test, proposal or positive finding to
  fill a section.
- Keep each currency separate when one run covers several brands.

### Flow (per brand, weekly)

1. **Choose the windows.** The current window is the latest seven fully
   completed days in the advertiser profile's local timezone (the
   marketplace's time, e.g. Pacific time for US; state the timezone you
   used). For the usual Monday brief that is Monday to Sunday. The prior
   window is the seven days immediately before it, unless the operator
   supplies two equal windows. Never anchor on today: Sellerboard's
   `total_*` columns and the newest SYNQ day can read 0 or settle late.
   State both windows in the brief.

2. **Sync health first.** Run the start-of-pull checks above. Then pull
   `get_daily_metrics(group_by: date)` across both windows: every day
   must have a row. A failed sync, a stale `updated_at` or a missing day
   blocks the brand ("blocked: SYNQ data incomplete for <dates>") rather
   than filling it with zeros; continue with the other brands.

3. **Scorecard and drivers.**
   - Scorecard: `get_daily_metrics(group_by: total)` once per window.
     Report current, prior, absolute delta and percent delta.
   - Drivers: `get_daily_metrics(group_by: campaign)` once per window,
     each saved separately, then join by `campaign_id` (an id present in
     only one window counts as zero in the other, so a campaign that
     dropped to zero still shows). Rank campaigns by absolute spend delta
     and by absolute attributed-sales delta, and name the few that
     explain the movement. Prefer contribution over extreme low-volume
     ratios.
   - Drill into targets for the driver campaigns: `get_daily_metrics`
     takes no `campaign_id`, so pull `group_by: target` for the window
     (keyword rows come back empty, targets carry `keyword_text`) and
     filter the driver campaigns locally by `campaign_id`. Pull
     placements (`entity_type: placement`) for delivery mix.
   - Change context: `get_ads_change_log` and `get_entity_changes` for
     the current window show which bid, budget and placement changes
     landed and who made them (`source_module` BidOptimizer,
     CampaignManager; `source` app or external). Name a change when it
     explains a driver.
   - Entities for the engine: pull `get_daily_metrics` for the current
     week once with `group_by: campaign` and once with `group_by: target`,
     save each as `{"note","rows"}`, then run
     `python3 tools/synq/convert.py entities --metrics campaign:CAMPAIGNS_WEEK.json target:TARGETS_WEEK.json --campaigns LIST_CAMPAIGNS.json [--search-terms ST.json ...] --out ENTITIES.json`
     (`ST.json` are the step 4 pulls) and pass `ENTITIES.json` with
     `--ads-json` in step 9. Build the prior week's entities file the
     same way when you need the per-entity join.

4. **Search terms.** `get_search_terms(date_from, date_to)` for the
   current window (SP and SB). It returns one row per day per term per
   keyword, so it hits the cap fast: split by `ad_product` or
   `campaign_id`, or shorten the range, until no page carries a note.
   Convert with
   `python3 tools/synq/convert.py search-terms --pages <pages> --out-dir _local/ads-monitor/inbox/<brand>/ --week-start monday`
   (use `--week-start sunday` for a Sunday-to-Saturday window). It writes
   `searchterms_weekly_<week_end>.json` with per-term: term, campaign, ad
   group, match type, impressions, clicks, spend, sales, orders. Keep
   (a) top terms by orders with CVR -- the HARVEST candidates (converting
   terms not yet running as their own exact), and (b) top terms by spend
   with 0 orders -- the NEGATE candidates.

   Classify every search term as branded or nonbrand before reporting or proposing
   optimization. The account may intentionally keep profitable brand traffic in Auto
   or product targeting, but aggregate ACOS must never hide how much performance came
   from branded demand.

5. **Pull weekly rank rows (SoldScope rank tracker) -- the live
   organic-rank input.** These are free reads (no credits):
   `rank_tracker_list_groups` (filter by marketplace and ASIN) gives the
   `group_id`; check that the group's marketplace matches the brand's, since
   a group tracking another country's listing scores the wrong country
   silently. `rank_tracker_list_products(group_id)` gives the own
   `product_id`. `rank_tracker_list_phrases(group_id, product_id,
   heatmap=true, heatmap_date_from, heatmap_date_to, results_type=organic,
   per_page=100)`, every page, over at least the last 8 complete
   Sunday-Saturday weeks (at most 92 days); save each page and read it from
   the file, because large pages overflow context. Then run
   `python3 tools/soldscope/ranks.py --organic <pages> --asin <ASIN>
   --marketplace <code> --weekly-rows --out <rows JSON>`, which writes
   `{keyword, rank_now, rank_prev, weeks_stable}` (weeks_stable = consecutive
   weeks at/below rank 3) and fails on a marketplace mismatch, and pass the
   file via `--rank-json` (`--rank-radar-json` is the legacy alias). This
   drives the GRADUATE list (rank 1-3 stable 2+ weeks -> step down
   toward break-even) and per-keyword rank protection (an
   improving-rank keyword is never proposed for a cut -- moved to notes).
   Omitting it is a valid run; the brief states the gap in a note.

6. **Goal-aware flags.** The toolkit's day-level flags run inside the CLI
   with the brand lens. Add the goal check from `get_catalog`:
   `acos_target` (a percent, e.g. 45) and `target_tacos` (a ratio, e.g.
   0.2) per ASIN. Compare ASIN-level ads ACOS (`get_daily_metrics`
   `group_by: asin`) with `acos_target`, and Sellerboard TACOS with
   `target_tacos`. Read every miss through the lens: an ASIN above target
   because of Rank/SKW spend under rank-launch is expected, so say so
   instead of flagging it, and never re-promote a flag the toolkit
   suppressed. Report active flags first, then suppressed ones with the
   reason. Days of cover come from `get_catalog.days_inventory`.

7. **Pacing.** `get_spend_pacing` gives `mtd_spend`, `monthly_target`,
   `projected_month_end` and `pace_pct`. Pass the client's monthly ad
   budget via `--monthly-budget` (from the `_local/ads-monitor/` client
   config) for the toolkit's run-rate read (on_pace / warn / act /
   underpace, goal-lens-aware thresholds; when acting it restates the
   fixed cut order: waste -> discovery -> profit; Rank last and ONLY by
   explicit operator decision). MTD needs Sellerboard history back to
   the 1st of the month -- raise `--window-days` late in the month. When
   the SYNQ `monthly_target` and the configured budget differ, state both
   and which one the read used. With neither, write "Pacing unavailable:
   no monthly budget is configured." Cut-order guidance is review
   context, never an instruction to execute.

   **Per-campaign budget delivery.** After the stock read and before proposals,
   use Amazon's time-in-budget metric when available. SYNQ metric rows carry no
   budgets or budget-capped days, and this skill reads no browser page. Use them
   only from an Ads console report or bulk download already delivered to the
   brand's inbox. Otherwise name the gap in the data-confidence section and point
   to the skill that can read it: `amazon-ads-console` for budgets,
   time-in-budget and top-of-search share, and the read-only Bid Optimizer check
   in `amazon-ppc-weekly-management` for runner membership. Without budgets the
   engine's budget-capped Push rules cannot fire; say so. With budgets in hand, flag campaigns whose
   spend repeatedly approaches the daily budget and verify that they are actually
   capping. A capped campaign at or below target ACOS is a budget-increase or
   reallocation proposal, subject to monthly pacing. A capped campaign above target
   ACOS is a bid-reduction proposal so the same budget lasts longer. An intentionally
   capped Rank campaign stays capped until the operator decides otherwise.

   When the operator has declared event mode, record its dates, objective, approved
   budget, and loss limits. Do not let the normal pacing status recommend cuts to
   approved event spend. Separate event data from normal performance after the event.

8. **Run the recommendations engine.** This happens inside step 9's CLI
   call (`recommendations.build_recommendations`): it classifies every
   normalized entity by strategy category (Rank/Discovery/Profit/Shield)
   and proposes goal-aware Push / Pause-Optimize items, plus Test ideas
   filtered against this week's actual signals (never fabricated to
   fill space -- see recommendations.py's module docstring for the exact
   rules, especially that a Rank/SKW target is never proposed for a cut
   on ACOS grounds alone).

9. **Merge the signal digest, apply the goal lens and run the CLI (MCP context,
   done here, not in the Python toolkit):**
   - **Signal digest:** read `_local/ads-signals/<ISO-year>-W<week>/digest.md`
     (produced by the weekly Firecrawl ingestion pipeline, see
     `_local/ads-signals/README.md` -- each entry has already passed the
     Phase-0 critical-review protocol) and pass its path via
     `--signal-digest`; `recommendations.parse_signal_digest_markdown`
     parses it and folds any digest item that maps to this week's actual
     signals into the Test list. A digest with no pertinent item for
     this brand contributes nothing -- that's correct, not a bug.
   - **Goal lens -- RE-DERIVE EVERY RUN:** seed from the brand's shared
     team-vault `Amazon Ops.md`, then refresh it against the Notion
     **meeting database** (most recent
     meeting notes -- the freshest operational context), plus its Slack
     channel (`#<brand>-ew-amazon` +
     `#amazon-check`, Slack MCP `read_channel`). Pass the resolved lens as
     `--goal` and a short situation string as `--situation` (the latter
     lightly tags Test selection -- e.g. a hijacker or a recurring ACOS
     spike). If the live sources show the lens/situation changed, use the
     live version this run and flag a proposed durable profile update in the
     operator note. Do not create a local context cache. This step reads the
     shared profile, Notion, and Slack; it never edits them during enrichment.

   Run the CLI:

   ```bash
   python3 tools/amazon-ads-monitor/run_weekly.py \
     --csv <inbox path 30d>[,<7d path>] --account <brand-slug> \
     --goal <lens> --situation "<brief free-text>" \
     --date <the last day of the current window> \
     --ads-json <step 3's entities JSON, or omit> \
     --signal-digest _local/ads-signals/<ISO-year>-W<week>/digest.md \
     --rank-json <step 5's weekly rank rows JSON, or omit> \
     --monthly-budget <amount from the client config, or omit> \
     --out output --slack-json <path or ->
   ```

   Get the Sellerboard CSV the same delivered-file/local-fetch way as the
   daily brief (prefer a delivered 30d export so both windows are
   covered; check that a fetched file's dates span both). `--ads-json`
   takes a list or a `{"note", "rows"}` wrapper; a non-null note is
   carried into the brief's notes. `--ads-source` defaults to `SYNQ`;
   `--adlabs-json` is a legacy alias. Omitting `--ads-json` is a valid
   run -- Push/Pause-Optimize just come back empty with a note, not an
   error.

10. **Data confidence.** Every brief states: the SYNQ client confirmed by
    SKU or title, sync status and `updated_at`, both windows and the
    timezone, any row-cap note and what was done about it, that Sales and
    Traffic lags 2-3 days, that SYNQ sales use an unconfirmed attribution
    window (SYNQ-reported sales), the cross-check verdict, partial days,
    and each gap left open (current bids and budgets, budget-capped days,
    top-of-search impression share, runner membership) with the skill that
    can read it (`amazon-ads-console`, or the read-only Bid Optimizer check
    in `amazon-ppc-weekly-management`).

11. **Operator review guidance.** Give short instructions for the SYNQ
    web-app pages that reproduce the brief's evidence, normally Campaign
    Manager (campaign and target drivers), Keyword Harvester and Search
    Term Negator (harvest and negate candidates), Bid Optimizer (runner
    status and roles), Exposure (top-of-search share) and Change History
    (what changed). Use the form `Open <page> -> select <client and
    marketplace> -> set <window> -> filter <entity or rule> -> sort
    <metric>`. Do not claim that a link or saved view exists, and do not
    paste more than about ten detail rows when the instruction lets the
    operator reproduce the view.

12. **Deliver -- detailed, threaded (operator feedback 2026-07-14:
   "more detailed analysis, bullet points, actual keywords/targets to
   harvest and negatives to negate").**
   - **Slack identity**: for an attended run, use the supervising operator's
     native Slack MCP `send_message`. For a scheduled/background Evo run, use
     the guarded Wizards AI helper. Post to **#amazon-daily-report**
     (channel ID from `slack_channel_id` in the `_local/ads-monitor/`
     config; resolve by name if unset) as a THREAD. Parent message: the
     `<!channel>` mention, a one-line header ("<!channel> Weekly Amazon
     Ads analysis -- week ending <date>"), and a 1-2 line WoW headline
     per brand -- urgent brands first (Rank/Shield targets losing
     impression share, self-competition, data mismatches). Then ONE
     THREADED REPLY PER BRAND (`thread_ts` = parent message ts) with the
     full detail -- this beats the 5,000-char message limit without
     thinning the analysis.
   - Each brand's thread reply uses bullet points and NAMES the exact
     entity with its week numbers -- never bare counts or campaign-level
     generalities. Keep this order, so every brand reads the same:
     *Scope and data confidence* (step 1 and step 10), *Executive read*
     (one sentence each on sales, efficiency and the main driver), then:
     - *WoW read*: sales, ad sales, spend, TACOS, Real ACOS, margin
       with ▲/▼, plus 1-2 sentences of interpretation tied to the
       brand's lens and situation.
     - *What changed*: the step 3 drivers, ranked by absolute delta,
       with the Change History context.
     - *Harvest* (from the step 4 search-term pull): each converting
       term worth graduating -- `"term" -- campaign, X orders, CVR y%,
       ACOS z% -> create SKW exact (Rank or Profit per SV/intent)`.
     - *Negate*: each wasted term/ASIN -- `"term" -- campaign, $spend,
       0 orders -> add negative exact in <campaign/ad group>`. Respect
       the philosophy: never propose negating a Rank/SKW term on ACOS
       alone.
     - *Flags*: active first (goal-aware, step 6), suppressed separately
       with the reason; never re-promote a suppressed one.
     - *Pacing*: the step 7 read, or "Pacing unavailable: no monthly
       budget is configured."
     - *Push / Pause-Optimize*: the engine's items with entity name,
       week metrics, and the specific action (bid direction, placement
       modifier, budget) -- trimmed to what matters, not all N items.
     - *Review in SYNQ*: the step 11 page and filter instructions.
   - Save the markdown weekly brief exactly where the toolkit wrote it:
     `output/{brand}/ads-monitor/{week_end}_weekly.md`.

13. **Finish with a short operator note per brand**: data source used,
    the SYNQ client confirmed, goal lens applied (and whether it changed
    this week), both windows, WoW headline (spend/TACOS/margin direction),
    push/pause-optimize/test counts, any blocked or capped data, and the
    Slack message link. End the brief with "Read-only brief: no account
    changes were made."

### What this brief does -- and does not -- do

The weekly brief **shares proposed changes** (Push -- scale these;
Pause/Optimize -- fix these) and **suggests new tests only if
pertinent** -- never a fabricated filler test to fill out the section.
It stays **strictly read-only**, exactly like the daily brief: every
Push/Pause-Optimize item is a recommendation for the operator to review,
not an executed action. If a proposal should actually happen, that is a
separate, explicit, operator-approved step routed to
`amazon-sponsored-products-bulk-files` (bulk create/update) or `amazon-ads-console`
(interactive Console work) -- stop before taking any action that could
change spend, bids, budgets, or targeting, and hand off with the
specific change named, never execute it from this skill.

## Cross-links

- Interactive Console work (bids, budgets, targeting, one-off
  investigation) -> `amazon-ads-console`.
- Bulk campaign create/update -> `amazon-sponsored-products-bulk-files`.
- Full audit narratives (prospect/bulk-file or SYNQ-managed) ->
  `amazon-audit`.

## Rules

- **Read-only, always.** This skill never creates, edits, pauses,
  archives, or bulk-uploads anything. If a flag implies an obvious
  action (raise a budget, add a negative), name it in the report and
  route the actual change to `amazon-ads-console` or `amazon-sponsored-products-bulk-files`
  with the operator's explicit go-ahead.
- **Suppressed false alarms stay suppressed.** High or volatile ACOS on
  a Rank/SKW campaign is expected (last-click top-of-search attribution,
  per `strategy.md`); a goal lens that expects rising TACOS/falling
  margin (rank-launch, liquidate) suppresses that account-level read too
  -- the toolkit already keeps these out of active flags; do not re-add
  them as a "just in case" warning when writing the Slack summary.
- **Resolve brand identity through `_local/ads-monitor/brand-aliases.json`.**
  The same brand is spelled differently across systems -- a Sellerboard
  slug like `acme-us` can be "Acme Labs US" in Notion, its Slack channel
  `#acmee-ew-amazon` (typo and all), and its channel-name word order can
  differ from every other brand's. The real mappings live only in
  `_local/ads-monitor/brand-aliases.json` and the Notion "Brand Identity /
  Alias Resolver" page, never in this repo.
  Before matching a Sellerboard feed to a shared Amazon Ops profile, a Slack
  channel, or a SYNQ client, normalize the name (lowercase, strip
  spaces/hyphens) and resolve it through this alias map -- never assume the
  same spelling carries across systems, or you will silently report the
  wrong brand's context. A SYNQ client name alone does not prove whose
  seller data it is: confirm it by SKU or title through `get_catalog`.
- **Context is re-derived every run, never assumed.** Each daily and
  weekly run rebuilds the brand's lens + situation from live Slack
  (`#<brand>-ew-amazon` + `#amazon-check`), the shared team-vault Amazon
  Ops profile, and Notion meeting notes. A stale durable situation must
  never override what the live channels/meeting notes say today.
- **Sellerboard feed URLs stay on this machine.** `sellerboard-feeds.json`
  is SECRET. Refer to a feed by brand slug only. Never echo its URL or
  token, and never pass it to Firecrawl, Monid, a browser, a web-fetch
  tool or any other third-party service: a URL that carries a token goes
  to no third-party fetcher. Only `fetch_sellerboard.py` reads it.
- **Delivered file first, local fetch on a miss.** Check
  `_local/ads-monitor/inbox/<brand>/` (and its `fetched/` subfolder)
  before running the fetcher.
- **Mock output must say PREVIEW.** Never present synthetic data as if
  it were the real account.
- **Weekly proposals never fabricate.** The Test list only ever contains
  items that map to this week's actual signals (vetted backlog or the
  signal digest) -- an empty Test list is a correct, expected outcome,
  not a gap to fill.
- **Weekly SQP movements are signals.** Do not let one weekly movement trigger an
  action. Decisions require a sufficient representative multi-week sample and
  confirmation against sales, CVR, PPC delivery, rank, promotions, and the longer
  trend.
- **Zero-spend is not performance evidence.** Exclude zero-spend targets from
  performance comparisons, but surface enabled targets above their calculated bid
  ceiling before a traffic-routing change makes them active.
- **A capped SYNQ list is never complete.** A response with a "ROW LIMIT
  REACHED" or "TRUNCATED" note is a partial list: narrow the filters,
  raise the limit, or use `group_by: total` for exact sums, and say so in
  the brief when a cut list is shown.
- Run `python3 tools/amazon-ads-monitor/selftest.py` after any change to
  the toolkit -- it must stay green.

## AdLabs carve-out only

The AdLabs carve-out account (US and CA) keeps AdLabs as its ads source
until it moves to SYNQ. Everything above applies, except the SYNQ pull steps:

- **Daily:** `start_chat_session` -> `read_resource adlabs://docs/entities`
  -> `get_entity_data(entity_type='profile'|'campaign', team_id,
  profile_id, filters=[DATE=<report date>, COMPARE_DATE])` for
  spend/sales/ACOS and campaign-level anomalies. Write the profile-level
  `{ad_spend, ad_sales, total_sales}` to a small JSON file and pass it as
  `--ads-json <file> --ads-source AdLabs`. Today's AdLabs figures are
  slightly off and correct the next day; caveat the report date only.
- **Weekly:** the same calls with `entity_type='campaign'|'target'|'keyword'`
  and `filters=[DATE=<week range>, COMPARE_DATE=<prior week range>]`, plus
  `search_term` for the same week (SP+SB). Normalize the rows into the
  shape `recommendations.normalize_entities` expects and pass them as
  `--ads-json <file> --ads-source AdLabs`.
- **Profile filter quirk:** `get_entity_data` returns rows for ALL team
  profiles, whatever `profile_id` the filter passes. Filter the response
  yourself, post-fetch, to the carve-out account's `profile_id` before
  normalizing.
- **Latest-day quirk:** AdLabs `total_*` columns can read 0 for the
  in-progress latest day. Anchor on a fully completed day, and shift the
  week end back a day if an implausible drop sits entirely in the final day.
- The carve-out account's live AdLabs dayparting schedules overwrite
  console and bulk bid edits on its campaigns; see the AdLabs carve-out
  section of `amazon-ppc-weekly-management` before proposing a bid
  change there.

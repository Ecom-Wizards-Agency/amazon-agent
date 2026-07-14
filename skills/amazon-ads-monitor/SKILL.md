---
name: amazon-ads-monitor
description: Use to produce and post the automated daily (and weekly) Amazon Ads performance brief -- previous-day trends, % changes vs prior day and trailing-7-day average, a Sellerboard-vs-AdLabs data cross-check, and goal-aware philosophy-aware flags -- to Slack. Trigger on requests like run the ads monitor, daily ads brief, post the ads report, Amazon Ads daily report, or a scheduled daily/weekly run. Read-only: never creates, changes, pauses, or archives campaigns. For interactive Console work use amazon-ads; for bulk create/update use amazon-campaign-builder; for full audit narratives use amazon-ad-audit or amazon-adlabs-audit.
---

# Amazon Ads Monitor

Browser: None; read-only; file+Slack output.

Automated performance surveillance with judgment, not a raw metric dump.
Produces a **daily previous-day** Amazon Ads report (trends + % changes,
a Sellerboard-vs-AdLabs cross-check, goal-aware flags) and posts a
compact summary to Slack. Never touches campaigns -- this skill only
reads and reports; any resulting bid/budget/keyword change is a
separate, operator-confirmed action in `amazon-ads` or
`amazon-campaign-builder`.

## Source of truth

1. **Toolkit:** `tools/amazon-ads-monitor/` -- `datasource.py` (pluggable
   data-source layer + adapters, incl. `SellerboardDataSource`),
   `analyze.py` (deltas/trends + `aggregate_week` for the weekly WoW
   read), `flags.py` (severity-tagged, philosophy-aware, goal-lens-aware
   flags), `crosscheck.py` (Sellerboard-vs-AdLabs data-quality verdict),
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
4. **Corroborated heuristics:** `_local/ads-knowledge/knowledge-digest.md`
   (bidding/troubleshooting/reporting-metrics themes) for the reasoning
   behind each flag's likely cause text.

## Data source priority

**Sellerboard's "Dashboard Totals" CSV is the PRIMARY source** (as of
2026-07-14) -- whole-account truth (total sales, ad spend, ad sales,
Real ACOS, margin, units, refunds, sessions), parsed by
`SellerboardDataSource`/`parse_sellerboard_csv` in `datasource.py`.
**AdLabs is the ad-granular cross-check** paired against it via
`crosscheck.py` (ad spend, ad sales, total sales, within +/-7% by
default -> "verified", else "mismatch"), and its own campaign-level
detail. Amazon Ads API v3 (`SPAdsApiDataSource`) is now a **secondary**
fallback (not live-tested) for accounts without Sellerboard/AdLabs
access. Mock (`--source mock`) remains the no-credentials PREVIEW path.
Note: today's AdLabs figures are known to be slightly off and correct
themselves tomorrow -- caveat this for the **report date only**, not
older days.

## Getting the Sellerboard CSV: two ways, file-first

Each brand's feed is fetched **file-first (credit-free)**, with a
firecrawl fallback that costs Firecrawl credits:

1. **PRIMARY -- delivered file, no credits.** Check
   `_local/ads-monitor/inbox/<brand>/` for a CSV already there (Sellerboard
   can email/auto-export the report to a synced folder that lands here).
   A file counts as fresh if its date/window covers the report date (7d
   feed for the daily brief). If a fresh file exists, use it directly --
   no MCP call needed for this brand.
2. **FALLBACK -- firecrawl fetch, ~1 credit per feed.** If no fresh
   delivered file exists, look up the brand's feed URL(s) in
   `_local/ads-monitor/sellerboard-feeds.json` (SECRET -- never echo the
   full URL/token in chat or commit it) and call **`firecrawl_scrape`**
   with `formats: ["markdown"]` (this endpoint returns the raw CSV text
   in the markdown field). Save the returned text to
   `_local/ads-monitor/inbox/<brand>/` (so the next run can use it
   file-first) before handing it to the toolkit. Note in the operator
   note that this brand cost a Firecrawl credit.
   - A just-requested Sellerboard report can come back **blank** -- that
     is not an error (`parse_sellerboard_csv` returns `[]`); per
     `sellerboard-feeds.json`'s `"fallback": "if_sellerboard_blank_use_adlabs"`,
     fall back to AdLabs entirely for that brand/day and label the report
     accordingly.

## Flow (per brand)

1. **Obtain the CSV** per the file-first/firecrawl-fallback rule above,
   then run the toolkit against it (pick the 7d window for the daily
   brief; use the 30d feed only if the 7d one is missing/blank):

   ```bash
   python3 tools/amazon-ads-monitor/run_monitor.py \
     --source sellerboard --csv <inbox path>[,<second feed path>] \
     --accounts <brand-slug> --goal <lens from step 4, or omit for neutral> \
     --date <yesterday, or the requested report date> \
     --adlabs-json <path to a small JSON file with step 2's figures, or omit> \
     --out output --slack-json <path or ->
   ```

   If the Sellerboard feed is blank/missing for this brand/day, skip to
   AdLabs as the sole source for the write-up and say so plainly in the
   report -- do not silently present AdLabs-only figures as if they were
   cross-checked.

2. **Pull AdLabs ad detail** (for the cross-check + campaign anomalies):
   `start_chat_session` -> `read_resource adlabs://docs/entities` ->
   `get_entity_data(entity_type='profile'|'campaign', team_id, profile_id,
   filters=[DATE=<report date>, COMPARE_DATE])` for spend/sales/ACOS and
   campaign-level anomalies. Write the profile-level `{ad_spend, ad_sales,
   total_sales}` to a small JSON file and pass it via `--adlabs-json` above
   so the toolkit runs `crosscheck.py` and the report shows the verdict.
   Caveat **today's** AdLabs figures only (they correct tomorrow); older
   days are reliable.
3. **Cross-check** happens inside the CLI call above (step 1's
   `--adlabs-json`); the rendered report/Slack payload already shows
   "data verified" or "data mismatch (ad spend SB $X vs AdLabs $Y, +Z%)"
   -- don't recompute or restate it differently in the write-up.
4. **Brand context -- RE-DERIVE EVERY RUN (MCP, done here, not in the
   Python toolkit).** Situations change daily (hijackers, listing
   takedowns, buy-box loss, offboarding, launches), so never trust a
   cached snapshot on its own -- rebuild the brand's context from the live
   sources every run, in this order:
   - **Seed:** read the brand's lens + situation from
     `_local/ads-monitor/brand-goals.json` (a fallback cache only), then
     verify/refresh it against the live sources below. Lenses: rank-launch,
     scale, profit-maintain, defend, maintain, liquidate, inactive (see
     `flags.py` `GOAL_LENSES`). Unknown -> omit `--goal` (neutral lens).
   - **Notion MCP -- Ops Profiles + meeting database**: `search` + `fetch`
     the brand's row in the "Amazon Agent Ops Profiles" database (goal/
     stage if the field exists) AND the Notion **meeting database** for the
     brand's most recent meeting notes -- meeting notes carry the freshest
     operational context and usually predate any profile-field update.
   - **Slack MCP -- read_channel**: read the brand's `#<brand>-ew-amazon`
     channel and `#amazon-check` for the report window plus a few days of
     look-back for launches, promos, price/stock changes, or incidents.
   - **Reconcile + persist:** if the live sources show the lens or
     situation changed since `brand-goals.json`, use the live version for
     this run AND update `brand-goals.json` (the situation string, and the
     lens if it changed) so the cache stays current for the next run. Pass
     the resolved lens as `--goal`. If a flag matches a known intentional
     change from Slack/meeting notes, annotate it in the Slack/markdown
     write-up rather than presenting it as a surprise (don't suppress it in
     the file).
   - This step only reads Notion and Slack (and writes the local
     `brand-goals.json` cache); it never posts to or edits Notion/Slack.
5. **Deliver.**
   - **Slack MCP -- send_message**: post the Slack payload (from
     `--slack-json`, annotated per step 4 if anything needed
     softening/context) to **#amazon-daily-report** (channel ID
     `C0BGWLFMW3V`). Start the message with a `<!here>` mention and a
     one-line header (e.g. "<!here> Daily Amazon Ads report -- <date>")
     -- `<!here>` daily, not `<!channel>`, to avoid pinging everyone
     every day. When running multiple brands in one pass, lead with
     any brand that has a critical/alert flag or a data-mismatch verdict
     before the clean ones.
   - Save the markdown report exactly where the toolkit wrote it:
     `output/{brand}/ads-monitor/{date}_daily.md`. Do not duplicate it
     elsewhere.
6. **Finish with a short operator note per brand**: data source used
   (sellerboard file/firecrawl/AdLabs-fallback/mock-PREVIEW), goal lens
   applied, cross-check verdict, report date, critical/alert/warn/info
   counts, what context enrichment changed (if anything), and the Slack
   message link.

## Exact MCP tools this flow uses

- `firecrawl_scrape` (fallback CSV fetch only, formats `["markdown"]`).
- AdLabs: `start_chat_session`, `read_resource`, `get_entity_data`
  (and `query` for anything the entity-data shape doesn't cover).
- Notion: `search`, `fetch` (Amazon Agent Ops Profiles row lookup).
- Slack: `read_channel` (brand + `#amazon-check` context), `send_message`
  (posting the final report to `#amazon-daily-report`).

## Weekly variant

A weekly brief (`{week_end}_weekly.md`) shares the daily brief's data
sources and philosophy but replaces the day-over-day read with a
week-over-week (WoW) read, then adds three read-only PROPOSAL lists on
top: **Push**, **Pause/Optimize**, and **Test** (only if pertinent). It
never executes anything -- see Rules below.

### Toolkit

`tools/amazon-ads-monitor/run_weekly.py` is the weekly CLI:
`analyze.aggregate_week` (this-week vs last-week totals + WoW deltas),
`recommendations.py` (the Push/Pause-Optimize/Test engine), and
`report.render_weekly_markdown`/`render_weekly_slack`. See each module's
docstring for exact signatures.

### Flow (per brand, weekly)

1. **Aggregate the week from Sellerboard.** Get the brand's Sellerboard
   CSV the same file-first/firecrawl-fallback way as the daily brief
   (prefer the 30d feed so both this week and last week are covered),
   then run:

   ```bash
   python3 tools/amazon-ads-monitor/run_weekly.py \
     --csv <inbox path 30d>[,<7d path>] --account <brand-slug> \
     --goal <lens from step 4> --situation "<brief free-text from step 4>" \
     --date <the latest FULLY COMPLETED day> \
     --adlabs-json <path to step 2's normalized entities JSON, or omit> \
     --signal-digest _local/ads-signals/<ISO-year>-W<week>/digest.md \
     --out output --slack-json <path or ->
   ```

   **Anchor the week on a completed day, never today.** Sellerboard's
   `total_*` columns (and AdLabs' figures generally) can read as 0 or be
   incomplete for the still-in-progress current day -- pass `--date` for
   the most recent day you can confirm is fully closed out (typically
   yesterday), the same rule the daily brief follows.

2. **Pull AdLabs campaign+target-level data for the completed week**,
   comparing it against the prior week (`COMPARE_DATE` = the prior
   7-day window): `start_chat_session` -> `read_resource
   adlabs://docs/entities` -> `get_entity_data(entity_type='campaign'|
   'target'|'keyword', team_id, profile_id, filters=[DATE=<week
   range>, COMPARE_DATE=<prior week range>])`. Normalize the response
   into the shape `recommendations.normalize_entities` expects (`{
   entity_type, name, campaign_name, campaign_id, category (optional),
   match_type, impressions, clicks, spend, sales, orders, daily_budget,
   budget_capped_days}`), write it to a JSON file, and pass it via
   `--adlabs-json`. Omitting it is a valid run -- Push/Pause-Optimize
   just come back empty with a note, not an error.

   **Two AdLabs quirks discovered in testing, both required for a
   correct pull:**
   - **(a) `get_entity_data` returns rows for ALL team profiles,
     regardless of the `profile_id` passed in the filter.** Always
     filter the response yourself, post-fetch, `WHERE profile_id =
     <this brand's profile_id>` before normalizing -- passing the
     filter to the call alone is not enough and will silently mix in
     other brands' campaigns/targets.
   - **(b) `total_*` columns can read 0 for the in-progress latest
     day.** This is the same reason step 1 anchors the week on a fully
     completed day, not today -- if the week's last day is still
     accumulating, its totals (and therefore the whole week's sum) will
     understate reality. Re-pull or shift the week-end back a day if
     you see an implausible drop concentrated entirely in the final day.

3. **Run the recommendations engine.** This happens inside step 1's CLI
   call (`recommendations.build_recommendations`): it classifies every
   normalized entity by strategy category (Rank/Discovery/Profit/Shield)
   and proposes goal-aware Push / Pause-Optimize items, plus Test ideas
   filtered against this week's actual signals (never fabricated to
   fill space -- see recommendations.py's module docstring for the exact
   rules, especially that a Rank/SKW target is never proposed for a cut
   on ACOS grounds alone).

4. **Merge the signal digest and apply the goal lens (MCP context,
   done here, not in the Python toolkit):**
   - **Signal digest:** read `_local/ads-signals/<ISO-year>-W<week>/digest.md`
     (produced by the weekly Firecrawl ingestion pipeline, see
     `_local/ads-signals/README.md` -- each entry has already passed the
     Phase-0 critical-review protocol) and pass its path via
     `--signal-digest`; `recommendations.parse_signal_digest_markdown`
     parses it and folds any digest item that maps to this week's actual
     signals into the Test list. A digest with no pertinent item for
     this brand contributes nothing -- that's correct, not a bug.
   - **Goal lens -- RE-DERIVE EVERY RUN:** seed from
     `_local/ads-monitor/brand-goals.json` (fallback cache only), then
     refresh it against the live sources: the brand's row in the Notion
     **Amazon Agent Ops Profiles** database AND the Notion **meeting
     database** (most recent meeting notes -- the freshest operational
     context), plus its Slack channel (`#<brand>-ew-amazon` +
     `#amazon-check`, Slack MCP `read_channel`). Pass the resolved lens as
     `--goal` and a short situation string as `--situation` (the latter
     lightly tags Test selection -- e.g. a hijacker or a recurring ACOS
     spike). If the live sources show the lens/situation changed, use the
     live version this run AND update `brand-goals.json` so the cache stays
     current. This step only reads Notion/Slack (and writes the local
     cache); it never posts or edits Notion/Slack during enrichment.

5. **Deliver.**
   - **Slack MCP -- send_message**: post the weekly Slack payload (from
     `--slack-json`) to **#amazon-daily-report** (channel ID
     `C0BGWLFMW3V`) -- the same channel as the daily brief. Start the
     message with a `<!channel>` mention and a one-line header (e.g.
     "<!channel> Weekly Amazon Ads analysis -- week ending <date>");
     weekly posts tag the whole channel. Lead with any
     brand whose Push/Pause-Optimize list flags something urgent (a
     Rank/Shield target losing impression share, a self-competition
     conflict) before the routine ones.
   - Save the markdown weekly brief exactly where the toolkit wrote it:
     `output/{brand}/ads-monitor/{week_end}_weekly.md`.

6. **Finish with a short operator note per brand**: data source used,
   goal lens applied (and whether it changed this week), week-end date,
   WoW headline (spend/TACOS/margin direction), push/pause-optimize/test
   counts, and the Slack message link.

### What this brief does -- and does not -- do

The weekly brief **shares proposed changes** (Push -- scale these;
Pause/Optimize -- fix these) and **suggests new tests only if
pertinent** -- never a fabricated filler test to fill out the section.
It stays **strictly read-only**, exactly like the daily brief: every
Push/Pause-Optimize item is a recommendation for the operator to review,
not an executed action. If a proposal should actually happen, that is a
separate, explicit, operator-approved step routed to
`amazon-campaign-builder` (bulk create/update) or `amazon-ads`
(interactive Console work) -- stop before taking any action that could
change spend, bids, budgets, or targeting, and hand off with the
specific change named, never execute it from this skill.

## Cross-links

- Interactive Console work (bids, budgets, targeting, one-off
  investigation) -> `amazon-ads`.
- Bulk campaign create/update -> `amazon-campaign-builder`.
- Full audit narratives (prospect/bulk-file or AdLabs-managed) ->
  `amazon-ad-audit` / `amazon-adlabs-audit`.

## Rules

- **Read-only, always.** This skill never creates, edits, pauses,
  archives, or bulk-uploads anything. If a flag implies an obvious
  action (raise a budget, add a negative), name it in the report and
  route the actual change to `amazon-ads` or `amazon-campaign-builder`
  with the operator's explicit go-ahead.
- **Suppressed false alarms stay suppressed.** High or volatile ACOS on
  a Rank/SKW campaign is expected (last-click top-of-search attribution,
  per `strategy.md`); a goal lens that expects rising TACOS/falling
  margin (rank-launch, liquidate) suppresses that account-level read too
  -- the toolkit already keeps these out of active flags; do not re-add
  them as a "just in case" warning when writing the Slack summary.
- **Resolve brand identity through `_local/ads-monitor/brand-aliases.json`.**
  The same brand is spelled differently across systems -- Sellerboard slug
  `swissklip` is "Swissker US" in Notion; `sven-island` is "Svens Island";
  `allmedica-sheko` is "Sheko"; the Alphainfuse Slack channel is
  `#alphaninfuse-ew-amazon` (extra n); Pawsan's is `#pawsan-amazon-ew`.
  Before matching a Sellerboard feed to a Notion Ops Profile row, a Slack
  channel, or an AdLabs profile, normalize the name (lowercase, strip
  spaces/hyphens) and resolve it through this alias map -- never assume the
  same spelling carries across systems, or you will silently report the
  wrong brand's context.
- **Context is re-derived every run, never assumed.** Each daily and
  weekly run rebuilds the brand's lens + situation from live Slack
  (`#<brand>-ew-amazon` + `#amazon-check`) and Notion (Ops Profiles + the
  meeting database); `_local/ads-monitor/brand-goals.json` is only a
  fallback seed and is updated in place when the live sources show a
  change. A stale cached situation must never override what the live
  channels/meeting notes say today.
- **Never echo Sellerboard feed tokens.** `sellerboard-feeds.json` is
  SECRET; reference a brand's feed by slug/name in chat, never paste the
  full URL with its embedded token.
- **File-first, firecrawl only on a miss.** Always check
  `_local/ads-monitor/inbox/<brand>/` before calling `firecrawl_scrape` --
  every avoidable fallback call is a wasted Firecrawl credit.
- **Mock output must say PREVIEW.** Never present synthetic data as if
  it were the real account.
- **Weekly proposals never fabricate.** The Test list only ever contains
  items that map to this week's actual signals (vetted backlog or the
  signal digest) -- an empty Test list is a correct, expected outcome,
  not a gap to fill.
- Run `python3 tools/amazon-ads-monitor/selftest.py` after any change to
  the toolkit -- it must stay green.

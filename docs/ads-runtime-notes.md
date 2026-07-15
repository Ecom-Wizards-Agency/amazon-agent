# Ads Monitor & Campaign Builder v2 - Team Runtime Notes

Added 2026-07. Read `AGENTS.md` first; this note covers the new advertising capabilities and how the
team runs them.

## New capabilities

### amazon-ads-monitor (daily + weekly performance briefs)
Read-only. Posts to Slack. Data comes from two sources, cross-checked:
- Sellerboard = whole-account truth (revenue, ad sales, ad spend, TACOS, margin, orders).
- AdLabs = granular advertising detail (campaign/target spend, sales, ACOS) for the same period.
- A cross-check gate compares the overlapping figures; within tolerance it marks the report
  "data verified", otherwise it flags a "data mismatch".
Flags are goal-aware (per the brand's lens) and philosophy-aware (rank-first: ACOS is an indicator,
not a decision factor; high top-of-search ACOS on Rank campaigns is expected and suppressed).
The weekly brief additionally proposes PUSH / PAUSE-OPTIMIZE / TEST actions and folds in the weekly
external-signal digest. Proposals only; it never changes campaigns.

Run examples:
```
python3 tools/amazon-ads-monitor/run_monitor.py --source sellerboard --csv <daily.csv> --goal <lens>
python3 tools/amazon-ads-monitor/run_weekly.py  --csv <csvs> --adlabs-json <adlabs.json> --goal <lens> --signal-digest <digest.md>
python3 tools/amazon-ads-monitor/selftest.py    # regression suite
```

### amazon-campaign-builder v2 (create AND update)
Creates SP campaigns and now UPDATES existing ones as Bulk Operations files, from a text brief or a
keyword-research workbook, using the EW naming convention and per-type bidding. File-only output,
paused by default; uploading stays a separate operator-confirmed step. See
`tools/amazon-campaign-builder/references/bulksheets-2.0-reference.md` for the Amazon format rules
(entity IDs, partial-update semantics, portfolio re-inclusion, immutable keyword text, archive cascade).

## What lives in _local/ (NOT in git - required to actually run)

GitHub intentionally excludes `_local/`. Without it the skills describe the work but cannot run real
reports. Get `_local/` from the Amazon Agent Team Pack (shared privately), not from GitHub:
- `_local/ads-strategy/` : rank-first strategy + PPC naming convention (source of truth, from Notion)
- `_local/ads-knowledge/` : distilled PPC knowledge base + vetted test backlog
- `_local/ads-signals/`  : news/creator sources + the weekly signal digest
- `_local/ads-monitor/`  : `sellerboard-feeds.json` (SECRET tokens), `brand-goals.json`, config,
  `inbox/` (delivered CSVs), `samples/`
Each teammate keeps their own `_local/` plus their own connector credentials.

## Cowork vs Slack - who runs what

- Cowork (desktop): the operator with full `_local/` context and the live connectors (AdLabs,
  Notion, Sellerboard feeds, Slack). This is where real daily/weekly reports and campaign files run.
- Slack @Claude (Claude Tag): repo-bound; good for questions, code changes, and research. It has the
  committed code but not `_local/` or the connectors, so it is not the place to execute real reports.
- Branch etiquette: work on feature branches and PR into `main`; avoid two agents pushing `main` at
  once. The Slack agent uses `claude/slack-session-*` branches.

## Known operational caveats

- AdLabs `get_entity_data` returns ALL team profiles regardless of the `profile_id` argument - filter
  post-fetch. Its `total_*` columns read 0 for the in-progress latest day, so the daily "today" figure
  is provisional (corrects next day); anchor weekly aggregates on completed days.
- The Slack connector must be connected for scheduled reports to post.
- Scheduled tasks (daily ~10:30 Lisbon; weekly signal digest + weekly brief Monday morning) only run
  while the desktop app is open.
- Sellerboard CSV delimiter varies by account (comma vs semicolon) and ad-spend columns are negative;
  the parser handles both. Feeds can be pulled credit-free from a delivered folder or via Firecrawl.

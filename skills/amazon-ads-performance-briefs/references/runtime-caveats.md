# Runtime Caveats

Mode browser: None; applies to both daily and weekly briefs.

Known operational caveats for the brief toolkit and its data sources, recorded in 07.2026 (Sellerboard, scheduler, Slack) and 11.2026 (SYNQ). Re-verify a caveat that looks stale before relying on it.

- Every SYNQ tool caps at `limit` (max 2000) and prefixes a "ROW LIMIT REACHED" or "TRUNCATED" note when rows were cut. Save each response as `{"note", "rows"}` and never present a cut list as complete: narrow the filters, raise the limit, or use `group_by: total` for exact sums. Sums over truncated grouped rows are not account totals.
- SYNQ Sales and Traffic (`get_sales_traffic_daily`) runs 2 to 3 days behind ads data, so the previous day's total sales come from Sellerboard. One 502 Bad Gateway was seen on it; a single retry worked.
- The attribution window behind SYNQ `sales` is not confirmed (asked of SYNQ). Label it SYNQ-reported sales; an ad-sales gap against Sellerboard with matching spend is an attribution difference, not lost data.
- SYNQ metric rows carry no current bids, budgets, budget-capped days, match type or top-of-search impression share. Match type joins in from `get_search_terms`. This skill reads no browser page for the rest: the brief names each gap and points to the skill that can read it, `amazon-ads-console` for current bids, budgets, budget-capped days and top-of-search share, or the read-only Bid Optimizer check in `amazon-ppc-weekly-management` for runner membership.
- `get_daily_metrics` keyword rows come back empty; keywords appear as target rows, which carry `keyword_text`. Some `get_metrics` rows carry an older `computed_at`; those are inactive entities.
- The newest day of SYNQ ads data can still settle. Treat a same-day figure as provisional and anchor weekly aggregates on completed days.
- AdLabs carve-out only: AdLabs `get_entity_data` returns rows for every team profile whatever `profile_id` the call passes, so filter to the carve-out account's `profile_id` after the fetch; its `total_*` columns read 0 for the in-progress latest day.
- Sellerboard feeds come from a delivered inbox file or the local `fetch_sellerboard.py` GET to the feed's own host. The earlier Firecrawl route (07.2026) sent feed tokens to a third party and is retired. A runtime without shell network access cannot run the fetcher, so its brief is SYNQ-only unless a file was delivered.
- The Sellerboard CSV delimiter varies by account (comma or semicolon), and ad-spend columns are negative. `parse_sellerboard_csv` handles both, so pass the file as delivered.
- A scheduled brief runs only while its host scheduler is running. A desktop-app scheduler skips runs while the app is closed, so a missing brief is a scheduler question before it is a data question.
- A scheduled brief posts only when the actor's Slack posting identity is available. Missing access fails closed and produces no post; it never falls back to another identity.

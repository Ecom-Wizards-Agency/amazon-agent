# Runtime Caveats

Mode browser: None; applies to both daily and weekly briefs.

Known operational caveats for the brief toolkit and its data sources, first recorded in 07.2026. Re-verify a caveat that looks stale before relying on it.

- AdLabs `get_entity_data` returns rows for every team profile, whatever `profile_id` the call passes. Filter the response to the brand's `profile_id` after the fetch, in the daily pull as well as the weekly one.
- AdLabs `total_*` columns read 0 for the in-progress latest day. A same-day figure is provisional and corrects the next day; anchor weekly aggregates on completed days.
- The Sellerboard CSV delimiter varies by account (comma or semicolon), and ad-spend columns are negative. `parse_sellerboard_csv` handles both, so pass the file as delivered.
- A scheduled brief runs only while its host scheduler is running. A desktop-app scheduler skips runs while the app is closed, so a missing brief is a scheduler question before it is a data question.
- A scheduled brief posts only when the actor's Slack posting identity is available. Missing access fails closed and produces no post; it never falls back to another identity.

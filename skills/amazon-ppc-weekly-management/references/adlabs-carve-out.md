# AdLabs carve-out only

This file applies only to the AdLabs carve-out account, US and CA (identification: `docs/synq-mcp.md`). Every other client runs the SYNQ loop in `SKILL.md`. AdLabs was retired for everyone else on 03.11.2026; the carve-out account keeps its full AdLabs loop (optimizer, harvest, opt-groups and live AdLabs dayparting schedules) until it moves to SYNQ.

**The overwrite trap comes first.** The carve-out account's AdLabs dayparting schedules multiply a stored base bid on every hourly run. A bid edited in the Ads console, a bulk file or any tool other than AdLabs on an assigned campaign is overwritten at the next run. Make every bid change on this account in AdLabs. A SYNQ runner never takes one of its campaigns while an AdLabs optimizer group or dayparting schedule still covers it (one-writer rule).

The staged-apply standard, the standing conventions, the stock and budget-delivery gates, the weekly brief, graduation doctrine and output rules in `SKILL.md` still apply. This file replaces only the data source, the write path and the steps that are AdLabs tools.

## Startup

1. Run `python3 tools/ads_recall.py management` and read the returned decision, Playbook, and Research files in order. Continue quietly when it returns no paths.
2. `start_chat_session` -> `read_resource(adlabs://instructions)`; pass `chat_session_id` on every call.
3. Resolve team/profile; read `adlabs://profiles/<slug>` (profile_id, Target ACOS) and `context_and_prompts(get_context, PROFILE, ...)`.
4. Load break-even ACOS from the client's Sellerboard P&L (margin % + Real ACOS %). If unconfirmed, it is an ASSUMPTION and every verdict in the run says so.
5. Ask once for the week window (dates are always operator-supplied; the optimizer and harvesting tools must never default them).

## Write policy

Every write follows the same gate: **preview -> operator approval of that specific batch -> apply with a meaningful `note`**. A general "sounds good" earlier in the chat is not approval for a new batch. Consistent with the universal guardrail in `AGENTS.md`: no campaign/budget/bid change without explicit per-action operator instruction. Never create or edit Campaign Optimizer automation rules via MCP (only pause/enable exists there anyway); rule definitions live in the AdLabs UI and are documented per client in the client profile.

AdLabs-specific staged-apply lines:

- **Batch = one opt-group, never the whole account.** Never mix opt-groups in one apply.
- The apply `note` carries the batch tag.
- Past applies can be backfilled into `batches.py snapshot` from AdLabs `logs` with `--date`.
- **Scoring windows** come from one source: AdLabs `product`/`profile` with explicit DATE + COMPARE_DATE.
- **Revert**: `batches.py revert --client <slug> --tag <tag>` emits the old values as an `update_entities` payload. A revert is a write like any other (preview -> approval -> apply), then `mark-reverted`.

## Stock gate source

Pull `product` stock fields (`out_of_stock_days`, `days_of_cover`, `fulfillable_units`). Amazon deranks what it cannot ship; an OOS ASIN's campaigns get paused/parked (tag the batch so the pause is reversible), not bid-optimized. Anything the stock gate catches leaves the rest of this run.

ToS impression share for the four-axis read comes from the AdLabs target field `top_of_search_impression_share`. Campaign creation still goes through `amazon-sponsored-products-bulk-files` (bulk file, paused; AdLabs MCP cannot create campaigns).

## Weekly brief input

`tools/amazon-ads-monitor/run_weekly.py` takes the normalized AdLabs weekly entities through `--adlabs-json`. Rank rows, pacing and the other flags are the same as in `SKILL.md`.

## Opt-group audit (the unit of strategy)

`optimizer(list_groups)` and check against the doctrine standard (strategy.json `management.opt_groups`):

- Four groups mapped 1:1 to roles. Rank: tacos 1.5-2x break-even, INCREASE_SALES, bid floor TIMES_CPC ~0.5, bid_max_decrease PERCENT ~0.10, placement_max_decrease capped low (the loose leash: the optimizer trims true waste but can never choke a push). Discovery: tacos = BE, BALANCED, bid ceiling. Profit: tacos = BE or client target, REDUCE_ACOS when over. Shield: high tacos, BALANCED.
- Every campaign assigned to exactly one role group; unassigned campaigns are a finding.
- Fixes go through the write gate as `create_group` / `update_group` / `assign_campaigns`. **`update_group` has PUT semantics**: always `list_groups` first and resend every current field, or omitted settings silently reset.

## Bid run (weekly)

Per opt-group: `optimizer(preview_optimization, reference=<campaign reference>, start_date/end_date=<operator dates>, tacos=<group target>)` -> `query` the preview reference and read `change_reasons` per entity. Veto before proposing:

- Protect any keyword whose organic rank (SoldScope rank tracker) is improving or that sits in a mid-flight push; cross out its decreases.
- If pacing says **act**, present the cuts in the fixed order: waste (high-spend-no-sales) -> discovery -> profit trims. Rank cuts only with an explicit operator decision, never bundled into the batch.
- If pacing says **underpace**, lead with the PUSH list and capped Rank budgets instead.

The whole-system bid and placement doctrine in `SKILL.md` applies. Do not trust an AdLabs placement recommendation automatically: if it conflicts with the placement RPC relationship, stop for review.

**Caps are ceilings, never steps** (operator, 2026-07-26). The opt-group's `bid_max_increase/decrease` and `placement_max_*` settings clamp the calculated change. Only apply values supported by a preview or the whole-system calculation; never author a change equal to the cap merely because the cap exists. Validate every batch before approval with `batches.py validate`.

Assemble the surviving preview into per-opt-group batches per the staged-apply standard (a group's bids, placements, negatives, and budget may share one batch; rows labeled per lever), then per batch: summary (entities, old -> new, reasons, expected spend delta) -> approval -> snapshot -> `apply_optimization(preview_id, note=<tag + reason>)` with a filtered reference for the partial apply. Placements: monthly cadence, small steps; use `skip_placement_optimization` on the weekly bid runs in placement-off weeks.

## Harvest run (weekly or biweekly)

`harvesting(preview_harvest)` over qualifying Discovery search terms (needs campaign mappings; `campaign_mapping(list_mapping_targets)` first). The harvest and negation doctrine in `SKILL.md` applies. Filter every row with a non-empty `warning` and review the destination role before approval.

## Graduation

For each GRADUATE keyword: step the ToS modifier and bid down toward break-even over 2-3 optimizer cycles, respecting the group's max-decrease. Never cliff-drop.

## AdLabs dayparting schedules

Read the current `adlabs://docs/dayparting_actions` resource before operating. It is the execution authority.

### Before a write

1. Start one AdLabs chat session and read `adlabs://instructions`.
2. Resolve the exact team and profile and verify the profile timezone.
3. List existing dayparting schedules and check whether the target campaigns are already assigned.
4. Read the current schedule before editing it. Unmentioned cells on an update keep their stored values.
5. Render the proposed grid with `dry_run=true`.
6. Show the schedule name, state, timezone, campaign count, changed-cell count, minimum and maximum percentage, and the warning below.
7. Obtain explicit approval for the exact create, update, assignment, pause, clone, or delete operation.

Required warning:

> While dayparting is assigned, make bid changes in AdLabs. Bid changes made elsewhere can be overwritten because the schedule continues to multiply its stored base bid.

### Units and timing

- Grid cells are whole percentages. `20` means +20%, `-25` means -25%, and `0` means base bid.
- Accepted values are -99 through 300.
- Grid hours use the profile's local timezone.
- A write does not immediately prove live bids changed. It applies on the next AdLabs hourly run.
- Assignment is separate from schedule creation. A created schedule affects nothing until campaigns are assigned.

### Safer operations

- Create or update: dry run first, then one approved write.
- Pause: preserves the grid and rolls bids back asynchronously.
- Delete: destructive and not recoverable. Prefer pause unless deletion is explicitly required.
- Clone: validate the resulting grid and name collision in dry-run mode.
- Timeout: re-read schedules before retrying. A timed-out create may already have succeeded.

Do not report bids as restored or applied until the relevant subsequent state is observable. Logs do not prove every asynchronous rollback.

### Hourly analysis

The retired dayparting skill's analyzer stays available for a carve-out schedule proposal: `tools/amazon-dayparting/analyze_dayparting.py` (usage and retired note in `tools/amazon-dayparting/README.md`). Its output is a proposed grid only; the write steps above still apply.

## Moving the carve-out account to SYNQ

Planned, not yet scheduled: take a live-bid snapshot, unassign the AdLabs dayparting schedules and optimizer groups, then set up the SYNQ runner, goals and roles. Each step is its own exact-action approval. Until then this file stays the carve-out account's loop.

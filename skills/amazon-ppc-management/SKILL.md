---
name: amazon-ppc-management
description: Weekly PPC management loop for AdLabs-managed accounts. Trigger on `/ppc-manage` or "run the weekly ads management" for a client. Stock gate, run-rate pacing, Rank Radar graduation, opt-group audit, then AdLabs optimizer/harvest preview -> operator approval -> staged lever-batch applies (snapshot, cooldown, revert). Audits stay in `amazon-audit` (diagnose); this skill operates.
---

# Amazon PPC Management (weekly loop, AdLabs-managed accounts)

Browser: None (AdLabs MCP + DataDive MCP; Sellerboard CSV via the ads-monitor inbox convention).

Use this when the operator asks to RUN a managed account's week: adjust bids, budgets, opt-groups, harvests. It is the operating counterpart to `amazon-audit` (diagnose) and `amazon-ads-monitor` (observe). Prospects and bulk-file accounts also route to `amazon-audit`; this skill requires a live AdLabs connection.

Doctrine source of truth: `_local/ads-strategy/strategy.md` v3 (Run-rate governor, Opt-group standard, Rank keyword lifecycle, Optimizer cadence) and `_local/ads-strategy/strategy.json` `management` bands. Never guess thresholds; if the local file is missing, ask the operator.

**The core stance.** Run rate is a portfolio governor on top of the rank engine, not the strategy. The AdLabs bid optimizer prices every target off revenue per click x the opt-group's target ACOS, which is exactly right for ACOS optimization; our job on top of it is (a) point it at the right target ACOS per role, (b) protect deliberate above-break-even rank pushes from it, and (c) stop paying above break-even once a keyword's organic rank has stuck. Never "stupidly optimize" a campaign whose job the blended numbers cannot see.

## Write policy (critical, differs from the audit skill)

Every write follows the same gate: **preview -> operator approval of that specific batch -> apply with a meaningful `note`**. A general "sounds good" earlier in the chat is not approval for a new batch. Consistent with the universal guardrail in `AGENTS.md`: no campaign/budget/bid change without explicit per-action operator instruction. Never create or edit Campaign Optimizer automation rules via MCP (only pause/enable exists there anyway); rule definitions live in the AdLabs UI and are documented per client in the client profile.

## Staged applies (attribution + revert standard, operator decision 2026-07-26)

Never optimize the whole account in one apply. A whole-account apply cannot be reverted cleanly, and next week's numbers blend every cause (the three Jul-24 whole-account runs are the cautionary tale). Thresholds live in strategy.json `management.staged_apply`.

- **Batch = one opt-group, never the whole account** (operator refinement 2026-07-26). Within a group's batch, several levers may land together: bids, placements, negatives, budget for that group. Label every row with its lever (`waste-cut`, `bid-down`, `push`, `budget`, `placement`, `harvest`, `negative`, `pause`) so scoring stays per-lever. Never mix opt-groups in one apply.
- **Tag every batch** `<client>-<YYYY>W<ww>-<group>`, with a `-<lever>` suffix when a batch is single-lever (e.g. `acme-2026W31-profit` or `acme-2026W31-profit-bid-down`). The apply `note` carries the tag.
- **Per-run cap**: at most `max_batches_per_run` (3) batches per weekly run, highest conviction first. Queued batches are listed in the action log, never silently dropped.
- **Group cadence + priority (operator, 2026-07-26)**: under the cap, Rank and Profit batches come first, Discovery second, Shield last. Rank and Profit are weekly; Discovery weekly or biweekly; Shield biweekly, batched into the same run as Discovery. Rank may run more often than weekly during a strong push: mid-push Rank keywords may be re-stepped after `push_rank_min_days` (3) instead of the full cooldown, recorded as bypass `rank_push`.
- **7-day entity cooldown**: an entity written by an applied batch is not re-touched for `cooldown_days` (7), so each change gets one readable week. Bypasses (always recorded in the batch file): stock gate, fraud/budget-cap emergency, pacing **act**. Check candidates before proposing: `python3 tools/amazon-ppc-management/batches.py check --client <slug> --rows <rows.json>`.
- **Snapshot before apply**: after approval and before the write, save the old -> new rows: `batches.py snapshot --client <slug> --tag <tag> --lever <lever> --group <group> --note "<note>" --rows <rows.json>`. Files live in `_local/ppc-manage/<client>/batches/` (gitignored). No snapshot, no apply. Past applies can be backfilled from AdLabs `logs` with `--date`.
- **Read before write**: every run, right after the stock gate, `batches.py status --client <slug>`. Score each batch older than the cooldown (`score --tag <tag> --verdict "..."`) BEFORE proposing new changes on its entities, and check stock/price confounds first: a bad day after an apply is not automatically the ads, and day-1/day-2 reads are attribution noise by definition.
- **Scoring uses same-source windows, never dashboard percentages** (client lesson 2026-07-26): compare equal-length windows before/after the apply date from ONE source (AdLabs `product`/`profile` with explicit DATE + COMPARE_DATE). Establish WHEN the trend broke before attributing: a decline that started before the batch date exonerates the batch. Sellerboard daily percent tiles compare against baselines you have not verified (often month-ago or event-inflated periods); quote their euros, never their percentages.
- **Revert**: `batches.py revert --tag <tag>` emits the old values as an `update_entities` payload. A revert is a write like any other (preview -> approval -> apply), then `mark-reverted`.

## 0. Startup (always)

1. `start_chat_session` -> `read_resource(adlabs://instructions)`; pass `chat_session_id` on every call.
2. Resolve team/profile; read `adlabs://profiles/<slug>` (profile_id, Target ACOS) and `context_and_prompts(get_context, PROFILE, ...)`.
3. Load break-even ACOS from the client's Sellerboard P&L (margin % + Real ACOS %). If unconfirmed, it is an ASSUMPTION and every verdict in the run says so.
4. Ask once for the week window (dates are always operator-supplied; the optimizer and harvesting tools must never default them).

## 1. Stock gate (before any bid logic)

Pull `product` stock fields (`out_of_stock_days`, `days_of_cover`, `fulfillable_units`). Amazon deranks what it cannot ship; an OOS ASIN's campaigns get paused/parked (tag the batch so the pause is reversible), not bid-optimized. Anything the stock gate catches leaves the rest of this run.

## Standing conventions (apply to every step below)

- **Four-axis keyword read** for every Rank keyword, in order: 1. organic rank (Rank Radar), 2. ad ToS impression share (AdLabs target `top_of_search_impression_share`), 3. SQP impression share, 4. SQP purchase share (the client KPI). Diagnosis: ToS saturated (>20%) + SQP impressions low = organic gap, keep pushing. SQP impressions high + purchases low = listing problem, not bids. All low = fund it.
- **ToS saturation veto**: a generic Rank keyword at >20% ToS impression share (or sponsored rank 1) gets NO further bid/ToS raises; hold if organic climbs, investigate relevance if organic is stuck. Not applicable to Discovery; Profit ignores share.
- **Profit is gated per keyword, always**: long-tails must run at/under their target ACOS even in push mode. Push loosens Rank only.
- **Non-round final values**: every bid and ToS percentage actually written ends non-round (EUR 2.21, 51%, 151%); internal limits/settings stay round.
- **Conquest SPCs**: one competitor per campaign, ASIN-exact targets, Down only, high ToS modifier; campaign creation goes through `amazon-campaign-builder` (bulk file, paused; AdLabs MCP cannot create campaigns).
- **Negatives always at AD GROUP level** (operator standard 2026-07-24): create negative keywords/targets as `AD_GROUP_NEGATIVE_*`, never `CAMPAIGN_NEGATIVE_*`. If campaign-level negatives exist (or slip in), archive them and re-create at ad group level. Ad groups added to a campaign later must get the standard negatives too; when verifying coverage, check enabled ad groups in enabled campaigns (paused shells can wait until re-enable).

## 2. Weekly checker with rank + pacing input

Run the ads-monitor weekly brief with the full v3 inputs:

```
python3 tools/amazon-ads-monitor/run_weekly.py \
  --csv <sellerboard 30d csv> --account <slug> --goal <lens> \
  --adlabs-json <normalized weekly entities> \
  --rank-radar-json <radar rows> --monthly-budget <amount> \
  --out output --slack-json -
```

- Rank Radar rows come from the DataDive MCP (`list_rank_radars` -> `get_rank_radar_data`), shaped to `{keyword, rank_now, rank_prev, weeks_stable}` per tracked keyword. Big radar payloads overflow; parse the saved tool-result file with python.
- `--monthly-budget` from the client config (`_local/ads-monitor/`); needs Sellerboard history back to the 1st of the month (raise `--window-days` late in the month).
- The brief now carries: Run-rate pacing (on_pace / warn / act / underpace), PUSH, **GRADUATE** (rank 1-3 stable 2+ weeks -> step down), PAUSE/OPTIMIZE with rank-improving keywords protected into notes.
- When the question is "did click share fall because spend fell", run `/supa` for the per-keyword SQP x PPC read; its P/O/E flags feed the same decisions.

## 3. Opt-group audit (the unit of strategy)

`optimizer(list_groups)` and check against the doctrine standard (strategy.json `management.opt_groups`):

- Four groups mapped 1:1 to roles. Rank: tacos 1.5-2x break-even, INCREASE_SALES, bid floor TIMES_CPC ~0.5, bid_max_decrease PERCENT ~0.10, placement_max_decrease capped low (the loose leash: the optimizer trims true waste but can never choke a push). Discovery: tacos = BE, BALANCED, bid ceiling. Profit: tacos = BE or client target, REDUCE_ACOS when over. Shield: high tacos, BALANCED.
- Every campaign assigned to exactly one role group; unassigned campaigns are a finding.
- Fixes go through the write gate as `create_group` / `update_group` / `assign_campaigns`. **`update_group` has PUT semantics**: always `list_groups` first and resend every current field, or omitted settings silently reset.

## 4. Bid run (weekly)

Per opt-group: `optimizer(preview_optimization, reference=<campaign reference>, start_date/end_date=<operator dates>, tacos=<group target>)` -> `query` the preview reference and read `change_reasons` per entity. Veto before proposing:

- Protect any keyword whose Rank Radar rank is improving or that sits in a mid-flight push; cross out its decreases.
- If pacing says **act**, present the cuts in the fixed order: waste (high-spend-no-sales) -> discovery -> profit trims. Rank cuts only with an explicit operator decision, never bundled into the batch.
- If pacing says **underpace**, lead with the PUSH list and capped Rank budgets instead.

**Caps are ceilings, never steps** (operator, 2026-07-26). The opt-group's `bid_max_increase/decrease` and `placement_max_*` settings clamp the optimizer's formula (bid = RPC x target ACOS; placement adjustment = target ACOS / current ACOS - 1; full sheet in `AdLabs Help/articles/000-formula-summary.md`); the actual change per entity is whatever the formula says, anywhere from 1% up to the cap. Only apply values proposed by a preview; never author a change equal to the cap (the ToS +40% incident: cap applied as the step, wrong placement, no performance read). Manual bid math outside a preview uses the same formula, then clamps. Validate every batch before approval: `batches.py validate --rows <rows.json> --max-increase <f> --max-decrease <f>` errors on over-cap deltas and flags at-cap rows for confirmation that they are formula clamps, not authored steps.

**Placement raises need a placement read.** Before raising any placement modifier, compare placement-level performance (CVR / ROAS / CPC for top-of-search vs product pages vs rest-of-search) and boost only the placement that earns it. Small steps sized by the performance gap, never the cap.

Assemble the surviving preview into per-opt-group batches per the staged-apply standard (a group's bids, placements, negatives, and budget may share one batch; rows labeled per lever), then per batch: summary (entities, old -> new, reasons, expected spend delta) -> approval -> snapshot -> `apply_optimization(preview_id, note=<tag + reason>)` with a filtered reference for the partial apply. Placements: monthly cadence, small steps; use `skip_placement_optimization` on the weekly bid runs in placement-off weeks.

## 5. Harvest run (weekly or biweekly)

`harvesting(preview_harvest)` over qualifying Discovery search terms (needs campaign mappings; `campaign_mapping(list_mapping_targets)` first). Filter rows with a non-empty `warning` column, review destination roles (a proven term goes to Profit, a big-SV proven term is a Rank candidate with its own SKW campaign + Rank Radar tracking BEFORE above-break-even spend starts), then approval -> `apply_harvest`.

## 6. Graduation

For each GRADUATE keyword (rank 1-3, 2+ consecutive stable weeks): step the ToS modifier and bid down toward break-even over 2-3 optimizer cycles, respecting the group's max-decrease. Never cliff-drop; deranking follows cliff-drops. Tag the change so next week's run measures it. Rank slipping past 5 after graduation = operator decision to re-escalate, never automatic.

## 7. Output

Per client per week: a short action log (what changed, why, expected effect, tags), the weekly brief markdown, and the Slack summary via the ads-monitor conventions. Every applied batch carries its audit `note` and its snapshot file. What was NOT done (vetoed cuts, skipped OOS campaigns, queued-over-cap batches, cooldown-blocked entities, pending operator decisions) is listed, never silent. Include the batch scoreboard: last week's batches with their verdicts or "still in cooldown".

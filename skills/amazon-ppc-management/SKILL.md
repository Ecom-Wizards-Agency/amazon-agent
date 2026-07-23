---
name: amazon-ppc-management
description: Weekly PPC management loop for AdLabs-managed accounts. Trigger on `/ppc-manage` or "run the weekly ads management" for a client. Stock gate, run-rate pacing, Rank Radar graduation, opt-group audit, then AdLabs optimizer/harvest preview -> operator approval -> apply. Audits stay in `amazon-adlabs-audit` (diagnose); this skill operates.
---

# Amazon PPC Management (weekly loop, AdLabs-managed accounts)

Browser: None (AdLabs MCP + DataDive MCP; Sellerboard CSV via the ads-monitor inbox convention).

Use this when the operator asks to RUN a managed account's week: adjust bids, budgets, opt-groups, harvests. It is the operating counterpart to `amazon-adlabs-audit` (diagnose) and `amazon-ads-monitor` (observe). Prospects and bulk-file accounts route to `amazon-ad-audit`; this skill requires a live AdLabs connection.

Doctrine source of truth: `_local/ads-strategy/strategy.md` v3 (Run-rate governor, Opt-group standard, Rank keyword lifecycle, Optimizer cadence) and `_local/ads-strategy/strategy.json` `management` bands. Never guess thresholds; if the local file is missing, ask the operator.

**The core stance.** Run rate is a portfolio governor on top of the rank engine, not the strategy. The AdLabs bid optimizer prices every target off revenue per click x the opt-group's target ACOS, which is exactly right for ACOS optimization; our job on top of it is (a) point it at the right target ACOS per role, (b) protect deliberate above-break-even rank pushes from it, and (c) stop paying above break-even once a keyword's organic rank has stuck. Never "stupidly optimize" a campaign whose job the blended numbers cannot see.

## Write policy (critical, differs from the audit skill)

Every write follows the same gate: **preview -> operator approval of that specific batch -> apply with a meaningful `note`**. A general "sounds good" earlier in the chat is not approval for a new batch. Consistent with the universal guardrail in `AGENTS.md`: no campaign/budget/bid change without explicit per-action operator instruction. Never create or edit Campaign Optimizer automation rules via MCP (only pause/enable exists there anyway); rule definitions live in the AdLabs UI and are documented per client in the client profile.

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

Present the batch summary (entities, old -> new, reasons, expected spend delta) -> approval -> `apply_optimization(preview_id, note=...)`, optionally with a filtered reference for partial applies. Placements: monthly cadence, small steps; use `skip_placement_optimization` on the weekly bid runs in placement-off weeks.

## 5. Harvest run (weekly or biweekly)

`harvesting(preview_harvest)` over qualifying Discovery search terms (needs campaign mappings; `campaign_mapping(list_mapping_targets)` first). Filter rows with a non-empty `warning` column, review destination roles (a proven term goes to Profit, a big-SV proven term is a Rank candidate with its own SKW campaign + Rank Radar tracking BEFORE above-break-even spend starts), then approval -> `apply_harvest`.

## 6. Graduation

For each GRADUATE keyword (rank 1-3, 2+ consecutive stable weeks): step the ToS modifier and bid down toward break-even over 2-3 optimizer cycles, respecting the group's max-decrease. Never cliff-drop; deranking follows cliff-drops. Tag the change so next week's run measures it. Rank slipping past 5 after graduation = operator decision to re-escalate, never automatic.

## 7. Output

Per client per week: a short action log (what changed, why, expected effect, tags), the weekly brief markdown, and the Slack summary via the ads-monitor conventions. Every applied batch carries its audit `note`. What was NOT done (vetoed cuts, skipped OOS campaigns, pending operator decisions) is listed, never silent.

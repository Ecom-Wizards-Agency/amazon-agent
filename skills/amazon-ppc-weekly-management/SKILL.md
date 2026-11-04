---
name: amazon-ppc-weekly-management
description: "Run the weekly SYNQ PPC loop: stock and budget-delivery gates, Bid Optimizer runner review, goal, role and exclusion proposals, approved SYNQ web-app changes and Change History rollback. The AdLabs carve-out account keeps its AdLabs loop."
---

# Amazon PPC Weekly Management

Browser: Mixed (SYNQ MCP and SoldScope MCP reads; the SYNQ web app in the attended operator browser on 9222, read-only for runner status and for approved changes; Ads console target report or bulk download for ToS impression share and budget-capped days).

For Sponsored Brands video concept tests, use `<vault>/Playbooks/amazon-sb-video-concept-testing-playbook.md` (team vault, resolved via `AMAZON_AGENT_TEAM_VAULT` or `_local/team-vault-path.txt`) as the canonical test-cell, confidence, verdict, and learning method. PPC management owns scaling decisions under the account strategy. The editor brief and Creative Reference do not contain performance methodology.

Use this when the operator asks to RUN a managed account's week: review the SYNQ Bid Optimizer runners, propose goal, role and exclusion changes, and make approved one-off changes to bids, budgets, placements, harvests and negatives. It is the operating counterpart to `amazon-audit` (diagnose) and `amazon-ads-performance-briefs` (observe). Prospects and clients not yet in SYNQ route to `amazon-audit` (bulk path). The AdLabs carve-out account (US and CA) keeps its AdLabs loop: see the AdLabs carve-out section at the end.

The SYNQ MCP contract (client confirmation, row caps, lag, gaps) is `docs/synq-mcp.md`.

Doctrine source of truth: `_local/ads-strategy/strategy.md` for narrative judgment, `_local/ads-strategy/strategy.json` for every numeric threshold, and this skill for operating procedure. The ownership map is `docs/ads-doctrine-sources.md`. Never guess thresholds; if the local file is missing, ask the operator.

**The core stance.** Run rate is a portfolio governor on top of the rank engine, not the strategy. The SYNQ Bid Optimizer runners price routine bids against the ACOS or TACOS goal set in Catalog Manager, which is exactly right for ACOS optimization; our job on top of them is (a) set the right goal per role, (b) protect deliberate above-break-even rank pushes through campaign roles and exclusions, and (c) stop paying above break-even once a keyword's organic rank has stuck. Never "stupidly optimize" a campaign whose job the blended numbers cannot see.

## Write policy (critical, differs from the audit skill)

Writes happen only in the SYNQ web app, in the attended operator browser: `node tools/browserctl/browserctl.mjs run --session operator -- <command>` (9222). The SYNQ MCP is read-only. Grimoire and scheduled runs never write; they prepare proposals.

Every change follows the same gate: **proposal -> operator approval of that exact action -> snapshot -> web-app change -> readback**. The approval names the client, marketplace, exact entities, old -> new values, and the expected result. A general "sounds good" earlier in the chat is not approval for a new batch. Consistent with the universal guardrail in `AGENTS.md`: no campaign/budget/bid change without explicit per-action operator instruction.

- **Runner changes** (goal in Catalog Manager, campaign role, exclusions) and **one-off changes** (Campaign Manager bids, budgets, placement modifiers, negative lists; Keyword Harvester; Search Term Negator) pass the same gate.
- **One-writer rule.** A SYNQ runner and any other bid writer (AdLabs optimizer or dayparting, manual pushes) never share a campaign. A one-off bid, budget or placement push goes only to an entity no runner writes: an unassigned campaign or a runner exclusion. **Required check before any one-off bid or budget push on a campaign:** read the SYNQ Bid Optimizer page read-only in the attended operator browser and confirm the campaign is in no runner or is excluded from its runner; record what the page showed in the action log. Runner membership is a SYNQ MCP gap. `get_ads_change_log` with `source_module: BidOptimizer` is supporting evidence only: it has no campaign filter (match the campaign in `entity_ids` yourself), and a runner that changed nothing in the window leaves no row, so an empty result never clears a campaign.
- **New campaigns** stay bulk files through `amazon-sponsored-products-bulk-files` (file only, paused).

## Staged applies (attribution + revert standard, operator decision 2026-07-26)

Never change the whole account in one go. A whole-account change cannot be reverted cleanly, and next week's numbers blend every cause (the three Jul-24 whole-account runs are the cautionary tale). Thresholds live in strategy.json `management.staged_apply`.

- **Batch = one role group, never the whole account** (operator refinement 2026-07-26). A role group is the set of campaigns sharing one runner role. Within a group's batch, several levers may land together: bids, placements, negatives, budget for that group. Label every row with its lever (`waste-cut`, `bid-down`, `push`, `budget`, `placement`, `harvest`, `negative`, `pause`) so scoring stays per-lever. Never mix role groups in one batch.
- **Tag every batch** `<client>-<YYYY>W<ww>-<group>`, with a `-<lever>` suffix when a batch is single-lever (e.g. `acme-2026W31-profit` or `acme-2026W31-profit-bid-down`). Where the web app offers a note or name field, it carries the tag; otherwise the snapshot file links the change by entity ids and time.
- **Per-run cap**: at most `max_batches_per_run` (3) batches per weekly run, highest conviction first. Queued batches are listed in the action log, never silently dropped.
- **Group cadence + priority (operator, 2026-07-26)**: under the cap, Rank and Profit batches come first, Discovery second, Shield last. Rank and Profit are weekly; Discovery weekly or biweekly; Shield biweekly, batched into the same run as Discovery. Rank may run more often than weekly during a strong push: mid-push Rank keywords may be re-stepped after `push_rank_min_days` (3) instead of the full cooldown, recorded as bypass `rank_push`.
- **7-day entity cooldown**: an entity written by an applied batch is not re-touched for `cooldown_days` (7), so each change gets one readable week. Bypasses (always recorded in the batch file): stock gate, fraud/budget-cap emergency, pacing **act**. Check candidates before proposing: `python3 tools/amazon-ppc-management/batches.py check --client <slug> --rows <rows.json>`.
- **Snapshot before the change**: after approval and before the write, save the old -> new rows: `batches.py snapshot --client <slug> --tag <tag> --lever <lever> --group <group> --note "<note>" --rows <rows.json>`. Files live in `_local/ppc-manage/<client>/batches/` (gitignored). No snapshot, no change. Past changes can be backfilled from SYNQ `get_ads_change_log` with `--date`.
- **Read before write**: every run, right after the stock gate, `batches.py status --client <slug>`. Score each batch older than the cooldown (`batches.py score --client <slug> --tag <tag> --verdict "..."`) BEFORE proposing new changes on its entities, and check stock/price confounds first: a bad day after a change is not automatically the ads, and day-1/day-2 reads are attribution noise by definition.
- **Scoring uses same-source windows, never dashboard percentages** (client lesson 2026-07-26): compare equal-length windows before/after the change date from ONE source, SYNQ `get_daily_metrics` with each window pulled separately and joined by id, so an entity that fell to zero still shows. Establish WHEN the trend broke before attributing: a decline that started before the batch date exonerates the batch. Sellerboard daily percent tiles compare against baselines you have not verified (often month-ago or event-inflated periods); quote their euros, never their percentages.
- **Revert**: `batches.py revert --client <slug> --tag <tag>` emits the old values. A revert is a change like any other (proposal -> approval -> web-app change), made through SYNQ Change History revert or Campaign Manager, then `mark-reverted`.

## 0. Startup (always)

1. Run `python3 tools/ads_recall.py management` and read the returned decision, Playbook, and Research files in order. Continue quietly when it returns no paths.
2. SYNQ `list_clients`; skip every `is_demo` client. A client name alone does not prove whose seller data it is: confirm the client with `get_catalog` by a known SKU or product title from the client profile.
3. `get_sync_status` for the client and marketplace. A failed or stale sync is a finding and limits every verdict in the run.
4. Note the lag: Sales and Traffic runs 2 to 3 days behind ads data. The sales attribution window is unconfirmed; label sales as SYNQ-reported.
5. Save every SYNQ response as `{"note": <note text or null>, "rows": [...]}`. Tools cap at `limit` (max 2000) and prefix a "ROW LIMIT REACHED" or "TRUNCATED" note when rows were cut; never treat a cut list as complete. Narrow the filters, raise the limit, or use `group_by: total` for exact sums.
6. Load break-even ACOS from the client's Sellerboard P&L (margin % + Real ACOS %), or from `get_catalog` `cogs` and `gross_margin` when COGS is set. If unconfirmed, it is an ASSUMPTION and every verdict in the run says so.
7. Ask once for the week window (dates are always operator-supplied, never defaulted).

## 1. Stock gate (before any bid logic)

Pull `get_inventory` for current stock and `get_inventory` with `history: true` over the window for out-of-stock days, plus `get_catalog` `days_inventory` for days of cover. SKUs sharing an fnsku share one stock pool repeated on each row: count one row per fnsku. Amazon deranks what it cannot ship; an OOS ASIN's campaigns get paused/parked (tag the batch so the pause is reversible), not bid-optimized. Anything the stock gate catches leaves the rest of this run.

## Standing conventions (apply to every step below)

- **Four-axis keyword read** for every Rank keyword, in order: 1. organic rank (SoldScope rank tracker), 2. ad ToS impression share (Ads console target report or bulk download; the SYNQ MCP does not carry it), 3. SQP impression share, 4. SQP purchase share (the client KPI). Diagnosis: ToS saturated (>20%) + SQP impressions low = organic gap, keep pushing. SQP impressions high + purchases low = listing problem, not bids. All low = fund it.
- **Weekly SQP is a signal, not a verdict.** A decision needs a sufficient representative multi-week sample with meaningful impression share, click share, absolute impressions, and clicks. Confirm any movement against sales, CVR, PPC delivery, rank, promotions, and the longer trend. Never act from one noisy week or one-sale CVR.
- **Full Rank pushes need an entry gate.** Compare the ASIN's SQP purchase CVR with the market on the same query and period. Reliably at or above market with sufficient data is eligible. Reliably below market means fix the offer before above-break-even spend. Insufficient data permits only a capped validation test with explicit spend, time, and stop criteria. Any strategic exception needs operator approval.
- **Catalog structure is a pre-spend gate.** Verify Product Type, browse node, and required category attributes for every relevant child ASIN from backend catalog evidence before a full Rank push. Fix child-level drift before spending to force rank.
- **ToS saturation veto**: a generic Rank keyword at >20% ToS impression share (or sponsored rank 1) gets NO further bid/ToS raises; hold if organic climbs, investigate relevance if organic is stuck. Not applicable to Discovery; Profit ignores share.
- **Profit is gated per keyword, always**: long-tails must run at/under their target ACOS even in push mode. Push loosens Rank only.
- **Non-round final values**: every bid and ToS percentage actually written ends non-round (EUR 2.21, 51%, 151%); internal limits/settings stay round.
- **Conquest PAT grouping is hybrid.** Group by shopper intent, product type, or relevant price band first. Within a group, split stronger and weaker competitors when the cohort supports a useful comparison. Reserve one-competitor campaigns for strategic targets with enough traffic to justify independent control. Exact remains the default. Expanded and refined-category targeting are controlled Discovery tests, never standing requirements. Campaign creation goes through `amazon-sponsored-products-bulk-files` (bulk file, paused).
- **Negatives default to ad-group level for the normal single-ad-group SP structure.** Use campaign-level negatives only when a multi-ad-group campaign needs an exclusion that is correct for every ad group. Do not migrate a valid existing negative solely because of its level. Auto and product-targeting safety-net exceptions remain account-specific.
- **Brand separation is mandatory in reporting.** The account may retain profitable own-brand traffic in Auto or product targeting, but every optimization read splits branded and nonbrand terms and attribution. If brand traffic distorts bidding or allocation, test staged isolation instead of negating it automatically.
- **Zero-spend targets are a separate risk class.** Keep them out of performance comparisons, but before bid changes, negations, or duplicate cleanup flag enabled zero-spend targets whose bids exceed their calculated ceiling. Check overlaps and traffic-routing risk before proposing a reduction.
- **Launches use a higher-frequency cadence than mature accounts.** Review them throughout the opening launch window. Daily data is a signal, not a verdict; confirm ordinary changes on rolling multi-day evidence and act immediately only on verified operational failures or loss-limit breaches.

## 2. Per-campaign budget-delivery gate

After the stock gate and before any optimization batch, run a read-only out-of-budget check for every enabled campaign. `get_spend_pacing` gives month-to-date spend, the daily target and the projected month end. Budget-capped days and current budgets are not in the SYNQ MCP: read them from the Ads console (time-in-budget where shown) or a bulk download. Otherwise, flag campaigns whose daily spend repeatedly approaches their daily budget and verify that they are actually capping.

- Capped at or below target ACOS: propose a budget increase or reallocation from weaker campaigns, subject to monthly pacing.
- Capped above target ACOS: hold the cap and propose a lower goal or lower one-off bids so the same budget lasts longer.
- Deliberately capped Rank: record the cap as intentional and require an operator decision before extending it.

The check creates findings and proposals only. Every resulting bid or budget action still needs approval, snapshot, and staged application.

If the operator has declared event mode, record the dates, objective, approved budget, and loss limits. Do not let the normal pacing governor cut approved event spend automatically. Separate event data from normal performance afterward and return to baseline through a reviewed recovery plan; never apply a universal post-event bid reduction without account evidence.

## 3. Weekly checker with rank + pacing input

Build the weekly entity rows from SYNQ: pull `get_daily_metrics` for the week once with `group_by: campaign` and once with `group_by: target`, save each as `{"note","rows"}`, add `list_campaigns` and the week's `get_search_terms` pulls (for match type), then run

```
python3 tools/synq/convert.py entities --metrics campaign:CAMPAIGNS_WEEK.json target:TARGETS_WEEK.json --campaigns LIST_CAMPAIGNS.json [--search-terms ST.json ...] --out ENTITIES.json
```

Then run the ads-monitor weekly brief with the full v3 inputs, passing `ENTITIES.json` as `--ads-json`:

```
python3 tools/amazon-ads-monitor/run_weekly.py \
  --csv <sellerboard 30d csv> --account <slug> --goal <lens> \
  --ads-json <weekly entity rows> \
  --rank-json <weekly rank rows> --monthly-budget <amount> \
  --out output --slack-json -
```

`--adlabs-json` is the legacy alias of `--ads-json`.

- Weekly rank rows come from the SoldScope rank tracker. All four steps are free reads (no credits):
  1. `rank_tracker_list_groups` (filter by marketplace and ASIN) gives the `group_id`. **Check the group's marketplace matches the account's**: a client can track another country's listing of the same product, and using it scores the wrong country silently.
  2. `rank_tracker_list_products(group_id)` gives the own `product_id` (the primary product, or the one whose ASIN matches).
  3. `rank_tracker_list_phrases(group_id, product_id, heatmap=true, heatmap_date_from, heatmap_date_to, results_type=organic, per_page=100)`, every page, covering at least the last 8 complete Sunday-Saturday weeks (at most 92 days). Save each page; large pages overflow context, so read them from the saved files.
  4. `python3 tools/soldscope/ranks.py --organic <pages> --asin <ASIN> --marketplace <code> --weekly-rows --graduate-rank-max <strategy.json value> --out <rank rows JSON>` writes `{keyword, rank_now, rank_prev, weeks_stable}` per tracked keyword. It fails when the group marketplace differs from `--marketplace`. Pass the file to `--rank-json` (`--rank-radar-json` is the legacy alias).
- Rank-tracker writes (`rank_tracker_create_group`, `rank_tracker_attach_products`, `rank_tracker_apply_suggested_phrases`, `rank_tracker_toggle_phrases_boost`) need approval of that exact action; `rank_tracker_init_export` and `rank_tracker_get_suggested_keywords` spend credits and need a run approval (`tools/soldscope/README.md`).
- `--monthly-budget` from the client config (`_local/ads-monitor/`); needs Sellerboard history back to the 1st of the month (raise `--window-days` late in the month).
- The brief carries: Run-rate pacing (on_pace / warn / act / underpace), PUSH, **GRADUATE** (rank 1-3 stable 2+ weeks -> step down), PAUSE/OPTIMIZE with rank-improving keywords protected into notes.
- When the question is "did click share fall because spend fell", run `/supa` for the per-keyword SQP x PPC read, or call `tools/sqp-supa/build_supa_workbook.py` directly where no slash command exists (method: `tools/sqp-supa/README.md`); its P/O/E flags feed the same decisions.

## 4. Runner health (the unit of strategy)

Read the SYNQ Bid Optimizer page read-only in the attended operator browser. The MCP does not carry runner membership, status or roles.

- Runner status: every runner enabled as intended, none overdue or failing.
- Roles: each of our four roles (Rank, Discovery, Profit, Shield) maps to one SYNQ campaign role, and every enabled campaign has exactly one. Unassigned campaigns and campaigns with the wrong role are findings. Record the role mapping in the action log.
- Goals: `get_catalog` shows each ASIN's current `acos_target`, `target_tacos`, `assigned_strategy_id` and the role multipliers (`rnk_multiplier`, `rsc_multiplier`, `coq_multiplier`). These are the old values in any goal proposal. Check them against the role targets in `strategy.md` and `strategy.json`.
- One-writer conflicts: a runner campaign that also has a manual push, an AdLabs optimizer group or a dayparting schedule is a finding to resolve before any other change on it.

What the runners did: `get_ads_change_log` with `source_module: BidOptimizer` over the window (`user_email` `system@synq.app` is automation). Read `action_type`, `total_changes`, `failed_changes` and `payload_summary`; failed changes are a finding. `get_entity_changes` with `source: external` shows edits made outside SYNQ (console, bulk, other tools), which break the one-writer rule on runner campaigns. `get_campaign_changes` shows state transitions, including those made outside SYNQ.

## 5. Graduation

For each GRADUATE keyword (rank 1-3, 2+ consecutive stable weeks, from the SoldScope weekly rows), confirm with the ToS impression share from the Ads console target report, then step spend down toward break-even over 2-3 cycles: a lower goal or a role change for the runner, or stepped one-off bid and ToS modifier cuts when the keyword sits outside every runner. Never cliff-drop; deranking follows cliff-drops. Tag the change so next week's run measures it. Rank slipping past 5 after graduation = operator decision to re-escalate, never automatic.

## 6. Proposals

Assemble proposals per role group under the staged-apply standard, highest conviction first:

- **Runner proposals**: goal changes in Catalog Manager (old -> new `acos_target` or `target_tacos`), role changes, and exclusions that take a Rank push or a manual test out of the runner's hands.
- **One-off pushes** in Campaign Manager, only on entities no runner writes, confirmed by the Bid Optimizer page check in the write policy. Veto before proposing:
  - Protect any keyword whose organic rank (SoldScope rank tracker) is improving or that sits in a mid-flight push; cross out its decreases.
  - If pacing says **act**, present the cuts in the fixed order: waste (high-spend-no-sales) -> discovery -> profit trims. Rank cuts only with an explicit operator decision, never bundled into the batch.
  - If pacing says **underpace**, lead with the PUSH list and capped Rank budgets instead.

**Treat the base bid and every placement modifier as one bidding system.** Before any bid or placement change, calculate the current effective bid for ToS, RoS, and Product Pages and compare their relative gaps. Current bids and modifiers come from the Ads console or a bulk download; `get_entity_changes` gives a current value only for entities that changed. Opening and manual bids come from RPC times the role target ACOS, using actual data or conservative comparable-product assumptions, then back-calculate the base around active modifiers. Amazon's suggested range is only a visibility and competition reference.

For profit optimization, relative placement modifiers come from the RPC relationship between placements. Target ACOS scales the overall base and effective bids; placement ACOS is an outcome and diagnostic, not the primary sizing input. Use per-placement RPC/CVR only when the sample is sufficient. With weak data, use the documented campaign-group/account fallback, hold the setup, or label the action as a deliberately capped Rank or visibility test with an explicit hypothesis. Never present one-sale RPC as precise math.

Do not change a base bid alone on a campaign with active modifiers unless the proposal accounts for the whole system. Do not trust a tool's placement recommendation automatically: if it conflicts with the placement RPC relationship, stop for review. Normalize the lowest-priority placement to zero where practical. Rank pushes may override the profit relationship only when explicitly labelled and judged on rank, impression share, and purchase share. Placements: monthly cadence, small steps.

**Placement changes need a placement read and a response check.** Before a change, compare placement-level RPC, CVR, CPC, spend, orders, and delivery for ToS, RoS, and Product Pages. Afterward, compare delivery, impression or click share, CPC, spend, and orders before and after. Realized CPC is not an engagement ratio and need not equal the theoretical maximum. If delivery shows no meaningful response, run a controlled test before claiming the modifier failed.

**Caps are ceilings, never steps** (operator, 2026-07-26). A maximum change per step clamps the calculated change. Only propose values supported by the whole-system calculation; never author a change equal to the cap merely because the cap exists. Validate every batch before approval: `batches.py validate --rows <rows.json> --max-increase <f> --max-decrease <f>` errors on over-cap deltas and flags at-cap rows for confirmation that they are formula clamps, not authored steps.

**Harvest (Keyword Harvester, weekly or biweekly).** A promotion needs relevance, sufficient search volume, a meaningful click sample, and conversion evidence. Read search terms from `get_search_terms` (it carries `keyword_id` and `match_type`). Route it to an explicit Rank, Profit, Shield, or other approved destination. Own-brand terms and ASINs never enter nonbrand destinations, and ACOS alone is not an automatic veto when the term has strategic value. Review the destination role before approval.

Promotion and source negation are separate decisions. Add the term as Exact while keeping a productive source active. Do not automatically negative an Auto campaign or pause a source target because one term graduated. If isolation is later justified, use ad-group negative exact, never negative phrase, and create a review task comparing combined source and destination sales, ACOS, Exact delivery, source bid drift, SQP share, and rank. Keep the negative only when the combined outcome improves.

**Negation (Search Term Negator or Campaign Manager negative lists).** Negation formulas are review triggers, not automatic actions. Before negating, inspect relevance, sample size, placement, branded status, campaign purpose, and ranking value. Use negative exact for isolated bad terms and negative phrase only for clearly unwanted themes.

## 7. Approved changes, readback and rollback

Per batch:

1. Summary: client, marketplace, entities, old -> new, lever, reasons, expected spend delta and expected result.
2. Operator approval of that exact batch.
3. `batches.py check`, then `batches.py snapshot`.
4. Make the change in the SYNQ web app (Catalog Manager, Bid Optimizer, Campaign Manager, Keyword Harvester or Search Term Negator) in the operator browser. Change only what was approved.
5. Readback: `get_ads_change_log` over the change date (match `entity_ids`, `source_module`, `successful_changes`, `failed_changes`; record SYNQ's `batch_id` in the action log), `get_entity_changes` for the old -> new values on each entity once the next sync runs, and `get_campaign_changes` for state changes. A change is done only when the readback matches the snapshot; partial or failed rows are reported by entity id.

Rollback: `batches.py revert --client <slug> --tag <tag>` gives the old values. After approval, revert through SYNQ Change History (it logs as `source_module` `change_history_revert`) or set the old values in Campaign Manager, read it back the same way, then `batches.py mark-reverted --client <slug> --tag <tag>`.

## 8. Output

Per client per week: a short action log (what changed, why, expected effect, tags, SYNQ `batch_id`s), the weekly brief markdown, the runner-health findings, and the Slack summary via the ads-monitor conventions. Every applied batch carries its tag and its snapshot file. What was NOT done (vetoed cuts, skipped OOS campaigns, queued-over-cap batches, cooldown-blocked entities, one-writer conflicts, pending operator decisions) is listed, never silent. Include the batch scoreboard: last week's batches with their verdicts or "still in cooldown".

## AdLabs carve-out only

The AdLabs carve-out account (US and CA) stays fully on AdLabs (optimizer, harvest, opt-groups and live AdLabs dayparting schedules) until it moves to SYNQ. `docs/synq-mcp.md` says how to identify it. Load `references/adlabs-carve-out.md` for every run on it; it holds the AdLabs startup, opt-group audit, bid run, harvest run, revert path and the AdLabs dayparting schedule procedure.

The overwrite trap: while a dayparting schedule is assigned, it multiplies its stored base bid every hour, so a bid edited in the Ads console, a bulk file or any other tool on an assigned campaign is overwritten at the next run. Make the carve-out account's bid changes in AdLabs. A SYNQ runner never takes one of its campaigns while an AdLabs optimizer group or dayparting schedule still covers it.

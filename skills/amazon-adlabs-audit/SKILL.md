---
name: amazon-adlabs-audit
description: Use for PPC audits of AdLabs-managed accounts via the AdLabs MCP. Trigger on `/adlabs-audit`, audit via AdLabs, or analyze this AdLabs account. Context-first, 10 steps per marketplace, read-only by default. For prospect audits from downloaded bulk files use `amazon-ad-audit` instead.
---

# AdLabs PPC Audit (managed accounts)

Use this when the operator asks to audit/analyze/optimize a managed account's Amazon PPC "through AdLabs" (e.g. `/adlabs-audit`). It complements `amazon-ad-audit` (bulk-file MASTER workbook for prospects): this one runs live on the AdLabs MCP, grades against the account's own goal structure, and ends in an actionable, context-aware recommendation set.

**Which audit to use: the routing rule.** Is the brand an existing managed client connected to our AdLabs? → this skill. Is it a prospect / new brand not yet in our AdLabs? → `amazon-ad-audit` (it must download bulk files because there's no live connection). That connection status is the whole reason the two skills exist and it drives the data source below.

**MCP-native: no downloads, no data handoff.** Because a managed client is connected, this workflow needs NO Codex download step and no bulk-file contract. Do not ask for exports. Every metric (campaigns, targets, search terms, placements, SQP via `search_query`, products, DSP) comes live from the AdLabs MCP, and rank data from the DataDive MCP. The only external input is human context (targets, break-even, events), not data.

**Depth limit: supplement when needed.** AdLabs SQP (`search_query`) is weekly and profile-level, and there is no Business-Report-by-child-ASIN feed here; for deep per-ASIN query-level SQP or organic-traffic/conversion analysis, pull the Seller Central Business Report + multi-ASIN SQP download (the `amazon-ad-audit` inputs) to supplement.

## Shared standards (do not duplicate)

Narrative and design are governed by `docs/amazon-ad-audit-playbook.md`, the single source of truth for both audit skills. Follow it, don't restate it:

- **Narrative voice + structure**: playbook Part 1. It gives the section skeleton (Ads Summary → Current Performance → Demand/SQP → DataDive → Good and Bad → Growth Levers → Sources), the cut-list (no 30-day plan, no "what can be reached", no bottom-line recap, no standalone praise section), and the operator voice (second person, first-person opinion, layer next-level tactics, hedge unprovable causals, blunter/shorter). Number problems `Problem N` and recommendations `Lever N`.
- **Workbook design system**: playbook Part 2. It gives the EW CI palette (obsidian/coral/violet…), Aptos fonts, restrained traffic-light fills on decision cells only, the ACOS-is-a-ratio helper (never ÷100; bands good <0.30 / ok <0.50 / warn ≤0.60 / bad >0.60, retuned to the confirmed break-even), the break-even assumption banner, hidden helper sheets, gridlines off.

This skill only adds what is AdLabs-specific (below).

## Modes

- **audit** (default): full 10-step audit per marketplace + consolidated report.
- **actions**: skip the narrative; deliver only the prioritized action list (bids to cut, negatives, budgets, reallocations) with spend impact in the profile's currency and GoTo links.

## 0. Startup sequence (always)

1. `start_chat_session` → `read_resource(adlabs://instructions)`; pass the `chat_session_id` on every call.
2. `get_entity_data(teams)` → `get_entity_data(profiles, team_id)` → read each target profile's `adlabs://profiles/<slug>` resource for **profile_id, Target ACOS, Target Total ACOS**.
3. Read the audit methodology once per session: `read_resource(adlabs://guides/account_audit)`.

## 1. Context first, before any data pull

Collect, and **flag explicitly what is missing** instead of assuming a clean window:

- **AdLabs profile memory**: `context_and_prompts(get_context, PROFILE, <profile_id>)` holds brand terms, product-fact negatives, break-even, strategy doctrine. If empty, gather the below and (with explicit operator approval; see Write policy) offer to save it.
- **Local memory / client ops profile** (`_local/client-profiles/profiles.json`, Notion Partner Success page): account naming, marketplaces, stakeholders, restrictions.
- **Notion event log**: query the brand's **A/B Tests database** for rows overlapping the audit window (real tests + event rows typed Promo/Deal, Stock Event, Price Change, Launch). Also check recent client call summaries (meeting-notes DB + notion-search) for goals, break-even, stock events, and strategy intent. If no events are recorded for the window, say so in the report.
- **Scoping questions** (ask the operator once, in a single message; skip what's already supplied): profiles/marketplaces · date range (default last 30 days, compare = preceding period) · target source (see Grading) · brand terms incl. misspellings + which sub-brands count as branded.

## 2. Grading rules

- **Target hierarchy**: Optimization-Group goal ACOS (campaign_group) > profile Target ACOS > break-even ACOS. Grade each campaign against ITS group's goal; note profiles that have no Optimization Groups (recommend creating them).
- **Break-even ACOS** comes from the client (margin/ROAS); if unknown, flag as assumption. State where profile targets sit relative to break-even.
- **Strategic vs waste**: spend above target is only "strategic" if it demonstrably buys something. For rank campaigns, verify with **DataDive Rank Radar** (`list_rank_radars` → `get_rank_radar_data` over the audit window): compute rank start→end/best per keyword and cost-per-rank (profile currency). A rank campaign that holds/gains top positions on a high-SV core term is justified; flat/slipping core terms or gains on tiny-SV terms mean reallocate. Big radar payloads overflow; parse the saved tool-result file with python (per-keyword SV, start, end, best).
- **ACOS is a ratio; >100% is never presented as healthy.** Spend totals must reconcile across steps (audit_summary vs campaign sums); flag if not.

## 3. The audit (per marketplace, following `adlabs://guides/account_audit`)

Steps 1–4 (audit_summary scorecard · product-level TACOS vs target · campaign structure incl. ad-type bands + bid strategies + Optimization-Group allocation via `group_by_column(campaign_group_name)` · placement deep-dive) → **midpoint check-in** → steps 5–10 (bid categories with recommended bids via the guide's formulas · search-term waste + harvest with profile-derived aCTC/CVR benchmarks · brand leak with brand_name against a non-brand campaign reference · 1- and 2-gram waste · tactic allocation · budget caps; flag campaigns that are capped AND unprofitable: fix bids before budgets).

Practical MCP notes learned the hard way:
- Always read the **aggregate reference first**; `query` is SELECT-* only (no GROUP BY; use `group_by_column`, which recalculates derived metrics).
- Match-type value casing differs between audit_summary labels and row filters. Use `LOWER(col) LIKE` when a literal match returns 0 rows.
- Placement modifiers can multiply a low base bid several-fold (a Top-of-Search modifier can push a ~0.8 base bid to a ~2.5 effective CPC). When a target shows a low bid but high CPC, the placement modifier is the mechanism; fix the modifier or the base bid, not the symptom.
- Do not sum placement-entity totals with target/keyword rows. The placement entity carries campaign-level placement totals (the playbook's "Bidding Adjustment" double-count trap, in MCP form). Keep placements in their own view.
- Product entity: `organic_sales` is derived from `total_sales`; never sum it with ad sales.
- **SQP** comes from the `search_query` entity: weekly, profile-level, NOT campaign-linked. Good for intent split, CTR/CVR vs market, and purchase capture; but coarser than a raw multi-ASIN SQP download and it does not expose portfolio/campaign columns. Lead with impression share + purchase capture and average the available weeks; if the job needs per-ASIN query-level detail, that depth lives in the download route (`amazon-ad-audit`), not here.
- DataDive niche/MKL exports cap at 500 visible rows of the full niche. Keep outliers visible; don't imply full coverage.
- The brand / generic / competitor split is rule-based (brand tokens + own-ASIN + competitor names). It is audit-grade; review before any bulk campaign change.
- Attach the auto-generated "View in AdLabs" GoTo links per flagged dataset (guide checklist); they are session-generated and expire, so describe the filters in the deliverable too.

## 4. Deliverables

- Default: inline consolidated report (per-marketplace + cross-market summary; health score, PoP metrics, top issues by spend impact, quick wins, GoTo-link checklist), framed against the client's actual mandate (growth vs profit).
- On request: styled `.xlsx` + compact `.docx`, built by an openpyxl/python-docx script under `output/<client>/reporting/`, following the **playbook Part 2 design system** (EW CI palette, Aptos fonts, ACOS-ratio helper, break-even banner, hidden helper sheets, gridlines off), not ad-hoc colors. Tabs: Business Context · Overview · Action List · per-market Detail · Waste & Negatives · Brand Leak · GoTo Links. The **Overview** follows the playbook's traffic-mix pattern: Branded / Generic / Competitor rows × (ad spend, % spend, ACOS, SQP SV share, SQP purchase capture) so spend efficiency and demand capture sit side by side; build the SQP columns from the `search_query` entity and the split from the brand-leak analysis. Values in the profile currency; >100% ACOS never green. Deliver to the client's audit folder on the agency Drive (delivery-location convention in the project docs) via the desktop mount; MD5-verify local↔Drive and keep the build script beside the output for reruns/delta tracking.
- Unlike `amazon-ad-audit` this ships a single per-run workbook, not the 3-workbook MASTER set (no separate Codex-downloaded SQP workbook to merge): same visual standard, lighter assembly.

## 5. Recommendation posture (managed account, not a pitch)

This is a live account we already run, not a prospect before/after, so recommendations read as a **transition, not an abrupt overhaul**. Phase the changes:
- Move bids toward target over 2–3 steps, not one large cut; re-measure between steps.
- Roll out negatives / harvests / budget shifts in **batches**, watching for collateral before the next batch.
- Keep strategic rank spend flowing while you redirect it. Protect velocity and organic rank (verified via Rank Radar) while fixing efficiency; don't yank a rank lever the same week you tighten bids.
- State the sequence explicitly (Lever 1 first, then 2…) and note the risk of doing it all at once.

Mention bigger structural moves (e.g. re-segmenting campaigns, new Optimization Groups) as **where this is heading**, staged after the quick wins land, not as a same-day rebuild. This pairs with the batch-by-batch write policy below.

## 6. Write policy (critical)

- The audit itself is **strictly read-only**: no `update_entities`, `create_entities`, `optimizer`, `harvesting`, `tags`, or dashboard/context mutations.
- AdLabs writes (including `set_core_context`) happen only after the operator **explicitly lifts the read-only rule for that write in the current chat**. A general "sounds good" is not a lift, and the permission layer will block otherwise. Apply approved changes batch-by-batch with a what-will-change summary per batch, tagged so the next audit can measure each batch's impact.

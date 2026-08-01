---
name: amazon-audit
description: Use for every Amazon ad or sales audit, whether the brand is an AdLabs-managed client or a prospect audited from downloaded files. Trigger on `/amazon-audit`, `/adlabs-audit`, ad audit, sales audit, account audit, or analyze this AdLabs account. Auto-detects the data source, then asks one question for the report posture (deep / monthly / actions). Self-contained: narrative voice, workbook standard, figure set and branded-document contract all live here. Read-only.
---

# Amazon Ad / Sales Audit

Browser: Mixed (AdLabs and DataDive over MCP; Business Report, SQP and the ads bulk over the CDP report fetcher on the download path; live creative capture over CDP on both paths; build is local).

This file is the whole standard. It replaces the two former audit skills and the separate
playbook doc, so nothing here points outside this directory.

## The thesis

**We run ads to rank organically high.** Everything below is ordered by that. Five rules fall
straight out of it, and the second one is the part most audits get wrong.

1. **The audit opens on organic reality**, not on ads. Who outranks you and why comes first.
2. **Ads do not buy rank. They buy velocity and conversion evidence.** Ad rank and organic rank
   are separate systems: bidding $100 a click wins the ad slot, not the organic one. What
   keyword spend does is attach sales to a query, which feeds velocity and BSR and gives Amazon
   conversion data for that term. So spend converts into rank only when the product's own
   conversion performance on that term is already competitive. **Below-market CVR means the push
   will not land**, and a failed ranking experiment actively teaches Amazon the product deserves
   to rank lower. Check CVR against market before recommending a rank push; if it is below,
   the recommendation is to fix the offer (price, main image, A+) and retest, not to bid.
3. **Spend above target is not automatically waste.** It is waste only if it fails to buy
   something. For rank campaigns, verify with DataDive Rank Radar and quote cost-per-rank in
   the profile currency. Holding or gaining a high-SV core term is the spend working. Flat or
   slipping core terms, or gains on tiny-SV terms, turn it back into waste.
4. **Never cut bids where organic slips while ads carry it.** Check the rank series before any
   bid-down recommendation. If spend has to come down, step it down while watching a rank
   tracker; never cliff-drop it.
5. **Amazon scores conversion per keyword**, so traffic arriving without a keyword (external,
   social, influencer, direct) builds **no** organic rank. It builds the brand term and nothing
   else. That is why ads buy long-tail rank, and stating the mechanism is what separates a
   recommendation from an assertion. Two structural facts follow: BSR is category-wide, so ad
   sales on any keyword lift it and can indirectly help terms never bid on; and keyword ranking
   history survives campaign changes, so recreating a campaign does not reset the product's
   history with that term.

**When a rank push is not worth recommending at all:** the product is structurally uncompetitive
on price, category demand is declining, it already ranks first, the rating is too low to convert
regardless, or the auction has no ceiling left (competitors stop playing along once one brand
dominates, so bids climb while realized CPC stays capped).

**Audit versus operate.** This skill DIAGNOSES. The weekly loop that actually moves bids,
budgets and opt-groups is `amazon-ppc-management` (`/ppc-manage`). When the ask is "run the
week" or "apply the changes", route there. When the ask is what is wrong and why, stay here.
For week-over-week per-keyword SQP against PPC spend, pair with `/supa` (`tools/sqp-supa/`).

---

## 0. Which audit is this

### Detect the data source. Do not ask.

Run the AdLabs startup sequence and look for the brand:

1. `start_chat_session`, then `read_resource(adlabs://instructions)`. Pass the returned
   `chat_session_id` on every later call.
2. `get_entity_data(teams)`, then `get_entity_data(profiles, team_id)`.

- Profile found: **MCP path** (section 2A). The brand is a managed client.
- Not found: **download path** (section 2B). The brand is a prospect with no live connection.
- MCP unavailable, or the name match is ambiguous: ask, folded into the question below.

**Name the detected source in the confirmation message** so the operator can override it in one
word. Connection status drives the data source and nothing else: the analysis is identical.

### Then ask the posture. Once, in a single message.

Skip anything the arguments or the conversation already supply. Never carry a previous client's
values as placeholders.

| Posture | For | Voice | Default scope | Deliverable |
|---|---|---|---|---|
| `deep` | Onboarding or a prospect pitch | Full narrative, blunt, organic-first | Lens A + Lens B | MASTER `.xlsx` + branded `.docx` **with cover** |
| `monthly` | Recurring managed-client review | Lean, internal, learnings-forward, no roasting | Lens A + tripwire | Inline report **and** branded `.docx`, **no cover**. Workbook on request |
| `actions` | "Just tell me what to change" | None | Lens A only | Prioritized action list with spend impact and GoTo links |

Also capture, in the same message: marketplaces, date window (default last 30 days, compare to
the preceding period), break-even ACOS (real margin if known, otherwise confirm we assume and
flag), brand tokens including real misspellings and which sub-brands count as branded, and
competitor brand names.

Scope defaults from posture so this stays one question. Override in one word.

---

## 1. Context first, before any data pull

Flag explicitly what is missing rather than assuming a clean window.

### `deep`: read the call notes, then move on

There is no prior work to account for. Search the Notion meeting-notes database for the brand
and **match on people and product, not just the name**: accounts rebrand mid-engagement and the
call may be filed under the old name, while a same-week call for a different prospect can look
like a hit. Use `notion-query-meeting-notes` where available, otherwise Notion search and fetch.

The client's stated core problem is often invisible in the exports. An audit that never mentions
the thing they are living with reads as though you were not listening. Call notes also supply
facts the data cannot: reseller counts, agency history, trademark status, off-Amazon spend, SKUs
about to launch.

### `monthly`: build the learnings layer

**This is not a report card on last month's changes.** Write what we learned and what we do
next. Only attribute a metric move to a specific batch when the before and after windows are
equal length, from **one** source, with explicit DATE and COMPARE_DATE. Otherwise state the
learning and the next action and say the attribution is not clean. Never mix Sellerboard
percentages into an AdLabs comparison; quote their currency, not their percentages.

| Source | Where | Notes |
|---|---|---|
| Applied PPC changes | `_local/ppc-manage/<client>/batches/<tag>.json` | Best source: structured, local, per change. `rows[]` carry entity, field, old, new. `score` carries the verdict. Tag form `<client>-<YYYY>W<ww>-<group>[-<lever>]`. |
| AdLabs apply history | AdLabs `logs` (job_overview, job_details) | Batch tags live in the apply `note` string, not in the `tags` tool, which this skill must not call. |
| Vault run notes | `<vault>/Clients/<Name>/Runs/YYYY-MM-DD-<workflow>.md` | Vault path resolves from `AMAZON_AGENT_TEAM_VAULT`, else `_local/team-vault-path.txt`. Only some clients have a `Runs/` folder. |
| Vault lessons | `<vault>/Lessons/wizards-ai-lessons.md` | One global append-only file, not per client. Filter by client mention. Long-form sits in `<vault>/Playbooks/`. |
| Notion tasks | `Client Tasks - Overview` | Fields `Task`, `Status`, `Brand` (relation), `date:Due:start`. Query with `content_search_mode: "workspace_search"`; the default search returns the pages that mention the database, not the database. |
| Events and tests | Notion A/B Tests database | Row types `Promo/Deal`, `Stock Event`, `Price Change`, `Launch`, plus real A/B tests. Resolve the title and properties at runtime. |
| AdLabs profile memory | `context_and_prompts(get_context, PROFILE, <profile_id>)` | Brand terms, product-fact negatives, break-even, strategy doctrine. |
| Slack | Per-client `#<brand>-ew-amazon`; the ID sits in `Clients/<Name>/Amazon Ops.md` under `slack_destination` | Read-only here. Vault first, Slack to verify. Some clients have no dedicated channel. |
| Client ops profile | `node tools/client-profiles/find-client-profile.mjs <slug>` | Account naming, marketplaces, stakeholders, restrictions. Some clients have no `Amazon Ops.md` and will not resolve. |

**Disclose these gaps rather than papering over them:**

- **Notion tasks carry no completion timestamp.** There is only `Status` plus `date:Due:start`,
  so "what we did in month X" is a proxy for completion, not a record of it. Say so.
- **If no events are recorded for the window, say that explicitly.** Silence is not evidence of
  a clean window.
- Vault run notes and per-client history do not exist for every client. Name what was missing.

---

## 2. Get the data

Both paths must fill the same Lens A rows. "That is not available on this path" is only an
acceptable answer for **margin**, and only until the client's P&L arrives.

### 2A. MCP path (managed clients)

**No downloads. No handoff. Do not ask for exports.** Every metric comes live from the AdLabs
MCP and rank comes from the DataDive MCP. The only external input is human context.

Read the audit methodology once per session: `read_resource(adlabs://guides/account_audit)`.
Read each target profile's `adlabs://profiles/<slug>` resource for profile_id, Target ACOS and
Target Total ACOS.

What is available, verified against the filter schemas:

- **Per-ASIN, query-level SQP is available.** The `search_query` entity exposes `PRODUCT_ASIN`
  and `PRODUCT_PARENT_ASIN` plus `ASIN_IMPRESSION_SHARE`, `ASIN_CLICK_SHARE`,
  `ASIN_CART_ADD_SHARE`, `ASIN_PURCHASE_SHARE`, `ASIN_CTR` and `ASIN_CONVERSION_RATE`, each
  beside its `TOTAL_*` market counterpart. The CTR and CVR gaps against market are therefore
  free. It is weekly, Sunday to Saturday, snapped, and not campaign-linked.
- **The Business Report is available** through the Seller Central SP-API link on the `product`
  entity: sessions `ORGANIC_TRAFFIC` / `TOTAL_CLICKS`, page views `TOTAL_VIEWS`, unit-session
  rate `UPS` / `UPPW`, session CVR `TCVR`, Buy Box `FEATURED_OFFER_PERCENT` / `BUY_BOX_VIEWS`,
  sales `TOTAL_SALES` / `ORGANIC_SALES` / `TOTAL_UNITS`, plus `ACOTS` and `ACOTS_TO_TARGET`.
- **Stock is available and is often the real story**: `out_of_stock_days`, `scarce_stock_days`,
  `days_of_cover`, `fulfillable_units`, `availability_trend`, `best_seller_rank`, and the
  `PRODUCT_HISTORICAL_AVAILABILITY` / `PRODUCT_AVAILABILITY_CHANGE` filters.
- **The one real gap is margin.** `PRODUCT_PROFIT`, `PRODUCT_COGS` and `PRODUCT_PROFIT_MARGIN`
  exist only when profit tracking is enabled on the profile, and never break out FBM against
  FBA fees. For a confirmed break-even ACOS use the client's Sellerboard P&L. Break-even =
  margin % + Real ACOS %, cross-checkable as (net profit + ad spend) / sales.

### 2B. Download path (prospects)

Scaffold a config, preflight, hand the browser downloads to Codex, pull DataDive yourself.

1. Copy `tools/amazon-ad-audit/config.TEMPLATE.json` to `config.<client>-<market>.json`
   (gitignored). Fill client, marketplaces, product lines and ASINs, break-even ACOS, brand and
   competitor tokens, `core_tokens`, `asin_groups`, windows. Never reuse another client's values.
2. `python3 tools/amazon-ad-audit/build_audit.py --config <cfg> --preflight` prints per-input
   OK or MISSING, then either READY or a copy-ready Codex download task.
3. Codex gathers the browser downloads to the exact contract paths, notes evidence and caveats,
   and stops. It does not run the builder and does not write the narrative.
4. Pull the DataDive niche and competitors over MCP to the config paths, then re-run
   `--preflight` until READY.

| Input | Config key | Gatherer |
|---|---|---|
| Ads bulk `.xlsx` (SP required; SB, SB-Multi, SD, RAS if running) | `ads_bulk_xlsx` | Codex |
| Business Report `.csv` (Detail Page Sales and Traffic by Child ASIN) | `business_report_csv` | Codex, or `tools/report-fetcher/` |
| Multi-ASIN SQP `.csv`, one per product group, weekly | `sqp_csvs` | Codex, or `tools/report-fetcher/` |
| DataDive niche keywords + competitors JSON | `datadive_niche_json`, `datadive_competitors_json` | This skill, over MCP |
| Rank Radar payload (optional, drives the rank chart) | `rank_radar_json` | This skill, over MCP |

Recommended extras: the SB campaign placement report (the bulk's SB placement rows are
incomplete, only Detail Page populated in practice) and the SP Search-Term Impression-Share
report (top-of-search headroom, and the only real paid share-of-voice number). Not needed:
SB and SD search-term reports.

**Fix the window BEFORE the ads bulk is exported.** The bulk carries no date dimension:
`Start Date` and `End Date` are campaign scheduling fields, and performance is aggregated over
whatever range was requested. A window cannot be sliced afterwards, so a clean-weeks-only cut
needs a second export. Default to 4 complete SQP weeks, Sunday to Saturday, about 28 days, so
ads, BR and SQP line up. `--weeks` takes the period-END date, the Saturday; a Sunday returns
HTTP 400.

Raw exports stage under gitignored `downloads/{client}/` and stay there. Clear the same files
from the browser's `~/Downloads` afterwards. Only deliverables reach the client's Drive folder,
never raw source files.

---

## 3. Lens A: Performance. Every run, every posture.

Each row names its source on both paths. A row that produced no number must be named in the
output with the reason.

| # | Check | Download path | MCP path |
|---|---|---|---|
| A1 | Stock and offline days, before grading any rank campaign | Business Report + operator | `product`: `out_of_stock_days`, `days_of_cover`, `fulfillable_units`, `availability_trend` |
| A2 | Buy Box share, seller count and price, **weekly** | `run.mjs business --start/--end` per week | `product`: `FEATURED_OFFER_PERCENT`, `BUY_BOX_VIEWS` |
| A3 | Organic rank bands and movement; cost-per-rank on every rank campaign | DataDive niche + Rank Radar | same, DataDive MCP |
| A4 | SQP demand and intent split; click share, purchase capture, CVR against market | SQP `.csv` per group | `search_query`, `ASIN_*` beside `TOTAL_*` |
| A5 | **Funnel decomposition** (the tripwire) | SQP, presence-adjusted per week | `search_query`: `ASIN_CTR`, `ASIN_CART_ADD_SHARE`, `ASIN_CONVERSION_RATE` |
| A6 | Demand trajectory: is the niche draining, and is the brand draining faster | DataDive niche + SQP week series | same, plus `search_query` per week |
| A7 | Channel mix and placement mechanism (base bid times multiplier) | ads bulk | `campaign`, `placement` entities |
| A8 | Search-term waste and harvest, 1-gram and 2-gram | ads bulk search terms | `target` + search-term entities, profile-derived aCTC and CVR benchmarks |
| A9 | Structure diagnosis, **enabled and spending only** | `parse_bulk` structure block | `group_by_column(campaign_group_name)` + target reads |
| A10 | Bid categories and budget caps; flag campaigns capped **and** unprofitable | ads bulk | guide formulas |
| A11 | Missing channels: no SB, no SD, no DSP, no retargeting | channel presence in bulk | `campaign` ad-type bands, DSP |
| A12 | Brand leak, and whether branded spend buys anything | search terms + SQP | `analyze(brand_spend_leak_detection)`, then manual variant scan |
| A13 | TACOS against target, period-over-period | BR + bulk | `ACOTS`, `ACOTS_TO_TARGET`, profile deltas |

**A2 in detail.** Sponsored Products only serves while you hold the featured offer, so a
hijacked listing silently caps how much the account is *able* to spend, and the ACOS you are
reading is measured only on the share that survived. Grade the Buy Box before you grade the
ads. Always pull it weekly: a six-week average of 82% once hid a 96% to 57% collapse. **When
the weekly cut moves, go daily before interpreting it.** A real audit showed a 72% weekly drop
that was a single day (Buy Box 93.57% to 43.03%, sales $15,506 to $3,684 on one Tuesday) with
a two-day warning the weekly view erased. Daily also orders the mechanism, which is what decides
the levers: conversion fell first while sessions held, then sessions halved days later as lost
velocity fed organic rank. Buy Box loss usually has **two** causes at once, stock and third-party
sellers; do not settle on the first. Tells: Buy Box bottoming near but not at zero, DataDive's
scraped price sitting far above the brand's own, and `advertisedKws: 0` on the competitor payload.

**A5, the tripwire.** Always compute it. It is arithmetic on data both paths already hold, and it
is the cheapest signal that the problem is not in the ads. Index click rate, cart-adds per click
and purchases per cart-add as your count divided by the market total on the same queries, per
week, then sum. That isolates **which step** differs from the market instead of reporting one
blended conversion rate.

**Read it as three shares, and let the shape name the asset.** This is the diagnosis, not just
the trigger:

- Impression share high, click share disproportionately low: a **CTR problem**. Main image,
  title, price. Stop overspending on the term until it is fixed.
- Click share high, purchase share lower: a **conversion problem**. The detail page. Fix the
  listing, not the bids.
- **Purchase share exceeding click share**: you out-convert the market once clicked. The term is
  **under-exploited**. Send more traffic. This is an opportunity finding, not a defect.

Cross it with CTR and CVR against their own averages to name the asset precisely: above-average
on both means raise bids and double down; below on both means reduce bids or negate; **below-average
CTR with above-average CVR means fix the thumbnail and title; above-average CTR with below-average
CVR means fix the secondary images and A+**. A verdict that stops at "fix the listing" can trigger
an expensive rework of the wrong asset.

**Data-sufficiency gates before any of this becomes a finding.** Filter to a minimum of 100
impressions and 5 clicks per term (raise to about 1,000 impressions and 10 to 20 clicks on large
brands). Per-query rates on tiny denominators are noise. Never let a single week trigger an action
on its own. Sort by the brand's own purchase count to find the terms worth diagnosing, and mine
mid-tail terms: head terms are high-volume and low-relevance, long tails are too thin.

Declare **Lens B due** when any of these fire, and quote the number that fired it:

- the cart-add or purchase step sits below market while click rate does not
- the rating is below the category median, or has moved
- the return rate has moved
- organic rank is slipping while ads carry the traffic

Good CTR plus solid impression share plus below-market CVR is a listing problem, not a bidding
problem. Say that plainly and stop looking in the ads.

**Two things that will make you misread this if you forget them.** SQP impressions count
**page-one results only**, so a low organic rank mechanically depresses your measured CTR: a bad
CTR can be a rank symptom rather than a creative one. And blended CVR moves when the traffic mix
moves, with nothing wrong on the page: a falling branded share of traffic can cut total CVR by
10 to 20% month over month. Segment branded against non-branded before blaming the listing.

**A8, what counts as waste.** Get this wrong and the audit is dishonest in a way a sharp client
will catch.

**Summing the spend on search terms with zero sales is not "wasted ad spend".** A 20% conversion
rate means 80% of clicks do not convert; the inverse of your conversion rate is not waste. On one
$100k-a-month account the honest keyword-level number was about $7k against $40k from a naive
sales-equals-zero filter. An agency that mass-negated every zero-sale term lost most of the
account's sales the following month. Never present that number.

The positive definition, three criteria:

1. Negate only what is **both irrelevant and carrying meaningful volume or spend**.
2. A relevant high-ACOS term is a **bid or harvesting problem, not a negation candidate**.
   High ACOS signals genuine irrelevance only rarely.
3. **Target CPA = AOV × target ACOS.** That is the spend line past which a no-sale term needs
   action. Below it, it has not yet had a fair test.

Useful bands, as bands and not laws: non-converting spend around 10 to 30% is normal (keyword
level lower, search-term level higher), and above 50% is the signal for materially more bid work,
harvesting and negation cleanup.

**Never sort a keyword audit by ACOS alone.** Weigh spend and ACOS together: $70 at an extreme
ACOS does less damage than $1,000 at 100%.

**The death-by-1,000-cuts query.** Compute average clicks to conversion (clicks divided by orders,
which is 1 over CVR) and the target CPC (RPC times target ACOS). Then filter for
`clicks < ACTC AND bid > target CPC`: targets that will never accumulate enough clicks to convert,
each bleeding a little. Well-run accounts sit near 1% of spend in that state. One safety edge:
low visibility can be duplicate cannibalization rather than underbidding, so check for a dormant
twin before cutting the spending copy, or traffic simply shifts onto the twin and spends worse.

**Check the mirror image too: spend that looks good but is not.** An unrefined auto or catch-all
campaign can look brilliant because most of its sales come from a couple of branded terms leaking
through. **Verify any surprisingly good campaign by splitting its converting search terms by
tactic before trusting the aggregate.** The same leakage makes placement-level ACOS a vanity
metric, because branded searches score far better on ad quality and inflate the top-of-search read.

**Re-audit inherited negatives; do not accept them.** A large negative stockpile usually means a
prior agency auto-negated at fixed click or spend cutoffs without checking whether the real failure
was a placement problem or a miscalibrated bid. Over-negation is waste that an audit can see. A
floored bid retests itself as the listing improves; a negative is only ever retested if somebody
remembers to remove it.

**A9 scoping.** Never cite paused or archived campaign counts as a finding; they are already off,
so "archive the N dead campaigns" is not advice worth writing. Look only at ENABLED campaigns and
ask what is wrong inside the live account: enabled campaigns that ran with zero impressions
(live but dark: budget, eligibility, stock, suppression, or empty targeting), paused targets
sitting inside enabled ad groups, and duplicate keyword-plus-match among live targets. A count
computed across all campaigns is inflated by the paused tail and will be wrong. Standard findings
worth naming: duplicate keyword and match pairs, campaigns with no negatives (judge by targeting
type, since an exact-match campaign cannot match what negatives would exclude), oversized ad
groups, branded and generic mixed in one campaign, **mixed match types in one campaign** (placement
multipliers are campaign-level, so placement control becomes impossible), the brand not excluded
as a negative phrase from generic campaigns, and ad groups advertising several parent families.

**A10, the out-of-budget check.** The cheapest read in the whole audit and the one budget failure
that is always wrong. The rule has two sides and they point in opposite directions:

- **Profitable campaign hitting its cap: extend the budget.** Do not cut winners.
- **Unprofitable campaign burning its budget early: reduce the bids, not the budget.** The same
  spend then buys more, cheaper clicks spread across the whole day. A $100 budget gone by morning
  at $1 CPC is 100 clicks; halve the bids and the same $100 buys roughly 200 clicks with full-day
  delivery, at a lower ACOS.

Where a time-in-budget figure is available, read it directly: about 97% in budget means little
opportunity, 63% means missing roughly 37% of the day. On the MCP path the proxy is the last-7-day
average daily spend sitting at the daily budget. Flag campaigns that are **capped and unprofitable
at once**: fix the bids before the budget.

**A13, and a per-product view that finds things the account view hides.** Join total sales per
product against ad spend per product and put **% of total sales beside % of total ad spend**. The
recurring defect it exposes: one product taking 30% of sales but 50% of spend, sitting next to
revenue-carrying products at zero spend. An account-level number cannot show that.

**Judge TACOS at parent-ASIN or category level, never at child level where cross-sell exists.** On
one brand roughly 60% of sales were cross-sales, and a child showed about 80% "TACOS" against a
real 28 to 30%. Also note TACOS alone is gameable: it can be "hit" by cutting budget while sales
fall, so never report it without the sales trend beside it. Where you have enough months, regress
monthly ACOS against monthly TACOS: a weak correlation flags cannibalization, except when ad sales
are only a small share of total sales, where a weak correlation is expected anyway.

**A12 in detail.** High paid impression share plus high organic rank plus high SQP click share is
the signature of overpaying, and it deserves a number rather than a hunch. Match the SP and SB
search-term rows to the hero ASIN's own SQP grid on the branded queries present in **both**, then
report paid clicks over total clicks and ad orders over total purchases. One account: 43.1% of
branded clicks were paid and 51.8% of branded purchases came through an ad, while ranking first
organically. Guardrail the cut with branded click share and purchase share watched weekly, never
SQP impression share.

Two more reads before recommending anything on branded. **Verify branded search volume exists at
all**: no volume means the brand needs awareness, not defence, and defence spend has nothing to
defend. And **if branded purchase share is already above about 90%, additional defence spend is
unlikely to add anything**. The one real holdout in the evidence we hold: a mid-size brand
phase-paused all brand defence for months and its branded purchase share did not move, with the
only measurable effect being a better total ACOS. That is a single account with no seasonality
control, so treat it as a reason to test rather than a reason to cut.

**Open question, decide per client rather than by rule.** External practice caps brand defence at
roughly 10% of total ad spend and treats 20 to 30% as a standing finding. Our position is that the
branded verdict is about execution rather than allocation: a high branded share at solid ACOS is
acceptable in itself, and what deserves criticism is the bids, placements and measurability. These
give different verdicts on the same account. State which one you applied and why.

### When the question is "why did sales fall"

Sales = clicks times CVR, and clicks = impressions times CTR. **Deltas combine by multiplying
decimal multipliers, never by adding percentages.** Find the drivers by **sorting campaigns and
keywords by change**, not by absolute value: sorting by the lowest absolute number just surfaces
dead campaigns. **Compare year-over-year clicks, not spend.** Clicks and sessions are the only
metrics defined identically in the ad console and Seller Central, so they are the safe join.

Work the branches in this order:

1. **Buy Box and stock first.** This is check zero for us and it stays there. Below roughly 30
   days of cover a listing starts losing one-day-shipping eligibility and organic rank drops,
   worsening below about 14 days. On a coming stockout, stop advertising rather than trickling.
2. **Hard stops**, ranked by how often they are the cause: bids too low, then parent-ASIN sibling
   cannibalization (Amazon generally awards one impression per parent per keyword, so siblings
   compete with each other), then accidental or automated negatives, then ad ineligibility (Buy
   Box, out of stock, suppressed or restricted), then a non-indexed keyword. **Automated negation
   rules are the sneakiest**: a keyword that briefly met a rule's condition stays invisibly
   negated for months.
3. **Traffic branch**: search volume first (is the market smaller), then CPC and bids, then
   placement shifts, then impression share. Search volume down 10% with traffic down 25% means a
   visibility loss on top of a demand decline, and the two need separate sentences.
4. **Conversion branch**: listing, then seasonality, then targeting mix. The single biggest
   recurring conversion mover is a deal or promotion starting or ending, yours or a competitor's.
5. **If the metric that moved is ACOS**, reframe it as CPC divided by (CVR times AOV). Fast split:
   a campaign at twice the account CPC is a bid problem; a campaign at account CPC with twice the
   ACOS is a conversion problem. Note that lowering CPC can raise ACOS.
6. **Check our own change log** before calling it a decline. A drop can be a correct optimization
   whose cost was known and accepted. This is what section 1's learnings layer is for.
7. **After a peak** (Prime Day, Christmas), use short rolling windows that exclude the event and
   re-widen week by week, or the comparison is against an inflated base.

**Market against account.** Own CVR falling while market CVR holds is an account-specific problem.
Whole-market CVR declining is competitive or market-wide, and "we are capturing more of a shrinking
market" is a legitimate and useful thing to report.

---

## 4. Lens B: Shopper and Creative

Runs on `deep`, on a guaranteed **quarterly** pass for managed clients, or any time the tripwire
fires (which resets the quarterly clock). This is the half that needs a browser session and a POE
pull, which is the only reason it is not monthly.

### POE reviews and returns, at breadth

Pull wide, then **filter by positioning, not by hardware.** The related-niche graph bridges
categories through brands that span them, so a wide pull returns adjacent categories that share a
supplier rather than a shopper. On one run, 31 of 40 downloaded niches were the wrong category and
came out.

Average review and returns topics **across the relevant niches**, and show the niche count beside
each. Single-niche reads are noisy: one topic ranked eighth at 5.7% in the largest niche alone and
was the most-mentioned complaint at 10.6% across ten. Exclude topics appearing in only one or two
niches.

Pull only on the operator's explicit go: POE leaks viewed niches into the active Seller Central
account, so verify the account identity first. Never fabricate POE numbers. If the data has not
been pulled, keep the section as a clear next step that names the reads and the change each drives.

### Live creative capture

Read-only over the debug Chrome on port 9222, for the client **and the top two competitors**:

```
node tools/listing-capture/capture-cdp.mjs <ASIN,ASIN,ASIN> <out.json> [tld] [lang]
node tools/listing-capture/extract-amazon-listing-images.mjs <ASIN> [--marketplace com] [--out <file.json>]
```

**The extractors return image URLs and an A+ module count, not images.** Download the hi-res URLs
into `evidence/<client>/listing-capture/` and **read every file**. Every gallery frame and every
A+ module gets looked at, never inferred from alt text. On one audit that reversed three of seven
image recommendations, all of which were already implemented and would have shipped to a lead
whose agency had done decent work.

Two rules that came out of that run:

- **Duplication across the gallery and A+ is fine, not waste.** Shoppers split into swipers and
  scrollers, and repetition aids recall. If the strongest proof sits only in A+ below the fold,
  the fix is to put it in the gallery **as well**, not to move it.
- **Three-way beats two-way.** Comparing the client against two competitors surfaces findings
  neither single comparison shows, including advantages the client holds and does not display.

Build an image coverage matrix: for each thing the category rewards or punishes (from the POE
reads), is it covered, and where. The gap is usually coverage, not quality.

### The rest of Lens B

- **Category difficulty**: review and price moat, Ranking Juice listing gap. Rating targets are
  visual: 4.2 and 4.3 render the same star image, 4.5 is the half-star jump worth pushing toward.
- **Listing copy and compliance**: check live titles against the 75-character rule (effective
  2026-07-27) and flag as time-critical when non-compliant; use the forced rewrite to front-load
  target keywords. Check claims where the category is regulated.
- **Indexing, and check the Product Type field.** The Product Type field assigns keyword indexing
  independently of the listing text, so a wrong product type kills organic rank while ads keep
  serving. **Organic gone while ads still run is the signature.** Check it per child ASIN, not
  once per family. Also watch for styled Unicode "bold" glyphs in a title, which are invisible to
  search matching, and empty backend attribute fields, which make the listing invisible to
  left-rail filtered traffic. On a greenfield or relaunch, indexing comes before spend: even a
  large bid buys nothing on a term the listing is not indexed for.
- **Judge CVR inside its AOV band, never against a blanket number.** Conversion rate correlates
  strongly and inversely with average order value, so an 8%-is-good rule of thumb is wrong at both
  ends. Base CVR is set by competitive position, roughly 1% for a weak overpriced product against
  20 to 30% for best-in-class on non-brand terms.
- **Price.** At ASIN level price and CVR move close to one-for-one inverse, and sensitivity
  concentrates above roughly $60 and on increases beyond about 30 to 40%. A naked increase of
  16 to 17% once cut CVR by 30 to 40%, while **the same increase executed as a higher anchor price
  with a coupon back to the target price held the damage to about 10%**. Because RPC is price times
  CVR, and RPC drives the bid formula, **every price or coupon change silently reprices every
  correct bid in the account**. Say so when recommending one.
- **Reviews.** A rating falling from 4.5 to 4.0 materially hurts both CTR and CVR. When a single
  ASIN's conversion drops, a prominent bad photo review is a named first check.
- **The shopper's-eye test**: leave the dashboards and look at the search page. Why would a
  shopper pick this listing over the row of alternatives at their price, with their review counts,
  with their main image? If the honest answer is "they wouldn't", that is the headline and no bid
  change fixes it.

---

## 5. Grading

- **Target hierarchy**: Optimization-Group goal ACOS (`campaign_group`) beats profile Target
  ACOS beats break-even ACOS. Grade each campaign against its own group's goal. Note profiles
  with no Optimization Groups and recommend creating them.
- **Break-even ACOS is an assumption** until margin is confirmed, and every red or amber verdict
  keys off it. State it explicitly, in the deliverable, as a single constant that the whole
  document updates on. State where profile targets sit relative to it.
- **ACOS is always a ratio** (1.09 = 109%) and over 100% is never presented as healthy or
  coloured green. The `acos_fill` helper must never divide by 100.
- **Spend must reconcile** across steps (audit summary against campaign sums; buckets against
  search-term rows). Flag it when it does not. Internal reconciliation will happily agree with a
  double-count, so also eyeball total ad sales against the Ads console before delivery: a gap over
  2 to 3% means a channel is double-counted or missing.
- **Audit only what spent in the window.** A campaign that spent nothing is an old campaign, not
  a peer, so never compare, grade or ACOS-rank it against spending campaigns. The money splits
  already spend-weight, so no math changes; the framing does.
- **Compare counts, not rates, across intents.** Branded and generic capture rates are not
  comparable to each other, because origination biases them. Chart searches by segment and
  purchases against the market, the same measure on both bars. Never chart branded capture % beside
  generic capture %, even with a caveat underneath: the picture wins over the footnote.
- **Split generic in two.** A two-way branded-versus-generic cut is the single most misleading
  thing in an SQP section. `config.core_tokens` splits generic into the winnable **core** (category
  language for this product) and the **head**. On a real audit the two-way cut implied 3.1M of
  addressable demand against 161k of actual winnable demand, roughly 20x, which turned a 7.0%
  category share into a 1.4% one. Competitor brands come out of generic for the same reason.
- **Zero ad waste is a finding, not a clean bill of health.** When the search-term sweep returns
  almost nothing above break-even, stop looking there. Say plainly that the PPC is well run, then
  go find the real story in stock, Buy Box, rating, missing channels or under-scaled prospecting.
- **Underspend is a finding too.** Split spend into harvest against acquisition and quote
  acquisition per day, rather than reporting a monthly total that sounds like a channel.

---

## 6. Write it

The audit is a diagnosis a smart operator hands to a client, not a formal report and not a
project plan. Make each point once, in plain words, in the operator's voice.

### Canonical section skeleton

Use these, in this order. Drop a section the data does not support. Never pad.

1. **Title and a one-line context block**: markets, and the report, ads, SQP and DataDive
   windows. No motivational tagline, no reassurance paragraph. Open on the problem.
2. **Where you stand organically.** The audit opens on organic reality, not ads. Who outranks
   you and why, organic-position bands (1 to 3 best, 1 to 4 workable, 5+ below the sponsored
   fold), rank screenshots, plus time-critical listing flags as callouts here.
3. **Current Account Performance.** Business Report by ASIN. Tables carry the numbers, one line
   of read-through under each.
4. **Demand: what shoppers are actually doing (SQP).** Intent split, CTR and CVR against market,
   branded demand worth defending, which generic is and is not winnable yet, and the funnel
   decomposition. Name the diagnostic play.
5. **DataDive: category difficulty and the SEO gap.** Market size, review and price moat,
   Ranking Juice listing gap.
6. **Ads Summary.** The one-paragraph "what is really going on", the intent-split table, then
   ads by format and SP placement. State the single headline. The TACOS band we call solid is
   10 to 15%.
7. **Good and Bad.** Problems, numbered `Problem N`, each with its evidence. Strengths stated
   inline in a sentence where relevant, never as a separate praise section.
8. **Growth Levers.** Recommendations, numbered `Lever N`, including next-level tactics.
9. **Sources Used** and **Method Notes.** Files, dates, assumptions (especially break-even ACOS),
   classification logic, caveats.

On `monthly`, keep the skeleton but lead with the learnings and next actions from section 1, and
carry period-over-period deltas through sections 3 and 6.

### Cut these

- No opening reassurance paragraph and no standalone punchy tagline.
- No standalone "What Is Working" section. Fold strengths into Good and Bad.
- No "Recommended 30-Day Plan" or Week 1 to 4 breakdown. The levers already say what to do.
- No "What Can Be Reached" and no "Bottom Line" recap. Do not say the same thing a third time.
- Opening questions: keep only the 2 or 3 that change the recommendation (real contribution
  margin and break-even ACOS; growth against profitability mandate). Drop the nice-to-knows.
- **Never touch the data.** Numbers, tables and calculations stay exactly as computed. Only
  prose, framing and section count get trimmed.
- **Always state the intent-split coverage** at the traffic-mix table, for example "SP and SB by
  customer search term, covering 97.8% of spend". Never present Branded, Generic and Competitor
  as if they sum to 100% of spend; name the unclassified remainder. If a reader adds the rows and
  lands below 100%, the document must already have told them why.

### The voice

1. **Second person.** "You are not invisible", "you convert about 10pp below market". Not
   "{Brand} is not invisible".
2. **First-person opinion, plainly stated.** "In my opinion you should keep some strategic
   rank-building spend." "I would highly recommend creating variation parents."
3. **Layer in concrete next-level tactics and reference examples** the raw data will not surface:
   variation parents, AMC audiences on top of generic, main-image and CRO fixes, conditional
   advice ("run SB on generic too, once you know which keywords win").
4. **Hedge causal claims you cannot isolate.** "Creatives could also be a reason why." Not "this
   is not the creative." Do not rule out an alternative you have not proven.
5. **Blunter, shorter.** "not healthy", not "not equally healthy". Prefer plain section names:
   Ads Summary over Executive Summary, Current Account Performance over Current Account Reality.
6. **No spaced em-dashes anywhere.** It reads as AI style. End the sentence and start a new one,
   the way somebody would speak. Colons and parentheses are fine, and lead-ins use a colon:
   `**Problem 1: Title.**` and `**Lever 1: Title.**`. Only exceptions: an em-dash as an empty
   table cell, and numeric ranges.
7. **No reveal framing. State the fact and its size.** The audit is not a story with a twist. Cut
   build-ups like "here is the headline, and it is an unusual one" or "here is the kicker". They
   read as sensational and they delay the number. An operator says "you run zero ads, and it is
   about $1.3k a day, which is small for us", not "what I found here is remarkable".
8. **Ask the strategic question back.** When a recommendation depends on what the client actually
   wants, pose it as the conditional it is. Do not assert a goal the client never stated.
9. **Short paragraphs, one to three sentences.** The client reads this on screen, often while
   skimming before a call. A six-sentence paragraph reads as a wall and the point inside it dies.
   Let a punchy line stand alone. The operator has hand-edited delivered documents purely to split
   paragraphs apart, so write it that way the first time.

### Two checks that decide credibility

- **Scale calibration.** Never state an absolute (revenue, sessions, units) without a reference
  the reader can feel. Convert to a **daily rate** and say how the account compares to the book of
  business it sits next to. "$40k a month" sounds big; "about $1.3k a day, still a small product
  for us" is the truth and sets up the whole audit.
- **Uniqueness test on every claimed strength.** Before crediting an advantage (branded demand,
  external traffic, a rating, a hero SKU), check whether the competitors have it too: per-competitor
  `outlierKws` and `outlierSV`, review counts, price. **A strength everyone in the set has is not a
  moat**, and calling it one is the fastest way to lose a smart client.
- **Contradiction hunt.** Cross the client's positioning and targeting against where the demand
  actually sits: gender, use case, form factor, price tier, pack size. The two facts usually already
  live in different sections of your own analysis, and crossing them is the audit's job. The pattern
  to look for is "they have won a corner, and the corner is tiny".

### Standard operator plays

Check each one, and fold it into Problems or Levers where the data supports it.

- **Placement mechanism.** Do not stop at "product pages bleed". Read base bid times placement
  multiplier on the big campaigns. Multipliers are **campaign-level**: a $10 base bid with a 500%
  top-of-search boost authorizes about $50 per click. Mixed match types in one campaign make
  placement control impossible, and one match type per campaign is the fix. Reduce bids gradually;
  it is rarely smart to just cut. Tie-break bids: bid $10.01, not the round $10 everyone picks, and
  never round a bid or a percentage.
- **Brand negatives in generic campaigns.** Branded search terms leaking into non-branded campaigns
  flatter their numbers. Exclude the brand as a negative phrase from every generic campaign. Negatives
  always go on the ad group, never the campaign.
- **CTR-good, CVR-bad.** Relevant keyword, good CTR, solid impression share, below-market CVR: fix
  the listing, then push that keyword into its own exact campaign (SB and keyword-specific video too).
  Target mid-size terms near the use case, not the giant heads. Match imagery to the query.
- **SD retargeting window.** For non-rebuy products, views and purchases lookback is the last 7 days
  only, ROAS-focused. Top and mid-funnel SD only after the basics work.
- **Branded-spend verdict is about execution, not allocation.** A high branded share with solid ACOS
  is okay in itself. Critique the bids, placements and measurability, and note that organic holds
  brand demand while generic pushes lift overall relevance.
- **Hijackers are an ads problem, not just brand protection.** When resellers hold the Buy Box the
  client cannot scale spend and cannot trust ACOS, so it outranks every optimisation lever. Sequence:
  short-term price under the resellers, then a registered trademark, then Transparency (roughly 44
  days from activation until unauthorised sellers are out). Recommend a **German** trademark: about a
  three-month fast track, and Transparency is worldwide, so a German mark activates it for a US
  listing. Check whether the brand's own D2C funnel is arming them: a funnel selling six units at $10
  hands resellers their cost base, which is why "just price below them" only half works.
- **Creator Connections is a commission channel, not a review engine.** Do not sell it as review
  velocity. Frame it as volume at a cost you set: 20 to 30% commission, paid only on the sale, nothing
  upfront and nothing wasted on traffic that does not convert. Put it beside the account's current
  ACOS and break-even. Sequence it after the Buy Box is secure, or the client pays creators to send
  shoppers to a reseller's offer.
- **Price and scale calls are tests, not directives.** Frame them with the metric to watch: "worth
  trying at the current price, but watch conversion rate and contribution margin after ads". Note
  explicitly that a lower price can end up more profitable through volume. Anchor a price test on the
  funnel's revenue per unit, not its list price.

### Micro before and after

- Bad: "{Brand} is not invisible, but it has an authority gap."
  Good: "You are not invisible. You can win branded and ingredient-adjacent demand now."
- Bad: "the thin review count, not at the creative."
  Good: "the thin review count. Creatives could also be a reason why."
- Bad: "Some of this may be strategic; without a confirmed break-even I'd assume it's too expensive."
  Good: "And don't get me wrong, I would still spend on these. But structure the campaigns so you
  know exactly where they bleed. If it still won't work, layer AMC audiences on top."

---

## 7. Build it

### The workbook set

Ship one **MASTER** Excel file plus its component workbooks: the Ad/Sales Audit workbook, the SQP
Intelligence workbook, and the MASTER that merges both under a built one-page Overview. On the
download path `build_audit.py` produces all three. On the MCP path, build to the same depth using
`ew_audit_style.py` and a per-run script; **do not use `build_audit.py`**, whose preflight and
`parse_bulk` hardcode a contract the MCP does not reproduce.

`① Overview`, built by the master script:

- Obsidian header band and coral subtitle band (market, window, ad-type mix, break-even assumption).
- One coral one-liner: the whole story in a sentence.
- **KPI strip**: ad spend, ad sales, ad ACOS, ad ROAS, total sales across all traffic, TACOS,
  organic-implied sales, ad-to-organic ratio.
- **Traffic-mix table**: per bucket (Branded, Generic, Competitor) list ad spend, % spend, ad ACOS,
  SQP SV share, SQP purchase capture. This is the core story: spend efficiency against demand capture,
  side by side.
- **Placement** table, **Top findings** numbered, **Recommendations**, break-even note in violet.

Then the audit tabs in order, then the `SQP ·` tabs, then one `ⓩ Sources & Notes` appended last.
Merge by copying each source sheet cell by cell (value, style, merges, column widths, freeze panes).
Drop rules: skip the audit's thin per-keyword search-query tab (superseded by the full SQP tabs) and
each component's own Sources tab.

Tab set that earns its place on a full audit: Overview, Executive Summary, Channel Mix, Branded vs
Generic, By Product Group, Placement, Bid Categories, Business Report, Products & Stock, Rank Radar,
SQP Query Intelligence, SQP Top Opportunities, Waste & Winners, Brand Leak, Structure Diagnosis,
Campaigns, Discovery Campaigns, Branded Keywords, Action List, Legacy, Sources & Notes.

### Design system, all tabs

- **Palette** from `_local/branding/branding.json` (see `tools/amazon-ad-audit/BRANDING.md`).
  Reference values: obsidian `0F1318`, coral `FD4807`, violet `3322E0`, deep `0E01A2`, mist
  `5B6573`, cloud `F5F6F8`, hairline `E3E7ED`, ink `1E242C`.
- **Fonts**: Aptos body, Aptos Display headers.
- **Traffic-light fills on decision columns only**, soft pastels: good `C6EFCE`, ok `E2EFDA`,
  warn `FFEB9C`, bad `FFC7CE`. Keep colouring restrained: decision cells, not whole tables.
- **ACOS is a ratio.** Bands keyed to break-even: good below 0.30, ok below 0.50, warn at or below
  0.60, bad above 0.60. Retune the edges to the confirmed break-even.
- **Break-even is an ASSUMPTION** until margin is confirmed. Show it in an explicit banner and say
  every ACOS colour verdict updates on the real number.
- Hidden helper sheets (`sheet_state="hidden"`, `wb.active=0`), gridlines off on presentation sheets.
- `ew.acos_fill` and `gap_fill` return `None` for blank values and openpyxl rejects a `None` fill,
  so guard every conditional fill assignment.

### The standard figure set

Seven charts, built client-agnostically by `tools/amazon-ad-audit/build_figures.py` straight from
the contract inputs, dropped next to the narrative `.md`. Each is **guarded**: a missing input skips
the figure, never fakes it, and never fails the audit.

| Figure | Answers | Needs |
|---|---|---|
| `fig_rank_movement.png` | How did our rank MOVE over the window | `rank_radar_json` |
| `fig_rank_distribution.png` | Where do we rank across the category keyword set now | DataDive niche + `asin_groups` |
| `fig_visibility_vs_competition.png` | Versus who, in one number: share of category SV ranked top 10 | DataDive niche + competitors |
| `fig_price_vs_rating.png` | The price and rating moat. Would a shopper pick us | DataDive competitors; `client_price` or BR ASP |
| `fig_demand_segments.png` | Where demand is, across four exclusive segments | SQP + `brand_tokens`; `core_tokens` to split generic |
| `fig_purchases_vs_market.png` | Purchases, you against the market, same measure both bars | SQP + `brand_tokens` |
| `fig_brand_name_leak.png` | Who ranks on the brand's OWN name, and where we sit | DataDive niche + competitors + `brand_tokens` |

**The rank-movement chart** shows where each keyword's organic rank started and ended: a dumbbell
with a direction arrow, red slipped, green gained, both endpoints labelled, on a real position axis
(1 = top) with a page-2 marker at 20. An earlier version used an INVERTED axis, so a tick like "22"
read as "we rank 22 overall" when it was one keyword's worst position. It pairs well with the hero
term as a small week-by-week table, rank against days out of stock, when stock is the story.

**The brand-name-leak chart** came out of an audit where copycats held ranks 1, 2, 3 and 11 on the
client's exact product name while the client sat at 18, and the market bought 3,420 units on that
query against the client's 28. It earns a standing slot because of the thesis: external and
influencer traffic builds the **brand term** and no category rank, so a brand spending off-Amazon is
creating branded demand that whoever ranks above it will harvest. When it renders with somebody else
on top, it usually outranks every optimisation lever in the deck.

**Price sits against RATING, not review count.** Review count spans three orders of magnitude and
needed a log axis that rendered as exponents, which prospects do not read; worse, plotting only
volume hides the rating, which is usually the number doing the damage. Count is bubble size now.
**Never plot the client at DataDive's price**: it is the Buy Box price, so during a hijack it is a
third party's. Take it from `config.client_price`, else BR ASP.

Chart rules: one measure per chart with categories on the axis and colour as emphasis only, **never
a dual axis**. Single series means no legend. Ordered bands take a sequential ramp, never a
categorical palette. **Derive headline numbers in titles from the data, never type them.** Palette
and font come from the branding file. **Render it and look at it**, because collided labels and
clipped titles only show up when you open the PNG. Simpler beats complete.

---

## 8. Brand it

The narrative ships as a brand-styled **A4 `.docx`**, rendered from the narrative `.md` by
`tools/amazon-ad-audit/render_branded.py`. Not a pixel deck: a clean, readable report carrying the
CI. `render(cfg, outdir, scaffold_md, cover=False, brand_dir=None)` takes a **Path**, not a string.
It is client- and source-agnostic, so the MCP path uses it too: set `custom_kpis` in `metrics.json`
as `[[number, label, sub-or-null], ...]` and the renderer needs no `totals` or `breakeven` at all
(the hook sits in `_kpis(M)`).

- **Typeface Inter.** The brand guide names Geist primary with Inter fallback, but the site and
  these documents use Inter. Scale: cover title 800, section 700, big stat 800, body 400/1.55,
  eyebrow 600 caps.
- **Colour**: neutrals about 70% (Obsidian `#0F1318`, Ink `#11151C`, Cloud `#F5F6F8`, white), one
  accent at 5% or less, Signal Orange `#FD4807`. Numbers tabular.
- **Body is light, not dark.** Dark full-body is hard to read. Keep dark for the cover only.
- **Cover page for first-time audits only** (`branding.first_time`, `--cover` / `--no-cover`), so
  `deep` gets one and `monthly` does not. Dark Obsidian, faint grid, white logo with an orange rule
  and eyebrow, big title, "Prepared for" plus the `branding.prepared_by` byline, "What's inside"
  from the section names, footer `Confidential · <agency URL>`.
- **Content pages**: full black lockup at header left, uppercase report label plus month and year at
  header right. Footer text only: report and client left, `page X of Y` centred, website right, in
  Mist `#9AA5B4`. Never the standalone rocket mark in the footer. The cover carries no duplicated
  running furniture.
- **KPI stat-cards** auto-build from `metrics.json` and sit under the summary section.
- **Page-break hygiene**: widow and orphan control, headings kept with their first lines, and KPI
  rows, tables and figures never split across a page.
- **Brand assets are local and gitignored** (`tools/amazon-ad-audit/brand/`). Regenerate with
  `prepare_brand_assets.py`, which uses headless Chrome for SVG to PNG on macOS. If assets or Chrome
  are missing the build degrades to a plain `md_to_docx` with a warning, never a hard failure.

**Markdown authoring contract, so blocks render as intended and not as headlines:**

- **Levers**: bold lead-in with the body on the SAME line, `**Lever N: Short title.** Body continues
  here.` The renderer splits that into a LEVER N eyebrow plus a title card, then the body as a normal
  paragraph. Do **not** put the whole lever on a heading line; the lever regex will swallow title and
  body into one giant H3.
- **Problems** render as plain bold-lead paragraphs. No card, by design.
- `## H2` is a section header and also feeds the cover's "inside" list. A `> ` line is a pull-note.
  `![caption](rel.png)` is a figure, paths relative to the `.md`. Pipe tables get Ink headers.
  `<!-- ... -->` stubs are dropped. Inline code spans render italic.
- **Render every page and look at it** before delivery: confirm the lockup is proportional on each
  content page, `page X of Y` resolves, and nothing overlaps or clips.

**The narrative `.md` is protected from the builder.** `narrative_scaffold.build()` keeps any file
that no longer contains `<!-- operator:` markers and prints `KEPT authored ...`. Pass
`--force-scaffold` to deliberately restore boilerplate. Rebuilding to refresh figures or the branded
`.docx` is therefore safe. **Delivered audits freeze at build time**, so when the toolkit changes,
rebuild and verify by looking at the rendered pages: captions drift from figures otherwise.

---

## 9. Deliver it

| Posture | Ships |
|---|---|
| `deep` | MASTER `.xlsx` + branded `.docx` with cover, to the client's Drive audit folder |
| `monthly` | Inline consolidated report **and** branded `.docx`, no cover. Workbook on request |
| `actions` | Prioritized action list inline: bids to cut, negatives, budgets, reallocations, each with spend impact in the profile currency and a GoTo link |

The `.docx` is the primary deliverable and the `.pdf` is optional: default is **docx-only**, render
a PDF only when a send-ready one is asked for. The A4 `.docx` opens in Google Docs preserving
layout; upload with conversion disabled, because a native Google Doc conversion breaks the
full-bleed cover, the KPI cards and the font.

**Uploading the binaries.** The Google Drive MCP `create_file` only takes content inline as base64,
so a 1 MB file is roughly 1.5M tokens and the call fails. Copy the files into the local Google Drive
for Desktop mount instead and let Drive sync them, then verify with `search_files parentId=<folder>`.
Delete or replace by operating on the mount file, and MD5-verify local against Drive. Only the MASTER
`.xlsx` and the `.docx` go in the client folder, never raw source files. Keep the build script beside
the output for reruns. Confirm with the operator before a prospect sees anything.

**Attach the GoTo links** per flagged dataset on the MCP path. They are session-generated and expire,
so describe the filters in the deliverable as well.

**Keep sources separate and labelled.** Ads cite AdLabs, net of VAT; P&L cites Sellerboard, gross.
Never mix product totals from one with ad cost from the other. Expect roughly a VAT-sized gap between
the two ad-spend figures and reconcile it explicitly rather than silently picking one.

### Recommendation posture on a managed account

A live account we already run is not a prospect before-and-after, so recommendations read as a
**transition, not an overhaul**. Move bids toward target over 2 to 3 steps, re-measuring between.
Roll out negatives, harvests and budget shifts in batches, watching for collateral before the next
batch. Keep strategic rank spend flowing while you redirect it: protect velocity and organic rank,
verified via Rank Radar, and do not yank a rank lever the same week you tighten bids. State the
sequence explicitly and note the risk of doing it all at once. Mention bigger structural moves as
where this is heading, staged after the quick wins, not as a same-day rebuild.

### Re-delivering after the operator has edited the file

The operator edits the delivered `.docx` in place on Drive. From that moment it is the source of
truth for wording.

**Pull it back before any rebuild.** Copy the Drive `.docx`, extract `word/document.xml` to text,
diff it against the scaffold, and carry their version into the `.md`, because the scaffold is
protected and that is the only way their wording survives.

- **Never restore a paragraph they deleted**, and never rewrite a sentence they wrote. Fix an
  outright typo and say that you did.
- **Correct a number even inside their sentence.** Wording is theirs, arithmetic is ours. If an
  edit introduces a factual error, fix it and flag it plainly rather than shipping it.
- **Archive their copy** to `evidence/<slug>/operator-edits/` before overwriting anything.
- **Bump the version** and delete the superseded Drive file so the wrong one cannot be sent.
- Images can be anchored inside a section you are removing: clear the text runs but keep the
  drawing runs, and never delete an image-bearing paragraph.

Editing their `.docx` directly is only worth it for a text-only change. Anything touching a figure,
a table or the title is safer through the scaffold.

---

## 10. Traps and method notes

### Report-definition traps

Each of these shipped, or nearly shipped, into a real client audit.

- **Never quote a report definition from industry blogs. Check Amazon.** Every SEO blog states SQP
  uses a 24-hour attribution window. Amazon documents no such thing. The real rule is
  **origination**: purchases counted are those originated from the search results page. First-party
  sources, both login-gated and reachable over the debug CDP Chrome: help article
  `G8J4CB5ZBF3NX7TP` and `sellercentral.amazon.com/brand-analytics/metric-glossary` (the content is
  in an iframe and only renders once every "Hide/Show additional metric details" toggle is clicked).
- **Never compare branded capture to generic capture.** Origination is not neutral between them: a
  branded shopper searches and buys in one motion, while discovery leaves the results page and
  returns via brand, link or ad, so that sale is never counted against the generic query that started
  it. Compare you against the market on the same query type only; the market denominator carries the
  identical bias, which is what makes it fair. Expect SQP to explain roughly a third of the business,
  and treat every capture rate as a floor.
- **DataDive `price` is the Buy Box price at scrape time and may not be the client's.** On a hijacked
  listing it is the reseller's. One audit reported the client priced at the category median of $26.35
  when their real price was $34.95, which inverted the whole positioning read. Derive the brand's
  price from Business Report ASP (sales divided by units, checked across weeks).
- **Pin every narrative number to the definition of the figure shipping beside it.** Several "page 1"
  definitions coexist. The rank chart bands 1-4, 5-10, 11-20, 21-50, 51+ and not-ranked, so page 1 is
  the first four added up. **Report rank 1-4 separately and lead with it**: it is what fits above the
  fold and where the sales are, and a single "top 10" count hides the difference between 2nd and 9th.
  Never let a chart title grade the result; the verdict belongs in the narrative, not the axis.
- **Classify SB intent by customer search term, not by target.** An ASIN-targeted SB ad still serves
  against searches. On one account, of $14.7k of SB ASIN targeting, 53% reached generic queries, 45%
  reached the brand's own name and 2% reached someone typing a competitor. By target it read as
  $16.6k of conquesting at 24.6% ACOS, the second most efficient bucket; by search term it was $6.9k
  at 45.4%, the weakest, and it inverted a whole growth lever. Confirm `metrics.st_method` says
  search-term before writing any conquesting number.
- **SQP impression share is not share of voice.** `Impressions: Total Count` counts an impression for
  every product shown on the query, so on a page of about 48 results one ASIN structurally cannot hold
  much. One brand sat at 5.5% impression share on its own name while taking 57.4% of clicks and 71.1%
  of purchases. Use click share and purchase share. The real paid share-of-voice number comes from the
  SP Search-Term Impression Share report.

### Attribution and timing traps

These decide whether a number is real or just early.

- **Always exclude the incomplete current day.** Sales and ACOS reporting lags true attribution by
  roughly 24 to 48 hours, and the data only fully actualizes around day 14. In a 7-day lookback the
  last two days are about 28.5% of the window, so a 33% reading against a 30% target can resolve to
  target a week later with nothing changed. Never open an audit on a number that has not settled.
- **The ad console books a sale to the CLICK date; Seller Central books it to the PURCHASE date.**
  Sales near a month boundary therefore land in different months in the two systems. This directly
  affects any reconciliation of an ads export against a Business Report, which is exactly what this
  audit does, so expect a small gap at the edges and do not chase it.
- **SQP will not reconcile with the SP Search-Term Impression Share report**, and should not be
  forced to. They count different things.
- **View-through attribution inflates SD and vertical-video SB**, which credit sales after an
  impression alone. Where those channels are material, compute click-only ACOS separately from the
  view-inclusive figure. On one account SD and vCPM ran over half of spend and drove attributed
  organic to near zero while making ACOS look artificially strong.

### Placement traps that invalidate a finding

- **Sponsored Products exposes no keyword-by-placement report.** Only campaign-level averages
  exist, so in a multi-keyword ad group you cannot attribute a top-of-search result to a keyword.
  Do not write a per-keyword placement claim.
- **Placement-level ACOS is an aggregation of the ACOS of the keywords delivering there, not an
  independent metric.** A placement can show the lowest ACOS purely because the cheapest keywords
  happen to deliver there.
- **Branded leakage inflates the top-of-search read**, because branded searches score far better
  on ad quality. Split brand out before grading placements or the modifier recommendation is wrong.
- **Top of search is not always best.** Product pages genuinely win sometimes, and during major
  events revenue per click and CVR flatten across placements, so event bid increases should not be
  concentrated on top of search.
- **Data sufficiency**: never read placements on a 7-day window. Use 30 to 60 days, require at
  least one order per placement, and require clicks of at least 1 over CVR. One click and one order
  produce an astronomical revenue-per-click that must not be acted on.

### Method-note caveats to always include

- **SQP week coverage biases every multi-week total, and not neutrally across segments.** A query only
  appears in a week where the ASIN drew impressions. On one account branded queries averaged 2.84 of 4
  weeks and generic 2.33, so a straight sum quietly favours branded. **Average search volume per query
  across the weeks it appears, never sum it.** Purchases are summed, which is safe for ratios because
  your count and the market's come from the same rows, but absolute market totals are floors, more so
  for the sparser segment. **Say this in the document in the client's language**, not only in the
  method notes.
- **Sponsored Brands appears in two bulk sheets** with the same campaigns. Dedupe by Campaign ID and
  count SB once, or ad spend and sales inflate; this once added about $112k of phantom ad sales.
- **SP "Bidding Adjustment" rows carry placement-level campaign totals.** Never sum them with keyword
  or target rows. Audience-cohort rows are excluded from the placement table for the same reason: they
  re-slice the same traffic by audience. On the MCP path the same trap appears as the placement entity,
  whose totals must not be summed with target rows.
- **PAT rows with no typed query classify by target**: own ASIN is branded defence, foreign ASIN is
  conquesting. Only where the row genuinely has no search term.
- **SQP revenue gap.** Brand Analytics may have no SQP for some ASINs. Say plainly which high-revenue
  ASINs are missing and that capture figures are floors on the covered set.
- **Ad groups spanning several parent families** are a standard structural finding, since Amazon
  chooses which product serves each query. Note the counter can be inflated by zero-session ASINs that
  each count as their own parent; verify before quoting it.
- **Intent classification is rule-based** (brand, own-ASIN, competitor, generic) and audit-grade only.
  Review before any bulk campaign change.
- **RAS absence is not a finding.** It places ads on non-Amazon retailer sites and is a deliberate
  opt-in. Only SB and SD count as missing motions.
- **DataDive MKL caps at 500 visible rows** of the full niche, so category demand totals are a floor.
  Keep outliers visible and do not imply full coverage.
- **AdLabs availability labels lie.** "In Stock" or "Eligible" can appear with `fulfillable_units = 0`.
  Check units before diagnosing dark campaigns.

### Path-specific mechanics

**MCP path.** Read the aggregate reference first. `query` is SELECT-only, with no GROUP BY, so use
`group_by_column`, which recalculates derived metrics. Match-type casing differs between audit-summary
labels and row filters, so use `LOWER(col) LIKE` when a literal returns zero rows. Placement modifiers
can multiply a low base bid several-fold, so when a target shows a low bid but a high CPC, fix the
modifier or the base bid, not the symptom. `organic_sales` on the product entity is derived from
`total_sales`; never sum it with ad sales. The `search_query` entity has **no date column**, so a
single range pull aggregates the weeks: pull once per week whenever week-over-week movement is the
point, which is what `/supa` does, and `COMPARE_DATE` is unsupported there. The `campaign` entity
returns only ENABLED and PAUSED, **never ARCHIVED**, so archived spend is invisible: say so rather
than reconciling to it. **Delta conventions differ**: the profile entity returns `*_delta_percent` as
a ratio while the product aggregate returns a true percent. `analyze(brand_spend_leak_detection)`
substring-matches `brand_name`, so it silently misses misspellings that do not contain the root; scan
variants manually before trusting its total. Big Rank Radar payloads overflow, so parse the saved
tool-result file with python.

**Download path.** Reading Amazon bulk `.xlsx` needs streaming: `openpyxl` with `read_only=True` and
bounded `iter_rows`. A real account hit about 288k rows on the SP Campaigns sheet alone, roughly
355 MB decompressed. Amazon writes a bogus `A1:A1` sheet `<dimension>` and openpyxl 3.1.5 clips the
read to it on **both** axes; `reset_dimensions=True` does not override it. The fix is explicit bounds
on both axes: read the header with a generous `max_col`, trim trailing empties to the true width, then
stream from `min_row=2` with a large `max_row` at that width. Never open the bulk with
`read_only=False`: per-cell access over 288k rows ran about 40 minutes at multi-GB RSS. If a build
hangs for minutes on a large account, this is why.

**Brand tokens.** Include real misspellings; exclude dictionary words that merely resemble the brand.
The match is a plain substring, so bare `elf` catches "shelf" and bare `mac` catches "macadamia". Use
`e.l.f.` or `mac makeup` instead and disclose that the short forms are under-counted. Mine tokens from
the client's own SQP rather than guessing.

### Data-completeness gate

On the download path, `--validate` must pass three hard gates (spend reconciliation, no ACOS ratio
above 1.0 carrying a green fill, master tab count) and also prints soft WARNINGS plus a DATA
COMPLETENESS panel: low intent coverage, SQP revenue gap, missing channels, multi-parent ad groups.
These are not bugs, they are thin data. **Resolve or disclose every one before delivery.**

On the MCP path there is no `--validate`, so state the equivalent explicitly: which Lens A rows
produced numbers, which did not, and why.

### Where our doctrine deliberately differs from outside practice

Keep these. They are ours, tested, and the external corpus either never got burned the way we did
or actively disagrees.

- **Buy Box and stock are check zero.** Outside diagnostic trees barely mention the featured offer.
  Ours opens on it because Sponsored Products only serves while you hold it.
- **Negatives go on the ad group, never the campaign.** Outside practice prefers campaign level for
  the auto-coverage. Our standard is ad group, and a campaign-level negative found in an audit is a
  finding to fix, not a style choice.
- **Bids and percentages are never rounded.** Bid the odd cent, not the round number everyone picks.
- **A bid corridor is not a duplicate.** The same keyword across match types at deliberately
  different bids is a corridor; only unintended same-match repeats are duplicates. Nothing outside
  makes that distinction, and conflating them produces a wrong structural finding.

Research in the team vault is **evidence, not doctrine**. Where a claim there is single-source,
vendor-adjacent, or self-reported by whoever sells the service, treat it as a hypothesis worth
testing rather than a rule to apply to a client's account.

---

## 11. Read-only, and where to stop

- **The audit is strictly read-only.** No `update_entities`, `create_entities`, `optimizer`,
  `harvesting`, `tags`, or dashboard and context mutations. No campaign, bid, budget or listing
  changes on either path.
- **AdLabs writes, including `set_core_context`, happen only after the operator explicitly lifts the
  read-only rule for that specific write in the current chat.** A general "sounds good" is not a lift,
  and the permission layer will block otherwise. Apply approved changes batch by batch with a
  what-will-change summary per batch, tagged so the next audit can measure each batch.
- **Never hand-edit the builders per client.** Everything client-specific lives in the config. If the
  code cannot express something, extend the toolkit rather than forking it.
- Verify the artifact, not the exit code: count outputs against inputs before reporting success.
- Stop before any account-changing action. This is analysis only.

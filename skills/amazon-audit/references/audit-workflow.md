# Audit Workflow

Mode browser: Mixed (AdLabs and DataDive over MCP; Business Report, SQP and the ads bulk over the CDP report fetcher on the download path; live creative capture over CDP on both paths; build is local).

This skill is the whole standard. It replaces the two former audit skills and the separate playbook
doc, so nothing here points outside this directory.

This file is the spine: it decides the numbers and the stops. The mechanics for each phase load
from `skills/amazon-audit/references/` at the step that needs them. Every one of those loads sits on a gate the run
cannot bypass, so read the named file when the step says to.

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
budgets and opt-groups is `amazon-ppc-weekly-management` (`/ppc-manage`). When the ask is "run the
week" or "apply the changes", route there. When the ask is what is wrong and why, stay here.
For week-over-week per-keyword SQP against PPC spend, pair with `/supa`. Without that slash
command, run the same build from `tools/sqp-supa/build_supa_workbook.py`; the method lives in
`tools/sqp-supa/README.md`.

---

## 0. Which audit is this

Three stages: ask the job, resolve what is already known, then ask only what is left. Never fire
every field at the operator regardless of the job. Most of what a recurring client needs is
already on file, and asking for it again invites an answer that contradicts what is stored.

### Stage 1. Ask the job. Before any lookup.

This is operator intent, and no lookup can infer it, so it comes first. Ask this and nothing else.

| Ask it as | Internal key | For |
|---|---|---|
| First-time audit | `deep` | A prospect pitch before the brand is connected to AdLabs |
| Monthly review | `monthly` | A client we already run |
| Actions only | `actions` | A read-only prioritized change list for an AdLabs-managed client |

The rest of this file and both lens references use the internal key, so read `monthly` wherever
the posture is named later.

**The posture fixes the data source.** A first-time audit is always prospect work and never calls
AdLabs. Monthly and actions-only audits are managed-account work and require AdLabs. Applying any
action leaves this skill and routes to `amazon-ppc-weekly-management`.

Skip this stage entirely when the arguments already say it.

**Named style shortcut.** If the operator says `same style as UltimaPeak`, `UltimaPeak style`, or
`evidence-hybrid`, treat it as a request for the `deep` posture with
`narrative.mode=evidence_hybrid`. This shortcut controls presentation and evidence selection only.
It does not reuse UltimaPeak's ASINs, competitors, market, dates, claims, assumptions, or findings.
Resolve the new prospect brief normally and build every conclusion from that prospect's evidence.

| Job | Voice | Default scope | Deliverable |
|---|---|---|---|
| `deep` | Full narrative, blunt, organic-first | Lens A + Lens B | Native MASTER Google Sheet + branded Google Doc **with cover** |
| `monthly` | Lean, internal, learnings-forward, no roasting | Lens A + tripwire | Inline report **and** branded Google Doc, **no cover**. Workbook on request |
| `actions` | None | Lens A only | Prioritized action list with spend impact and GoTo links |

### Stage 2. Route and pre-fill. Silent, no questions.

**`deep`: download path.** Read `references/source-bulk.md`. Do not start an AdLabs session and do
not look for a profile. Resolve any existing per-client audit config, then read the matched prospect
call notes for context. A first-time audit still asks the full brief in stage 3 because prospect
facts and margin assumptions must be explicit.

**`monthly` and `actions`: AdLabs path.** Read `references/source-adlabs.md`, then run the startup
sequence:

1. `start_chat_session`, then `read_resource(adlabs://instructions)`. Pass the returned
   `chat_session_id` on every later call.
2. `get_entity_data(teams)`, then `get_entity_data(profiles, team_id)`.

Require an unambiguous profile. If AdLabs is unavailable or the profile is missing, stop and report
the blocker. Never fall back to downloaded files for these postures.

Then **resolve what is already known instead of asking for it** from profile memory, the client ops
profile, and the per-client config: brand terms, product-fact negatives, break-even, doctrine,
account naming, marketplaces, ASINs, product groups, competitor tokens, and `core_tokens`.

### Stage 3. Ask only what stage 2 did not resolve.

Never carry a previous client's values as placeholders.

**First-time audit** asks the full brief, because nothing is on file: client and marketplaces,
product lines and ASINs, DataDive niche (URL or ID), break-even ACOS (real margin if known,
otherwise confirm we assume and flag it), brand tokens including real misspellings and which
sub-brands count as branded, and competitor brands.

**Monthly review** asks three things:

1. Which marketplaces this cycle. Default to every profile found.
2. Date window. Default last 30 days against the preceding period.
3. Anything not in the tracker we should know: stock event, promo, price change, launch.

Then **state what stage 2 auto-filled** (break-even, brand tokens, competitors, ASINs, product
groups, targets) so a wrong value can be corrected in one word. Do **not** ask whether the Lens B
quarterly pass is due: compute it and report it.

**Actions only** asks marketplaces and window, and nothing else.

---

## 1. Context first, before any data pull

Flag explicitly what is missing rather than assuming a clean window.

For managed postures, stage 2 already read the AdLabs profile memory and client ops profile for the
**brief** values. This step reads for a different purpose: what happened, what we learned, and what
to do next. Reuse what stage 2 already pulled rather than fetching it twice, and never turn any of
it into a question.

### `deep`: read the call notes, then move on

There is no prior work to account for. Search the Notion meeting-notes database for the brand
and **match on people and product, not just the name**: accounts rebrand mid-engagement and the
call may be filed under the old name, while a same-week call for a different prospect can look
like a hit. Use `notion-query-meeting-notes` where available, otherwise Notion search and fetch.

The client's stated core problem is often invisible in the exports. An audit that never mentions
the thing they are living with reads as though you were not listening. Call notes also supply
facts the data cannot: reseller counts, agency history, trademark status, off-Amazon spend, SKUs
about to launch.

Turn every material call statement into an **internal hypothesis matrix** before writing. Verdicts
are `Confirmed`, `Not supported`, `Mixed or confounded`, or `Not verifiable from available data`.
Keep the full matrix internal. Do not create a separate call-validation section. Integrate only
contradictions and conclusions that change the client recommendation into the relevant diagnosis
or action. Goals and preferences remain labelled as goals, never verified facts.

For any cart-abandonment claim, use Search Catalog Performance for the absolute ASIN funnel and
SQP for the same-query market comparison. A large absolute click-to-cart or cart-to-purchase drop
does not prove underperformance. Confirm the claim only when sufficiently sampled, commercially
important queries materially trail the market at the relevant step. Mark it not supported when the
ASIN matches or beats the market, and mixed when suppression, traffic mix, or thin coverage prevents
a clean conclusion. Never screenshot SQP; point to its workbook tab. A Search Catalog Performance
screenshot is allowed only when it visibly supports a material finding.

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

- **`deep`: download path.** Scaffold the config, preflight, gather browser downloads, pull
  DataDive over MCP, and build locally. Never call AdLabs.
- **`monthly` and `actions`: AdLabs path.** Campaigns, targets, search terms, placements, per-ASIN
  SQP, the Business Report, and stock are live on the MCP. Never fall back to bulk downloads.

Rank data comes from the DataDive MCP on both paths.

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
| A5 | **Funnel decomposition** (the tripwire) | Search Catalog Performance + SQP, per average week (see the method notes) | `search_query`: `ASIN_CTR`, `ASIN_CART_ADD_SHARE`, `ASIN_CONVERSION_RATE` |
| A6 | Demand trajectory: is the niche draining, and is the brand draining faster | DataDive niche + SQP week series | same, plus `search_query` per week |
| A7 | Channel mix and placement mechanism (base bid times multiplier) | ads bulk | `campaign`, `placement` entities |
| A8 | Search-term waste and harvest, 1-gram and 2-gram | ads bulk search terms | `target` + search-term entities, profile-derived aCTC and CVR benchmarks |
| A9 | Structure diagnosis, **enabled and spending only** | `parse_bulk` structure block | `group_by_column(campaign_group_name)` + target reads |
| A10 | Bid categories and budget caps; flag campaigns capped **and** unprofitable | ads bulk | guide formulas |
| A11 | Missing channels: no SB, no SD, no DSP, no retargeting | channel presence in bulk | `campaign` ad-type bands, DSP |
| A12 | Brand leak, and whether branded spend buys anything | search terms + SQP | `analyze(brand_spend_leak_detection)`, then manual variant scan |
| A13 | TACOS against target, period-over-period, only when Ads and sales windows align | BR + bulk; otherwise N/A | `ACOTS`, `ACOTS_TO_TARGET`, profile deltas |

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
and purchases per cart-add as your count divided by the market total **on the same queries and the
same weeks**, averaged per query across the weeks it appeared, then summed within the segment. That
puts both sides of every ratio on one basis and isolates **which step** differs from the market
instead of reporting one blended conversion rate. See the method notes for why a window sum is
never the right total here.

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

Runs on `deep`, on a guaranteed **quarterly** pass for managed clients, or any time the Lens A
tripwire fires (which resets the quarterly clock). It is the half that needs a browser session and
a POE pull, which is the only reason it is not monthly.

**Read `references/lens-b-shopper-creative.md` when it runs.** Say which of the three reasons
triggered it, and quote the number if it was the tripwire.

If it does not run this cycle, say so in the output and name the date of the last full pass. A
skipped Lens B is a disclosure, never a silence.

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
- **Split generic in two, in the table as well as the charts.** A two-way branded-versus-generic
  cut is the single most misleading thing in an SQP section. `config.core_tokens` splits generic
  into the winnable **core** (category language for this product) and the **head**. On a real audit
  the two-way cut implied 3.1M of addressable demand against 161k of actual winnable demand, roughly
  20x, which turned a 7.0% category share into a 1.4% one. Competitor brands come out of generic for
  the same reason. Note which way the error runs: the client's capture rate barely moves, so this
  never flatters or damages their performance. What it inflates is **the size of the prize**, which
  is the number a prospect uses to decide whether to hire us.
- **Say out loud why the head is excluded, naming the client's own keywords.** Do not leave it as a
  method note. Both figures are true, and a combined number is not wrong on its face; the damage is
  in what it implies. Tell the reader that quoting a share of the whole category would invite them
  to read the remainder as available to them, that it is not, and that no single listing wins terms
  like the head example. Name a real core term and a real head term from their own data, state the
  multiple between combined and core, and say every target in the document is set against the core.
  `narrative_scaffold` pre-fills this paragraph with the client's actual terms, so it ships by
  default; never delete it to save space. Then add the honest caveat: the line between core and head
  is our judgement from a keyword list they can inspect and argue with. **If the operator cannot say
  this on the call, the lead leaves with a number twice its real size.**
- **Zero ad waste is a finding, not a clean bill of health.** When the search-term sweep returns
  almost nothing above break-even, stop looking there. Say plainly that the PPC is well run, then
  go find the real story in stock, Buy Box, rating, missing channels or under-scaled prospecting.
- **Underspend is a finding too.** Split spend into harvest against acquisition and quote
  acquisition per day, rather than reporting a monthly total that sounds like a channel.

---

## 6. Traps that change a number

These are applied during analysis, not during writing. Each one has shipped, or nearly shipped, into a real client audit.

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

**Brand tokens.** Include real misspellings; exclude dictionary words that merely resemble the brand.
The match is a plain substring, so bare `elf` catches "shelf" and bare `mac` catches "macadamia". Use
`e.l.f.` or `mac makeup` instead and disclose that the short forms are under-counted. Mine tokens from
the client's own SQP rather than guessing.

---

## 7. Write, build, brand and deliver

**Read `references/writing-and-delivery.md` before writing a line.** It carries the canonical
section skeleton, the operator voice, the cut-list, the standard operator plays, the workbook and
design system, the figure set, the branded A4 document and its markdown authoring contract, the
delivery rules, and the method-note caveats that must appear in every deliverable.

What the posture decides: `deep` ships the native MASTER Google Sheet plus a branded Google Doc
with a cover. `monthly` ships an inline consolidated report plus a branded Google Doc with no cover, workbook on
request. `actions` ships the prioritized change list only, with spend impact in the profile
currency and GoTo links, and skips the narrative entirely.

The native Google Doc is the audit deliverable. Never create, export, retain, or deliver a PDF
unless the operator explicitly requests one. Inspect the native Google Doc directly.

The default document label is **Account Audit**. An explicit client-specific `branding.doc_label`
override still wins.

**Native conversion is not finished until the cover and header are normalized.** For every `deep`
audit, read the converted Google Doc, build the request batch with
`tools/amazon-ad-audit/native_doc_normalize.py`, apply it with revision control, and read the Doc
back. The native result must have a zero-margin first section, an A4 cover image that fills the
entire first page, no header or footer on the cover, a next-page section break before body content,
and content-page labels aligned to the right content edge. DOCX section or header-table geometry is
not proof. Google conversion can flatten both. Visually inspect the cover and every content-page
header in the native Doc before delivery.

After native Google conversion or any in-place heading edit, explicitly normalize every
`Priority N:` heading to Inter 12.5 pt, bold, Ecom Wizards Ink `#11151C`. Never leave priority
headings in Google Docs' default blue or another inherited Heading 2 colour.
Keep every diagnosis, evidence sentence, and `I would` recommendation beneath a priority in
regular Inter 10.5 pt Ink. Do not bold or italicize the whole supporting paragraph. Bold is
reserved for the priority title and isolated metrics that genuinely need emphasis.

---

## 8. Hard rules, always apply

These hold on both paths, in every posture, whether or not a reference was loaded.

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

The next four are where our doctrine deliberately differs from outside practice. Keep them. They
are ours, tested, and the external corpus either never got burned the way we did or actively
disagrees.

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

## References

- `references/source-adlabs.md`: the AdLabs MCP path. Entities and what each carries, the margin
  gap, and the MCP mechanics that silently return wrong rows.
- `references/source-bulk.md`: the download path. Config contract, capability-based preflight,
  the window rule, the bulk parse traps, and the `--validate` gates.
- `references/lens-b-shopper-creative.md`: POE reviews and returns at breadth, live creative
  capture for the client plus two competitors, image coverage, indexing, price and reviews.
- `references/writing-and-delivery.md`: everything from the first sentence of the narrative to the
  file landing in the client's Drive folder, including re-delivery after the operator has edited it.

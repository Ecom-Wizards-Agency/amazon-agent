# Amazon Ad / Sales Audit Playbook

The repeatable standard for Ecom Wizards Amazon ad/sales audits: the same narrative
structure, the same operator voice, and the same master-workbook layout every time.
Follow this for any "make an ad audit / sales audit" task **before** writing the
narrative or building the workbook.

This file is client-agnostic and public-safe on purpose. **Never** put a real client
or brand name, ASIN, niche ID, account ID, Drive/file ID, or personal (pCloud/vault)
path in this file. Use placeholders like `{Brand}`, `{ASIN}`, `{niche-id}` and
repo-relative example paths only.

Scope: this narrative + design standard is shared. It backs the bulk-file
`amazon-ad-audit` skill (prospects / brands not yet on our AdLabs) **and** the
`skills/amazon-adlabs-audit/SKILL.md` skill (existing managed clients, live over the
AdLabs MCP). The two differ only in data source and a few audit-type-specific parts;
voice and workbook design come from here for both.

---

## Part 1: The Narrative

The audit is a diagnosis a smart operator hands to a client, not a formal report and
not a project plan. Make each point **once**, in plain words, in the operator's voice.

### Canonical section skeleton

Use these sections, in this order. Drop a section if the data doesn't support it.
Never pad.

1. **Title + one-line context block**: market(s), the report/ads/SQP/DataDive
   windows. No motivational tagline, no reassurance paragraph. Open on the problem.
2. **Where you stand organically**: the audit opens on organic reality, not ads
   (the operator starts every walkthrough here: "organic ranking is way more
   important"). Who outranks you and why, organic-position bands (1–3 best, 1–4
   workable, 5+ below the sponsored fold), DataDive rank screenshots, plus any
   time-critical listing flags (e.g. title-length compliance deadlines, claims
   crackdowns) as callouts here.
3. **Current Account Performance**: Business Report by ASIN. Tables carry the
   numbers; one line of read-through under each.
4. **Demand: what shoppers are actually doing (SQP).** Intent split, CTR/CVR vs
   market, branded demand worth defending, and which generic is/ isn't winnable yet.
   Name the diagnostic play: good CTR + solid impression share + below-market CVR =
   a listing problem (main image / title / images), not a bidding problem.
5. **DataDive: category difficulty & SEO gap.** Market size, review/price moat,
   Ranking Juice listing gap. Rating targets are visual: 4.2 and 4.3 render the same
   star image on the search page; 4.5 is the half-star jump worth pushing toward.
6. **Ads Summary**: the one-paragraph "what's really going on" + the intent split
   table (Branded / Generic / Competitor), then Ads by format + SP placement. State
   the single headline. TACOS band the operator calls solid: 10–15%.
7. **Good and Bad**: the problems, numbered (`Problem 1…`), each with its evidence.
   Strengths are stated inline in a sentence where relevant, **not** as a separate
   praise section.
8. **Growth Levers**: the recommendations, numbered (`Lever 1…`), including
   next-level tactics (see voice rule 8).
9. **Sources Used** + **Method Notes**: files/dates, assumptions (esp. break-even
   ACOS), classification logic, caveats.

### Cut these: they add length, not value

- No opening reassurance paragraph ("the product isn't failing…") and no punchy
  standalone tagline line.
- No standalone **"What Is Working"** section. Fold strengths into "Good and Bad" and
  into the read-throughs.
- No **"Recommended 30-Day Plan" / Week 1–4** breakdown. The levers already say what
  to do; a week-by-week PM schedule just restates them.
- No **"What Can Be Reached"** section and no **"Bottom Line"** recap. Don't say the
  same thing a third time.
- Opening questions: keep only the **2–3 that change the recommendation** (real
  contribution margin / break-even ACOS; growth vs profitability mandate). Drop the
  "nice to know" ones.
- **Never touch the data.** Numbers, tables, and calculations stay exactly as
  computed. Only prose, framing, and section count get trimmed.
- **State the intent-split coverage explicitly** at the traffic-mix table (e.g.
  "covers 97% of spend: SP by search term, SB by target"). Never present the
  Branded/Generic/Competitor rows as if they sum to 100% of spend; show the
  unclassified remainder (SB video/reach + SD) as its own row. If a reader adds the
  rows and lands below 100%, the doc must have already told them why.

### The voice

Write like the operator talking directly to the client, not a neutral analyst.

6. **Second person.** "You are not invisible", "you convert ~10pp below market".
   Not "{Brand} is not invisible".
7. **First-person opinion, plainly stated.** "In my opinion you should keep some
   strategic rank-building spend." "I would highly recommend creating variation
   parents." "And don't get me wrong, I would still spend on these. But structure it
   so you know exactly where it bleeds."
8. **Layer in concrete, next-level tactics + reference examples** the raw data won't
   surface on its own: variation **parents** (link an example listing), **AMC
   audiences** on top of generic, **main-image / CRO** fixes (is the primary keyword
   even visible on the search page?), conditional advice ("run SB on generic too,
   *once you know which keywords win*").
9. **Hedge causal claims you can't isolate.** "Creatives could also be a reason why".
   Not "this is not the creative". Don't rule out an alternative you haven't proven.
10. **Blunter, shorter.** "not healthy" not "not equally healthy"; "unused" not
    "underpowered"; drop filler like "immediately". Prefer plain section names:
    *Ads Summary* over *Executive Summary*, *Current Account Performance* over
    *Current Account Reality*, *Good and Bad* over separate *What Is Working* /
    *Problems*.
11. **No spaced em-dashes (" — ") anywhere in the narrative.** It reads as AI
    style. End the sentence and start a new one, the way somebody would speak.
    Colons and parentheses are fine. Lead-ins use a colon: `**Problem 1: Title.**`
    and `**Lever 1: Title.**`. Only exceptions: "—" as an empty table cell and
    numeric ranges.
12. **No reveal framing. State the fact and its size.** The audit is not a story with
    a twist. Cut build-ups like "here is the headline, and it is an unusual one",
    "that is rare, and it tells me two things straight away", "and here is the kicker".
    They read as sensational and they delay the number. Say the unusual thing once,
    plainly, then immediately give the scale (see analytical check 1). An operator
    says "you run zero ads, and it is about $1.3k a day, which is small for us", not
    "what I found here is remarkable".
13. **Ask the strategic question back.** When a recommendation depends on what the
    client actually wants (grow rank vs harvest margin, category vs niche), pose it as
    the conditional it is: "the question behind this is what you want to achieve. If
    you want to rank, then…". Do not assert a goal the client never stated.
14. **Short paragraphs. One to three sentences.** The client reads this on screen, often
    in Google Docs, often skimming before a call. A six-sentence paragraph reads as a wall
    and the point inside it dies. Land one idea, then break. Let a punchy line stand alone
    as its own paragraph ("That is the whole problem in one bar. You are sixth."). The
    operator has hand-edited delivered docs purely to split paragraphs apart, so write it
    that way the first time.

### The seven analytical checks (run these before writing a line)

These are the moves that separate an audit from a metrics dump. They came out of real
operator reviews of delivered audits; every one of them was a gap the data already
contained but the write-up had missed. Run all seven, every time. Checks 6 and 7 were
added after an audit shipped without noticing that resellers had taken the client's Buy
Box, which was the single thing the founders had told us on the call was their core
problem.

1. **Scale calibration.** Never state an absolute (revenue, sessions, units) without a
   reference the reader can feel. Convert to a **daily rate**, and say plainly how the
   account compares to the book of business it sits next to. "$40k a month" sounds big;
   "about $1.3k a day, still a small product for us" is the truth and sets up the whole
   audit. An uncontextualised big number reads as hype and costs credibility.
2. **Mechanism, not just metric.** Every finding carries the *why*, not only the number.
   The rank mechanism specifically: Amazon scores conversion and sales **per keyword**,
   so traffic that arrives without a keyword (external, social, influencer, direct)
   builds **no** organic rank. It builds the brand term and nothing else. That is why ads
   buy long-tail rank: ads attach sales to keywords, and keyword sales buy the rank. State
   the mechanism or the recommendation is just an assertion.
3. **Contradiction hunt.** Actively cross the client's positioning/targeting against where
   the demand actually sits: gender, use case, form factor, price tier, pack size. The two
   facts usually already live in different sections of your own analysis. Crossing them is
   the audit's job. The pattern to look for is "they have won a corner, and the corner is
   tiny."
4. **Uniqueness test on every claimed strength.** Before crediting an advantage (branded
   demand, external traffic, a rating, a hero SKU), check whether the competitors have it
   too. In DataDive: per-competitor `outlierKws` / `outlierSV` for off-niche and branded
   pull, plus review counts and price. **A strength everyone in the set has is not a moat**,
   and saying it is one is the fastest way to lose a smart client.
5. **The shopper's-eye test.** Leave the dashboards and look at the search page. Why would
   a shopper pick this listing over the row of alternatives sitting next to it, at their
   price, with their review counts, with their main image? If the honest answer is "they
   wouldn't", that is the headline, and no bid change fixes it.
6. **Context before data: read the call notes first.** Search the Notion meeting-notes
   database (and the ops profile) for the brand **before** writing, and match on the
   brand's *people and product*, not just its name: the account may be mid-rebrand and the
   call filed under the old name, and a same-week call for a different prospect can look
   like a hit. The client's stated core problem often is not visible in the exports you
   pulled, and an audit that never mentions the thing they are living with reads as though
   you were not listening. It also supplies facts the data cannot: reseller counts, agency
   history, trademark status, off-Amazon spend, SKUs about to launch.
7. **Own the Buy Box before you grade the ads.** Check Buy Box share, active seller count
   and price **first**, because they invalidate everything downstream. **Sponsored Products
   only serve while you hold the featured offer**, so a hijacked listing silently caps how
   much the account is *able* to spend and the ACOS you are reading is measured only on the
   share that survived. Grading spend or recommending scale on top of that is wrong in a way
   the client will feel. **Always pull this weekly**: a six-week Business Report average of
   82% hid a 96% → 57% collapse, and the weekly cut plotted against conversion was the
   single most persuasive chart in that audit. `run.mjs business` has no granularity flag,
   so fetch week by week with `--start`/`--end`.

**Price and scale calls are tests, not directives.** Frame them with the metric to watch:
"worth trying at the current price, but watch conversion rate and **contribution margin
after ads**". Note explicitly that a lower price can end up *more* profitable through
volume. Let the numbers decide, and say which numbers.

### Standard operator plays (fold into Problems/Levers where the data supports them)

These came out of real client walkthroughs; check each one on every audit:

- **Placement-mechanism check.** Don't stop at "product pages bleed". Open the big
  campaigns and read base bid × placement multiplier. Multipliers live on **campaign
  level**: a ~$10 base bid with a 500% top-of-search boost authorizes ~$50/click.
  Mixed match types in one campaign make placement control impossible; **one match
  type per campaign** is the fix, and reduce bids gradually (rarely smart to just
  cut). Tie-break bids: bid $10.01, not the round $10 everyone else picks.
- **Brand negatives in generic campaigns.** Branded search terms leaking into
  non-branded campaigns flatter their numbers. Exclude the brand as negative phrase
  from every generic campaign (plus obvious irrelevants, e.g. "shoes").
- **Title-length compliance.** Check live titles against the ≤75-char rule
  (effective 2026-07-27). Flag as time-critical when non-compliant, and use the
  forced rewrite to front-load target keywords.
- **CTR-good / CVR-bad play.** Relevant keyword + good CTR + solid impression share
  + below-market CVR → fix the listing, then push that keyword into its own Exact
  campaign (SB and keyword-specific video ads too). Target specific mid-size terms
  near the brand's use case, not the giant heads. Match imagery to the query
  ("…for men" → show men).
- **SD retargeting window.** For non-rebuy products: views/purchases lookback =
  **last 7 days only**, ROAS-focused; top/mid-funnel SD only after the basics work.
- **Branded-spend verdict is about execution, not allocation.** A high branded share
  with solid ACOS is "okay in itself". Critique the bids/placements/measurability,
  and note organic holds brand demand as generic pushes lift overall relevance.
- **POE mining.** Product Opportunity Explorer return reasons + review themes for
  the niche feed the listing-fix lever.
- **Hijackers are an ads problem, not just a brand-protection one.** When resellers hold the
  Buy Box the client cannot scale spend (SP stops serving) and cannot trust ACOS, so it
  outranks every optimisation lever. Sequence: short-term price under the resellers, then a
  registered trademark, then Transparency (roughly 44 days from activation until
  unauthorised sellers are out). **Recommend a German trademark**: there is a fast track of
  about three months, and Transparency is a worldwide program, so a German mark activates it
  for the US listing. Also check whether the brand's own D2C funnel is arming them: a funnel
  selling six units at $10 each hands resellers their cost base, which is why "just price
  below them" only half works.
- **Creator Connections is a commission channel, not a review engine.** Do not sell it as
  review velocity. Frame it as volume at a cost you set: 20-30% commission, paid only on the
  sale, nothing upfront and nothing wasted on traffic that does not convert. Put it beside
  the account's current ACOS and break-even to show it is competitive with none of the risk,
  and sequence it after the Buy Box is secure or the client pays creators to send shoppers to
  a reseller's offer.

### Micro before → after

- ❌ "{Brand} is not invisible, but it has an authority gap. It can win branded…"
  ✅ "You are not invisible. You can win branded and ingredient-adjacent demand now…"
- ❌ "…the thin review count, not at the creative."
  ✅ "…the thin review count. Creatives could also be a reason why."
- ❌ "Some of this may be strategic; without a confirmed break-even I'd assume it's
  too expensive."
  ✅ "And don't get me wrong, I would still spend on these. But structure the
  campaigns so you know exactly where they bleed. If it still won't work, layer AMC
  audiences on top."

---

## Part 2: The Deliverable (Workbook Standard)

Ship one **MASTER** Excel file plus its component workbooks. The master is a single
file a client can open and read top-to-bottom.

### The three-workbook set

- **Ad/Sales Audit workbook**: the branded audit tabs (Executive Summary, Ads by
  Type, Branded vs Generic, By Product Group, Placement, Waste & Winners, Structure,
  etc.).
- **SQP Intelligence workbook**: the full week-aware SQP tabs (intent/group rollups,
  per-keyword detail with CTR/CVR vs market and CVR gap, data-completeness caveats).
- **MASTER workbook**: merges the two above under one built one-page Overview.

Canonical builders to copy per client (templates, not client-specific logic) live
under the most recent audit's reporting folder as a trio:
`output/{client}/reporting/build_{client}_master_workbook.py` plus its
`build_{client}_audit_workbook.py` and `build_{client}_sqp_workbook.py`. Copy the
latest set, re-point the paths/metrics, and keep the logic. (These local `output/`
files are gitignored; this doc is the committed reference to their shape.)

### MASTER file structure

The master is assembled by copying each source sheet **cell-by-cell** (value + style
+ merges + column widths + freeze panes), then prepending a built Overview:

- `① Overview` (built in the master script):
  - Obsidian header band + coral subtitle band (market · window · ad-type mix ·
    break-even ACOS assumption).
  - One coral one-liner: the whole story in a sentence.
  - **KPI strip**: ad spend, ad sales, ad ACOS, ad ROAS, total sales (all traffic),
    TACOS, organic-implied sales, ad:organic ratio.
  - **Traffic-mix table**: per bucket (Branded / Generic / Competitor) list ad spend,
    % spend, ad ACOS, SQP SV share, SQP purchase capture. This is the core story:
    spend efficiency × demand capture side by side.
  - **Placement** table (spend, ACOS, traffic-lit).
  - **Top findings** (numbered) + **Recommendations** (short/medium term).
  - Break-even-assumption note in violet.
- `② Executive Summary …` and the rest of the audit tabs (audit workbook, in order).
- `SQP · …` tabs (SQP workbook, in order).
- `ⓩ Sources & Notes`: one master sources/notes tab appended last.
- Drop rules when merging: skip the audit's thin per-keyword "Search Query Intel"
  (superseded by the full `SQP ·` tabs) and each component's own "Sources & Notes"
  (folded into the single master one).

### Design system (all tabs)

- **Agency palette** (from `_local/branding/branding.json`, see `tools/amazon-ad-audit/BRANDING.md`; EW values shown as reference): obsidian `0F1318`, coral `FD4807`, violet `3322E0`,
  deep `0E01A2`, mist `5B6573`, cloud `F5F6F8`, hairline `E3E7ED`, ink `1E242C`.
- **Fonts**: Aptos (body), Aptos Display (headers).
- **Traffic-light fills** on decision columns only (soft pastels): good `C6EFCE`,
  ok `E2EFDA`, warn `FFEB9C`, bad `FFC7CE`. Keep coloring restrained: decision cells,
  not whole tables.
- **ACOS is always a ratio** (1.09 = 109%). The `acos_fill` helper must **never**
  divide by 100. Thresholds keyed to break-even: good `<0.30`, ok `<0.50`,
  warn `≤0.60`, bad `>0.60` (retune the band edges to the confirmed break-even).
- **Break-even ACOS is an ASSUMPTION** until margin is confirmed. Show it in an
  explicit banner and say every ACOS color verdict updates on the real number.
- **Hidden helper sheets**: keep raw/working sheets in the file but
  `sheet_state="hidden"` so the client sees only the presentation tabs; `wb.active=0`.
- Turn off gridlines on presentation sheets (`sheet_view.showGridLines=False`).

### Report-definition traps (these produce confidently wrong numbers)

Each of these shipped, or nearly shipped, into a real client audit. Verify all four.

- **Never quote a report definition from industry blogs. Check Amazon.** Every SEO blog
  states that SQP uses a **24-hour attribution window**. Amazon documents no such thing:
  probing the whole Brand Analytics Metric Glossary returns zero hits for "24", "hour",
  "window" or "same session". That claim went into a delivered audit as fact. Amazon's real
  rule is **origination**: Purchases = "the total number of ASIN purchases for the selected
  time period **originated from the search results page**", and "the purchases and sales
  totals may not match the total count from your sales reports as these metrics include
  only those originated from Search results". First-party sources, both login-gated and
  reachable through the debug CDP Chrome: help article **G8J4CB5ZBF3NX7TP** and
  **`sellercentral.amazon.com/brand-analytics/metric-glossary`** (content sits in an
  iframe, and the definitions only render once every "Hide/Show additional metric details"
  toggle is clicked).
- **Never compare branded capture to generic capture.** The origination rule is not neutral
  between them: a branded shopper searches and buys in one motion, while discovery leaves
  the results page and returns via brand, link or ad, so that sale is never counted against
  the generic query that started it. Branded is therefore always measured at its best and
  generic at its worst. Compare **you against the market on the same query type** only. The
  market denominator carries the identical bias, which is what makes it fair. Expect SQP to
  explain roughly a third of the business (one audit: 3,711 SQP purchases vs 10,711 BR
  order items), and treat every capture rate as a floor: Amazon publishes the top 1,000
  queries and says "not all queries qualify".
- **DataDive `price` is the Buy Box price at scrape time, and it may not be the client's.**
  On a hijacked listing it is the reseller's offer. One audit reported the client "priced on
  the category median at $26.35" when their real price was **$34.95** and $26.35 was a
  hijacker holding their Buy Box. That inverted the whole positioning read, median versus a
  40%-above-median premium. **Derive the brand's price from the Business Report ASP**
  (ordered product sales ÷ units, checked across weeks for stability); treat DataDive's
  price only as "what a shopper currently sees".
- **Pin every narrative number to the definition of the figure that ships beside it.** Three
  different "page 1" definitions coexist in this toolkit: `analyze_audit` counts rank ≤15,
  `build_figures` counts rank ≤10, and DataDive's own `kwRankedOnP1Percent` uses a looser
  threshold. One audit shipped "114 keywords on page 1" in prose next to a chart labelled
  "63%", which are the same claim under two definitions. Quote the shipped figure's number.

### Method-note caveats to always include

- SQP is a weekly snapshot set (average the available weeks; per-query rates on tiny
  denominators are noisy, so lead with impression share + purchase capture).
- DataDive MKL is capped at 500 visible rows of the full niche. Keep outliers
  visible; don't imply full coverage.
- SP "Bidding Adjustment" rows carry placement-level campaign totals. **Never** sum
  them with keyword/target rows (double-count trap). Audience-cohort adjustment rows
  (Shopper Cohort with no Placement) are excluded from the placement table for the
  same reason: they re-slice the same traffic by audience.
- **Sponsored Brands appears in two bulk sheets** ("Sponsored Brands Campaigns" +
  "SB Multi Ad Group Campaigns") with the SAME campaigns. Dedupe by Campaign ID and
  count SB once, or ad spend/sales inflate. Always sanity-check the total against the
  Ads console; internal spend-reconciliation alone will not catch a double-count.
- Intent split uses **two methods by channel**: SP by customer search term (complete),
  SB/SB-Multi by keyword text + product-target expression (SB search-term reporting
  covers only ~half of SB spend). State the resulting coverage %; the unclassified
  remainder (SB video/reach + SD) is a labeled row, not hidden.
- **PAT rows classify by target:** own ASIN → Branded (defense), foreign ASIN →
  Competitor (conquesting). This flips a naive "generic is fine" read when a lot of
  spend is ASIN conquesting.
- **SQP revenue gap:** Brand Analytics may have no SQP for some ASINs; the
  completeness gate reports the uncovered revenue share. Say plainly which
  high-revenue ASINs are missing and that capture figures are floors on the covered set.
- **Ad groups spanning several parent families** are a standard structural finding.
  Amazon chooses which product serves each query, so keyword→product fit is
  uncontrolled and per-product ad stats blur.
- Intent classification is rule-based (brand / own-ASIN / competitor / generic).
  It is audit-grade; review before bulk campaign changes.

## Part 2b: The Standard Figure Set

Six charts earn their place in every audit. They are built client-agnostically by
`tools/amazon-ad-audit/build_figures.py` straight from the contract inputs, dropped next to
the narrative `.md`, and referenced by `narrative_scaffold.py`, so the operator writes prose
around figures that already exist. `build_audit.py` runs it automatically. Each figure is
**guarded**: if its input is missing it is skipped, never faked, and a missing chart never
fails the audit.

| Figure | Answers | Needs |
|---|---|---|
| `fig_rank_movement.png` | How did our rank MOVE over the window? The standard rank chart. | `rank_radar_json` |
| `fig_rank_distribution.png` | Where do we rank across the category keyword set right now? | DataDive niche + `asin_groups` |
| `fig_visibility_vs_competition.png` | Versus who, in one number: share of category search volume ranked top 10 | DataDive niche + competitors |
| `fig_reviews_vs_price.png` | The price/review moat. Would a shopper pick us? (analytical check 5) | DataDive competitors |
| `fig_branded_vs_generic.png` | Where the demand is versus where the purchases go | SQP + `brand_tokens` |
| `fig_brand_name_leak.png` | Who ranks on the brand's OWN name, and where we sit | DataDive niche + competitors + `brand_tokens` |

**On the rank-movement chart (the standard rank chart).** It shows where each keyword's
organic rank started and ended over the window: a dumbbell with a direction arrow, red for
slipped and green for gained, both endpoint ranks labelled, on a real position axis (1 = top)
with a page-2 marker at 20. The design exists because the earlier version put rank on an
INVERTED axis, so a tick like "22" read to a client as "we rank 22 overall" when it was one
keyword's worst position (operator's call, 2026-07-16). Showing the actual
position with a direction arrow kills that misread and makes better-versus-worse instant. It
pairs well with the specific hero term as a small week-by-week TABLE (rank against days out of
stock) when stock is the story, rather than forcing time and keywords onto one chart. Input is
a DataDive Rank Radar payload (`keyword` + `ranks` over time); guarded to skip when absent, and
when there are fewer than three ranked keywords.

**On the brand-name leak chart.** It came out of an audit where copycats and namesakes held
ranks 1, 2, 3 and 11 on the client's exact product name while the client sat at 18, and the
market bought 3,420 units on that query against the client's 28. Check 2's mechanism is why
it earns a standing slot: external, social and influencer traffic builds the **brand term**
and no category rank, so a brand spending off-Amazon is *creating* branded demand that anyone
ranking above it will harvest. When this chart renders with somebody else on top, it usually
outranks every optimisation lever in the deck, and it makes the brand-protection sequence
(trademark, then Transparency) a measurable argument rather than a nag. It is guarded twice:
the top branded query must clear `MIN_BRAND_SV` (500) and at least three sellers must rank on
it, so single-product or no-brand-demand accounts get no empty chart. A brand that owns its
own name simply shows itself on top, which is a finding worth stating too.

**A note on zero-review clients.** `fig_reviews_vs_price` plots ratings on a log axis, which
cannot place 0, and a not-yet-rated listing reports `reviewCount: null`. Both used to drop the
client silently off its own chart, which is precisely the audit where the point matters most.
Null is normalised to a real 0 and the client is clamped onto the axis floor and labelled
"no reviews yet". Comparisons and the derived headline still use the true count.

Chart rules (they are why these read clean, so keep them):

- **One measure per chart, categories on the axis.** Identity comes from the axis and direct
  labels, so colour is *only* emphasis: the accent marks the client, a neutral marks context.
  **Never a dual axis.** A second measure means a second panel.
- **Single series means no legend.** The title names it. Never a label on every point: label
  the subject plus the extremes that carry the argument, and let the rest be context.
- **Ordered bands take a sequential ramp** (one hue, light to dark), never a categorical
  palette. Rank bands are ordinal. Absence ("not visible") gets a neutral outside the ramp.
- **Derive headline numbers in titles from the data, never type them.** A hand-typed "90%"
  above a bar labelled 91% is the kind of thing a sharp client spots.
- **Palette and font come from the branding file**, so figures track the brand guide.
- **Render it and look at it.** The palette can be validated automatically; layout cannot.
  Collided labels and clipped titles only show up when you open the PNG.
- **Simpler beats complete.** A chart carrying five segments across fifteen brands and two
  panels loses to one bar per brand with one number on it. If the detail matters, it belongs
  in the workbook.

## Part 3: The Branded Document (agency identity from `_local/branding/`)

The narrative ships as a **brand-styled A4 document**, `.docx` (editable) + `.pdf` (send), rendered from
the narrative `.md` by `tools/amazon-ad-audit/render_branded.py`. Not a pixel deck; a clean, readable report
that carries the CI.

- **Typeface: Inter** (the website font). The brand-guide PDF names Geist primary / Inter fallback, but the
  site (and therefore these documents) uses Inter. Type scale: cover title 800, section 700, big stat 800,
  body 400/1.55, eyebrow 600 caps.
- **Colour:** neutrals ~70% (Obsidian `#0F1318` / Ink `#11151C` / Cloud `#F5F6F8` / White); **one accent,
  ≤5%: Signal Orange `#FD4807`** (eyebrows, rules, KPI-card tops, "Lever n" labels). Numbers tabular.
- **Body is light, not dark.** The brand deck uses dark report pages, but dark full-body is hard to read.
  Keep dark for the **cover only** and use light body + orange accents. State the intent-split coverage %
  at the traffic-mix table; never present the split as if it sums to 100% of spend.
- **Cover page = first-time audits only** (`branding.first_time` / `--cover` / `--no-cover`). Dark Obsidian,
  faint grid (<6%), white logo grouped with an orange rule + eyebrow, big title, "Prepared for" +
  `prepared_by` byline (default "Victor Uhl, Founder"), "What's inside" = the section names, footer
  `Confidential · <agency URL from branding.json>`. Horizontal rules snap onto the grid.
- **Content-page header and footer:** full black Ecom Wizards lockup at header left; uppercase
  `<REPORT LABEL> · <MONTH YYYY>` at header right. The footer is text only: `<Report label> · <Client>`
  at left, `page X of Y` centered, and `www.ecomwizards.agency` at right. Use Inter and Mist
  `#9AA5B4`. Never use the standalone rocket mark in the footer. The cover has no duplicated running
  header or footer.
- **KPI stat-cards** (spend / ad sales / blended ACoS vs break-even / TACoS) are auto-built from
  `metrics.json` and placed under the verdict/summary section: Cloud card, orange top rule, big Inter stat.
- **Markdown conventions** the renderer reads: `## H2`, `**Lever N: title.** body` (the legacy
  `**Lever N — …**` form still parses, but write the colon form per voice rule 11) →
  orange "LEVER N" eyebrow, `> quote` → orange note callout, `![caption](file.png)` → figure + caption,
  pipe tables → Ink-header tables. `<!-- ... -->` stubs are dropped.
- **Page-break hygiene:** widow/orphan control, headings kept with their first lines, KPI-card row / tables
  / figures never split across a page, so no page ends on a lone dangling sentence.
- **Running-furniture QA:** render every page and confirm the full lockup is proportional on each content
  page, `page X of Y` resolves consistently, and no header/footer overlaps, clips, or causes bad reflow.
- **Brand assets are LOCAL/gitignored** (`tools/amazon-ad-audit/brand/`). Regenerate with
  `prepare_brand_assets.py` (headless Chrome for SVG→PNG on macOS). If assets/Chrome are absent the build
  degrades to a plain `md_to_docx` `.docx` with a WARN, never a hard failure.
- **Delivery:** the A4 `.docx` is the Google-Docs-editable file (opens in Docs preserving layout). Do **not**
  convert to a native Google Doc (the full-bleed cover + KPI cards + font break). Send the `.pdf`.

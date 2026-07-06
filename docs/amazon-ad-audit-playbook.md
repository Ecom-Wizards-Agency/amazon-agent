# Amazon Ad / Sales Audit Playbook

The repeatable standard for Ecom Wizards Amazon ad/sales audits: the same narrative
structure, the same operator voice, and the same master-workbook layout every time.
Follow this for any "make an ad audit / sales audit" task **before** writing the
narrative or building the workbook.

This file is client-agnostic and public-safe on purpose. **Never** put a real client
or brand name, ASIN, niche ID, account ID, Drive/file ID, or personal (pCloud/vault)
path in this file — use placeholders like `{Brand}`, `{ASIN}`, `{niche-id}` and
repo-relative example paths only.

Scope: this narrative + design standard is shared. It backs the bulk-file
`amazon-ad-audit` skill (prospects / brands not yet on our AdLabs) **and** the
`skills/amazon-adlabs-audit/SKILL.md` skill (existing managed clients, live over the
AdLabs MCP). The two differ only in data source and a few audit-type-specific parts;
voice and workbook design come from here for both.

---

## Part 1 — The Narrative

The audit is a diagnosis a smart operator hands to a client, not a formal report and
not a project plan. Make each point **once**, in plain words, in the operator's voice.

### Canonical section skeleton

Use these sections, in this order. Drop a section if the data doesn't support it —
never pad.

1. **Title + one-line context block** — market(s), the report/ads/SQP/DataDive
   windows. No motivational tagline, no reassurance paragraph. Open on the problem.
2. **Where you stand organically** — the audit opens on organic reality, not ads
   (the operator starts every walkthrough here: "organic ranking is way more
   important"). Who outranks you and why, organic-position bands (1–3 best, 1–4
   workable, 5+ below the sponsored fold), DataDive rank screenshots, plus any
   time-critical listing flags (e.g. title-length compliance deadlines, claims
   crackdowns) as callouts here.
3. **Current Account Performance** — Business Report by ASIN. Tables carry the
   numbers; one line of read-through under each.
4. **Demand: what shoppers are actually doing (SQP)** — intent split, CTR/CVR vs
   market, branded demand worth defending, and which generic is/ isn't winnable yet.
   Name the diagnostic play: good CTR + solid impression share + below-market CVR =
   a listing problem (main image / title / images), not a bidding problem.
5. **DataDive: category difficulty & SEO gap** — market size, review/price moat,
   Ranking Juice listing gap. Rating targets are visual: 4.2 and 4.3 render the same
   star image on the search page; 4.5 is the half-star jump worth pushing toward.
6. **Ads Summary** — the one-paragraph "what's really going on" + the intent split
   table (Branded / Generic / Competitor), then Ads by format + SP placement. State
   the single headline. TACOS band the operator calls solid: 10–15%.
7. **Good and Bad** — the problems, numbered (`Problem 1…`), each with its evidence.
   Strengths are stated inline in a sentence where relevant, **not** as a separate
   praise section.
8. **Growth Levers** — the recommendations, numbered (`Lever 1…`), including
   next-level tactics (see voice rule 8).
9. **Sources Used** + **Method Notes** — files/dates, assumptions (esp. break-even
   ACOS), classification logic, caveats.

### Cut these — they add length, not value

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
  "covers 97% of spend — SP by search term, SB by target"). Never present the
  Branded/Generic/Competitor rows as if they sum to 100% of spend; show the
  unclassified remainder (SB video/reach + SD) as its own row. If a reader adds the
  rows and lands below 100%, the doc must have already told them why.

### The voice

Write like the operator talking directly to the client, not a neutral analyst.

6. **Second person.** "You are not invisible", "you convert ~10pp below market" —
   not "{Brand} is not invisible".
7. **First-person opinion, plainly stated.** "In my opinion you should keep some
   strategic rank-building spend." "I would highly recommend creating variation
   parents." "And don't get me wrong, I would still spend on these — but structure it
   so you know exactly where it bleeds."
8. **Layer in concrete, next-level tactics + reference examples** the raw data won't
   surface on its own: variation **parents** (link an example listing), **AMC
   audiences** on top of generic, **main-image / CRO** fixes (is the primary keyword
   even visible on the search page?), conditional advice ("run SB on generic too —
   *once you know which keywords win*").
9. **Hedge causal claims you can't isolate.** "Creatives could also be a reason why"
   — not "this is not the creative". Don't rule out an alternative you haven't proven.
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

### Standard operator plays (fold into Problems/Levers where the data supports them)

These came out of real client walkthroughs; check each one on every audit:

- **Placement-mechanism check.** Don't stop at "product pages bleed" — open the big
  campaigns and read base bid × placement multiplier. Multipliers live on **campaign
  level**: a ~$10 base bid with a 500% top-of-search boost authorizes ~$50/click.
  Mixed match types in one campaign make placement control impossible — **one match
  type per campaign** is the fix, and reduce bids gradually (rarely smart to just
  cut). Tie-break bids: bid $10.01, not the round $10 everyone else picks.
- **Brand negatives in generic campaigns.** Branded search terms leaking into
  non-branded campaigns flatter their numbers — exclude the brand as negative phrase
  from every generic campaign (plus obvious irrelevants, e.g. "shoes").
- **Title-length compliance.** Check live titles against the ≤75-char rule
  (effective 2026-07-27) — flag as time-critical when non-compliant, and use the
  forced rewrite to front-load target keywords.
- **CTR-good / CVR-bad play.** Relevant keyword + good CTR + solid impression share
  + below-market CVR → fix the listing, then push that keyword into its own Exact
  campaign (SB and keyword-specific video ads too). Target specific mid-size terms
  near the brand's use case, not the giant heads. Match imagery to the query
  ("…for men" → show men).
- **SD retargeting window.** For non-rebuy products: views/purchases lookback =
  **last 7 days only**, ROAS-focused; top/mid-funnel SD only after the basics work.
- **Branded-spend verdict is about execution, not allocation.** A high branded share
  with solid ACOS is "okay in itself" — critique the bids/placements/measurability,
  and note organic holds brand demand as generic pushes lift overall relevance.
- **POE mining.** Product Opportunity Explorer return reasons + review themes for
  the niche feed the listing-fix lever.

### Micro before → after

- ❌ "{Brand} is not invisible, but it has an authority gap. It can win branded…"
  ✅ "You are not invisible. You can win branded and ingredient-adjacent demand now…"
- ❌ "…the thin review count, not at the creative."
  ✅ "…the thin review count. Creatives could also be a reason why."
- ❌ "Some of this may be strategic; without a confirmed break-even I'd assume it's
  too expensive."
  ✅ "And don't get me wrong, I would still spend on these — but structure the
  campaigns so you know exactly where they bleed. If it still won't work, layer AMC
  audiences on top."

---

## Part 2 — The Deliverable (Workbook Standard)

Ship one **MASTER** Excel file plus its component workbooks. The master is a single
file a client can open and read top-to-bottom.

### The three-workbook set

- **Ad/Sales Audit workbook** — the branded audit tabs (Executive Summary, Ads by
  Type, Branded vs Generic, By Product Group, Placement, Waste & Winners, Structure,
  etc.).
- **SQP Intelligence workbook** — the full week-aware SQP tabs (intent/group rollups,
  per-keyword detail with CTR/CVR vs market and CVR gap, data-completeness caveats).
- **MASTER workbook** — merges the two above under one built one-page Overview.

Canonical builders to copy per client (templates, not client-specific logic) live
under the most recent audit's reporting folder as a trio:
`output/{client}/reporting/build_{client}_master_workbook.py` plus its
`build_{client}_audit_workbook.py` and `build_{client}_sqp_workbook.py`. Copy the
latest set, re-point the paths/metrics, and keep the logic. (These local `output/`
files are gitignored — this doc is the committed reference to their shape.)

### MASTER file structure

The master is assembled by copying each source sheet **cell-by-cell** (value + style
+ merges + column widths + freeze panes), then prepending a built Overview:

- `① Overview` (built in the master script):
  - Obsidian header band + coral subtitle band (market · window · ad-type mix ·
    break-even ACOS assumption).
  - One coral one-liner: the whole story in a sentence.
  - **KPI strip**: ad spend, ad sales, ad ACOS, ad ROAS, total sales (all traffic),
    TACOS, organic-implied sales, ad:organic ratio.
  - **Traffic-mix table**: per bucket (Branded / Generic / Competitor) — ad spend,
    % spend, ad ACOS, SQP SV share, SQP purchase capture. This is the core story:
    spend efficiency × demand capture side by side.
  - **Placement** table (spend, ACOS, traffic-lit).
  - **Top findings** (numbered) + **Recommendations** (short/medium term).
  - Break-even-assumption note in violet.
- `② Executive Summary …` and the rest of the audit tabs (audit workbook, in order).
- `SQP · …` tabs (SQP workbook, in order).
- `ⓩ Sources & Notes` — one master sources/notes tab appended last.
- Drop rules when merging: skip the audit's thin per-keyword "Search Query Intel"
  (superseded by the full `SQP ·` tabs) and each component's own "Sources & Notes"
  (folded into the single master one).

### Design system (all tabs)

- **Agency palette** (from `_local/branding/branding.json`, see `tools/amazon-ad-audit/BRANDING.md`; EW values shown as reference): obsidian `0F1318`, coral `FD4807`, violet `3322E0`,
  deep `0E01A2`, mist `5B6573`, cloud `F5F6F8`, hairline `E3E7ED`, ink `1E242C`.
- **Fonts**: Aptos (body), Aptos Display (headers).
- **Traffic-light fills** on decision columns only (soft pastels): good `C6EFCE`,
  ok `E2EFDA`, warn `FFEB9C`, bad `FFC7CE`. Keep coloring restrained — decision cells,
  not whole tables.
- **ACOS is always a ratio** (1.09 = 109%). The `acos_fill` helper must **never**
  divide by 100. Thresholds keyed to break-even: good `<0.30`, ok `<0.50`,
  warn `≤0.60`, bad `>0.60` (retune the band edges to the confirmed break-even).
- **Break-even ACOS is an ASSUMPTION** until margin is confirmed — show it in an
  explicit banner and say every ACOS color verdict updates on the real number.
- **Hidden helper sheets**: keep raw/working sheets in the file but
  `sheet_state="hidden"` so the client sees only the presentation tabs; `wb.active=0`.
- Turn off gridlines on presentation sheets (`sheet_view.showGridLines=False`).

### Method-note caveats to always include

- SQP is a weekly snapshot set (average the available weeks; per-query rates on tiny
  denominators are noisy — lead with impression share + purchase capture).
- DataDive MKL is capped at 500 visible rows of the full niche — keep outliers
  visible, don't imply full coverage.
- SP "Bidding Adjustment" rows carry placement-level campaign totals — **never** sum
  them with keyword/target rows (double-count trap). Audience-cohort adjustment rows
  (Shopper Cohort with no Placement) are excluded from the placement table for the
  same reason — they re-slice the same traffic by audience.
- **Sponsored Brands appears in two bulk sheets** ("Sponsored Brands Campaigns" +
  "SB Multi Ad Group Campaigns") with the SAME campaigns — dedupe by Campaign ID and
  count SB once, or ad spend/sales inflate. Always sanity-check the total against the
  Ads console; internal spend-reconciliation alone will not catch a double-count.
- Intent split uses **two methods by channel**: SP by customer search term (complete),
  SB/SB-Multi by keyword text + product-target expression (SB search-term reporting
  covers only ~half of SB spend). State the resulting coverage %; the unclassified
  remainder (SB video/reach + SD) is a labeled row, not hidden.
- **PAT rows classify by target:** own ASIN → Branded (defense), foreign ASIN →
  Competitor (conquesting) — this flips a naive "generic is fine" read when a lot of
  spend is ASIN conquesting.
- **SQP revenue gap:** Brand Analytics may have no SQP for some ASINs; the
  completeness gate reports the uncovered revenue share. Say plainly which
  high-revenue ASINs are missing and that capture figures are floors on the covered set.
- **Ad groups spanning several parent families** are a standard structural finding —
  Amazon chooses which product serves each query, so keyword→product fit is
  uncontrolled and per-product ad stats blur.
- Intent classification is rule-based (brand / own-ASIN / competitor / generic) —
  audit-grade, review before bulk campaign changes.

## Part 3 — The Branded Document (agency identity from `_local/branding/`)

The narrative ships as a **brand-styled A4 document** — `.docx` (editable) + `.pdf` (send) — rendered from
the narrative `.md` by `tools/amazon-ad-audit/render_branded.py`. Not a pixel deck; a clean, readable report
that carries the CI.

- **Typeface: Inter** (the website font). The brand-guide PDF names Geist primary / Inter fallback, but the
  site — and therefore these documents — use Inter. Type scale: cover title 800, section 700, big stat 800,
  body 400/1.55, eyebrow 600 caps.
- **Colour:** neutrals ~70% (Obsidian `#0F1318` / Ink `#11151C` / Cloud `#F5F6F8` / White); **one accent,
  ≤5%: Signal Orange `#FD4807`** (eyebrows, rules, KPI-card tops, "Lever n" labels). Numbers tabular.
- **Body is light, not dark.** The brand deck uses dark report pages, but dark full-body is hard to read —
  keep dark for the **cover only** and use light body + orange accents. State the intent-split coverage %
  at the traffic-mix table; never present the split as if it sums to 100% of spend.
- **Cover page = first-time audits only** (`branding.first_time` / `--cover` / `--no-cover`). Dark Obsidian,
  faint grid (<6%), white logo grouped with an orange rule + eyebrow, big title, "Prepared for" +
  `prepared_by` byline (default "Victor Uhl, Founder"), "What's inside" = the section names, footer
  `Confidential · <agency URL from branding.json>`. Horizontal rules snap onto the grid.
- **KPI stat-cards** (spend / ad sales / blended ACoS vs break-even / TACoS) are auto-built from
  `metrics.json` and placed under the verdict/summary section — Cloud card, orange top rule, big Inter stat.
- **Markdown conventions** the renderer reads: `## H2`, `**Lever N: title.** body` (the legacy
  `**Lever N — …**` form still parses, but write the colon form per voice rule 11) →
  orange "LEVER N" eyebrow, `> quote` → orange note callout, `![caption](file.png)` → figure + caption,
  pipe tables → Ink-header tables. `<!-- ... -->` stubs are dropped.
- **Page-break hygiene:** widow/orphan control, headings kept with their first lines, KPI-card row / tables
  / figures never split across a page — so no page ends on a lone dangling sentence.
- **Brand assets are LOCAL/gitignored** (`tools/amazon-ad-audit/brand/`). Regenerate with
  `prepare_brand_assets.py` (headless Chrome for SVG→PNG on macOS). If assets/Chrome are absent the build
  degrades to a plain `md_to_docx` `.docx` with a WARN — never a hard failure.
- **Delivery:** the A4 `.docx` is the Google-Docs-editable file (opens in Docs preserving layout). Do **not**
  convert to a native Google Doc — the full-bleed cover + KPI cards + font break. Send the `.pdf`.

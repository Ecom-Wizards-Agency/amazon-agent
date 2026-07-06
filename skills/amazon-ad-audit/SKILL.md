---
name: amazon-ad-audit
description: Use for end-to-end Amazon ad/sales audits — ads bulk + Business Report + multi-ASIN SQP + DataDive niche → branded MASTER workbook (Ad Audit + SQP Intelligence under a one-page Overview) + operator narrative. Covers branded/generic/competitor split, placement, structure diagnosis, SQP purchase-capture, premium price-outlier analysis, and the Codex↔Claude two-agent handoff.
---

# Amazon Ad / Sales Audit Workflow

Use this when the operator asks for an Amazon advertising or sales audit (often a prospect audit in the `04_Sales Audits` Drive folder). It is the repeatable standard behind our real client ad/sales audits.

## Source of truth

1. **Narrative + design standard:** `docs/amazon-ad-audit-playbook.md` — section skeleton, operator voice (second person, first-person opinion, blunt, lean), master-workbook layout, the cut-list (no 30-day plan / "what can be reached" / "bottom line" by default), break-even handling, and the ACOS-is-a-ratio rule.
2. **Toolkit:** `tools/amazon-ad-audit/` — client-agnostic, config-driven builders. See its `README.md`, `NEW-CLIENT.md`, `WORKFLOW.md`.

## Required data inputs (the config contract)

- **Ads bulk `.xlsx`** — Amazon Ads console bulk export (SP required; SB/SB-Multi/SD/RAS included if running). **Codex download.**
- **Business Report `.csv`** — Seller Central → Business Reports (Detail Page Sales & Traffic by Child ASIN). **Codex download.**
- **Multi-ASIN SQP `.csv`** — one per product group, weekly. **Codex download.** (Caveat: multi-ASIN SQP caps the query grid; SV is a floor.) SQP genuinely may not exist for some ASINs in Brand Analytics — the completeness gate flags the uncovered revenue; disclose it, don't hide it.
- **DataDive niche JSON** — `get_niche_keywords` + `get_niche_competitors`. **Claude pulls via MCP** (do not commit the API key).
- **Recommended extras (optional):** SB campaign placement report (the bulk's SB placement rows are incomplete — only Detail Page populated in practice; the dedicated report gives the true ToS/RoS/PP split) and the SP Search-Term Impression-Share report (Top-of-Search headroom). **Not needed:** SB/SD search-term reports — SB intent is split by target from the bulk itself.

## Flow

1. **Scope + scaffold config.** Client, marketplace(s), product lines + ASINs, break-even ACOS (assumption vs confirmed margin), brand + competitor tokens. Copy `config.TEMPLATE.json` → `config.<client>-<market>.json` (gitignored).
2. **Preflight.** `python3 tools/amazon-ad-audit/build_audit.py --config <cfg> --preflight` → emits a copy-ready Codex download task for missing browser inputs, or READY.
3. **Codex gathers** the browser downloads to the contract paths, notes evidence + caveats, stops. Does NOT run the builder or write the narrative.
4. **Claude pulls DataDive** via MCP, saves to the config paths. Re-run `--preflight` → READY.
5. **Build.** `--config <cfg>` → analyze → audit + SQP workbooks → MASTER → narrative scaffold under `output/<client-slug>/reporting/`.
6. **QA.** `--validate` gates must PASS (spend reconciliation; no >100% ACOS colored green; master tab count). It also prints soft **WARNINGS** and a **DATA COMPLETENESS** panel (see rules) — resolve or disclose each before delivery.
7. **Write narrative** into the pre-filled scaffold per the playbook (voice, lean, Problems + Growth Levers). Reference screenshots inline as `![caption](file.png)` (paths relative to the `.md`). The build renders the branded deliverable from this `.md`.
8. **Deliver** the MASTER `.xlsx` + the **branded audit `.docx` + `.pdf`** to the client's Google Drive audit folder. Confirm with the operator before a prospect sees it.

## Branded deliverable (agency identity from `_local/branding/` — see tools/amazon-ad-audit/BRANDING.md)

`render_branded.py` turns the narrative `.md` + `metrics.json` into an **A4, Inter**, EW-branded **`.docx`
and `.pdf`** — light readable body, one accent (Signal Orange `#FD4807`), KPI stat-cards auto-built from
metrics, Ink-header tables, footer with page number, smart page-break hygiene (no dangling single-sentence
page ends; KPI/table/figure never split). `build_audit.py` calls it automatically; it falls back to plain
`md_to_docx` if brand assets/Chrome are missing.

- **Cover page = first-time audits ONLY.** Controlled by config `branding.first_time` (or `--cover` /
  `--no-cover`). Regular update audits set `first_time:false` → no cover, same branded body.
- **Byline** from `branding.prepared_by` (default `Victor Uhl, Founder`); subtitle from `branding.cover_subtitle`.
- **Font is Inter** (the website typeface). The brand-guide PDF lists Geist primary / Inter fallback, but the
  site — and these docs — use Inter.
- **Brand assets are LOCAL/gitignored** (`tools/amazon-ad-audit/brand/`): logo/mark PNGs + Inter font.
  Regenerate with `python3 tools/amazon-ad-audit/prepare_brand_assets.py` (reads your pCloud brand sources;
  macOS has no SVG rasteriser so it uses headless Chrome). Never commit the binaries.
- **Editable-in-Google-Docs = the A4 `.docx`** (opens in Docs preserving layout). A *native* Google Doc
  conversion breaks the full-bleed cover + KPI cards + font, so don't convert; send the `.pdf`, edit the `.docx`.
- **Markdown authoring contract (so blocks render as intended, not as headlines):**
  - **Growth levers**: write each as a bold lead-in with the body on the SAME line:
    `**Lever N: Short title.** Body sentence continues here…`. The renderer splits this into a
    `LEVER N` eyebrow + short title card, then the body as a normal paragraph. Do NOT put the whole
    lever on a heading line (`### Lever N …`) or the entire paragraph renders as one giant headline
    (the historical bug: the lever regex swallowed title *and* body into the H3).
  - **Problems** render as plain bold-lead paragraphs (`**Problem N: …** body`). No card, by design.
  - **Section headers** are `## H2` (also feed the cover's "Inside" list) and `### H3`; a `> ` line is a
    pull-note; `![caption](rel.png)` is a figure. Keep levers as the bold-lead form, not `###`.
  - **No spaced em-dashes (" — ") in any written text** (narrative, captions, workbook notes). It reads
    as AI style. Short sentences with periods instead; colons for lead-ins. Exceptions: "—" as an empty
    table cell, numeric ranges. See AGENTS.md "Writing Style" and playbook voice rule 11.

## Rules

- **Break-even ACOS is an assumption** until margin is confirmed; every red/amber verdict keys off it (single config constant → rebuild). State it explicitly in the deliverable.
- **Intent split = SP by customer search term + SB/SB-Multi by target.** SP search-term reporting is complete; SB's is not (only ~half of SB spend maps to a customer search term — the rest is product-targeting, category, video), so SB/SB-Multi are classified by keyword text + product-target expression. This slightly overstates branded on broad SB keywords but lifts coverage from ~79% to ~97%. **Always state the coverage % at the traffic-mix table; never present the split as if it sums to 100% of spend** — the remainder (SB video/reach + SD) has no search term or target and shows as a "Not classified" row.
- **Product-targeting (PAT) rows classify by target:** own ASIN → Branded (defense), foreign ASIN → Competitor (conquesting). Bare-ASIN "search terms" in the SP report are PAT rows and classify the same way.
- Include real brand misspellings in `brand_tokens`; exclude dictionary words that merely resemble the brand. Populate `competitor_tokens` from both DataDive niches + brands seen in the search-term report.
- **SB is ONE channel across two sheets — dedupe it.** Amazon's bulk lists every Sponsored Brands campaign in BOTH "Sponsored Brands Campaigns" (legacy) and "SB Multi Ad Group Campaigns" (superset) — same Campaign IDs, same spend/sales. Summing both double-counts SB (it inflated a real audit's ad sales by ~$112k). The toolkit assigns each SB campaign to one sheet by Campaign ID (`_sb_owner`, superset wins) and counts/parses it once, for both channel totals and the SB target intent-split.
- **Sanity-check total ad sales against the console, not just internal reconciliation.** The spend-reconciliation gate proves buckets == search-term rows (internal consistency) — it will happily agree with a double-count. Before delivery, eyeball total ad sales/spend against the Ads console figure; a >2–3% gap means a channel is double-counted or missing.
- **Placement: never sum SP "Bidding Adjustment" audience-cohort rows** (they slice the same traffic by audience — including them double-counts spend). Only true placement rows count.
- **Structural checks that are standard findings:** duplicate keyword+match pairs (self-competition), campaigns with no negatives, oversized ad groups, branded/generic mixed in one campaign, **mixed match types in one campaign** (placement multipliers are campaign-level → placement control impossible), **brand not excluded as negative phrase from generic campaigns** (branded terms flatter generic numbers), and **ad groups advertising several parent families** (Amazon picks which product serves each query → keyword→product fit uncontrolled, per-product stats blurred).
- **Narrative opens organic-first** (playbook skeleton): organic reality → BR → SQP → DataDive → ads. Read base bid × placement multiplier on the big campaigns (the product-page-bleed mechanism), check live titles against the ≤75-char rule (2026-07-27), and treat 4.5 stars as the visual review target (4.2/4.3 render the same). See the playbook's "Standard operator plays".
- **Data-completeness gate:** `--validate` emits soft WARNINGS (low intent coverage, SQP-revenue gap, missing channels, multi-parent ad groups) and the build prints a DATA COMPLETENESS panel. These are not bugs — they are thin data. Resolve (download the missing report) or disclose (in Method Notes) every one before delivery.
- **Never hand-edit the builders per client** — everything client-specific lives in the config. If the code can't express something, extend the toolkit, not a fork.
- **Once the operator starts editing the delivered `.docx`** (adds images, rewrites levers), do NOT regenerate/overwrite it — patch it in place (python-docx, back up first). Preserve their images and wording; correct only number tokens. Images can be anchored inside a section you're removing — clear the text runs but keep the drawing runs; never delete an image-bearing paragraph.
- **Reading Amazon bulk `.xlsx` in openpyxl read-only mode:** the export declares a broken sheet dimension, so `ws.iter_rows()` returns nothing until you call `ws.reset_dimensions()` first.
- Stop before any account-changing action; this is analysis only.

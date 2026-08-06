# Client Monthly Report Template

Status: pilot template. It is not an active skill trigger.

## Purpose

This package turns the approved Swissker July report into the mandatory base
structure and registers Pawsan's root-cause pages as an explicit opt-in module.
It preserves the exact structural decisions made during review:

- Approved dark cover with no cover footer
- A4 body pages with the approved header and footer
- Headline-safe width and a two-line maximum
- Deliberate headline wrapping instead of overflow or stranded words
- Compact 16-point table rows and uniform 6.35-point table text
- Tight numeric columns and usable narrative columns
- Right-aligned numeric columns and left-aligned narrative columns
- Readable previous-period gray (`#7B8491`), never washed out
- Metric-aware green/red MoM changes
- Full-width visual first, table second
- Consistent gaps between headline, subtitle, visual, table, bullets, and callout
- No large artificial whitespace created by accidental page flow
- Mandatory full-month Slack channel and thread review for every brand
- Reply-level Slack decisions mapped into the measured section they explain
- Cross-brand context excluded by brand, product, account, and marketplace
- No headline may exceed the safe content width or two lines; intentional line
  breaks must preserve natural phrases and avoid stranded words
- Optional pages inserted before goals, with dynamic page totals
- Optional contents entries shown only when the module is enabled
- `REPORT OVERVIEW` cover contents with client-relevant wording only
- Sales included in every applicable performance table
- Current-period performance rows sorted by Sales, highest to lowest
- Multi-marketplace reports split into complete, currency-isolated parts
- Unsupported DataDive marketplaces omitted without invented Rank Radar output
- Final PDF and audit workbook delivered together in the monthly Desktop folder
- Stable brand source details remembered between runs; only missing, stale, or
  changed values are requested again

## Files

- `template_engine.py`: page registry, optional-section isolation, ordering, page
  totals, structural validation, and rendering.
- `reference_builds.py`: data-locked Swissker and Pawsan reference builds.
- `brand-config.example.json`: minimum per-brand source and filtering contract.

## Base pages

The Swissker reference defines the reusable base:

1. KPI overview
2. Break-even ACOS guardrail
3. Traffic segments
4. Top search terms
5. Ad type utilisation and bid categories
6. Match types and budget utilisation
7. Placement analysis
8. Focus-product performance
9. SQP product view
10. One organic-ranking page per focus product
11. Goals and next-month priorities

The page count changes with the number of focus products and enabled optional
modules. `goals_priorities` must remain the final page.

For multi-marketplace clients, repeat the complete base structure inside labeled
`Part 1`, `Part 2`, and later marketplace parts. Do not alternate marketplaces
within a section and do not combine currencies or economics.

## Pawsan opt-in

`pawsan_root_cause` is restricted to `pawsan-de` and off by default. When
enabled, it adds these pages before goals:

1. Root-cause overview, key numbers, and root causes
2. Keyword verdicts
3. Completed execution

It also adds the matching cover-contents item. The template raises an error if
the module is enabled for another brand.

Other brand-specific modules should follow the same pattern and remain off until
the user explicitly requests them or supplies the required source document.

## Build the references

```powershell
$python = "<workspace-dependencies-python.exe>"
$workspace = "<report-source-workspace>"
$out = Join-Path $workspace "outputs\templates"

& $python reference_builds.py `
  --workspace $workspace `
  --output-dir $out `
  --fixture all
```

The reference builder validates total pages and A4 page dimensions after each
render. Visual QA still requires rendering every page to PNG and inspecting the
contact sheets before promotion to the production skill.

## New-brand use

1. Copy `brand-config.example.json` and fill the exact account, marketplace,
   source, segment, focus-product, and Rank Radar fields.
2. Collect the four-item operator handoff: Sellerboard for both months grouped by
   parent, one full-month Rank Radar screenshot per supported focus product, the
   exact AdLabs custom dashboard, and meeting notes or a confirmed no-notes status.
   Retrieve the Slack channel from brand configuration and ask for it only when
   missing, ambiguous, or inaccessible. See `docs/monthly-report-input-handoff.md`.
3. Pass the mandatory AdLabs dashboard preflight: verify the exact dashboard ID,
   linked profile ID, currency, refresh timestamp, and both complete calendar
   month windows. If the screenshot comparison is wrong, lock the comparison to
   exact-dated MCP data and use the screenshot only for current-period validation.
4. Read the brand's Slack channel and all threads for the full reporting month;
   record reply-level decisions in a source ledger and exclude cross-brand
   discussion before writing analysis.
5. Run `amazon-audit` and create the audit workbook first.
6. Build brand page renderers using the Swissker page order and layout tokens.
7. Register any requested optional section with an explicit brand/source gate.
8. Render, validate sources and formulas, then visually inspect every page.
9. For multi-marketplace reports, validate and render each marketplace as a
   separately sourced part of the combined report.
10. Create `%USERPROFILE%\Desktop\<Month> Monthly Reports` and place the final
   report PDF and audit workbook directly in it.

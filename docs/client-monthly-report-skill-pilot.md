# Client Monthly Report Skill - Pilot Specification

Status: pilot, pending operator and internal-team approval. This document is not
an active skill trigger. Promote it to a dedicated skill only after the testing
phase is approved.

## Contents

1. Purpose and routing
2. Required outputs
3. Source contract
4. End-to-end workflow
5. Standard report structure
6. Audit modules woven into the report
7. Brand configuration and filters
8. Optional modules
9. Design and layout contract
10. Analysis and writing contract
11. Accuracy and QA gates
12. Promotion plan

## 1. Purpose and routing

This workflow creates one client-ready monthly Amazon report by running three
separate stages and combining them only after each stage passes validation:

1. Run the managed-account audit through `amazon-audit` and generate the
   audit workbook.
2. Build the normal monthly report from Sellerboard, AdLabs, Amazon reports,
   DataDive, Slack, meeting notes, and any supplied brand documents.
3. Weave the useful audit findings into the monthly report's approved design and
   narrative structure.

Do not replace the existing `amazon-reporting` or `amazon-audit` skills.
The eventual monthly-report skill should orchestrate both and own the final PDF,
workbook delivery, visual QA, and cross-source reconciliation.

## 2. Required outputs

Every completed brand run must deliver:

- One client-ready A4 monthly report PDF.
- One exact audit workbook generated for that brand and reporting window.
- Reproducible source/build files retained locally for corrections.
- A short source-and-window ledger used during QA.

Never deliver only the PDF. The audit workbook accompanies every brand report.
Create `%USERPROFILE%\Desktop\<Month> Monthly Reports` automatically and place
both final files directly in that folder. A supporting `Audit Workbooks`
subfolder is optional, but it cannot be the only location of the client audit.

## 3. Source contract

### Operator screenshot and notes handoff

Before asking the operator for anything, load the persisted brand configuration.
Reuse the known marketplace, Sellerboard account, AdLabs profile and dashboard,
focus products and parent ASINs, brand aliases and misspellings, DataDive Rank
Radar identifiers, currency, and Slack channel. Ask again only when a value is
missing, ambiguous, inaccessible, stale, or explicitly changed by the operator.

For each monthly run, request only these period-specific inputs:

1. Sellerboard screenshots for the reporting month and comparison month, with
   the correct brand/marketplace and `Group by parent`. The complete month dates,
   account totals, and focus-product parent rows must be visible.
2. One full-month DataDive Rank Radar heatmap screenshot per focus product. The
   complete date span and product identity must be visible, the text must be
   readable, and the image must not include a black border or unrelated blank
   area. Omit this request for a marketplace DataDive does not support.
3. The brand-specific AdLabs custom-dashboard screenshot with the exact reporting
   month and previous comparison month selected. The dashboard/profile identity,
   date selectors, and KPI tiles must be visible.
4. Meeting notes for calls held during the reporting month, or explicit
   confirmation that there were no meeting notes. Notes from after month-end may
   be used only as clearly labeled forward-planning context.

The Slack channel is normally not an operator handoff item. Resolve it from the
persisted brand configuration and read the full month, including thread replies.
Ask for the channel only when it is absent, ambiguous, or inaccessible.

Reject or replace an input before drafting when it shows an incomplete month,
the wrong account or marketplace, Sellerboard grouped by something other than
parent, the wrong AdLabs dashboard/comparison, a partial or unreadable Rank Radar,
or mixed-brand meeting notes that cannot be classified safely.

The reusable operator-facing version of this checklist is maintained in
`docs/monthly-report-input-handoff.md`.

### Sellerboard

Use Sellerboard for business KPIs:

- Revenue
- Net profit
- Margin
- Orders and units
- Refunds
- Ad cost when displayed as a business/P&L KPI

Use the exact account and marketplace, set `Group by parent`, and use the complete
calendar-month date range. Preserve the displayed precision and do not invent
rounding.

### AdLabs custom dashboard

Use `Insights > Custom Dashboards > <Brand>` for the advertising overview:

- Total sales, organic sales, and ad sales
- Ad Sales Ratio
- Ad spend
- Ad ACOS and ROAS
- CPC and RPC
- Clicks, impressions, CTR, and CVR
- Refund rate when available

AdLabs is the advertising source of truth. Keep Sellerboard and AdLabs values
labelled separately when their accounting basis differs.

The custom-dashboard screenshot is mandatory for every brand and marketplace,
even when exact-dated data can also be fetched through an integration. It verifies
the dashboard identity, profile, KPI configuration, and visible period selection.

### AdLabs search-term level

Use `Search Terms & Targeting > Search Terms` for:

- Traffic segments
- Top search terms
- Match types
- Ad types

For match type and ad type tables, apply only enabled campaign state and enabled
target state. Do not add traffic or intent filters.

Traffic segment filters are brand-specific. Show the exact brand and
misspelling terms used in the report rather than saying "configured terms."

### AdLabs placements

Use `Analyze > Placements` for placement performance. Apply the documented
placement filters and do not mix placement totals with search-term rows.

### Amazon reports and SQP

Use the Amazon reporting tools for Seller Central Business Reports and SQP.
Treat SQP as product/parent-ASIN data, not keyword-only data.

- One focus product: show that product.
- Up to three focus products: show each product separately.
- When a single ASIN must be selected, use the highest-selling focus parent/ASIN.
- Sort SQP rows by current-period search volume, highest to lowest.

### DataDive Rank Radar

Use the supplied or live DataDive Rank Radar screenshot for each focus product.
It must cover the complete reporting month, be cleanly cropped, remain readable,
and have no added black border. Do not recreate the heatmap.

When a previous full-month heatmap is available, compare material rank movement
against it and keep the comparison source-backed. If DataDive does not support
the marketplace, as with Australia, omit the Rank Radar section and never
fabricate a substitute heatmap.

### Slack, meeting notes, and supplied documents

Read the brand's Slack channel and every thread whose parent message falls
inside the full reporting month. The channel review is mandatory for every
brand, even when no meeting notes are supplied. Use reply-level decisions and
updates, not only thread headlines. If Slack's thread reader omits reported
replies, recover them with channel-scoped, month-bounded Slack searches.

Resolve the channel from the persisted brand record. Do not repeatedly ask the
operator for a channel that is already registered and accessible.

Build a short Slack evidence ledger with the date, thread topic, confirmed
facts, unresolved items, and the report section each item informs. Weave only
relevant context into the measured section it explains. Meeting notes and
operational documents add context; they never replace measured data or justify
a cause that the thread leaves unconfirmed.

Do not mix notes between brands that share a client, meeting, or Slack channel.
Classify each item by brand, product, account, and marketplace before use. When
the classification is uncertain, omit the item from the client report.

## 4. End-to-end workflow

### Phase A - Scope and preflight

Load the persisted brand configuration first, then confirm only missing, stale,
or changed values:

- Brand and marketplace
- Current calendar month and previous comparison month
- Focus products and parent ASINs
- Exact brand terms and misspellings
- Competitor terms if applicable
- Sellerboard account and grouping
- AdLabs profile and custom dashboard
- Exact custom-dashboard ID, linked profile ID, currency, and last-refreshed timestamp
- DataDive Rank Radar sources
- Slack channel ID/link, full-month thread window, and meeting-note sources
- Optional modules explicitly requested or supplied

Collect the current run's Sellerboard, AdLabs-dashboard, Rank Radar, and meeting-
note handoff using the checklist in the source contract. Do not make the operator
restate known brand details.

Create a source ledger before calculating or writing anything.

The brand-specific AdLabs custom dashboard is a hard preflight gate for every
report. Do not begin drafting when the dashboard identity is missing or when the
selected profile does not match the brand and marketplace. Confirm the current
and comparison periods are the complete calendar months requested. If a supplied
dashboard screenshot shows the wrong comparison selector, use exact-dated AdLabs
MCP results for the comparison and use the screenshot only to validate the
current-period tiles; record that boundary in the source workbook.

### Phase B - Audit

Run the managed-account AdLabs audit read-only. Produce the audit workbook before
building the report. Reconcile total spend and sales against the AdLabs dashboard.

Use Sellerboard margin and P&L data for confirmed break-even economics when
available. The standard break-even ACOS proxy is:

`(net profit + ad cost) / revenue`

Label the result as a proxy unless the client's contribution margin definition
has been confirmed.

### Phase C - Monthly report body

Build the normal monthly report independently from the audit narrative. Use the
approved source hierarchy, date windows, filters, sorting, and visual system.

### Phase D - Weave and consolidate

Insert only the audit modules that add a distinct decision layer. Do not paste
the audit into the report and do not duplicate an existing monthly section.

Audit bars appear first at full content width. The matching table appears below.
All audit-derived tables adopt the monthly report table style.

### Phase E - QA and delivery

Run numerical, source, formula, and visual QA. Deliver the PDF and audit workbook
only after every mandatory gate passes.

## 5. Standard report structure

Use this order unless the brand's evidence requires a small, justified change:

1. Cover and contents
2. KPI overview
3. Break-even ACOS guardrail
4. Advertising performance
5. Traffic segments
6. Top search terms
7. Ad type utilisation and performance
8. Target bid categories
9. Match type distribution
10. Budget utilisation
11. Placement analysis and action layer
12. Focus-product performance
13. SQP product view
14. Organic ranking by focus product
15. Explicitly requested optional sections
16. Goals and next-month priorities

The exact page count is content-driven. Do not force every brand into the same
number of pages. Merge adjacent sections when they fit cleanly, while preserving
clear module spacing and readable tables. Do not create pages with large unused
areas merely to maintain an inherited page count.

### Multi-marketplace reports

When one client report covers multiple marketplaces, use the combined-report
structure established for Rostschreck/Clueless and Sven's Island:

- Keep one client cover with a neutral report overview.
- Add a clear `Part 1`, `Part 2`, and so on separator for each marketplace.
- Present one marketplace's complete KPI, audit, advertising, product, organic,
  goal, and priority sections before starting the next marketplace.
- Never blend currencies, Sellerboard KPIs, AdLabs economics, goals, or actions.
- Run the Sellerboard, AdLabs-dashboard, audit, filter, and QA gates separately
  for every marketplace.
- Treat unsupported sources as marketplace-specific. For example, omit AU Rank
  Radar while retaining the supported US Rank Radar section.

## 6. Audit modules woven into the report

### Break-even ACOS guardrail

Keep the approved full-width threshold bar. Show target, actual Ad ACOS, and
break-even proxy. Put the compact guardrail table beneath it.

The performance headline must state the result, not merely say "Break-even ACOS
room."

### Ad type utilisation

Use the audit's ad-type utilisation logic and exact module naming. Show the
full-width mix bar above a compact table with spend, spend share, sales, ACOS,
and a concise read.

### Target bid categories

Show the category mix visual above the audit table. Preserve the measured audit
categories and counts:

- High ACOS
- Low ACOS
- Uncategorized
- High Spend, No Sales
- Low Visibility

The table includes targets, target share, spend, spend share, and ACOS.

### Budget utilisation

Show the budget-status visual above its table. Keep campaign counts, spend,
sales, ACOS, and action implications traceable to the audit workbook.

### Placement action layer

Do not create a redundant second placement section. Add the audit decision layer
to the standard placement section. Lead with the measured Top of Search result,
then show modifiers/issues/actions in the same placement table or an immediately
adjacent compact table.

### SQP opportunities

Use product-level SQP to show where the brand converts well but lacks impression
share. Keep the read column concise and client-readable.

### Prioritized actions

Fold relevant audit actions into the normal next-month priorities table. Do not
add a separate audit action page unless specifically requested.

## 7. Brand configuration and filters

### Default brands

Use two traffic segments:

- Branded
- Non-Branded

Branded includes the explicitly listed brand terms and verified misspellings.
Non-Branded excludes all branded and semi-branded phrases.

### Seranova exception

Seranova always uses three traffic segments:

- Branded
- Semi-Branded
- Non-Branded

Never collapse Seranova to two segments.

### Persisted brand configuration

The production skill should read a per-brand configuration rather than relying
on memory. At minimum it stores:

- Canonical brand name and aliases
- Marketplace
- AdLabs profile/dashboard
- Sellerboard account/grouping
- Brand and misspelling terms
- Semi-branded terms where used
- Focus products and parent ASINs
- SQP selection rules
- DataDive radar identifiers
- Slack channel
- Currency symbol
- Whether DataDive supports the marketplace
- Per-run input status and source timestamps

The source registry is durable brand knowledge. Monthly screenshots and meeting
notes are run-specific evidence. Keep those concepts separate so the system can
remember stable details without accidentally reusing stale monthly data.

## 8. Optional modules

Optional modules are off by default. Include one only when the user explicitly
requests it or supplies a source document that clearly requires it.

### Pawsan root-cause and corrective-action package

This module is Pawsan-specific. Never include it for another brand unless the
user explicitly asks for a root-cause package.

When included, it is a separate report section and contents entry containing:

- Overview
- Key numbers
- Root causes
- Keyword verdicts
- Executed actions
- Open owner actions, only when genuinely still open

Keep its diagnostic date window separate from the full-month KPI window and
label both. Do not invent agency actions. If the operator states there are no
remaining EW actions, record completed execution and omit an EW open-action list.

### Other optional modules

Examples include:

- Compliance or listing-suppression recap
- Inventory and stock-out diagnosis
- Buy Box or hijacker impact
- Pricing-test review
- Marketplace expansion
- Product launch or handover summary

Each optional module needs a named source, an explicit date window, a distinct
decision purpose, and a contents entry when it receives a dedicated page.

## 9. Design and layout contract

### Cover

- Use the approved dark premium branded cover.
- No orange page-edge gradient.
- Match the approved Ecom Wizards logo size.
- Use `PERFORMANCE REPORT - MONTH YEAR`.
- Use `<Brand> Monthly Report` as the large title.
- Show the exact date range beneath it.
- Use a professional overview caption.
- Do not use "Audit x Monthly Report," "client-facing report," or internal-review
  language.
- Do not place a footer on the cover.
- Use `REPORT OVERVIEW` for the contents block and list only the modules included
  in the report.
- Keep cover contents client-relevant and evergreen. Do not mention internal
  workflow, post-period meeting provenance, or implementation mechanics.

### Body

- A4 white pages with the approved Ecom Wizards header and body-page footer.
- Ink/black table headers, orange accent, thin rules, and restrained light-gray
  alternating rows.
- Use the approved bold headline font and weight on every section.
- Headlines state the measured takeaway and stay inside the content margins.
- Rephrase and deliberately wrap headlines into balanced lines. Never leave a
  single awkward word or push text beyond the page edge.
- Maintain graceful, consistent spacing between eyebrow, headline, subtitle,
  visual, table, bullets, and callout.
- Never let a bar or chart overlap a subtitle, headline, or table.
- Avoid unexplained large blank gaps. Dedicated one-section pages may retain
  bottom whitespace when enlarging content would hurt readability.

### Tables

- Align every table to the same content margins.
- Use a uniform, readable font size and compact row height.
- Keep numeric columns tight and give narrative/read columns enough width.
- Center or right-align numeric columns consistently.
- Previous-period values use a medium gray that remains readable.
- Current-period values remain visually primary.
- MoM changes use green for favorable movement and red for unfavorable movement.
  Apply metric-aware direction when possible; lower spend/ACOS/refunds can be
  favorable while lower sales/profit is unfavorable.
- Sort every applicable table by current-period sales, spend, search volume, or
  the section's primary metric, highest to lowest.
- Include a current-period Sales column in every applicable advertising,
  segmentation, match-type, ad-type, placement, and search-term performance
  table. Sort performance rows by current-period Sales, highest to lowest, unless
  the section has an explicitly required fixed order.
- Use the marketplace currency symbol (`$`, `€`, `A$`, etc.), never a
  three-letter currency code in client-facing money cells.

### Charts and bars

- Previous month first in light gray; current month second in the accent color.
- Use the full content width when the visual leads into a table.
- Keep labels legible and prevent label/table collisions.
- Every numerical section should have a useful visual when the data supports it.

### Traffic-section exception

Keep the comparison chart, but the detailed traffic table shows the current
month plus MoM instead of a duplicated previous-month row. Preserve room for
impressions, clicks, orders, CTR, and CVR.

## 10. Analysis and writing contract

- Use concise bullets beneath tables and visuals.
- Keep goal-achievement analysis to no more than two paragraphs.
- Set `Good` goals that are attainable and `Best` goals that are ambitious but
  semi-attainable within one month.
- Tailor every headline to the actual performance shown.
- Weave Slack and meeting context into the relevant measured section.
- Use "Overview," never "TLDR."
- Do not mention internal workflow labels or design provenance.
- Do not name a handover person unless the operator explicitly wants the name;
  use "next manager" by default.
- Remove data-integrity notes and internal disclaimers from the client report.

## 11. Accuracy and QA gates

### Numerical gate

- Confirm current and comparison calendar dates.
- Confirm the correct seller, marketplace, AdLabs profile, and Sellerboard view.
- Reconcile Sellerboard KPI values to the supplied/live screenshots.
- Reconcile AdLabs advertising values to the custom dashboard.
- Reconcile audit spend and sales totals to AdLabs.
- Verify every formula and scan the workbook for formula errors.
- Verify the break-even proxy from exact Sellerboard inputs.
- Verify all MoM calculations and percentage-point labels.
- Verify current-period sorting in every applicable table.
- Verify currency symbols and displayed precision.

### Filter gate

- Record the exact brand and misspelling terms.
- Confirm Non-Branded exclusions.
- Confirm Seranova's Semi-Branded segment.
- Confirm match/ad type filters use only enabled campaign and target states.
- Confirm placements come from the placement entity.

### Content gate

- Confirm the brand's full reporting-month Slack channel and thread review is
  complete, including reply-level decisions.
- Confirm the operator input checklist is complete or explicitly inapplicable:
  both Sellerboard months, the exact AdLabs custom dashboard, one Rank Radar per
  supported focus product, and meeting notes or a confirmed no-notes status.
- Confirm every Slack and meeting item belongs to the correct brand, product,
  account, and marketplace.
- Confirm optional modules have an explicit trigger and source.
- Confirm Pawsan root-cause content does not leak into another brand.
- Confirm no invented goals, actions, causes, or source claims.
- Search for banned/internal phrases: `TLDR`, `Audit x Monthly Report`,
  `client-facing`, `Heusom-style`, and unintended personal names.

### Visual gate

- Render every PDF page and inspect it at readable scale.
- Confirm all pages are A4.
- Check headlines, margins, line wrapping, spacing, table alignment, row heights,
  gray contrast, chart labels, image clarity, and overlaps.
- Confirm Rank Radar covers the full month and has no black border.
- Confirm the cover has no footer and body pages do.
- Confirm every table that can report sales includes Sales and follows the
  approved current-period sort order.
- Confirm multi-marketplace parts, currencies, and page separators are isolated.
- Confirm there are no avoidable near-empty pages and no crowded module
  transitions after compacting the report.

No client-ready delivery is allowed while a mandatory gate fails. If exact source
data cannot be verified, mark the report blocked rather than filling the gap with
an estimate.

## 12. Promotion plan

After internal approval:

1. Create a dedicated `amazon-client-monthly-report` skill.
2. Keep its `SKILL.md` lean and place this detailed contract in `references/`.
3. Promote the pilot template in
   `tools/client-monthly-report-template/` and its validated per-brand schema.
4. Extend the reusable builders for the workbook, charts, tables, PDF, and
   visual QA without creating brand-specific forks.
5. Route audit work to `amazon-audit` and report fetching to
   `amazon-reporting` instead of duplicating those implementations.
6. Add regression fixtures from approved Swissker and Pawsan runs.
7. Validate the skill folder with `quick_validate.py` and run a full brand test.
8. Activate the trigger only after operator sign-off.

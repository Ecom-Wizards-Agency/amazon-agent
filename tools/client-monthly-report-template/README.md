# Client Monthly Report Template

Status: pilot template. It is not an active skill trigger.

## Purpose

This package defines the mandatory base structure of the approved client
monthly report and lets a brand register restricted opt-in modules without
leaking them into another brand's report. It preserves the structural decisions
made during the pilot review:

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
- Marketplaces the SoldScope rank tracker does not cover omitted without
  invented rank output
- Report document and audit workbook delivered together as native Google files
- Stable brand source details remembered between runs; only missing, stale, or
  changed values are requested again

## Files

- `template_engine.py`: page registry, optional-section isolation, ordering,
  page totals, structural validation, and the operator-input contract.
- `brand-config.example.json`: minimum per-brand source and filtering contract.
- `test_template_engine.py`: contract and composition tests.

The engine composes and validates only. Rendering runs through the owning
branded renderer per the client-facing brand precedence in `AGENTS.md`, and
delivery converts the intermediary with `tools/gdrive-deliver/deliver.py` into
`<Client> - Shared/<Reports>/` as one native Google Doc plus the audit workbook
as a native Google Sheet. No PDF is rendered anywhere; whoever needs one
downloads it from the delivered Doc.

Approved per-client reference builds (the data-locked July pilot reports) are
client work product. They live in the client workspace and pCloud archive and
are intentionally not shipped in this repo, following the same rule as the
listing-capture client artifacts.

## Base pages

The approved pilot reference defines the reusable base:

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

## Brand-restricted opt-in modules

A brand-specific module (for example a root-cause and corrective-action
package) is registered as an `OptionalSection` with `allowed_brands` set to the
single brand slug it was approved for, and stays off by default. When enabled,
its pages insert before goals and its cover-contents item appears. The engine
raises an error if the module is enabled for any other brand.

All brand-specific modules follow this pattern and remain off until the user
explicitly requests them or supplies the required source document.

## New-brand use

1. Copy `brand-config.example.json` and fill the exact account, marketplace,
   source, segment, focus-product, and rank-tracker fields
   (`focus_products[].rank_tracker_group_id`, `rank_tracker_url` and
   `sources.rank_tracker_marketplace_supported`; see Rank tracker below).
2. Collect the four-item operator handoff: Sellerboard for both months grouped by
   parent, one full-month SoldScope rank tracker heatmap screenshot per supported
   focus product, the
   exact SYNQ Report Builder dashboard, and meeting notes or a confirmed no-notes status.
   Retrieve the Slack channel from brand configuration and ask for it only when
   missing, ambiguous, or inaccessible. See Operator input handoff below.
3. Pass the mandatory SYNQ dashboard preflight (`sources.synq_dashboard_preflight`):
   verify the exact Report Builder dashboard (`sources.synq_dashboard`, its name
   or id), the linked SYNQ client (`sources.synq_client_id`, confirmed by a known
   SKU or title in `get_catalog`), marketplace, currency, the last sync
   (`get_sync_status`), and both complete calendar month windows. If the
   screenshot comparison is wrong, lock the comparison to exact-dated SYNQ MCP
   data (`get_daily_metrics` for each month, `group_by: total`) and use the
   screenshot only for current-period validation.
   `MonthlySourceRegistry.dashboard_preflight_issues()` lists any check the
   config has not marked verified.
4. Read the brand's Slack channel and all threads for the full reporting month;
   record reply-level decisions in a source ledger and exclude cross-brand
   discussion before writing analysis.
5. Run `amazon-audit` and create the audit workbook first.
6. Build brand page renderers using the approved page order and layout tokens.
7. Register any requested optional section with an explicit brand/source gate.
8. Compose with `compose_report`, render through the owning branded renderer,
   validate sources and formulas, then visually inspect every page.
9. For multi-marketplace reports, validate and render each marketplace as a
   separately sourced part of the combined report.
10. Deliver the report and audit workbook together as native Google files into
    the client's `<Client> - Shared/<Reports>/` folder via
    `tools/gdrive-deliver/deliver.py`, keeping intermediaries in
    `output/{client}/reporting/`.

## Rank tracker

Organic rank comes from the SoldScope rank tracker. Each focus product names its
tracking group:

- `focus_products[].rank_tracker_group_id`: the SoldScope group id.
- `focus_products[].rank_tracker_url`:
  `https://app.soldscope.com/rank-tracker/<group id>`. Built from the group id
  when it is blank.
- `sources.rank_tracker_marketplace_supported`: optional override. Without it,
  support follows the marketplace code. The SoldScope rank tracker covers US, CA,
  MX, BR, DE, ES, FR, IT, UK, NL, SE, IN, TR, AE, SA and AU; it does not cover
  JP.

`MonthlySourceRegistry.from_brand_config` reads these keys. Older configs still
load: `rank_radar_id`, `rank_radar_url`, `sources.datadive_marketplace_supported`
and `sources.datadive_supported` are read when the new key is missing. The
DataDive marketplace flag is used only when the config has no marketplace code,
so an AU brand that DataDive did not cover now gets a rank page.

The old DataDive Rank Radars were copied to SoldScope groups on 21.10.2026, so
SoldScope history for those products starts that day. The October 2026 report
therefore uses the full-month DataDive Rank Radar screenshot while that
subscription is active, or a note that October rank data is partial (21 to 31
October). November 2026 is the first full month from SoldScope.

## Ads source: SYNQ, with the AdLabs keys as a legacy fallback

The ads data and dashboard come from SYNQ. A brand config sets:

- `sources.synq_client_id`: the SYNQ client id from `list_clients`, confirmed
  by SKU or title in `get_catalog`.
- `sources.synq_dashboard`: the SYNQ Report Builder dashboard name or id
  (`sources.synq_dashboard_id` is read when the name key is blank).
- `sources.synq_currency`, `sources.synq_last_refreshed_utc` and
  `sources.synq_dashboard_preflight` (see New-brand use step 3).
- `sources.operator_handoff.synq_dashboard`: the screenshot request settings.

`MonthlySourceRegistry` and `MarketplacePart` take `synq_client_id` and
`synq_dashboard`; `MonthlyRunEvidence` takes `synq_dashboard_current_month` and
`synq_dashboard_previous_month`. Older configs still load: when a config has no
SYNQ key, `sources.adlabs_profile`, `sources.adlabs_dashboard` and
`sources.adlabs_dashboard_preflight` are read instead, the evidence booleans
`adlabs_dashboard_current_month` and `adlabs_dashboard_previous_month` still
count, and the dashboard request names the AdLabs custom dashboard. Only
The AdLabs carve-out account (US and CA) stays on AdLabs; every other brand moves to SYNQ.

## Operator input handoff

Use this checklist when preparing a brand's monthly report inputs. The reporting
system should already remember stable brand details such as marketplace, focus
products, parent ASINs, brand terms and misspellings, rank tracker links, SYNQ
client and Report Builder dashboard, Sellerboard account, currency, and Slack
channel. Only provide those
details again when they changed or the system says they are missing.

### Send these four items

#### 1. Sellerboard by month, grouped by parent

Send screenshots for both the reporting month and the previous comparison month.

- Select the correct brand account and marketplace.
- Use the complete calendar month.
- Set `Group by parent`.
- Keep the account KPI cards and focus-product parent rows visible.
- Do not crop away dates, totals, product names, or displayed decimals.

#### 2. SoldScope rank tracker by focus product

Send one rank tracker heatmap screenshot for every focus product being reported,
from the product's group at `https://app.soldscope.com/rank-tracker/<group id>`.

- Show the complete reporting month from the first through the final day.
- Keep the product identity and daily rank columns visible.
- Make the screenshot readable and tightly cropped.
- Do not add a black border or include unrelated blank space.
- A previous full-month heatmap may be requested when it is not already in the
  prior approved report and a month-over-month ranking comparison is needed.
- No screenshot is required when the SoldScope rank tracker does not cover the
  marketplace (for example Japan).
- For October 2026, SoldScope history starts on 21.10.2026 (see Rank tracker
  below). Send the full-month DataDive Rank Radar screenshot instead, or the
  report states that October rank data covers 21 to 31 October only.

#### 3. SYNQ Report Builder dashboard

Send a screenshot of the brand's saved dashboard in SYNQ Report Builder, for the
correct client and marketplace.

- Select the complete reporting month.
- Compare it with the complete previous month.
- Keep the dashboard name, client and marketplace, date selectors, and KPI tiles
  visible.
- Do not substitute another client's dashboard or a default overview.

AdLabs carve-out only: send the AdLabs dashboard from
`Insights > Custom Dashboards` with the same month, comparison and visibility
rules.

#### 4. Meeting notes

Send notes for meetings held during the reporting month. If there were no
meetings, say `No meeting notes for this month`.

Post-period notes may be supplied for next-month planning, but they will not be
used to rewrite the completed month's measured performance.

### Slack channel

The reporting system should retrieve the saved channel for the brand and read all
reporting-month messages, threads, and replies. The operator should be asked for
the Slack channel only when it is not registered, is ambiguous, or cannot be
accessed.

### When a replacement screenshot is required

The system should ask for a corrected input only when the screenshot has the
wrong account, marketplace, date range, comparison period, Sellerboard grouping,
focus product, or is too cropped or blurred to verify precisely.

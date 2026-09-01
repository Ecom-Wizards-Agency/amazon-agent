# <Client> Amazon Forecasting Context

TEMPLATE. Copy into the client's context pack and fill in. Keep the filled copy out of
this repository: it holds revenue, document links and account identifiers, and this
repository is public.

## Quick Reference

- Area: <client> Amazon forecasting and <region or expansion> scope.
- Intended users: agents preparing ad hoc forecasts, expansion sizing, monthly updates or
  executive readouts for this client.
- Coverage level: <Directional | Reliable | Audited>.
- Source inventory: `source-inventory.md`
- Evidence register: `evidence.md`
- Last synthesized: <YYYY-MM-DD>
- Freshness expectations: <when each source is refreshed, and what triggers a refresh>.
- Date rules: use explicit calendar dates, state the timezone used for conversation timing,
  and let the reporting export define the period. Say plainly when a month is partial.

## Entity Clarification

Ambiguity here is what produces a confident wrong answer, because two people filter the
same export differently and both believe they measured the brand.

| Entity | Means | Does Not Mean | Primary IDs | Grain Notes | Sources |
| --- | --- | --- | --- | --- | --- |
| <brand> | <the brand's own products on Amazon, and where> | <category demand not tied to the brand> | <how rows are identified> | <family x marketplace x month> | <sources> |
| Core marketplaces | <codes> | <passive markets> | Marketplace code | Forecast monthly by marketplace | <sources> |
| Passive marketplaces | <codes> | <growth engines> | Marketplace or country | Low-priority scenario lines only | <sources> |
| Product families | <families> | <accessories, unrelated rows> | <how to map a row to a family> | Family, month, marketplace | <sources> |

## Source Precedence

Numbered, because the point is the order. Actuals outrank estimates in any live market.

1. <Actuals source> is canonical for revenue, units, ads, profit, sessions, conversion, ASP
   and current baselines.
2. <Market-intelligence source> is canonical for demand, competitor scale, ranking gaps and
   opportunity sanity checks. It is never actual revenue where actuals exist.
3. <Strategy doc> is canonical for leadership framing, targets and country priority, unless
   contradicted by actuals.
4. <Project tracker> is canonical for live operational context, task state and blockers.
5. <Local or personal notes> are operator context. Cite them as such.
6. <Email> is optional context. Search only on explicit request.

## Key Metrics

Define each one where the client's usage differs from the obvious reading. A metric with an
obvious definition does not need a row.

| Metric | Definition | Canonical Source | Caveats |
| --- | --- | --- | --- |
| Sales | <scope: which rows count> | <source> | <what to exclude> |
| Normalized sales | Partial-month actual run-rated to a full month | <method> | Label as run-rate, never as reported actual |
| Adjusted sales | <the specific correction, and its exact scope> | <source> | Apply only within that scope |
| Units | <definition> | <source> | <row-to-family mapping caveat> |
| Ads | Amazon ad spend | <source> | Keep separate from off-Amazon spend unless populated |
| TACOS | Amazon ads divided by total sales | <source> | Launch markets can exceed steady state for a period |
| Off-Amazon lift | Inferred contribution from external channels | <source> | Do not claim attribution without external evidence |
| Net profit / margin | <definition> | <source> | Distorted by launch spend, blocks or allocation timing |
| Sessions / CVR / ASP | <definitions> | <source> | Use to separate demand, conversion and pricing changes |
| Market upside | Directional opportunity signal | <market tool> | Never replaces actuals in an active market |

## Standard Filters And Dimensions

<The filters every answer applies by default: marketplace, product family, date range, and
which rows are excluded. Write the default so a reader can reproduce a number exactly.>

## Historical Baseline Snapshot

<The last agreed baseline, by marketplace and product family, with its date and the export
it came from. This is what a forecast is measured against, so it needs a date on it.>

## Forecast Modeling Rules

<Run-rate method, scenario definitions, growth assumptions, TACOS assumptions per stage,
inventory and launch-timing constraints, and how a temporary disruption is adjusted for.
State which adjustments are allowed and their exact scope, so nobody widens one silently.>

## Market Data Pointers

<Niche or dataset identifiers, per marketplace and product family. IDs belong in the
client's pack, never in the public skill.>

## Related Sources

<Where the workbook, deck and prior forecasts live.>

## Gotchas

<The traps specific to this client: a blocked ASIN, a channel that reports zero, an export
whose column means something other than its name, a market where the brand is not the seller.>

## Open Questions

<What is unresolved, and what would settle it. An open question here is worth more than a
confident guess in an answer.>

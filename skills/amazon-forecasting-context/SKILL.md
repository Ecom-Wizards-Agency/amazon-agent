---
name: amazon-forecasting-context
description: Use when an Amazon forecasting question needs a client's source precedence, historical evidence, marketplace and product-family baselines, forecast assumptions, or caveats. Loads a per-client context pack that lives outside this repo. This is a context layer only. It does not perform Amazon audits or build launch plans.
---

# Amazon Forecasting Context

Browser: None (context and source-selection guidance only; live source retrieval follows the owning workflow).

Forecasts go wrong in a predictable way: two sources disagree about the same month and
whoever answers picks the one they opened first. This skill fixes the order in advance,
per client, so the answer does not depend on which tab was already open.

**The client's own numbers never live in this repo.** This skill is the structure. The
filled-in instance is a context pack under a gitignored path, one folder per client, and
the three reference files here are the templates it is built from. That split is not
bookkeeping: this repository is public, and a forecast pack holds revenue, document links
and account identifiers.

## Start Here

1. Resolve the client's context pack. Default location `_local/forecasting-context/<client>/`,
   overridable by an explicit path from the operator. If none exists, say so and build one
   from the templates rather than answering from whatever source is nearest.
2. Read the pack's `semantic-layer.md` before quoting any number.
3. Follow the pack's source precedence. Actuals beat market estimates in a live market,
   always: a market-intelligence tool's revenue figure is a model, and using it as actual
   revenue where real sales data exists is the most common way these answers go wrong.
4. Check freshness before answering anything time-sensitive, and state the date the number
   was true.
5. When sources disagree, or coverage is weak, or a figure is inferred rather than measured,
   say which and why. A labelled gap is usable; a confident wrong number is not.

## Building a pack for a new client

Copy the three `references/` templates into the client's pack folder and fill them in.

- `references/semantic-layer.md`: what each entity means, source precedence, metric
  definitions, standard filters, the historical baseline, modeling rules, gotchas, open
  questions.
- `references/source-inventory.md`: every source checked, its locator, permission status,
  what it supports, what it cannot answer, and the update boundary. Record rejected
  candidates too, so the next person does not re-litigate them.
- `references/evidence.md`: one row per material claim, with source, date and confidence.
  A forecast assumption with no row here is an opinion.

Keep locators in the pack, never in this skill. Record a run-rate as a run-rate and never
as a reported actual.

## Boundaries

- Use `amazon-audit` for historical Amazon ad or sales audits.
- Use `amazon-launch-strategy` for a forward-looking 13-week launch plan.
- Treat this skill as source-selection guidance, not as a substitute for a live read.
- Preserve marketplace, product family, date range, run-rate method, TACOS assumptions and
  any temporary-disruption adjustment when carrying a number between answers.
- Label stale, inferred, partial or conflicted evidence.
- Refresh actuals first, then market benchmarks, then strategy assumptions.
- Search a client's email only when the operator explicitly asks, or when a material
  forecast caveat cannot be resolved from any other source in the pack.

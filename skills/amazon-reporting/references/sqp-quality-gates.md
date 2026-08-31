# SQP Quality Gates

Read this for multi-week Search Query Performance analysis, parent-level rollups, or a reusable SQP workbook. Exact-query competitor benchmarking has its own reference.

## Published-Week Gate

SQP is weekly and can lag. Build the requested Sunday through Saturday periods, then inspect coverage before calculating a change:

1. Aggregate the full requested scope by week.
2. Mark a week as potentially unpublished only when every relevant volume measure is zero across the entire scope and surrounding settled weeks contain data.
3. Distinguish an unpublished week from a genuinely empty product/query scope. If the evidence cannot distinguish them, label the week unavailable rather than deleting it silently.
4. Compare equal counts of published weeks. If equal windows are impossible, show coverage and suppress percentage-change arrows that imply a like-for-like comparison.
5. State the actual weeks included in every table and chart.

Never chart a trailing unpublished week as a collapse to zero.

## Parent And Query Grain

- Resolve parent-child relationships before selecting the leading products. A child without a known parent becomes its own cluster.
- Select parent clusters using additive commercial measures, normally the brand's own purchases first and sales or clicks second. State the ranking rule.
- When several children expose the same query, deduplicate the market query totals before calculating parent-level query shares. Summing the market denominator once per child inflates demand and distorts capture.
- Sum the brand numerator across children only when those child measures are additive at that grain. If the source definition is ambiguous, retain child-level rows and disclose the limitation.
- Keep an auditable source tab with parent, child, query, and week keys. A polished rollup without the join keys is not reviewable.

## Query Prioritization

Use the brand's own purchases as the primary commercial signal. Break ties or broaden the view with search volume, clicks, and purchase opportunity. Do not rank only by search volume, which overweights broad head terms, or only by percentage change, which overweights tiny denominators.

Keep the selection method visible and count the excluded tail. If the operator names specific parents or queries, preserve them even when they fall outside the automatic top set.

## AdLabs Reference Handling

Current AdLabs reference queries require `SELECT * FROM reference_data`. Preserve all existing columns and append computed columns when needed. Do not copy the external narrow-select pattern into this workflow.

Reuse one fetched reference through group, query, and read operations where possible. Do not re-fetch the same SQP rows per parent. Read compact slices only after filtering and aggregation.

## Reconciliation

- Reconcile parent totals to included child rows.
- Reconcile weekly totals to the final analysis window.
- Count source rows, unique parent-child-query-week keys, deduplicated query-week keys, and output rows.
- Name missing or duplicated keys instead of accepting a percentage-only reconciliation.
- Preserve the Amazon SQP origination caveat. SQP is organic plus paid search activity that originated on the search results page; it is not a full sales ledger.

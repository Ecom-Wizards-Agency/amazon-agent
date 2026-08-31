# AMC SQL Contract

Read this before drafting custom AMC SQL. Re-read the live AdLabs AMC guide when executing because the connected contract may change.

## Measurement Queries

- Confirm every table and column with AMC `get_data_sources` for the selected profile.
- Avoid `SELECT *`, `RIGHT JOIN`, and correlated subqueries.
- Every non-aggregated output field must appear in the matching `GROUP BY`.
- Never expose `user_id` in measurement output. Aggregate distinct users inside a CTE and return only threshold-safe measures.
- Protect division with `NULLIF` or a `CASE` expression that handles a zero denominator.
- A separate totals CTE is the portable default for percentage-of-total metrics. A window total is
  acceptable for a one-time query after runtime validation, but keep it as a portability warning.

### One-Time Executions

An observed AdLabs one-time execution succeeded with its date range supplied by the execution
arguments, no built-in time-window tokens, and an outer `ORDER BY`. The local validator therefore
treats those two conditions as portability warnings in `one-time` context, not failures.

- Always supply and report the exact execution date range.
- Use both built-in time-window tokens or neither. A partial pair is an error.
- Outer `LIMIT` remains unsupported because the observed run did not validate it.
- Runtime acceptance applies only to one-time execution. It does not establish schedule compatibility.

### Scheduled Queries

- Require both `BUILT_IN_PARAMETER('TIME_WINDOW_START')` and
  `BUILT_IN_PARAMETER('TIME_WINDOW_END')`. Do not bake dates into reusable SQL.
- Do not put `ORDER BY` or `LIMIT` on the outermost query. Sort fetched results downstream.
- Keep the stricter contract until a scheduled execution provides contrary runtime evidence.

## Dates And Units

Use the date column that matches the business question:

- traffic timing: the traffic event date;
- conversion timing: the conversion event date;
- conversion attributed back to exposure: the traffic-time attributed source when available.

Do not join traffic-time and conversion-time sources casually. State which clock the result uses.

Sponsored Ads spend is commonly stored in microcents and divided by `100000000.0` for currency units. DSP spend is commonly stored in millicents and divided by `100000.0`. Confirm the selected profile's schema and field documentation before applying either conversion.

## Privacy And Grain

AMC applies column-specific aggregation thresholds. A syntactically valid query can still suppress rows. Choose a grain broad enough to clear privacy thresholds, especially when combining campaign, ASIN, audience, and daily dimensions.

AMC can suppress individual output dimensions after the source rows pass the SQL filters. Reconcile
rows with blank or null dimensions separately and describe them as dimension-suppressed unless the
output proves a more specific cause.

Check the unit of every metric before joining:

- impressions and clicks are events;
- `COUNT(DISTINCT user_id)` is people;
- purchases can be events or summed purchase measures;
- new-to-brand flags and measures vary by table;
- attributed sales may include different ad products and attribution clocks.

Never add measures with different units or different attribution clocks without labeling the result.

## Audiences

Audience SQL is not measurement SQL:

- the final output must be `user_id`;
- do not use AMC built-in time-window parameters;
- the date window comes from the audience creation arguments;
- custom audiences must meet Amazon's minimum unique-user threshold;
- omitting an optional template scope can widen the audience to the whole account.

Prefer an AdLabs library template when one covers the requested audience. Resolve it with `preview_audience_sql`, inspect the final scope, and obtain explicit approval before creation.

## Review Checklist

- Selected team, profile, and AMC connection verified.
- Required data sources exist on that profile.
- Query mode and date clock are explicit.
- Currency conversion matches the source table.
- Join keys and grains cannot multiply rows.
- Privacy threshold is plausible at the requested grain.
- Calculated metrics use `NULLIF` or a guarded `CASE` expression and compatible units.
- Validation context matches one-time execution, scheduled query, or audience SQL.
- Local validator passes.
- Execution, schedule, or audience creation has separate approval.

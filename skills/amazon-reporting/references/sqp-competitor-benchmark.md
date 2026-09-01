# SQP Competitor Benchmark

Mode browser: CDP (scripted capture via `tools/sc-sqp-competitor/`; manual UI walk only as fallback).

Capture Amazon's per-query top-ASIN comparison from Brand Analytics > Search Query Performance. This is the only source for **competitor-level** query share: the AdLabs MCP exposes our own share and nothing else, and no API returns the competitor table. Read-only throughout.

## Required Inputs

Obtain or infer only when unambiguous. Never hard-code an account, ASIN, keyword, or week from a previous run.

- Seller account or client
- Marketplace/country
- Target ASIN
- Exact keyword or keyword list
- Reporting range and period, normally a specific week
- Requested output format or destination, if any

## Capture Path: use the scripted runner first

`tools/sc-sqp-competitor/` (built 2026-07-25 on a live client run) drives the shared CDP debug Chrome and **skips all UI clicking** by navigating straight to the query-detail URL, roughly 10-15s per keyword-week:

```
https://sellercentral.amazon.de/brand-analytics/dashboard/query-detail
  ?view-id=query-detail-asin-view
  &asin={ASIN}
  &search-term-freeform={URL-ENCODED QUERY}
  &reporting-range=weekly
  &weekly-week={SUNDAY-SATURDAY WEEK END, e.g. 2026-07-18}
  &country-id=de
```

Append `&mons_sel_dir_mcid=<merchant id>` to preselect the account and skip the picker (IDs in `_local/sellercentral-links.md`). Modules: `cdp.py` (minimal CDP client, port 9222, `suppress_origin=True` is REQUIRED or Chrome 403s), `sc_navigator.py` (new-UI navigation), `sqp_extract.py` (geometry-based extractor; `capture_keyword()` returns row arrays). Full notes: `tools/sc-sqp-competitor/README.md`.

**Hard-won gotchas, do not rediscover these:**

- The account-picker marketplace rows and the confirm button live in **shadow DOM** and need **trusted** clicks (`Input.dispatchMouseEvent`). Synthetic JS clicks are silently ignored.
- Duplicate hidden widgets exist per tab (brand view vs ASIN view). Always filter by on-screen geometry, never by first DOM match.
- The tables are **virtualized shadow DOM**: `innerText` and `tr` selectors miss them entirely. That is why extraction is geometry-based.
- Never hard-code the screenshot-to-CSS scale. Read `window.innerWidth` (it was 1680, not 1512, on the reference machine).
- Query links open **new tabs**. Target them via `/json/list`.
- For isolated logins, create an incognito context with `Target.createBrowserContext` so the main window's client session survives, and dispose it afterwards.

## Fallback: manual UI walk

Only when the runner cannot reach a query. Prefer stable labels and semantic controls over fixed coordinates, and navigate through the query row where possible. Validate every URL-derived result against the page content.

1. Confirm Seller Central is logged in. Stop and ask the operator to log in if Amazon shows a login, password, OTP, authenticator, or session-recovery screen.
2. Verify the visible seller account, marketplace, Brand Analytics page, and reporting period **before reading data**. If a different or ambiguous account is active, stop and ask.
3. Open **Brand Analytics** > **Search Analytics** > **Search query performance**.
4. Select **ASIN view**, then the exact target ASIN. Verify both ASIN and product title.
5. Select and apply the requested reporting range and exact period.
6. For each exact keyword:
   - Open the exact matching query. Do not substitute a close spelling, singular/plural form, or translation. Two similar spellings are two independent queries.
   - If the query is absent for that ASIN and period, record it as **not present**. Do not invent or merge results. (An empty table is the "not present" signal.)
   - Re-verify keyword, ASIN, marketplace, range, and period on the detail page.
   - Capture query volume, total impressions, total clicks, click rate.
   - Capture the target ASIN's impressions, impression share, clicks, click share.
   - Capture the up-to-10 ASINs Amazon displays: product title, ASIN, brand, median price, impressions, impression share, clicks, click share.

Keep the workflow read-only. Do not edit listings, advertising, account settings, or any other Amazon data.

## What a capture must return

Whether scripted or manual, every keyword must come back with: query volume, total impressions, total clicks, click rate, target-ASIN impressions, target-ASIN impression share, target-ASIN clicks, target-ASIN click share, Amazon's displayed top-10 ASIN table, and any missing-data or UI caveats.

## Interpretation

- Treat the displayed table order as Amazon's top-ASIN comparison for that query and period. Amazon states top performance is based on query ASIN score, combining search-funnel impressions, clicks, basket adds, and purchases. Do not re-label it as a ranking by impressions or clicks.
- Keep the target ASIN in the benchmark table, but exclude it from any list labeled "competitors."
- Distinguish impressions from impression share, and clicks from click share.
- Compare click share against impression share. Lower click share than impression share can indicate weak click capture, but label it a diagnostic signal, not a proven cause.
- Use price differences as context only. Do not claim price caused performance without further evidence.
- Preserve Amazon's locale-specific units and decimal separators, or normalize consistently while stating the locale.
- **SQP shares are single-digit for virtually everyone.** Judge funnel shape (purchase/click share vs impression share), not absolute share.

## Output

Lead with the verified scope: account, marketplace, target ASIN, reporting period, exact keyword. Then:

1. Query-level metrics
2. Target-ASIN benchmark
3. Competitor table, sorted in Amazon's displayed order
4. Brief observations grounded in the captured metrics
5. Missing-data notes, spelling variants checked, and any UI caveats

| Amazon order | Product | ASIN | Brand | Median price | Impressions | Impression share | Clicks | Click share |
|---:|---|---|---|---:|---:|---:|---:|---:|

## Standing Cautions

- The account-identity rule applies to any Seller Central browsing: verify the **active** Seller Central account is the client's before opening SQP, because viewing leaks footprint into whichever account is active.
- Never expose credentials or sensitive information observed in the browser. Never inspect cookies, storage, or tokens.

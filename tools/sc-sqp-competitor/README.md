# SC SQP competitor capture (CDP, new Seller Central UI)

Captures the per-query top-10 ASIN comparison table (title, ASIN, brand, median
price, impressions + share, clicks + share) from Brand Analytics > Search Query
Performance query-detail pages. Built 2026-07-25 on a live client run; pairs with
`skills/amazon-reporting/references/sqp-competitor-benchmark.md`.

## Fast path (skips ALL UI clicking)
Direct URL template per keyword - navigate, wait, extract:

  https://sellercentral.amazon.de/brand-analytics/dashboard/query-detail
    ?view-id=query-detail-asin-view
    &asin={ASIN}
    &search-term-freeform={URL-ENCODED QUERY}
    &reporting-range=weekly
    &weekly-week={SUNDAY-SATURDAY WEEK END, e.g. 2026-07-18}
    &country-id=de

Account preselect (skips picker): append &mons_sel_dir_mcid=<merchant id>
(IDs in _local/sellercentral-links.md). ~10-15s per keyword-week.

## Modules
- cdp.py: minimal CDP client (port 9223; suppress_origin=True is REQUIRED,
  Chrome 403s the default Origin header).
- sc_navigator.py: new-UI navigation. Account label = top-left header leaf.
  Account picker marketplace rows + "Konto auswählen" confirm live in SHADOW
  DOM and need TRUSTED clicks (Input.dispatchMouseEvent); synthetic JS clicks
  are ignored. Duplicate hidden widgets exist per tab (Markenansicht/ASIN):
  always filter by on-screen geometry, never by first DOM match.
- sqp_extract.py: geometry-based extractor (tables are virtualized shadow-DOM;
  innerText/tr selectors miss them). capture_keyword() returns row arrays.

## Gotchas
- window.innerWidth was 1680 (not 1512): never hard-code screenshot->CSS
  scale; read innerWidth.
- Query links open NEW TABS (target them via /json/list).
- A query absent for the ASIN/week shows an empty table = "not present",
  record it as such (skill rule).
- Isolated logins: create an incognito browser context via
  Target.createBrowserContext so the main window's client session survives;
  dispose it afterwards.

Screenshot requests require `evidence_spec` with the exact released managed `task`
(taskId, workflow, targetId, slot) and expected Seller Central identity. The Python
bridge invokes the canonical task evidence helper, which reacquires that target
and verifies identity before and after capture. An unowned URL-matched tab cannot
produce evidence. Launch Python through `browserctl run --session grimoire -- …`
so nested capture workers inherit the same session lock.

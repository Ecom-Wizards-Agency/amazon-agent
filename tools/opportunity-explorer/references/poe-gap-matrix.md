# POE Captured-vs-Visible Gap Matrix

Verified 2026-07-05 on the `hydrocortisone cream` niche (a US seller account,
German UI), live side-by-side: UI screenshots in
`evidence/<client>/opportunity-data/2026-07-05_poe_*.png`, native CSV
exports vs `fetch-poe.js` output diffed cell-by-cell. Transports: A = evaluate
of fetch-poe.js source (Codex style), B = `run-poe.mjs` over CDP. A and B
outputs were byte-identical.

Legend: OLD = pre-rebuild capture (extract-opportunity-explorer.js DOM scrape +
manual CSV export). NEW = fetch-poe.js (`getNiche`/`getNiches` GraphQL).

| UI element (tab) | Visible in UI | OLD capture | NEW capture | Verified |
|---|---|---|---|---|
| Overview metric cards (SV 360d, growth 180d, top-clicked count, avg price, units range, return rate, last updated) | yes | text snippet, regex-parsed | `nicheSummary` structured + `overview.json` textLines (builder-regex compatible) | 2026-07-05 A+B; `_overview_metrics` smoke passes all 6 |
| Overview: fee breakdown, sales potential score, post-launch ad/glance/conversion metrics | partially (deep UI) | never | `nicheSummary` (bonus: more than UI shows) | 2026-07-05 |
| Products tab: all rows/columns | yes (14 rows) | native CSV (manual click) | `asinMetrics` → `NicheDetailsProductsTab.csv` EN canonical | 2026-07-05; 161/168 cells exact vs native export |
| Products "Average Customer Rating" | yes (2 decimals) | native CSV | API returns 1-decimal (`4.6` vs UI `4.59`) | KNOWN DEVIATION, cosmetic (±0.01, one column) |
| Search Terms tab: all rows/columns | yes (20 rows) | native CSV (manual click) | `searchTermMetrics` → `NicheDetailsSearchTermsTab.csv` | 2026-07-05; 240/240 cells exact vs native export |
| Search Terms extra fields (searchTermId, T90 volume, YoY growth, clickShareT360, product images) | no (API-only) | never | in `niche-full.json` (bonus) | 2026-07-05 |
| CRI positive topics + % mentions + snippets | yes ("Positive Themen") | text scrape, sentiment NOT distinguished | `nichePdr.positiveCustomerReviewInsights` (10 topics, verbatims inline) | 2026-07-05 A+B |
| CRI negative topics + % mentions + snippets | yes ("Negative Themen") | NOT captured separately | `nichePdr.negativeCustomerReviewInsights` (10 topics) | 2026-07-05 A+B |
| CRI star-rating impact table | yes | never | `nichePdr.productStarRatingImpact` (20 topics) | 2026-07-05 |
| CRI topic→subtopic drill-down with pos/neg snippets | yes (expanders) | never | `nichePdr.pdrTopics[].subTopics` | 2026-07-05 |
| CRI topic trends over time | yes (charts) | never | `pdrTopics[].{positive,negative}ReviewInsights.trends` | 2026-07-05 |
| Returns tab: topic table + % mentions | yes | loose text/JSON | `pdrTopics[].returnsInsights` → `returns.{json,csv}` (10 topics) | 2026-07-05; UI table values match (34.63% top topic) |
| Returns trend chart per topic | yes | never | `returnsInsights.trends[]` (monthly) | 2026-07-05 |
| Returns not-exposed niches | n/a | manual "not exposed" note | explicit `notExposed: true` + CSV marker row | self-test |
| Insights & Trends time series (SV, price, counts, conversion…) | yes (charts) | text snippets only | `trendsMetrics[]` (104 weekly points × ~24 metrics); captured as data even though tab is deprioritized | 2026-07-05 |
| Insights & Trends launch-potential cards | yes | text snippets | `launchPotential` (~30 metrics with QoQ/YoY) | 2026-07-05 |
| Keyword search box ("search it up") | yes (explore page) | never automated | `fetchPoeSearch` → `getNiches` (30 niches/query) | 2026-07-05 A+B ("manuka honey") |
| Related/search-results niche grid (keywords, SV, growth, units, price range, return rate) | yes | Chrome table scrape (`tables[0]`, flaky) | `getNiches` → `related-niches.json` v1 with 13-cell rows (builder shape (b)) | 2026-07-05; cells layout matches legacy sample |
| Niche typeahead suggestions | yes | never | `searchNicheSearchTerms` (documented, not needed) | endpoint doc |
| Merchant's own niches | yes (home) | never | `fetchPoeMerchantNiches` | 2026-07-05 |
| Trending niches modules (home) | yes | never | endpoints documented (`getTrendingNiches*`), not fetched (product-research surface, out of downloader scope) | doc only |
| Category browse tree drill-down | yes (home) | never | `getBrowseTreeChildren` documented, not fetched (out of scope) | doc only |
| Native CSV export buttons | yes | manual click + `~/Downloads` shuffle | obsolete: exports are client-side blobs of the same getNiche data; formatter reconstructs EN-canonical CSVs (locale-independent). Manual export retained as documented fallback only. | 2026-07-05 parity diffs |

## Builder (keyword-workbook) compatibility: read-only smoke, 2026-07-05

- `load_poe_terms(NicheDetailsSearchTermsTab.csv)` → 20 terms ✓
- `_poe_search_term_rows(...)` → 12 rows, term/SV/conversion positions ✓
- `_overview_metrics({overview: overview.json})` → all 6 metrics ✓
- `related-niches.json` emits shape (b) `relatedNiches[].cells` verbatim rows ✓
- No builder code changes made or required.

## EU verification (2026-07-05, a DE seller account, `collagen pulver` niche)

- `--origin https://sellercentral.amazon.de --marketplace de`: search returned
  52 niches (names match the legacy related-niches capture), full niche
  fetch returned EUR data, 18 products / 20 search terms / 104 trend points /
  CRI 10+10 / 3 returns topics. Products CSV header byte-identical to the
  legacy manual DE export.
- Search coverage: `getNiches` is UNCAPPED; it returns the complete grid
  ("honey" → 452, "vitamin" → 495 niches on US). No pagination needed.
- Note: CRI/PDR topic NAMES are localized per marketplace language (DE niche →
  "Geschmack insgesamt"); field names stay locale-independent.
- EU login is per-domain: the debug-Chrome profile needs a one-time sign-in on
  `sellercentral.amazon.de` in addition to `.com`.

## Outstanding

- CRI/Returns/Insights data for very small niches may be sparse. The
  formatter's not-exposed handling covers Returns; CRI empty lists pass
  through as empty arrays.

# POE Internal API Endpoints (discovered contract)

Discovered 2026-07-05 by walking one live niche in the connected debug Chrome
(US marketplace, German UI) while logging the page's own network traffic over
CDP. This is the contract `fetch-poe.js` codes against. Raw per-tab captures
(client data, gitignored) live under
`downloads/<client>/opportunity-data/poe-endpoint-capture-<date>/`; evidence
screenshots under `evidence/<client>/opportunity-data/`.

## Transport

Everything is ONE GraphQL endpoint, same-origin from the logged-in Seller
Central page:

```
POST {origin}/ox-api/graphql
Content-Type: application/json
anti-csrftoken-a2z: <content of the page's own meta[name="anti-csrftoken-a2z"] tag>
Body: {"operationName": "...", "variables": {...}, "query": "query ... { ... }"}
```

- The CSRF value comes from the SAME meta-tag mechanism the report fetcher
  uses (`tools/report-fetcher/`); the AGENTS.md safety carve-out applies
  identically. The meta tag is present on all `/opportunity-explorer/*` pages
  (verified; the page sends the header on every ox-api call).
- No cookies, storage, or tokens are ever read; the browser attaches the
  session automatically (same-origin).
- Responses are plain GraphQL JSON: `{"data": {...}}`.
- UI locale (German/English) does NOT affect the API: field names are
  locale-independent. Only the client-side CSV export uses localized headers.

## Identifiers

- `obfuscatedMarketplaceId`: e.g. `ATVPDKIKX0DER` (US). Returned per entity in
  every response; also available from `GetUserContext.marketplaceSelections`.
  fetch-poe accepts the country code and maps/derives this id at run time.
- `partnerAccountId`: from the `GetUserContext` operation (never hard-code).
- `nicheId`: 32-hex hash or UUID, from search results / niche URLs
  (`/opportunity-explorer/explore/niche/<nicheId>`).

## The three operations the downloader needs

### 1. `getNiche`: ONE call returns every niche-detail tab

`variables: {"nicheInput": {"nicheId": "<nicheId>", "obfuscatedMarketplaceId": "<mp>"}}`

~200 KB response, `data.niche`, no pagination (fixed-size lists). Sections and
their UI mapping:

| Response section | UI tab / element | Shape |
|---|---|---|
| `nicheSummary` | Overview metric cards (+ fee metrics the UI barely shows) | SV T90/T360 + growth T90/T180/T360, units-sold min/max T90/T360, min/max price, avgPrice(T360), productCount, returnRateT360, salesPotentialScore, nicheType, post-launch ad/glance/shipped/conversion, full fee breakdown T365 (referral, FBA, storage, …) |
| `launchPotential` | Insights & Trends "launch potential" cards | ~30 metrics, each `{currentValue, qoq, yoy}` (product/brand/seller counts + ages, click-share concentration top5/top20, BSR, price, reviews, OOS rate, launches, detail-page quality) |
| `asinMetrics[]` | Products tab (all rows) | asin, asinTitle, asinImageUrl, avgPrice(T360), brand, category, launchDate, clickCount(T360), clickShareT90/T360, customerRating, bestSellersRanking, avgSellerVendorCount(T360), totalReviews, currency |
| `searchTermMetrics[]` | Search Terms tab (all rows) | searchTermId, searchTerm, searchConversionRate(T360), searchVolumeT90/T360, searchVolumeQoq/Yoy, searchVolumeGrowthT180/T360Yoy, clickShare(T360), topClickedProducts[3]{asin, asinTitle, asinImageUrl} |
| `trendsMetrics[]` | Insights & Trends time series (~104 weekly points) | datasetDate + ~24 weekly metrics (SV T7, price, conversion, counts, click-share concentration, OOS, launches, …) |
| `nichePdr.positiveCustomerReviewInsights[]` | CRI tab, "Positive Themen" | topic, percentOfMentions, verbatims[] (snippets INLINE, no lazy loading) |
| `nichePdr.negativeCustomerReviewInsights[]` | CRI tab, "Negative Themen" | same shape |
| `nichePdr.productStarRatingImpact[]` | CRI "Auswirkungen auf Sternebewertung" | topic, starRatingImpactAllProducts, starRatingImpactTop25PercentProducts |
| `nichePdr.pdrTopics[]` | CRI topic drill-down + RETURNS tab + purchase-driver trends | name, positiveReviewInsights/negativeReviewInsights {percentOfMentions, verbatims, trends[]}, starRatingImpact, **returnsInsights {percentOfMentions, trends[]}**, subTopics[] (Topic→Subtopic hierarchy with pos/neg verbatims) |
| `lastUpdatedTimeISO8601` | "Datum der letzten Aktualisierung" | ISO date |

The Returns tab ("Rücksendungen") renders entirely from
`pdrTopics[].returnsInsights`. There is NO separate returns endpoint. A niche
with no returns data simply has empty/null `returnsInsights` → map to the
builder's `not_exposed` semantics.

### 2. `getNiches`: keyword search / niche grid ("search it up")

`variables: {"filter": {"obfuscatedMarketplaceId": "<mp>", "rangeFilters": [], "multiSelectFilters": [], "searchTermsFilter": {"searchInput": "<keyword>"}}, "useNewQuery": true, "searchImprovementsEnabled": true}`

Returns `data.niches[]` (30 rows observed, no pagination params in the UI
query): nicheId, nicheTitle, referenceAsinImageUrl, currency,
`nicheSummary {SV/growth/units/price/productCount/returnRateT360/avgPrice/demand/category/nicheType/salesPotentialScore}`,
`topSearchTermMetrics[] {searchTerm}` (the "keywords" column of the grid).

This IS the data behind the legacy "related niches" grid capture that the
keyword-workbook consumed: one row per niche, keywords + SV + growth + units
range + return rate + price range.

UI route after search: `/opportunity-explorer/explore/search?search=<kw>&search_type=KEYWORD`.

### 3. `searchNicheSearchTerms`: typeahead (optional)

`variables: {"input": {"obfuscatedMarketplaceId": "<mp>", "partialSearchTerm": "<kw>", "pageSize": 10}}`
→ `data.searchNiches.hits`. Only needed to mimic suggestions; `getNiches` is
the real search.

## Bootstrap / context operations (page loads them; fetcher may reuse)

| Operation | Purpose |
|---|---|
| `GetUserContext` | partnerAccountId, marketplaceSelections (source for ids) |
| `getMerchantInfoByPartnerId` | the merchant's OWN niches (nicheId + title) |
| `getUserSavedItems` | saved niches |
| `getBrowseTreeChildren` | category browse tree |
| `getTrendingNiches`, `getTrendingNichesByPdrMetrics`, `getTopPerformanceNichesT180` | home-page trending modules |

Full query texts for every operation are in the raw NDJSON captures
(`postData` field). Copy them verbatim into fetch functions; the getNiche
query is ~8.5 KB and is embedded in `fetch-poe.js`.

## CSV export finding (important)

The native "Herunterladen"/"Download" buttons on Products and Search Terms do
NOT hit a server endpoint. The page builds the CSV **client-side** (blob:
URL) from the `getNiche` data it already holds, with LOCALIZED headers and
filename (`Tab Nischendetails mit Suchbegriffen_5.7.2026.csv` on a German UI).
Consequences:

- There is no CSV endpoint to passthrough; `format-poe.mjs` reconstructs the
  CSVs from `getNiche` JSON instead.
- Reconstructing with the canonical ENGLISH headers
  (`NicheDetailsProductsTab.csv` / `NicheDetailsSearchTermsTab.csv` layouts)
  makes output locale-independent, more stable than the UI export, which
  changes headers with the operator's UI language.

### Verified CSV ↔ getNiche column mapping (Search Terms tab)

| CSV column (EN canonical) | getNiche field |
|---|---|
| Search term | `searchTermMetrics[].searchTerm` |
| Search Volume (Past 360 days) | `searchVolumeT360` |
| Search Volume Growth (Past 90 days) | `searchVolumeQoq` |
| Search Volume Growth (Past 180 days) | `searchVolumeGrowthT180` |
| Click Share (Past 360 days) | `clickShare` (⚠ the UI CSV uses `clickShare`, NOT `clickShareT360`, despite the 360-day label; verified against a live export; replicate bug-for-bug for parity) |
| Search Conversion Rate (Past 360 days) | `searchConversionRateT360` |
| Top Clicked Product 1–3 (Title/Asin) | `topClickedProducts[0..2]` |

Products tab maps 1:1 from `asinMetrics[]` (Product Name=asinTitle, ASIN,
Brand, Category, Launch date, Niche Click Count=clickCountT360, Click
Share=clickShareT360, Average Selling Price=avgPriceT360, Total
Ratings=totalReviews, Average Customer Rating=customerRating, Average
BSR=bestSellersRanking, Buyable Offer Average=avgSellerVendorCountT360).

## UI route map (for evidence screenshots / manual checks)

```
/opportunity-explorer/explore                     home (search box lives here; kat-predictive-input, shadow DOM)
/opportunity-explorer/explore/search?search=<kw>&search_type=KEYWORD
/opportunity-explorer/explore/niche/<nicheId>                    overview (fires getNiche)
/opportunity-explorer/explore/niche/<nicheId>/insights-trends    tab (client-side route, no new fetch)
/opportunity-explorer/explore/niche/<nicheId>/product            tab (client-side)
/opportunity-explorer/explore/niche/<nicheId>/search-queries     tab (client-side)
/opportunity-explorer/explore/niche/<nicheId>/review-insights    tab (client-side; Positive/Negative Themen toggles are client-side too)
/opportunity-explorer/explore/niche/<nicheId>/returns-insights   tab (client-side)
```

All tab switches are SPA routes over the one getNiche payload: clicking tabs
fires NO additional data requests. (The legacy DOM-scraping extractor's
tab-clicking was never necessary; one API call replaces the whole walk.)

## Open items for other marketplaces

- Verify the obfuscatedMarketplaceId per marketplace (DE, IT, ES, FR) on first
  use: read it from `GetUserContext.marketplaceSelections` rather than a
  hard-coded table.
- Re-verify response shapes once on one EU marketplace (expected identical;
  the API is locale-independent).

# Opportunity Explorer Downloader (fetch-poe)

Downloads everything the Product Opportunity Explorer UI shows for a niche —
overview, Products, Search Terms, Customer Review Insights (positive AND
negative, with snippets), Returns, Insights & Trends series, plus the keyword
search / related-niches grid — via POE's own internal GraphQL API, same-origin
from the logged-in Seller Central session. One `getNiche` call returns every
niche-detail tab; no DOM scraping, no manual CSV clicking.

Discovered API contract: `references/poe-endpoints.md`.
Captured-vs-visible verification: `references/poe-gap-matrix.md`.

## Files

- `fetch-poe.js` — browser-side fetcher (runs in the page main world; house
  pattern of `tools/report-fetcher/fetch-seller-reports.js`). Functions:
  `fetchPoeNiche({nicheId})`, `fetchPoeSearch({query})`,
  `fetchPoeMerchantNiches()`, `fetchPoeContext()`; also bound as
  `window.amazonAgentFetchPoe*`.
- `format-poe.mjs` — local, deterministic formatter (`--self-test` supported).
  Emits EN-canonical `NicheDetails{Products,SearchTerms}Tab.csv` (drop-in for
  the keyword workbook, locale-independent), sentiment-labeled CRI JSON+CSV,
  Returns JSON+CSV (explicit not-exposed handling), overview JSON (builder-regex
  compatible `text`/`textLines`), related-niches v1 JSON+CSV, full-niche JSON.
- `run-poe.mjs` — one-command CDP runner (shares `../report-fetcher/cdp.mjs`
  and `launch-chrome-debug.sh`).
- `discover-poe-endpoints.mjs` — network-capture logger used to (re)discover
  the API contract when Amazon changes POE. Attach, click through the UI,
  read the NDJSON.
- `extract-opportunity-explorer.js`, `format-opportunity-explorer-export.mjs`
  — DEPRECATED DOM-scraping fallback (kept until the fetch path has survived a
  few real client runs; do not use for new work).

## Usage

### Path B — terminal/CDP (Claude or any agent with shell access)

```bash
tools/report-fetcher/launch-chrome-debug.sh      # dedicated debug Chrome; sign into Seller Central once
node tools/opportunity-explorer/run-poe.mjs doctor

# find the niche (keyword search — also produces the related-niches files)
node tools/opportunity-explorer/run-poe.mjs search --query "manuka honey" --marketplace us --client <slug>

# full niche download (all tabs, one call)
node tools/opportunity-explorer/run-poe.mjs niche --niche-id <nicheId> --marketplace us --client <slug> [--verbose]

# coverage workflow: search several seed keywords, dedupe, download every kept niche in full
node tools/opportunity-explorer/run-poe.mjs batch --queries "kollagen pulver,collagen" \
  --marketplace de --client <slug> --origin https://sellercentral.amazon.de [--top 15 | --all]
```

Search coverage is complete by construction: `getNiches` returns the ENTIRE
matching grid per keyword (hundreds of niches, no pagination/cap) — `batch`
unions multiple queries and reports what it skipped when `--top` limits the
download. EU marketplaces: pass `--origin https://sellercentral.amazon.<tld>`
and sign into that domain once in the debug Chrome (per-domain login).
Verified on US and DE (see `references/poe-gap-matrix.md`). Note: CRI/PDR
topic names arrive localized per marketplace language.

`--marketplace` is required and verified against the session's actual
marketplace — a mismatch aborts. Output goes to
`output/<client>/opportunity-data/` (or `--out-dir`). `--verbose` keeps the raw
envelope JSON.

### Path A — Codex / internal-browser evaluate

Open any `/opportunity-explorer` page in the internal browser (logged in,
correct account + marketplace), then evaluate the source with the call
appended:

```js
await tab.playwright.evaluate(`(async function(){ ${src}\n return await fetchPoeNiche({nicheId: "<id>"}); })()`)
```

Save the returned JSON, then format locally:

```bash
node tools/opportunity-explorer/format-poe.mjs capture.json --out-dir output/<client>/opportunity-data
```

Both paths produce byte-identical files (verified 2026-07-05).

## Safety

Same-origin, read-only GraphQL reads in the operator's existing logged-in
session. The only header added is `anti-csrftoken-a2z`, read from the page's
OWN meta tag — the same sanctioned mechanism as `tools/report-fetcher/` (see
the carve-out in `AGENTS.md`). Never reads cookies, local/session storage,
passwords, or bearer/refresh tokens; never logs in. Connected/internal browser
only — never headless. ~5 s jittered pacing between heavy requests; one niche
per invocation; on `{error}` the tools stop and ask the operator (no retry
loops, no fabricated data).

Stop before changing listings, uploading images, editing A+ content, changing
catalog data, or publishing recommendations externally.

## Known deviations from the UI's own CSV export

- The UI export's "Average Customer Rating" column has 2-decimal precision
  (e.g. 4.59); the API returns 1 decimal (4.6). Cosmetic.
- The UI export uses localized headers/filenames; we deliberately emit the EN
  canonical layout (what the keyword workbook expects) regardless of UI locale.
- The UI's Search-Terms "Click Share (Past 360 days)" column is fed by the
  short-window `clickShare` field (UI quirk) — replicated for parity.

## Historical Reference

The old pCloud Chrome extension remains source-reference only:
`<your-pcloud>/Account shares/Amazon Wizards/2_Company/2.7_Tools/Chrome Extension-Opportunity Explorer Downloader`

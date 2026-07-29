# Opportunity Explorer Downloader (fetch-poe)

Downloads everything the Product Opportunity Explorer UI shows for a niche:
overview, Products, Search Terms, Customer Review Insights (positive AND
negative, with snippets), Returns, Insights & Trends series, plus the keyword
search / related-niches grid. It uses POE's own internal GraphQL API, same-origin
from the logged-in Seller Central session. One `getNiche` call returns every
niche-detail tab; no DOM scraping, no manual CSV clicking.

Discovered API contract: `references/poe-endpoints.md`.
Captured-vs-visible verification: `references/poe-gap-matrix.md`.

## Files

- `fetch-poe.js`: browser-side fetcher (runs in the page main world; house
  pattern of `tools/report-fetcher/fetch-seller-reports.js`). Functions:
  `fetchPoeNiche({nicheId})`, `fetchPoeSearch({query})`,
  `fetchPoeMerchantNiches()`, `fetchPoeContext()`; also bound as
  `window.amazonAgentFetchPoe*`.
- `format-poe.mjs`: local, deterministic formatter (`--self-test` supported).
  Emits EN-canonical `NicheDetails{Products,SearchTerms}Tab.csv` (drop-in for
  the keyword workbook, locale-independent), sentiment-labeled CRI JSON+CSV,
  Returns JSON+CSV (explicit not-exposed handling), overview JSON (builder-regex
  compatible `text`/`textLines`), related-niches v1 JSON+CSV, full-niche JSON.
- `run-poe.mjs`: one-command CDP runner (shares `../report-fetcher/cdp.mjs`
  and `launch-chrome-debug.sh`).
- `discover-poe-endpoints.mjs`: network-capture logger used to (re)discover
  the API contract when Amazon changes POE. Attach, click through the UI,
  read the NDJSON.
- `extract-opportunity-explorer.js`, `format-opportunity-explorer-export.mjs`:
  DEPRECATED DOM-scraping fallback (kept until the fetch path has survived a
  few real client runs; do not use for new work).

## Usage

### Path B: terminal/CDP (Claude or any agent with shell access)

```bash
tools/report-fetcher/launch-chrome-debug.sh      # dedicated debug Chrome; sign into Seller Central once
node tools/opportunity-explorer/run-poe.mjs doctor

# find the niche (keyword search; also produces the related-niches files)
node tools/opportunity-explorer/run-poe.mjs search --query "kollagen pulver" --marketplace de --client <slug>

# full niche download (all tabs, one call)
node tools/opportunity-explorer/run-poe.mjs niche --niche-id <nicheId> --marketplace de --client <slug> [--verbose]

# coverage workflow: search several seed keywords, dedupe, download every kept niche in full
node tools/opportunity-explorer/run-poe.mjs batch --queries "kollagen pulver,collagen" \
  --marketplace de --client <slug> --origin https://sellercentral.amazon.de [--top 15 | --all]
```

```bash
# mirror a client's captures into the shared pCloud archive
node tools/opportunity-explorer/run-poe.mjs archive --client <slug> [--dry-run]
```

POE serves trailing windows only, so a capture that is lost cannot be fetched
again. `output/<slug>/opportunity-data/` is the hot working copy on one machine;
`archive` mirrors it to
`<pcloud>/1_Delivery/1.1_Clients/<Client>/_Data/opportunity-data/<mp>/<date>_<niche>/`
so the history survives that machine. Copies are MD5-verified, already-archived
files are skipped, and names that do not parse land in `_unsorted/<source-folder>/`
instead of being guessed into a niche folder. The source-folder key matters for
clients captured per product (`output/<slug>/<product>/opportunity-data/`), where
every product folder emits the same filenames and a flat `_unsorted/` would have
them overwrite each other. Point `--out-dir` at each product folder in turn for
those clients. A destination that already holds DIFFERENT content is reported as a
collision and never overwritten. The pCloud root comes from `EW_PCLOUD_ROOT` or
`_local/pcloud-path.txt`; `<Client>` resolves from the slug via the team vault hub
notes (see `pcloud-archive.mjs`). An unmatched client reports and skips rather than
creating a folder that would sync to the whole team.

Search coverage is complete by construction: `getNiches` returns the ENTIRE
matching grid per keyword (hundreds of niches, no pagination/cap). `batch`
unions multiple queries and reports what it skipped when `--top` limits the
download. Data commands infer the canonical Seller Central origin from
`--marketplace`, so `--marketplace de` uses `sellercentral.amazon.de` and
`--marketplace us` uses `sellercentral.amazon.com`. `--origin` remains available
as an explicit override. `doctor` checks the origins of the Seller Central tabs
that are actually open instead of silently defaulting to the US domain. If more
than one regional origin is open, it prints one result per origin. Verified on US
and DE (see `references/poe-gap-matrix.md`). Note: CRI/PDR topic names arrive
localized per marketplace language.

`--marketplace` is required and verified against the session's actual
marketplace. A mismatch aborts. Output goes to
`output/<client>/opportunity-data/` (or `--out-dir`). `--verbose` keeps the raw
envelope JSON. Account verification and the data request share one POE page
session, preventing a second unprimed background tab from stalling the fetch.

### Path A: Codex / internal-browser evaluate

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
OWN meta tag, the same sanctioned mechanism as `tools/report-fetcher/` (see
the carve-out in `AGENTS.md`). Never reads cookies, local/session storage,
passwords, or bearer/refresh tokens; never logs in. Connected/internal browser
only, never headless. ~5 s jittered pacing between heavy requests; one niche
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
  short-window `clickShare` field (UI quirk); replicated for parity.

## Historical Reference

The old pCloud Chrome extension remains source-reference only:
`<your-pcloud>/Account shares/Amazon Wizards/2_Company/2.7_Tools/Chrome Extension-Opportunity Explorer Downloader`

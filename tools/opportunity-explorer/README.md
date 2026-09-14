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
  and the `browserctl` lifecycle policy).
- `discover-poe-endpoints.mjs`: network-capture logger used to (re)discover
  the API contract when Amazon changes POE. Attach, click through the UI,
  read the NDJSON.
- `extract-opportunity-explorer.js`, `format-opportunity-explorer-export.mjs`:
  DEPRECATED DOM-scraping fallback (kept until the fetch path has survived a
  few real client runs; do not use for new work).

## Usage

### Path B: terminal/CDP (any agent with shell access)

```bash
node tools/browserctl/browserctl.mjs ensure --port 9223
# If needed: node tools/browserctl/browserctl.mjs auth --port 9222 --target <target-id>
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
# migrate legacy local captures; verified source files are removed
node tools/opportunity-explorer/run-poe.mjs archive --client <slug> [--out-dir <legacy-dir>] [--dry-run]
```

pCloud is the sole permanent POE data store for Amazon Agent and Wizards AI.
The data commands require `--client`, check the existing pCloud client tree
before fetching, format in memory and publish through the installed pCloud API
helper. Stdout is one JSON receipt (`remote_folder`, `artifacts`, `captures`,
`complete`, `local_data_retained: false`). Upload bytes flow through stdin to pCloud; no payload files are created,
including when a worker is terminated or times out. Failed runs are incomplete; previously verified remote
files stay available. There is no local-output or delayed-quarantine mode.

The browser runner performs blocking pCloud transfers in an upload worker so
its task heartbeat continues throughout a batch. Storage checksums and browser
ownership checks remain mandatory; slow delivery does not extend the lease.

New remote names include a content hash to prevent concurrent captures with the
same original filename overwriting different bytes. Receipts retain the original
`name` alongside `remote_name`, `path`, `sha1` and byte count. Existing identical
legacy paths are reused. Store only receipts locally; download analysis inputs
from pCloud temporarily and remove them when the consuming task ends. Restore
the original `artifact.name` as the local basename for directory-based builders;
the hash-prefixed remote basename is a storage identifier.

`archive` migrates an explicitly selected legacy directory through the same API.
It verifies every remote checksum and unchanged local source before removing the
first source file. A remote migration manifest preserves each relative source
path, including run/product subfolders. Failed verification preserves original files. Use only POE source
directories, not directories mixed with unrelated evidence or executable scripts.
`POE_PCLOUD_SCRIPT` can select the installed API helper; the default is the company
pcloud-api skill under `~/os/company-ai-skills`. No desktop mount is required.

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
marketplace. A mismatch aborts. Output goes to the client pCloud archive.
`--out-dir` is rejected for data commands. `--verbose` archives the raw
envelope JSON in pCloud. Account verification and the data request share one POE page
session, preventing a second unprimed background tab from stalling the fetch.

Structured client requests verify `--account-name` separately from the
`--marketplace-label` suffix in the visible header. Similar seller names are
rejected, and `--expected-partner-account-id` requires exact equality. The
shared picker waits for visible options inside the exact seller; its errors
distinguish `ACCOUNT_SWITCH_MARKETPLACE_MISSING`,
`ACCOUNT_SWITCH_MARKETPLACE_AMBIGUOUS`, and `ACCOUNT_SWITCH_MARKETPLACE_TIMEOUT`.

### Path A: internal-browser page evaluation

Open any `/opportunity-explorer` page in the internal browser (logged in,
correct account + marketplace), then evaluate the source with the call
appended:

```js
await tab.playwright.evaluate(`(async function(){ ${src}\n return await fetchPoeNiche({nicheId: "<id>"}); })()`)
```

Pass the returned JSON through stdin from memory, without saving a capture file:

```bash
node tools/opportunity-explorer/format-poe.mjs --stdin --client <slug>
```

Both paths produce byte-identical files (verified 2026-07-05).

## Safety

Same-origin, read-only GraphQL reads in the operator's existing logged-in
session. The only header added is `anti-csrftoken-a2z`, read from the page's
OWN meta tag, the same sanctioned mechanism as `tools/report-fetcher/` (see
the carve-out in `AGENTS.md`). Never reads cookies, local/session storage,
passwords, or bearer/refresh tokens; never logs in. Dedicated CDP browser in its
machine-policy mode. ~5 s jittered pacing between heavy requests; one niche
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

# Amazon Ads Console Downloads

Use this reference for campaign bulk exports and Sponsored Ads reports created at
`advertising.amazon.com`.

## Contents

- Input contract and browser routing
- Download locations
- Reporting sequence and wait behavior
- Completion-state download cues
- Download filename normalization
- Pre-download coverage and cost check
- Campaign bulk export
- Sponsored Products Search Term Impression Share
- Sponsored Brands Campaign Placement
- CDP feasibility and Claude Code handoff

## Input contract

Collect these values before opening the Ads Console:

- expected advertiser or account name;
- marketplace or country;
- report or export type;
- canonical analysis start and end dates;
- SQP coverage start and end dates;
- targeting/status filter when relevant;
- exact destination path and filename.

Do not infer the account from a previous tab. Do not begin configuration until the
visible account and country match the request.

The canonical Ads window must be fully covered by the SQP data. Use the same dates for
the Ads performance view, campaign bulk files, Sponsored Ads reports, and Business
Reports whenever each report supports the range. If SQP period boundaries prevent an
exact match, keep every other source inside the SQP coverage window and document the
difference.

## Browser routing

Use the dedicated debug Chrome on port `9222` for feasibility checks and future scripted
polling and downloads. Launch or reuse it with:

```bash
tools/report-fetcher/launch-chrome-debug.sh
```

The Ads login must already exist in that profile. If Amazon shows a login screen, stop
and ask the operator to sign in. Never inspect cookies, local storage, session storage,
passwords, one-time codes, or tokens.

Use the Chrome extension or the CDP debug Chrome for operational Ads exports until a
dedicated CDP runner is implemented and validated. No VPN is required: the US VPN rule
came from the Codex Chrome plugin, not from Amazon (verified 31.07.2026 running US
Seller Central and Ads with egress in Seoul, unchallenged).

## Download locations

Amazon Ads data in this workflow comes from two places:

1. `Sponsored ads reports`: create specific reports such as Sponsored Products Search
   Term Impression Share and Sponsored Brands Campaign Placement.
2. `Bulk Operations`: create the campaign bulk workbook containing the selected campaign,
   placement, targeting, keyword, and search-term data families.

Do not treat one location as a substitute for the other. The bulk workbook provides broad
account coverage. Sponsored Ads reports provide report-specific views that are not
equivalent to bulk-sheet tabs.

## Reporting sequence and wait behavior

Create the slow Amazon Ads jobs near the beginning of the reporting workflow:

1. Verify the advertiser, country, canonical analysis window, and SQP coverage window.
2. In `Sponsored ads reports`, create every required specific report first.
3. In Campaign Manager, complete the All-but-archived versus Enabled cost comparison.
4. In `Bulk Operations`, submit the coverage bulk job and any justified Enabled-only job.
5. Continue the other reporting work while Amazon processes the Ads jobs.
6. Every five minutes:
   - refresh `Sponsored ads reports` and check the exact report history rows;
   - refresh `Bulk Operations` and check the exact bulk-operation rows;
   - download each requested file as soon as its status is complete.
7. Stop monitoring only when every requested Ads artifact is downloaded or a real blocker
   is confirmed.

Amazon generation is asynchronous and depends on account size. Use these timings as
planning guidance, not guarantees:

- Sponsored Products Search Term Impression Share often takes about 10 minutes.
- A campaign bulk export can take up to about 30 minutes on a large account.
- Other accounts and date ranges may finish faster or take longer.

Do not resubmit a job merely because it is still processing after one or two checks. A
refresh is required because the page may not update its status immediately. Match jobs by
report name or file label, requested date range, creation time, and status so an older job
is not downloaded by mistake.

For automation, use a recurring monitor or repeated `status` command at five-minute
intervals. Do not use one silent blocking sleep. Keep the maximum wait configurable and
do not treat the typical timing examples as an Amazon SLA.

## Completion-state download cues

Use the row-level state to distinguish a finished file from a job that has only been
submitted.

For campaign bulk exports:

1. Refresh the `Bulk Operations` page.
2. Find the exact job using its file label, requested dates, creation time, and expected
   account.
3. Treat the file as ready only when the row status is `Success`.
4. Use the link in that row's download column. The link may be localized, such as
   `Herunterladen`.

`Download campaigns` opens the form for creating a new export. It does not retrieve an
existing completed file. Do not submit a duplicate job when the intended row already
shows `Success`.

For Sponsored Ads reports:

1. Find the exact report definition in `Sponsored ads reports`, such as `Sponsored
   Products Search Term Impression Share report`.
2. Confirm the category, report type, country, and latest-run timing.
3. Open the report definition and inspect its run history.
4. Match the completed run by report period and creation time.
5. Use the completed history row's `Download` link.

The report-definition row is a route into its run history. Its presence in the reports
list is not proof that the requested run has finished.

After either download:

1. Confirm that Chrome started the transfer.
2. Wait until no partial `.crdownload` file remains.
3. Confirm that the downloaded file is a non-empty `.xlsx`.
4. Move or rename it to the exact destination requested by the task.

## Download filename normalization

Amazon's generated bulk filename starts with `bulk`, includes an opaque alphanumeric
job or account identifier, and includes the export start and end dates. Normalize it for
human use after the transfer completes:

1. Keep the `bulk` prefix.
2. Replace the opaque alphanumeric segment with the audited account name.
3. Preserve the original start and end dates in the filename.
4. Keep the `.xlsx` extension.

Example:

```text
bulk-<opaque-identifier>-2026-06-01-2026-06-30.xlsx
bulk-Heusom-2026-06-01-2026-06-30.xlsx
```

Preserve Amazon's exact date formatting and separator order when the generated filename
uses a different arrangement. The account name is the human-readable identity; do not
guess it from the opaque segment. Confirm it from the visible advertiser checkpoint.

The task's exact destination filename always overrides this default pattern. When the
opaque identifier may be needed for troubleshooting, deduplication, or matching a browser
download to its Amazon job, record the original filename in the evidence note before
renaming the file. The opaque identifier does not otherwise need to remain in the working
filename.

## Mandatory checkpoint

Before each page or download:

1. Confirm the visible account name.
2. Confirm the visible Ads account type or scope, such as `Sponsored ads, multiple countries`.
3. Confirm the country selector, such as `United States`.
4. Confirm the page:
   - `Bulk Operations` for campaign bulk files;
   - `Sponsored ads reports` for report definitions and run history.
5. Confirm the canonical analysis window and SQP coverage window.
6. Confirm the final visible report range before starting each export.

Abort on an account or country mismatch. An authenticated download link can return a
perfectly valid file from the wrong advertiser.

## Pre-download coverage and cost check

Start in Campaign Manager before opening either download location:

1. Set the Campaign Manager date range to the canonical SQP-aligned analysis window.
2. Set `Active status` to `All but archived`.
3. Record `Total cost`.
4. Change only `Active status` to `Enabled`.
5. Record `Total cost` again.
6. Calculate:
   - excluded cost = All-but-archived cost minus Enabled cost;
   - excluded-cost share = excluded cost divided by All-but-archived cost.
7. Keep the dates unchanged while comparing the two filters.

Use the result to plan the bulk downloads:

- Always create the broader coverage file with `Enabled & Paused` and the include settings
  below. This remains the authoritative account-coverage source.
- If the excluded-cost share is immaterial, also create an `Enabled`-only bulk file with
  the same dates and include settings. This second file is much smaller and is the
  preferred working file where enabled campaigns are sufficient.
- If the difference is material, do not use the Enabled-only file as the sole analysis
  input. Preserve and prioritize the coverage file.

Do not invent a universal materiality threshold. Use an explicit client or workflow
threshold when one exists. Otherwise record the dollar and percentage difference and
apply operator judgment. In the recorded example, about `$3,000` excluded from about
`$130,000` total cost was considered immaterial (roughly `2.3%`), so a second
Enabled-only file was justified.

## Campaign bulk export

Page: `https://advertising.amazon.com/bulk-operations`

Recorded flow:

1. Complete the Campaign Manager cost check above.
2. Open the side navigation.
3. Choose `Bulk operations`.
4. Select `Download campaigns`.
5. Set `Date range for performance metrics` to the canonical SQP-aligned window.
6. Set `Sponsored products: Targeting and keyword filter`.
7. Review every `Include` checkbox. Do not rely on Amazon's current defaults.
8. Optionally enter a file name.
9. Select `Download` to create the export job.
10. Return to the Bulk Operations table.
11. Wait for the job status to become `Success`.
12. Use the completed row's download link to retrieve the `.xlsx`. Do not click
    `Download campaigns`, which would start another export.
13. When the cost check justifies it, repeat the export with only the targeting filter
    changed from `Enabled & Paused` to `Enabled`.

The demonstrated audit settings were:

| Control | Value |
|---|---|
| Targeting and keyword filter | `Enabled & Paused` |
| Terminated campaigns | Included |
| Paused campaigns | Included |
| Campaign items with zero impressions | Included |
| Placement data for campaigns | Included |
| Brand asset data | Excluded |
| Sponsored Products data | Included |
| Sponsored Brands data | Included |
| Sponsored Brands multi-ad group data | Included |
| Sponsored Display data | Included |
| Guidance for Sponsored products | Excluded |
| Sponsored products search term data | Included |
| Sponsored brands search term data | Included in the demonstration, but not required for the standard audit |
| Budget Rules Data | Excluded |

These include settings are the important audit profile from the demonstration. Preserve
them for the coverage file unless the task explicitly requests a different data family.
The date range, advertiser, marketplace, filename, and targeting filter remain inputs.
For the second smaller file, change only the targeting filter to `Enabled`.

Amazon creates the export asynchronously. A click on `Download` starts the job. It does
not necessarily transfer the file immediately. Poll the Bulk Operations table until the
row is `Success`, then follow its authenticated download link.

## Sponsored Products Search Term Impression Share

Page: `https://advertising.amazon.com/reports`

1. Choose `Create report`.
2. Set `Report category` to `Sponsored Products`.
3. Set `Report type` to `Search Term Impression Share`.
4. Confirm `Country`.
5. Keep `Time unit` at `Summary` unless the task requests daily rows.
6. Set `Report period`.
7. Keep the generated report name or replace it with a clear client/date name.
8. Choose `Run report`.
9. Find the exact report definition in the reports table using its category, type,
   country, and latest-run timing.
10. Open the report definition and inspect its run history.
11. Wait for the matching report-period row to become `Completed`.
12. Follow that completed history row's `Download` link.

This report measures impression-share percentage and rank relative to other advertisers
for each search term. It is useful for identifying Sponsored Products headroom.

## Sponsored Brands Campaign Placement

Page: `https://advertising.amazon.com/reports`

1. Choose `Create report`.
2. Set `Report category` to `Sponsored Brands`.
3. Set `Report type` to `Campaign placement`.
4. Confirm `Country`.
5. Keep `Time unit` at `Summary` unless the task requests daily rows.
6. Set `Report period`.
7. Keep the generated report name or replace it with a clear client/date name.
8. Choose `Run report`.
9. Open the report definition from the reports table.
10. Wait for the history row to become `Completed`.
11. Follow the row's `Download` link.

This is the source for the Sponsored Brands Top of Search, Rest of Search, and Product
Page placement split.

## CDP feasibility result

Live-verified on 2026-07-30 in the dedicated debug Chrome. These results establish
technical feasibility in one authenticated session. They do not claim that a reusable
runner already exists.

| Capability | Result | Evidence |
|---|---|---|
| Open authenticated Ads Console | Live proof | The debug profile loaded Campaign Manager for the expected advertiser. |
| Verify account and country from page text | Live proof | The account name, account scope, and `United States` were visible in the DOM. |
| List report definitions | Live proof | The report center returned existing definitions through the page and `POST /reports/api/subscriptions`. |
| Resolve a completed report download | Live proof | A report history page exposed an authenticated `Download` link. |
| Transfer a report file through CDP | Live proof | A Sponsored Brands Campaign Placement `.xlsx` was saved to an isolated temporary folder. |
| Resolve a completed bulk download | Live proof | A successful Bulk Operations row exposed an authenticated `.xlsx` link. |
| Transfer a bulk file through CDP | Live proof | A campaign bulk `.xlsx` was saved to an isolated temporary folder. |
| Reusable Ads download runner in the repository | Not implemented | `cdp.mjs` supplies the protocol client, but no Ads command currently owns download paths, polling, or final filenames. |
| Create a new report through a direct endpoint | Not yet proven | The user demonstration established the form flow, but the create request was not captured in the debug profile. |
| Create a new bulk export through a direct endpoint | Not yet proven | The user demonstration established the form flow, but the create request was not captured in the debug profile. |

Conclusion: the Chrome extension is not required for authenticated Ads downloads. The
remaining engineering work is generation and polling automation, not file transfer.

## Claude Code handoff

Give Claude Code this reference plus:

- `tools/report-fetcher/cdp.mjs`;
- `tools/report-fetcher/capture-endpoints.mjs` as a pattern only. It currently filters
  for `sellercentral.amazon.*` and will not capture Ads traffic without an
  `advertising.amazon.com` variant;
- `docs/browser-checkpoints.md`;
- `docs/browser-routing-map.md`.

Ask Claude to build an Ads-specific CDP runner with these commands:

```text
doctor
plan
compare-cost
create-bulk
create-report
status
watch
download
```

Required runner behavior:

1. Open a background Ads Console tab in the dedicated debug Chrome.
2. Print the visible account, account scope, country, page, and entity context.
3. Require `--expect-account` and `--marketplace` on every stateful or download command.
4. Require canonical analysis start/end dates and SQP coverage start/end dates. Abort when
   the requested Ads window is not fully covered by SQP.
5. Make `plan` read-only and print all report settings, date windows, and destination paths.
6. Make `compare-cost` read-only. Return the All-but-archived cost, Enabled cost, excluded
   dollars, and excluded percentage for the unchanged canonical window.
7. Create the Enabled-only bulk file only when an explicit threshold or operator decision
   marks the excluded-cost share as immaterial. Keep the Enabled-and-Paused coverage file.
8. Capture the exact create and polling endpoints from the page's own network requests.
9. Reproduce same-origin requests from the page main world. Do not read browser storage or credentials.
10. Treat report generation as a report job only. Never change campaigns, bids, budgets, targeting, or account settings.
11. Add a deterministic idempotency key or pre-submit duplicate check. A retry after a
   timeout must not create the same report job twice.
12. Queue required Sponsored Ads reports early, then submit bulk jobs immediately after
    `compare-cost` so generation overlaps the remaining reporting work.
13. Make `watch` refresh and poll both report locations every 300 seconds. Use a recurring
    monitor or repeated status invocation, not one silent blocking process.
14. Keep timeouts configurable by workflow and account size. Do not interpret 10 minutes
    for impression-share reports or 30 minutes for bulk files as fixed SLAs.
15. Set `Browser.setDownloadBehavior` to an explicit, run-scoped destination directory.
16. Wait until the final file exists and no `.crdownload` remains.
17. Rename to the exact requested filename and validate the extension, nonzero size, and
    file signature. An `.xlsx` must be a valid ZIP/OOXML container.
18. Fall back to accessible DOM controls if a stable endpoint cannot be identified.

For endpoint discovery, capture only requests to `advertising.amazon.com`. Redact
analytics payloads, user identifiers, report IDs, entity IDs, signed URLs, and session
metadata from committed evidence. Keep raw captures local and gitignored.

## Caveats

- The recorded date picker demonstration selected a range by clicking calendar days.
  Always verify the final visible range. Do not trust click order alone.
- Amazon Ads report generation is asynchronous. `Run report` and `Download campaigns`
  create jobs; they do not guarantee an immediate file.
- Amazon is migrating Sponsored Ads reports toward unified reporting in late 2026.
  Recheck the current report center and endpoints before hard-coding page structure.
- Report download links and bulk download links are authenticated and may expire.
- Do not commit raw network captures. They can contain account and session metadata even
  when no cookies are explicitly read.

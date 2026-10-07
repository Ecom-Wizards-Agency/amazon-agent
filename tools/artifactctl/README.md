# artifactctl

`artifactctl` tracks exact local files under explicit workflow run IDs. It does
not scan for deletion candidates and it never modifies remote pCloud, Google
Drive, or FlatFilePro data.

```bash
tools/artifactctl/artifactctl run start --owner report-fetcher --client acme --workflow amazon-reporting
tools/artifactctl/artifactctl register --run RUN_ID --path output/acme/reporting/report.csv --disposition archive-pcloud
tools/artifactctl/artifactctl run complete --run RUN_ID --outcome success
tools/artifactctl/artifactctl cleanup --audit-only
tools/artifactctl/artifactctl quarantine list
tools/artifactctl/artifactctl quarantine restore --artifact ARTIFACT_ID
```

## Archiving to pCloud at run completion

Finished client work is archived when the run completes, not by the weekly job.
Register each file at its final local path. A run folder is never renamed after
registration, because the registry records exact paths. Then run `archive`:

```bash
# Delivered bundle: one dated folder per bundle, file names kept
tools/artifactctl/artifactctl register --run RUN_ID --path output/acme/logistics/2026-10-07_Acme_DE_Carton-Packing-Plan_SPD_v1.xlsx \
  --disposition archive-pcloud --archive-client acme --archive-dataset logistics --archive-market DE \
  --archive-bundle-date 2026-10-07 --archive-bundle-scope "DE to UK" \
  --archive-bundle-partner "3PL Name" --archive-bundle-carrier UPS
# Monthly raw file: flat, renamed YYYY-MM_MARKET_REPORT-TYPE_SCOPE
tools/artifactctl/artifactctl register --run RUN_ID --path output/acme/reporting/report.csv \
  --disposition archive-pcloud --archive-client acme --archive-dataset reporting --archive-market US \
  --archive-month 2026-09 --archive-report-type BUSINESS-REPORT
tools/artifactctl/artifactctl archive --run RUN_ID --audit-only   # checks only, no pCloud call
tools/artifactctl/artifactctl archive --run RUN_ID
tools/artifactctl/artifactctl run complete --run RUN_ID --outcome success
```

Bundle mode needs `--archive-bundle-date` and `--archive-bundle-scope`; partner,
carrier and `--archive-bundle-root` (keep paths relative to that directory, for
a change pack with numbered subfolders) are optional. It lands in
`_Data/{workflow}/[{market}/]YYYY-MM-DD - {Scope} - {Partner} - {Carrier}/`, and
each file name must start `YYYY-MM-DD_`. Monthly mode needs `--archive-month` and
`--archive-report-type`; `--archive-scope` defaults to `ALL-SKUS`. The two modes
cannot be combined.

`archive` archives every `archive-pcloud` file of the run that has no valid
receipt yet and is `registered` or `eligible-pending`, whether the run is active
or complete, and stores the verified receipt. Files in `review` or `preserved`
(a failed or blocked run) are listed under `skipped` and never uploaded. It
changes nothing else: state, eligibility and quarantine timing stay as they
were, and the weekly `cleanup` later quarantines the files without a second
upload. A batch already archived by a concurrent `archive` or `cleanup` is
reported as `already_archived`, not uploaded again. It exits 2 with
`"ok": false` when any file was preserved, and names each one with its reason
and, for a helper failure, a short `detail`. After a successful `run complete`,
a reminder goes to stderr while `archive-pcloud` files still lack a receipt;
the weekly job remains the safety net. Add one line per bundle to the run note, using the `bundles` field of the
output:

```text
pCloud: <share-relative bundle path> (N files, SHA-1 verified, run RUN_ID)
```

## Lifecycle

Successful runs become eligible after seven days. Eligible exact files enter a
30-day local quarantine only after their disposition-specific verification.
Changed, missing, unregistered, manually supplied, failed-run, and out-of-scope
files are preserved. Purge unlinks one verified quarantine file at a time.

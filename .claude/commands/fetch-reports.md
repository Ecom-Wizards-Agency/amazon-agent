# /fetch-reports: pull Seller Central reports (Business / SQP / SCP / TST)

Fetch Seller Central reports hands-off with `tools/report-fetcher/`: no manual download,
no console paste. Runs in the operator's logged-in Chrome over the debug protocol. Read-only
(report reads only); never change Seller Central settings. Full reference:
`tools/report-fetcher/README.md`; copy-paste prompts: `tools/report-fetcher/CODEX-PROMPT.md`.

Load the `amazon-reporting` skill first.

## Steps

1. **Confirm scope** if not given: client slug, which reports (sqp / business / scp / tst / all),
   ASIN(s) or ASIN groups, timeframe (SQP range weekly|monthly|quarterly + period-end dates;
   Business start/end). Prefer a per-client config: `tools/report-fetcher/config.<client>.json`
   (copy from `config.TEMPLATE.json`, gitignored) so runs are a fixed command.
2. **Check the debug Chrome**: `node tools/report-fetcher/run.mjs doctor`.
   - Unreachable → run `tools/report-fetcher/launch-chrome-debug.sh`, then ask the operator to
     sign into Seller Central in the debug window; wait. (Codex can run the launcher; only the
     operator can complete the login.)
   - Proceed only when it prints **"Login: OK"**.
3. **Plan then fetch** (config-driven):
   ```bash
   node tools/report-fetcher/run.mjs <report|all> --config tools/report-fetcher/config.<client>.json --plan
   node tools/report-fetcher/run.mjs <report|all> --config tools/report-fetcher/config.<client>.json --verbose
   ```
   Or explicit flags (see CODEX-PROMPT.md section B). SQP defaults to one combined CSV per
   group; add `--split` for one file per ASIN.
4. **Report** the row count per file and where each CSV landed
   (`output/<client>/reporting/`). SQP → `inputs.sqp_csvs`, Business → `inputs.business_report_csv`.
5. **On an "unmapped column" error**: it exits non-zero and lists the source columns; paste
   the column ids from the matching `<out>.raw.json`; the fix is a one-line map in
   `format-seller-reports.mjs`, never a wrong file.

Stop rules: read-only; if there's no active session, land nothing and ask the operator to
sign in. Never fabricate rows.

# Browser-capable agent prompt: fetch Seller Central reports

Canonical, client-agnostic prompt for pulling Seller Central reports with the report fetcher.
Use the current runtime's shell and connected browser capability. Fill the placeholders; nothing
here names a client.

Prerequisite (one-time): initialize the dedicated debug Chrome login with
`tools/report-fetcher/launch-chrome-debug.sh --mode recovery`, sign into Seller Central, then
return it to headless mode with `tools/report-fetcher/launch-chrome-debug.sh`. The login persists;
normal CDP commands start or reuse the headless profile automatically.

## Account safety

One login can hold several sellers, and the debug Chrome can have several regions open at once.
`doctor` prints the seller name and merchant id for every open tab. Confirm the name is the client
you were asked for before trusting any number. A report pulled from the wrong seller looks
completely normal: right shape, right dates, wrong company.

Always pass `--expect-account "<Client Name>"` on data commands. It resolves the active account and
aborts before fetching on a mismatch.

If it aborts, switch the account in the debug Chrome and re-run. Do not use `--account` as a safety
substitute: Seller Central may ignore that hint and return the tab's active seller. If you cannot
switch the account, stop and ask the operator.

Region comes from `--marketplace` (US `.com`, EU country through the applicable regional login,
AU `.com.au`, and so on), not from whichever tab happens to be first. If no open tab serves the
requested marketplace, the run aborts and tells you which host to open.

## A. Config-driven run

First, once per client, copy `tools/report-fetcher/config.TEMPLATE.json` to
`tools/report-fetcher/config.<CLIENT_SLUG>.json` (gitignored) and fill the ASIN groups, period-end
dates, range, and output paths.

```text
From the Amazon Agent repository root, fetch Seller Central reports.
Read-only. Change no Seller Central settings.

CONFIG: tools/report-fetcher/config.<CLIENT_SLUG>.json
CLIENT (must match the Seller Central account name): <CLIENT NAME>

1. node tools/report-fetcher/run.mjs doctor
   - The command starts or reuses headless CDP. If login is missing, run
     tools/report-fetcher/launch-chrome-debug.sh --mode recovery, ask the operator to sign in,
     and wait.
   - Proceed only when it prints "Login: OK".
   - Check the account line. If no tab shows <CLIENT NAME>, stop. Do not fetch from another seller.
2. node tools/report-fetcher/run.mjs all --config <CONFIG> --plan
3. node tools/report-fetcher/run.mjs all --config <CONFIG> --expect-account "<CLIENT NAME>" --verbose

Report the row count for each file. If the formatter reports an "unmapped column", provide the
column ids from the matching <out>.raw.json so the map can be corrected.
```

Use `sqp`, `business`, `scp`, or `tst` instead of `all` to run one report.

## B. Explicit flags

```text
From the Amazon Agent repository root, fetch Seller Central reports.
Read-only. Change no Seller Central settings.

FILL:
  CLIENT NAME:    <CLIENT NAME>
  CLIENT SLUG:    <CLIENT_SLUG>
  MARKETPLACE:    <us|de|it|es|fr|nl|uk|au|jp|ca|...>
  ASIN(S):        <ASIN>[,<ASIN>...]
  SQP RANGE:      weekly | monthly | quarterly
  SQP PERIOD(S):  <YYYY-MM-DD>[,<YYYY-MM-DD>...]
  BUSINESS RANGE: <START> to <END>

1. node tools/report-fetcher/run.mjs doctor
   - Proceed only on "Login: OK" and after confirming a tab shows <CLIENT NAME>.
2. SQP (add --split for one file per ASIN):
   node tools/report-fetcher/run.mjs sqp --asins <ASIN(S)> --weeks <SQP PERIOD(S)> \
     --range <SQP RANGE> --marketplace <MARKETPLACE> --expect-account "<CLIENT NAME>" \
     --out output/<CLIENT_SLUG>/reporting/sqp.csv --verbose
3. Business Report:
   node tools/report-fetcher/run.mjs business --start <START> --end <END> \
     --marketplace <MARKETPLACE> --expect-account "<CLIENT NAME>" \
     --out output/<CLIENT_SLUG>/reporting/business_<START>.csv --verbose
4. Optional SCP and TST:
   node tools/report-fetcher/run.mjs scp --weeks <SQP PERIOD(S)> --marketplace <MARKETPLACE> \
     --expect-account "<CLIENT NAME>" --out output/<CLIENT_SLUG>/reporting/scp.csv --verbose
   node tools/report-fetcher/run.mjs tst --weeks <SQP PERIOD(S)> --marketplace <MARKETPLACE> \
     --expect-account "<CLIENT NAME>" --out output/<CLIENT_SLUG>/reporting/tst.csv --verbose

Report row counts per file. On an "unmapped column" error, provide the column ids from the
matching <out>.raw.json.
```

## Notes

- SQP outputs feed `inputs.sqp_csvs`; Business outputs feed `inputs.business_report_csv`.
- TST is marketplace-wide. It defaults to the top rows; narrow with `--brand`, `--search-term`,
  or `--asins`, or use `--max-pages N` deliberately.
- SQP is fetched one ASIN per call, then combined or split.
- The runner opens a background tab, writes the CSV, and closes it. It never changes Seller
  Central settings.

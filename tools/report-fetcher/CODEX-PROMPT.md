# Codex prompt: fetch Seller Central reports (copy-paste)

Canonical, client-agnostic prompt for pulling Seller Central reports with the report
fetcher via Codex `@computer`. Fill the placeholders; nothing here names a client.

Prereq (one-time): a dedicated debug Chrome is running and signed into Seller Central.
Run `tools/report-fetcher/launch-chrome-debug.sh`, then log in once in that window. The login
persists in the debug profile.

---

## A. Config-driven (recommended: fill the config once, then this is fixed)

First (one-time per client): copy `tools/report-fetcher/config.TEMPLATE.json` to
`tools/report-fetcher/config.<CLIENT_SLUG>.json` (gitignored) and fill the ASIN groups,
period-end dates, range, and out paths.

Then paste this to Codex:

```
Using @computer, in ~/Codex Projects/Amazon Agent, fetch Seller Central reports.
Read-only. Change no Seller Central settings.

CONFIG: tools/report-fetcher/config.<CLIENT_SLUG>.json

1. node tools/report-fetcher/run.mjs doctor
   - If the debug port is unreachable: run tools/report-fetcher/launch-chrome-debug.sh,
     tell me to sign into Seller Central in the debug window, and wait for me.
   - Proceed only when it prints "Login: OK".
2. node tools/report-fetcher/run.mjs all --config <CONFIG> --plan     # show the plan
3. node tools/report-fetcher/run.mjs all --config <CONFIG> --verbose  # fetch everything
Report the row count for each file. If the formatter reports an "unmapped column",
paste the column ids from the matching <out>.raw.json so it can be fixed in one line.
```

(Use `sqp`/`business`/`scp`/`tst` instead of `all` to run just one report.)

---

## B. Explicit flags (no config)

```
Using @computer, in ~/Codex Projects/Amazon Agent, fetch Seller Central reports.
Read-only. Change no Seller Central settings.

FILL:
  CLIENT SLUG:    <CLIENT_SLUG>          (lowercase-kebab)
  ASIN(S):        <ASIN>[,<ASIN>...]
  SQP RANGE:      weekly | monthly | quarterly
  SQP PERIOD(S):  <YYYY-MM-DD>[,<YYYY-MM-DD>...]   (period-END date; weekly = week-ending Saturday)
  BUSINESS RANGE: <START> to <END>       (YYYY-MM-DD)

1. node tools/report-fetcher/run.mjs doctor   → proceed only on "Login: OK"
   (if unreachable: run launch-chrome-debug.sh and tell me to sign in)
2. SQP (one combined file for the ASINs; add --split for one file per ASIN):
   node tools/report-fetcher/run.mjs sqp --asins <ASIN(S)> --weeks <SQP PERIOD(S)> \
     --range <SQP RANGE> --out output/<CLIENT_SLUG>/reporting/sqp.csv --verbose
3. Business Report (Detail by Child ASIN):
   node tools/report-fetcher/run.mjs business --start <START> --end <END> \
     --out output/<CLIENT_SLUG>/reporting/business_<START>.csv --verbose
4. (Optional) SCP / TST for a period:
   node tools/report-fetcher/run.mjs scp --weeks <SQP PERIOD(S)> --out output/<CLIENT_SLUG>/reporting/scp.csv --verbose
   node tools/report-fetcher/run.mjs tst --weeks <SQP PERIOD(S)> --out output/<CLIENT_SLUG>/reporting/tst.csv --verbose

Report row counts per file. On an "unmapped column" error, paste the column ids from
the <out>.raw.json.
```

---

Notes:
- Output CSVs feed the ad-audit pipeline: SQP → `inputs.sqp_csvs["<group>"]`, Business →
  `inputs.business_report_csv`. SCP/TST are standalone.
- **TST is marketplace-wide** (huge). It defaults to the top ~500 rows; add `--brand`,
  `--search-term`, or `--asins` to narrow it, or `--max-pages N` to go deeper.
- SQP is fetched **one ASIN per call** (uncapped Search Query Volume), then combined or split.
- The runner opens its own background tab, writes the CSV, and closes it. It never disturbs
  the operator's tabs. Read-only report reads only.

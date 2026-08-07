# Codex prompt: fetch Seller Central reports (copy-paste)

Canonical, client-agnostic prompt for pulling Seller Central reports with the report
fetcher via Codex `@computer`. Fill the placeholders; nothing here names a client.

Prereq (one-time): initialize the dedicated debug Chrome login with
`tools/report-fetcher/launch-chrome-debug.sh --mode recovery`, sign into Seller Central, then
return it to headless mode with `tools/report-fetcher/launch-chrome-debug.sh`. The login persists;
normal CDP commands start or reuse the headless profile automatically.

## ACCOUNT SAFETY (read before every run)

One login can hold several sellers, and the debug Chrome can have several regions open at once.
`doctor` prints the seller name + merchant id for every open tab. **Confirm the name is the client
you were asked for before you trust a single number.** A report pulled from the wrong seller looks
completely normal: right shape, right dates, wrong company.

Always pass `--expect-account "<Client Name>"` on data commands. It resolves the active account and
**aborts before fetching** on a mismatch, so a wrong-account pull fails loudly instead of producing a
plausible file.

If it aborts, **switch the account in the debug Chrome and re-run.** Do not reach for `--account`:
that flag is only a hint, Seller Central may ignore it and return the tab's seller anyway, and it
deliberately cannot satisfy `--expect-account`. If you cannot switch the account, stop and ask.

Region comes from `--marketplace` (US .com, DE/IT/ES/FR/NL/UK/... .de and siblings, AU .com.au, and
so on), not from whichever tab happens to be first. If no open tab serves the requested marketplace
the run aborts and tells you which host to open.

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

CLIENT (must match the Seller Central account name): <CLIENT NAME>

1. node tools/report-fetcher/run.mjs doctor
   - The command starts/reuses headless CDP. If login is missing, run
     tools/report-fetcher/launch-chrome-debug.sh --mode recovery, tell me to sign in, and wait.
   - Proceed only when it prints "Login: OK".
   - CHECK THE ACCOUNT LINE. If no tab shows <CLIENT NAME>, stop and tell me. Do not
     fetch from a different seller "to see what comes back".
2. node tools/report-fetcher/run.mjs all --config <CONFIG> --plan     # show the plan
3. node tools/report-fetcher/run.mjs all --config <CONFIG> --expect-account "<CLIENT NAME>" --verbose
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
  CLIENT NAME:    <CLIENT NAME>          (as it appears in the Seller Central account switcher)
  CLIENT SLUG:    <CLIENT_SLUG>          (lowercase-kebab)
  MARKETPLACE:    <us|de|it|es|fr|nl|uk|au|jp|ca|...>
  ASIN(S):        <ASIN>[,<ASIN>...]
  SQP RANGE:      weekly | monthly | quarterly
  SQP PERIOD(S):  <YYYY-MM-DD>[,<YYYY-MM-DD>...]   (period-END date; weekly = week-ending SATURDAY)
  BUSINESS RANGE: <START> to <END>       (YYYY-MM-DD)

1. node tools/report-fetcher/run.mjs doctor   → starts/reuses headless CDP; proceed only on "Login: OK"
   (if login is needed, use `launch-chrome-debug.sh --mode recovery` and tell me to sign in)
   → confirm a tab shows <CLIENT NAME>. If none does, STOP and tell me.
2. SQP (one combined file for the ASINs; add --split for one file per ASIN):
   node tools/report-fetcher/run.mjs sqp --asins <ASIN(S)> --weeks <SQP PERIOD(S)> \
     --range <SQP RANGE> --marketplace <MARKETPLACE> --expect-account "<CLIENT NAME>" \
     --out output/<CLIENT_SLUG>/reporting/sqp.csv --verbose
3. Business Report (Detail by Child ASIN; --report parent|sku for the other cuts):
   node tools/report-fetcher/run.mjs business --start <START> --end <END> \
     --marketplace <MARKETPLACE> --expect-account "<CLIENT NAME>" \
     --out output/<CLIENT_SLUG>/reporting/business_<START>.csv --verbose
4. (Optional) SCP / TST for a period:
   node tools/report-fetcher/run.mjs scp --weeks <SQP PERIOD(S)> --marketplace <MARKETPLACE> \
     --expect-account "<CLIENT NAME>" --out output/<CLIENT_SLUG>/reporting/scp.csv --verbose
   node tools/report-fetcher/run.mjs tst --weeks <SQP PERIOD(S)> --marketplace <MARKETPLACE> \
     --expect-account "<CLIENT NAME>" --out output/<CLIENT_SLUG>/reporting/tst.csv --verbose

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

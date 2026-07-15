# Campaign Builder End-to-End Workflow (v2: create + update)

Two independent flows share this toolkit: **create** (text brief / keyword workbook →
brand-new SP bulk-upload `.xlsx`) and **update** (a bulksheets export of the live account +
a change-set → real-ID Update/Archive/Create `.xlsx`). The config (or change-set) is the
contract; nothing in the code is client-specific.

## Roles

- **Agent (Claude or Codex)**: parses the operator's brief/keyword workbook/change request,
  asks for missing required fields, scaffolds the config, runs preflight/preview/build,
  presents the review, and then **stops**.
- **Operator**: confirms the preview, uploads the file in Campaign Manager → Bulk Operations,
  flips paused campaigns live when ready (create), or accepts the consequences of the changes
  described in the update `_REVIEW.md` (update, which is live the moment it's uploaded).

## Create flow

1. **Brief or keyword workbook**: the operator describes the campaigns in plain text
   ("SKW campaigns for these 5 keywords on GB-001, $15 budget, plus one auto at $10…") or
   hands over a keyword-research workbook. Ask once for anything required but missing:
   marketplace/account, SKUs/ASINs, keywords or target ASINs (or the workbook path),
   budget, bid, portfolio, negatives, start date, paused vs enabled.

2. **Scaffold**: copy `config.TEMPLATE.json` → `config.<client>-<market>.json` (gitignored),
   fill `campaigns[]` from the brief, **or** pass `--keyword-file <workbook.xlsx>` to source
   `campaigns[]` from the workbook's "5. Campaign Structure" tab (or a generic flat sheet).
   See `NEW-CLIENT.md` and `README.md`'s "Keyword-file input" section. The config defaults to
   the **EW naming preset** (8-slot convention) unless `naming.preset: "LEGACY"` is set.

3. **Preflight**: `build_campaigns.py --config <cfg> [--keyword-file <wb>] --preflight`
   until READY. Catches invalid enums, sub-minimum bids/budgets, missing SKUs/keywords, past
   start dates, name fan-out without a disambiguating `Counter`/`CampCounter`/`Keyword` token,
   and NOTEs (non-blocking): bidding-strategy overrides of the naming-convention.md per-purpose
   defaults, discovery campaigns missing a negative-keyword list, Self-Targeting Expanded
   missing a negative-ASIN list, and ad-group names that collide with their campaign name.

4. **Preview**: `--preview` prints every planned campaign (name, type, state, budget, bid,
   strategy, target counts) and the combined daily budget. Show this to the operator; adjust
   the config until it matches intent.

5. **Build**: `--config <cfg>` writes `output/<client-slug>/ads/<date>_<Brand>_<Market>_SP_bulk_campaigns.xlsx`
   + `…_REVIEW.md` and auto-runs the QA gates (must PASS).

6. **Review + handoff**: give the operator the review file and the path. **The workflow ends here.**

## Update flow

1. **Get a fresh export**: ask the operator to download a bulksheets export of the
   "Sponsored Products Campaigns" tab for the account (Bulk Operations → create/download a
   spreadsheet including the campaigns/ad groups/keywords/targets in scope). This is the
   **only** valid source of real IDs: never the console UI, never IDs remembered from a
   prior session/report.

2. **Scaffold the change-set**: copy `config.UPDATE.TEMPLATE.json` →
   `config.UPDATE.<client>-<market>.json` (gitignored), set `export_file` to the downloaded
   path, and fill `changes{}` from the operator's request ("pause these 3 keywords, raise the
   Rank campaign budget to $30, archive the old BMM campaign"). Look up every real ID from
   the export. Never invent one.

3. **Preflight**: `update_campaigns.py --config <cfg> --preflight` until READY. Fails on any
   ID not found in the export, invalid enum, or a disallowed `clear_end_date`. NOTEs every
   no-op and cascade-skip (e.g. an explicit ad-group archive whose parent campaign is also
   archived in the same file).

4. **Preview**: `--preview` prints a plain-English line per change (and per skip). Show this
   to the operator. This is the change-set's real content, not a technical row dump.

5. **Build**: `--config <cfg>` writes `..._SP_bulk_UPDATE.xlsx` + `..._REVIEW.md`, auto-runs
   the QA gates (must PASS). **The `_REVIEW.md` is mandatory reading**: this file changes a
   live account when uploaded, unlike create mode's paused-by-default output.

6. **Review + handoff**: give the operator the review file and the path, and remind them a
   fresh export is needed before any *subsequent* update batch (yesterday's export's IDs may
   be stale once today's upload processes). **The workflow ends here.**

## Safety rails

- Create-mode campaigns default to **paused**; `enabled` requires the operator to ask for it
  and triggers a preflight live-on-upload note.
- **Update mode has no "paused-by-default" safety net**: an Update/Archive/Create row acts
  on a real, currently-serving entity the moment it's processed. The `_REVIEW.md` plain-
  English change list is the safety mechanism here; read it before uploading, every time.
- The tool writes a file; it has no Amazon Ads API or AdLabs write path. Uploading the bulk
  file, pushing via AdLabs `create_entities`/update calls, changing live bids/budgets: each
  is a stop-before-risk action needing explicit operator instruction in the current chat (or
  a matching `_local/local-permissions.md` standing permission).
- For AdLabs-managed accounts the operator may instead ask for a gated AdLabs push: that
  follows the `amazon-adlabs-audit` write policy (explicit per-write lift, batch-by-batch
  what-will-change summary, tags). It is not part of this toolkit.
- Run `python3 tools/amazon-campaign-builder/selftest.py` after any change to either toolkit.
  It must stay green (synthetic fixtures, no network/Amazon access).

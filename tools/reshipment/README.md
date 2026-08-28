# Reshipment / Weekly FBA Inventory Overview

Builds per-account reshipment + excess-inventory workbooks (CSV, XLSX, Slack staging text,
and a JSON manifest) from same-day Amazon MCP/SP-API data or narrow same-day Seller Central
fallback reports. MCP/SP-API is the default source. Browser downloads are used only when a
required field is unavailable or stale through MCP. This is the script behind the
`amazon-inventory-planning` skill's "Weekly FBA Inventory Overview".

## Setup

1. Copy the template and fill in the current run:

   ```bash
   cp tools/reshipment/config.TEMPLATE.json tools/reshipment/config.json
   ```

   `config.json` is gitignored. It holds run-specific local file paths and a `profile_key` for each account. Stable planning inputs are loaded from the shared team-vault profile and must not be copied into this config.

2. Download the same-day reports into your `downloads_dir` (default `~/Downloads`) and point each
   client's `fba` / `business` / `inventory` / `restock` field at the filename (relative to
   `downloads_dir`, or an absolute path). Use `null` for any report not available this run.

## Run

```bash
python3 tools/reshipment/generate_reshipment.py --config tools/reshipment/config.json
```

Validate profile resolution without reading reports or writing outputs:

```bash
python3 tools/reshipment/generate_reshipment.py --config tools/reshipment/config.json --check-config
```

Outputs are written under `<output_root>/output/<client key>/inventory/` (which is gitignored).

## Config fields

| Field | Meaning |
|-------|---------|
| `run_date` | Date stamp used in output filenames (`YYYY-MM-DD`). |
| `report_days` | Demand lookback window (default 30). |
| `downloads_dir` | Folder holding the downloaded reports (default `~/Downloads`). |
| `output_root` | Where the `output/` tree is created (default the repo root). |
| `clients[]` | One entry per brand-marketplace: `key`, canonical `profile_key`, `brand`, `market`, `country`, report paths, optional `restock_country`, and run-source `notes`. |

The resolved shared profile supplies target stock days, lead time, Amazon booking buffer, scaling multiplier, minimum monthly FBA threshold, and any product-level FBM exclusions. The tool refuses local duplicates of these fields. It records the profile source and resolved planning components in every manifest.

Requires `openpyxl` for the XLSX output (CSV/Slack/manifest are written even without it).

## Unattended run

`run_reshipment.py` does the whole thing for one Seller Central region: pulls
same-day inventory and demand for every roster account, plans it, and posts one
thread to #amazon-check. It is deterministic, so no model is involved.

```bash
tools/reshipment/run_reshipment.py --region us          # or europe, rest
tools/reshipment/run_reshipment.py --region us --dry-run   # plan, print, post nothing
```

`roster.json` is the single source of truth for which accounts are in scope and
which region reaches each one. Planning inputs stay in the team vault, so
changing a client's timing is a vault edit and needs no code change. AWD is
derived from the region rather than trusted per profile, because it is a US-only
program and requesting it elsewhere degrades the whole read.

Regions can run at the same time; accounts inside one region cannot, or they
fight over the same account picker. That is why the schedule is one job per
region.

The wizards-ai `reshipment` pass owns the schedule, the freshness guard, the
retry budget and the failure alerting. It replaced the older
`biweekly_preflight.sh`, which only posted a readiness list because at the time
the service account could not complete a pull.

## Slack posting

The commands below post a single account by hand. The unattended run above does
its own posting and does not use them.

Post each brand-market with a positive reshipment quantity as its own copy-ready thread through Wizards AI:

```bash
python3 tools/reshipment/post_slack_account.py \
  --channel <slack-channel-id> \
  --title "Acme Inventory Overview - United States" \
  --message-file "output/acme/inventory/2026-01-01_Inventory Overview_Acme_US_slack.txt"
```

The poster creates separate thread replies for:

1. `How it was calculated`, including the source and formula.
2. `Reshipment`, with the copy-ready ASIN list and total.
3. `Excess Inventory / Plan Sales`, when actionable.

Scope summaries and login blockers stay in the task summary.

Accounts with zero positive reshipment quantities do not get individual threads. Group them into one short parent post:

```text
*No reshipment needed for:*
• Brand 1 Market
• Brand 2 Market
```

Do not include blocked, incomplete, excluded, or unverified accounts in that list.

Use the grouped poster so line breaks are preserved:

```bash
python3 tools/reshipment/post_slack_no_reshipment.py \
  --channel <slack-channel-id> \
  --brand "Brand 1 US" \
  --brand "Brand 2 DE"
```

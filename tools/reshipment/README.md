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

   `config.json` is gitignored. It holds client names and local file paths and must stay local.

2. Download the same-day reports into your `downloads_dir` (default `~/Downloads`) and point each
   client's `fba` / `business` / `inventory` / `restock` field at the filename (relative to
   `downloads_dir`, or an absolute path). Use `null` for any report not available this run.

## Run

```bash
python3 tools/reshipment/generate_reshipment.py --config tools/reshipment/config.json
```

Outputs are written under `<output_root>/output/<client key>/inventory/` (which is gitignored).

## Config fields

| Field | Meaning |
|-------|---------|
| `run_date` | Date stamp used in output filenames (`YYYY-MM-DD`). |
| `report_days` | Demand lookback window (default 30). |
| `target_days` | Coverage target the reshipment quantity aims for (default 66 = 45 + 7 + 14). |
| `multiplier` | Demand multiplier, e.g. a Prime Day uplift (default 1.2). |
| `downloads_dir` | Folder holding the downloaded reports (default `~/Downloads`). |
| `output_root` | Where the `output/` tree is created (default the repo root). |
| `clients[]` | One entry per brand-marketplace: `key`, `brand`, `market`, `country`, report paths, optional per-account `target_days` / `multiplier`, optional `restock_country`, and `notes`. |
| `clients[].fba_exclude_patterns` | Optional case-insensitive regular expressions for products that must remain FBM. Matching rows receive zero FBA reshipment units and are labeled in `FBA Eligibility`. |
| `clients[].fba_exclude_asins` | Optional exact ASIN denylist for products that must remain FBM. Use this when report titles can omit bundle or pack-count wording. Exact ASIN exclusions take precedence over report text. |

Requires `openpyxl` for the XLSX output (CSV/Slack/manifest are written even without it).

## Slack posting

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

Scope summaries and login blockers stay in the Codex task.

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

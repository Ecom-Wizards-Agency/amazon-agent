# Reshipment / Weekly FBA Inventory Overview

Builds per-account reshipment + excess-inventory workbooks (CSV, XLSX, Slack staging text,
and a JSON manifest) from same-day Seller Central reports. This is the script behind the
`amazon-inventory-planning` skill's "Weekly FBA Inventory Overview".

## Setup

1. Copy the template and fill in the current run:

   ```bash
   cp tools/reshipment/config.TEMPLATE.json tools/reshipment/config.json
   ```

   `config.json` is gitignored — it holds client names and local file paths and must stay local.

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
| `clients[]` | One entry per brand-marketplace: `key`, `brand`, `market`, `country`, report paths, optional `restock_country`, and `notes`. |

Requires `openpyxl` for the XLSX output (CSV/Slack/manifest are written even without it).

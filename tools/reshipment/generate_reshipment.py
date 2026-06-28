#!/usr/bin/env python3
"""Generate FBA reshipment / inventory-overview workbooks from same-day Seller Central reports.

Client list, run date, and input paths are read from a JSON config (default:
`tools/reshipment/config.json`, which is gitignored). Copy `config.TEMPLATE.json`
to `config.json` and fill in the current run before running:

    python3 tools/reshipment/generate_reshipment.py --config tools/reshipment/config.json

Outputs land under `<output_root>/output/<client key>/inventory/`.
"""
import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
except Exception:
    Workbook = None


# Repo root = two levels up from this file (tools/reshipment/generate_reshipment.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config.json"


def load_config(config_path):
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    cfg.setdefault("report_days", 30)
    cfg.setdefault("target_days", 45 + 7 + 14)
    cfg.setdefault("multiplier", 1.2)
    cfg.setdefault("downloads_dir", "~/Downloads")
    cfg.setdefault("output_root", str(REPO_ROOT))
    cfg["downloads"] = Path(cfg["downloads_dir"]).expanduser()
    cfg["output_root"] = Path(cfg["output_root"]).expanduser()

    def resolve(value):
        if not value:
            return None
        p = Path(value).expanduser()
        return p if p.is_absolute() else cfg["downloads"] / value

    for client in cfg.get("clients", []):
        for field in ("fba", "business", "inventory", "restock"):
            client[field] = resolve(client.get(field))
    return cfg


def n(value):
    if value is None:
        return 0
    text = str(value).strip().replace(",", "").replace("$", "").replace("€", "").replace("%", "")
    if not text or text == "--":
        return 0
    try:
        return float(text)
    except ValueError:
        return 0


def i(value):
    return int(round(n(value)))


def short(text, limit=66):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def read_rows(path):
    if not path or not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delimiter = "\t" if "\t" in sample and sample.count("\t") > sample.count(",") else ","
        return list(csv.DictReader(fh, delimiter=delimiter))


def add_item(items, asin, **updates):
    if not asin:
        return
    item = items[asin]
    item["asin"] = asin
    for key, value in updates.items():
        if value in ("", None):
            continue
        if key in {"title", "sku"}:
            item.setdefault(key, value)
        elif key == "sources":
            item.setdefault("sources", set()).update(value)
        else:
            item[key] = item.get(key, 0) + value


def calculate(client, cfg):
    report_days = cfg["report_days"]
    target_days = cfg["target_days"]
    multiplier = cfg["multiplier"]
    run_date = cfg["run_date"]
    output_root = cfg["output_root"]

    items = defaultdict(dict)
    source_files = []

    for row in read_rows(client["business"]):
        asin = row.get("(Child) ASIN") or row.get("ASIN")
        add_item(
            items,
            asin,
            title=row.get("Title"),
            business_units=i(row.get("Units Ordered")),
            sources={"business"},
        )
    if client["business"] and client["business"].exists():
        source_files.append(str(client["business"]))

    for row in read_rows(client["fba"]):
        asin = row.get("asin")
        add_item(
            items,
            asin,
            sku=row.get("sku"),
            title=row.get("product-name"),
            available=i(row.get("available")),
            inbound=i(row.get("inbound-quantity")),
            reserved=i(row.get("Total Reserved Quantity")),
            unfulfillable=i(row.get("unfulfillable-quantity")),
            fba_units_30=i(row.get("units-shipped-t30")),
            fba_units_7=i(row.get("units-shipped-t7")),
            estimated_excess=i(row.get("estimated-excess-quantity")),
            days_of_supply=i(row.get("days-of-supply")),
            sources={"fba"},
        )
    if client["fba"] and client["fba"].exists():
        source_files.append(str(client["fba"]))

    for row in read_rows(client["restock"]):
        if client.get("restock_country") and row.get("Country") != client["restock_country"]:
            continue
        asin = row.get("ASIN")
        add_item(
            items,
            asin,
            sku=row.get("Merchant SKU"),
            title=row.get("Product Name"),
            restock_units_30=i(row.get("Units Sold Last 30 Days")),
            restock_total=i(row.get("Total Units")),
            restock_inbound=i(row.get("Inbound")),
            restock_available=i(row.get("Available")),
            restock_fc_transfer=i(row.get("FC transfer")),
            restock_fc_processing=i(row.get("FC Processing")),
            restock_customer_order=i(row.get("Customer Order")),
            unfulfillable=i(row.get("Unfulfillable")),
            sources={"restock"},
        )
    if client["restock"] and client["restock"].exists():
        source_files.append(str(client["restock"]))

    for row in read_rows(client["inventory"]):
        asin = row.get("asin")
        add_item(items, asin, sku=row.get("sku"), price=n(row.get("price")), sources={"inventory"})
    if client["inventory"] and client["inventory"].exists():
        source_files.append(str(client["inventory"]))

    rows = []
    for asin, item in sorted(items.items()):
        demand = item.get("business_units") or item.get("fba_units_30") or item.get("restock_units_30") or 0
        demand_source = "Business Report" if item.get("business_units") else ("FBA Inventory" if item.get("fba_units_30") else "Restock Report")
        available = max(item.get("available", 0), item.get("restock_available", 0))
        inbound = max(item.get("inbound", 0), item.get("restock_inbound", 0))
        reserved = max(
            item.get("reserved", 0),
            item.get("restock_fc_transfer", 0) + item.get("restock_fc_processing", 0) + item.get("restock_customer_order", 0),
        )
        required = demand / report_days * multiplier * target_days
        reship = int(math.ceil(max(0, required - available - inbound - reserved)))
        excess = item.get("estimated_excess", 0)
        if not excess and demand > 0 and available > (demand / report_days * 120):
            excess = int(max(0, available - demand / report_days * 90))
        rows.append(
            {
                "ASIN": asin,
                "SKU": item.get("sku", ""),
                "Product Name": item.get("title", ""),
                "Demand 30d": demand,
                "Demand Source": demand_source,
                "Available": available,
                "Inbound": inbound,
                "Reserved": reserved,
                "Unfulfillable": item.get("unfulfillable", 0),
                f"Required Units ({target_days}d x {multiplier})": round(required, 1),
                "Reshipment Units": reship,
                "Estimated Excess Units": excess,
                "Days of Supply": item.get("days_of_supply", ""),
                "FBA Units 7d": item.get("fba_units_7", 0),
                "FBA Units 30d": item.get("fba_units_30", 0),
                "Restock Units 30d": item.get("restock_units_30", 0),
            }
        )

    rows.sort(key=lambda r: r["Reshipment Units"], reverse=True)
    out_dir = output_root / "output" / client["key"] / "inventory"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{run_date}_Inventory Overview_{client['brand']}_{client['market']}"
    csv_path = out_dir / f"{stem}.csv"
    xlsx_path = out_dir / f"{stem}.xlsx"
    slack_path = out_dir / f"{stem}_slack.txt"
    json_path = out_dir / f"{stem}_manifest.json"

    fields = list(rows[0].keys()) if rows else ["ASIN"]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    if Workbook:
        wb = Workbook()
        ws = wb.active
        ws.title = "Inventory Overview"
        ws.append(fields)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="D9EAF7")
        for row in rows:
            ws.append([row[k] for k in fields])
        send = wb.create_sheet("Reshipment")
        send.append(fields)
        for row in [r for r in rows if r["Reshipment Units"] > 0]:
            send.append([row[k] for k in fields])
        excess = wb.create_sheet("Excess Inventory")
        excess.append(fields)
        for row in [r for r in rows if r["Estimated Excess Units"] > 0]:
            excess.append([row[k] for k in fields])
        for sheet in wb.worksheets:
            sheet.freeze_panes = "A2"
            for col in sheet.columns:
                letter = col[0].column_letter
                sheet.column_dimensions[letter].width = min(48, max(12, max(len(str(c.value or "")) for c in col[:80]) + 2))
        wb.save(xlsx_path)

    send_rows = [r for r in rows if r["Reshipment Units"] > 0]
    excess_rows = [r for r in rows if r["Estimated Excess Units"] > 0]
    parts = [
        f"{client['brand']} Inventory Overview - {client['country']}",
        "",
        f"Source: {client['notes']} Demand multiplier: {multiplier}x. Output saved: `{csv_path.name}` / `{xlsx_path.name}`.",
    ]
    if send_rows:
        parts.extend(["", "**Reshipment**"])
        for row in send_rows[:30]:
            parts.append(
                f"`{row['ASIN']}` {short(row['Product Name'])} - {row['Reshipment Units']:,} units needed | Available: {row['Available']:,} | Inbound: {row['Inbound']:,} | Reserved: {row['Reserved']:,}"
            )
        if len(send_rows) > 30:
            parts.append(f"Plus {len(send_rows) - 30} more low-volume rows in the workbook.")
        parts.append(f"Total: {sum(r['Reshipment Units'] for r in send_rows):,} units")
    else:
        parts.extend(["", "**Reshipment**", "No positive reshipment quantities from today’s source data."])
    if excess_rows:
        parts.extend(["", "**Excess Inventory / Plan Sales**"])
        for row in excess_rows[:20]:
            parts.append(
                f"`{row['ASIN']}` {short(row['Product Name'])} - {row['Estimated Excess Units']:,} excess units | Available: {row['Available']:,} | 30d demand: {row['Demand 30d']:,}"
            )
        if len(excess_rows) > 20:
            parts.append(f"Plus {len(excess_rows) - 20} more excess rows in the workbook.")
        parts.append(f"Total: {sum(r['Estimated Excess Units'] for r in excess_rows):,} excess units")
    slack_path.write_text("\n".join(parts) + "\n", encoding="utf-8")

    manifest = {
        "account": client["key"],
        "date": run_date,
        "sources": source_files,
        "csv": str(csv_path),
        "xlsx": str(xlsx_path),
        "slack": str(slack_path),
        "sendRows": len(send_rows),
        "sendUnits": sum(r["Reshipment Units"] for r in send_rows),
        "excessRows": len(excess_rows),
        "excessUnits": sum(r["Estimated Excess Units"] for r in excess_rows),
        "notes": client["notes"],
    }
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Generate FBA reshipment / inventory-overview workbooks.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to the run config JSON (default: tools/reshipment/config.json).")
    args = parser.parse_args()

    cfg = load_config(args.config)
    manifests = [calculate(client, cfg) for client in cfg.get("clients", [])]
    bundle = cfg["output_root"] / "output" / f"reshipment-plans-{cfg['run_date']}" / "summary.json"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    bundle.write_text(json.dumps(manifests, indent=2), encoding="utf-8")
    print(json.dumps(manifests, indent=2))


if __name__ == "__main__":
    main()

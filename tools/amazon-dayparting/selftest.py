#!/usr/bin/env python3
"""Regression checks for the deterministic dayparting analyzer."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from analyze_dayparting import DaypartingError, analyze_file  # noqa: E402


HEADERS = [
    "Start Date", "End Date", "Portfolio name", "Currency", "Campaign Name", "Status",
    "Start Time", "Impressions", "Clicks", "CTR", "Spend", "CPC", "Orders", "ACOS", "ROAS",
    "7 Day Total Sales",
]


def write_fixture(path: Path, mixed_currency: bool = False) -> None:
    start = date(2026, 6, 1)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        for day_offset in range(21):
            current = start + timedelta(days=day_offset)
            for hour in range(24):
                sales = 90.0 if hour >= 18 else 30.0
                currency = "EUR" if mixed_currency and day_offset == 0 and hour == 0 else "USD"
                writer.writerow([
                    current.strftime("%m/%d/%Y"), current.strftime("%m/%d/%Y"), "Portfolio", currency,
                    "Synthetic SP Campaign", "ENABLED", f"{hour:02d}:00", 3000, 30, 0.01, "$15.00",
                    0.5, 3, 0.5, 2.0, sales,
                ])


def require(label: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{label}: {detail}")
    print(f"PASS: {label}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="amazon-dayparting-selftest-") as tmp:
        root = Path(tmp)
        source = root / "hourly.csv"
        output = root / "out"
        write_fixture(source)
        summary = analyze_file(source, output, "America/New_York")
        require("two recent dates are excluded", summary["distinct_dates"] == 19, summary)
        require("all output artifacts exist", all(
            (output / name).exists() for name in
            ("summary.json", "by_day.csv", "by_hour.csv", "by_4hour.csv", "grid.csv",
             "adlabs_grid.tsv", "adlabs_rules.json")
        ))
        require("recommendations are available", summary["recommendations_available"] is True, summary)
        require("trusted grid cells exist", summary["trusted_grid_cells"] > 0, summary)
        require("best trusted block is the evening window",
                summary["best_trusted_4hour_window"]["window"] in ("20-23", "16-19"), summary)
        stored = json.loads((output / "summary.json").read_text())
        require("summary round-trips", stored["settled_rows"] == summary["settled_rows"])

        with (output / "grid.csv").open(newline="") as handle:
            grid_rows = list(csv.DictReader(handle))
        require("grid contains exactly 168 cells", len(grid_rows) == 168, len(grid_rows))
        evening = [row for row in grid_rows if int(row["hour"]) >= 18 and row["suggested_change_pct"]]
        require("higher-RPC evening cells receive positive suggestions", all(
            int(row["suggested_change_pct"]) > 0 for row in evening
        ), evening[:3])

        mixed = root / "mixed.csv"
        write_fixture(mixed, mixed_currency=True)
        try:
            analyze_file(mixed, root / "mixed-out", "America/New_York")
        except DaypartingError as exc:
            require("mixed currencies fail closed", "mixed currencies" in str(exc), exc)
        else:
            raise AssertionError("mixed currencies were accepted")
    print("Dayparting selftest: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

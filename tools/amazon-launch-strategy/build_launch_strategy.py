#!/usr/bin/env python3
"""Preflight, preview, and build Amazon launch strategy deliverables."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from launch_model import build_model, validate_config


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_node(explicit: str | None) -> str:
    candidates = [
        explicit,
        os.environ.get("AMAZON_LAUNCH_NODE"),
        shutil.which("node"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise RuntimeError("Node.js was not found. Pass --node, set AMAZON_LAUNCH_NODE, "
                       "or put node on PATH.")


def print_preflight(result: dict):
    print(f"PREFLIGHT: {result['status']}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    for item in result["missing"]:
        print(f"OPEN: {item['label']} [{item['field']}]")


def preview_payload(model: dict) -> dict:
    return {
        "status": model["validation"]["status"],
        "open_confirmations": [item["label"] for item in model["validation"]["missing"]],
        "scenarios": model["scenario_summary"],
        "months": model["month_summary"],
        "stock": model["stock_summary"],
        "pricing": model["pricing_summary"],
        "review_policy": model["review_policy"],
        "budget_cap_breaches": model["cap_breaches"],
        "commercial": model.get("commercial"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--build", action="store_true")
    parser.add_argument("--node", help="Path to the Codex workspace dependency Node binary")
    args = parser.parse_args()

    config = load_config(args.config.resolve())
    validation = validate_config(config)
    if args.preflight:
        print_preflight(validation)
        return 1 if validation["errors"] else 0
    if validation["errors"]:
        print_preflight(validation)
        return 1

    model = build_model(config)
    if args.preview:
        print(json.dumps(preview_payload(model), indent=2))
        return 0

    output_dir = Path(config["client"]["output_dir"]).expanduser().resolve()
    work_dir = output_dir / "_work"
    preview_dir = work_dir / "workbook-previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    stem = config["client"].get("file_stem") or f"{config['client']['brand']}_Amazon_90-Day_Launch_Strategy"
    model_path = work_dir / f"{stem}.model.json"
    docx_path = output_dir / f"{stem}.docx"
    xlsx_path = output_dir / f"{stem}.xlsx"
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    from build_document import build_document

    build_document(model, docx_path)

    node = resolve_node(args.node)
    workbook_builder = Path(__file__).with_name("build_workbook.mjs")
    subprocess.run([node, str(workbook_builder), str(model_path), str(xlsx_path), str(preview_dir)], check=True)
    print(json.dumps({
        "status": model["validation"]["status"],
        "docx": str(docx_path),
        "xlsx": str(xlsx_path),
        "model": str(model_path),
        "workbook_previews": str(preview_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

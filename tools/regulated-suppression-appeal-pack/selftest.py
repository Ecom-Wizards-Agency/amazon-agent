#!/usr/bin/env python3
"""Regression tests for the regulated suppression appeal pack utility."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from appeal_pack import MODULES, scaffold, validate_pack


def base_manifest() -> dict:
    return {
        "client_slug": "example-client",
        "case_slug": "synthetic-device-review",
        "case_date": "2026-07-23",
        "marketplace": "Amazon.com US",
        "issue_type": "device_or_application_tool",
        "status": "Draft",
        "affected_products": [
            {"asin": "EXAMPLE-ASIN-01", "skus": ["EXAMPLE-SKU-01"]},
            {"asin": "EXAMPLE-ASIN-02", "skus": ["EXAMPLE-SKU-02"]},
        ],
        "claims": [
            {
                "id": "C-001",
                "statement": "The tested component maps to both example products.",
                "material": True,
                "evidence": ["evidence/example-test-record.pdf"],
                "verified": True,
            }
        ],
        "consistency_checks": [
            {
                "subject": "listing, packaging, and manual intended use",
                "status": "consistent",
                "evidence": ["evidence/example-consistency-record.pdf"],
            }
        ],
        "catalog_correction": {
            "status": "processed",
            "submitted_skus": ["EXAMPLE-SKU-01", "EXAMPLE-SKU-02"],
            "processing_summary": "evidence/example-processing-summary.xlsx",
            "post_update_verification": None,
        },
        "victor_signoff": {"approved": False, "approved_at": None, "notes": None},
        "modules": {
            module: {
                "required": module
                in {
                    "01-appeal",
                    "02-technical-evidence-and-claim-register",
                    "04-catalog-correction-and-processing-proof",
                    "09-evidence-index",
                    "10-submission-checklist",
                },
                "files": [],
            }
            for module in MODULES
        },
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        manifest_path = root / "manifest.json"
        manifest = base_manifest()
        write_json(manifest_path, manifest)
        pack_dir = scaffold(manifest_path, root / "output")

        report = validate_pack(pack_dir)
        assert any("Required module has no declared files" in item for item in report.errors)
        assert any("missing evidence" in item for item in report.errors)
        assert any("missing processing summary" in item for item in report.errors)

        evidence = pack_dir / "evidence"
        (evidence / "example-test-record.pdf").write_bytes(b"%PDF-1.4\n")
        (evidence / "example-consistency-record.pdf").write_bytes(b"%PDF-1.4\n")
        (evidence / "example-processing-summary.xlsx").write_bytes(b"example")
        for module, record in manifest["modules"].items():
            if record["required"]:
                relative = f"{module}/completed.txt"
                (pack_dir / relative).write_text("Completed and reviewed.\n", encoding="utf-8")
                record["files"] = [relative]
        write_json(pack_dir / "00-case-manifest.json", manifest)
        report = validate_pack(pack_dir)
        assert report.passed, report.errors

        manifest["status"] = "Approved for manual submission"
        write_json(pack_dir / "00-case-manifest.json", manifest)
        report = validate_pack(pack_dir)
        assert any("requires Victor's approval" in item for item in report.errors)

        manifest["victor_signoff"] = {
            "approved": True,
            "approved_at": "2026-07-23T12:00:00+09:00",
            "notes": "Synthetic test approval.",
        }
        write_json(pack_dir / "00-case-manifest.json", manifest)
        report = validate_pack(pack_dir)
        assert report.passed, report.errors

        manifest["claims"][0]["verified"] = False
        write_json(pack_dir / "00-case-manifest.json", manifest)
        report = validate_pack(pack_dir)
        assert any("not verified" in item for item in report.errors)

        manifest = base_manifest()
        manifest["issue_type"] = "supplement"
        manifest["catalog_correction"]["submitted_skus"].append("UNRELATED-SKU")
        write_json(manifest_path, manifest)
        try:
            scaffold(manifest_path, root / "supplement-output")
        except ValueError as exc:
            assert "unrelated SKUs" in str(exc)
        else:
            raise AssertionError("Unrelated supplement SKU was not rejected")

        manifest = base_manifest()
        manifest["issue_type"] = "cosmetic_or_serum"
        manifest["consistency_checks"][0]["status"] = "conflict"
        write_json(manifest_path, manifest)
        cosmetic_pack = scaffold(manifest_path, root / "cosmetic-output")
        report = validate_pack(cosmetic_pack)
        assert any("Consistency check is unresolved" in item for item in report.errors)

    print("regulated-suppression-appeal-pack selftest: PASS")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""Synthetic contract tests for Amazon client onboarding manifests."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("onboarding_validator", HERE / "validate_run.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(validator)


def fixture() -> dict:
    manifest = json.loads((HERE / "manifest.TEMPLATE.json").read_text(encoding="utf-8"))
    manifest["run"]["mode"] = "SYNTHETIC"
    manifest["change_batch"]["fingerprint"] = validator.compute_fingerprint(manifest)
    return manifest


def validate(manifest: dict) -> list[str]:
    errors, _, _ = validator.validate_manifest(manifest)
    return errors


def refingerprint(manifest: dict) -> None:
    fingerprint = validator.compute_fingerprint(manifest)
    manifest["change_batch"]["fingerprint"] = fingerprint
    if manifest["run"]["state"] in {
        "approved",
        "executing",
        "verification_pending",
        "signed_off",
    }:
        manifest["change_batch"]["approved_fingerprint"] = fingerprint


def expect_valid(manifest: dict, label: str) -> None:
    errors = validate(manifest)
    if errors:
        raise AssertionError(f"expected valid {label}:\n" + "\n".join(errors))


def expect_invalid(manifest: dict, needle: str, label: str) -> None:
    errors = validate(manifest)
    if not any(needle in error for error in errors):
        raise AssertionError(
            f"expected {label} to fail with {needle!r}; got:\n" + "\n".join(errors)
        )


def signed_off_fixture() -> dict:
    manifest = fixture()
    run = manifest["run"]
    run.update(
        {
            "state": "signed_off",
            "overall_rag": "GREEN",
            "executor": run["task_owner"],
            "completed_at": "2026-08-10T16:00:00+05:00",
        }
    )
    fingerprint = validator.compute_fingerprint(manifest)
    batch = manifest["change_batch"]
    batch.update(
        {
            "fingerprint": fingerprint,
            "approved_fingerprint": fingerprint,
            "approved_by": run["task_owner"],
            "approved_at": "2026-08-10T09:00:00+05:00",
        }
    )
    for action in batch["actions"]:
        action.update(
            {
                "status": "VERIFIED",
                "executed_by": run["task_owner"],
                "executed_at": "2026-08-10T10:00:00+05:00",
                "verification_evidence_ref": f"evidence/{action['action_id']}.png",
            }
        )
    review = manifest["inventory_peer_review"]
    review.update(
        {
            "reviewed_by": run["inventory_reviewer"],
            "reviewed_at": "2026-08-10T13:00:00+05:00",
            "unfulfillable_setting_verified": True,
            "stranded_settings_verified": True,
            "return_destination_verified": True,
            "removal_orders_rechecked": True,
            "quantities_reconciled": True,
            "recall_notices_rechecked": True,
            "evidence_ref": "evidence/peer-review.md",
        }
    )
    manifest["monitoring_handoff"]["seven_day_watch"] = {
        "scheduled": True,
        "owner": run["task_owner"],
        "start_date": "2026-08-10",
        "end_date": "2026-08-16",
        "task_url": "https://app.notion.com/p/SYNTHETIC-WATCH-TASK",
    }
    return manifest


def run() -> None:
    template = json.loads((HERE / "manifest.TEMPLATE.json").read_text(encoding="utf-8"))
    expect_invalid(template, "TEMPLATE cannot enter approval", "template approval guard")

    base = fixture()
    expect_valid(base, "approval-pending assessment")

    unstamped = copy.deepcopy(base)
    unstamped["run"]["mode"] = "LIVE"
    unstamped["change_batch"]["fingerprint"] = ""
    with tempfile.TemporaryDirectory(prefix="amazon-onboarding-selftest-") as directory:
        path = Path(directory) / "manifest.json"
        validator.write_manifest(path, unstamped)
        completed = subprocess.run(
            [
                sys.executable,
                str(HERE / "validate_run.py"),
                "--manifest",
                str(path),
                "--stamp-fingerprint",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "fingerprint stamping failed:\n" + completed.stdout + completed.stderr
            )
        stamped = validator.load_manifest(path)
        expect_valid(stamped, "fingerprint-stamped manifest")

    signed_off = signed_off_fixture()
    expect_valid(signed_off, "GREEN signed-off run")

    case = copy.deepcopy(base)
    case["access"][2]["status"] = "BLOCKED"
    case["run"]["state"] = "access_blocked"
    case["run"]["overall_rag"] = "RED"
    case["checks"] = []
    case["promotion_inventory"] = None
    case["promotion_audiences"] = []
    case["change_batch"]["fingerprint"] = ""
    case["change_batch"]["actions"] = []
    expect_valid(case, "access-blocked preflight")

    case = copy.deepcopy(base)
    case["access"][2]["status"] = "BLOCKED"
    case["run"]["overall_rag"] = "RED"
    expect_invalid(case, "run.state must be access_blocked", "missing permission gate")

    for condition_type in ("ACTIVE_DISPOSAL", "RECALL_REQUIRED_REMOVAL"):
        case = copy.deepcopy(signed_off)
        case["red_conditions"].append(
            {
                "type": condition_type,
                "active": True,
                "details": f"Synthetic {condition_type.lower()}",
                "evidence_ref": f"evidence/{condition_type.lower()}.png",
            }
        )
        case["run"]["overall_rag"] = "RED"
        refingerprint(case)
        expect_invalid(
            case,
            "RED run cannot enter approval or execution",
            f"{condition_type} after safe settings were verified",
        )

    case = copy.deepcopy(signed_off)
    case["inventory_peer_review"]["reviewed_by"] = case["run"]["task_owner"]
    expect_invalid(case, "must differ from task owner/executor", "same-person inventory review")

    case = copy.deepcopy(signed_off)
    case["inventory_peer_review"]["return_destination_verified"] = False
    expect_invalid(case, "return_destination_verified must be true", "wrong return destination")

    case = copy.deepcopy(signed_off)
    case["inventory_peer_review"]["quantities_reconciled"] = False
    expect_invalid(case, "quantities_reconciled must be true", "unreconciled inventory")

    case = copy.deepcopy(signed_off)
    case["change_batch"]["actions"][0]["status"] = "EXECUTION_FAILED"
    case["run"]["overall_rag"] = "AMBER"
    expect_invalid(case, "signed_off requires verified, deferred, or rejected actions", "failed save")

    case = copy.deepcopy(base)
    case["scope"]["marketplace"] = ["DE", "FR"]
    expect_invalid(case, "scope.marketplace", "multi-market manifest")

    case = copy.deepcopy(base)
    case["promotion_audiences"][0]["proposal"] = None
    expect_invalid(case, "exactly one proposal or exclusion", "missing audience disposition")

    case = copy.deepcopy(base)
    case["promotion_inventory"]["live_eligible_audience_ids"].append("SECOND-LIVE-AUDIENCE")
    expect_invalid(case, "missing live eligible audiences", "missing live audience proposal")

    case = copy.deepcopy(base)
    case["scope"]["managed_asins"].append("B000000002")
    case["promotion_audiences"][0]["proposal"]["asin_exclusions"].append(
        {"asin": "B000000002", "reason": "Low stock"}
    )
    refingerprint(case)
    expect_valid(case, "unsafe ASIN excluded without blocking safe ASIN")

    for flag in ("in_stock", "featured_offer", "stacking_safe"):
        case = copy.deepcopy(base)
        case["promotion_audiences"][0]["proposal"]["asins"][0][flag] = False
        expect_invalid(case, f"{flag} must be true", f"unsafe ASIN {flag}")

    case = copy.deepcopy(base)
    case["promotion_audiences"][0]["proposal"]["asins"][0]["worst_case_discount_percent"] = 25
    expect_invalid(case, "worst_case_discount_percent must be <= 15", "promotion stacking")

    case = copy.deepcopy(base)
    case["promotion_audiences"][0]["proposal"]["budget_source"] = "APPROVED_CEILING"
    case["promotion_audiences"][0]["proposal"]["budget_amount"] = 150
    expect_invalid(case, "requires approved_budget_ceiling", "missing client budget ceiling")

    case = copy.deepcopy(base)
    case["promotion_audiences"][0]["proposal"]["duration_days"] = 60
    expect_invalid(case, "live maximum capped at 90", "shorter than live maximum duration")

    case = copy.deepcopy(base)
    case["checks"][0]["observed_value"] = "Changed after preview"
    expect_invalid(case, "change_batch.fingerprint: missing or stale", "stale fingerprint")

    case = copy.deepcopy(signed_off)
    case["monitoring_handoff"]["seven_day_watch"]["end_date"] = "2026-08-17"
    expect_invalid(case, "seven calendar days inclusive", "watch duration")

    print("[selftest] PASS: onboarding manifest state, safety, promotion, and signoff cases")


if __name__ == "__main__":
    run()

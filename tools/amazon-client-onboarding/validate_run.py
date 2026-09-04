#!/usr/bin/env python3
"""Validate and fingerprint an Amazon client onboarding run manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ACCESS_IDS = {
    "account_selector",
    "account_health",
    "inventory_settings",
    "removal_reports",
    "catalog",
    "brand_registry_analytics",
    "brand_tailored_promotions",
    "ads_console",
    "seller_reporting",
}

CHECK_IDS = {
    "account_identity",
    "account_health",
    "performance_notifications",
    "recall_product_safety",
    "listing_health",
    "automated_unfulfillable_settings",
    "automated_stranded_settings",
    "unfulfillable_inventory",
    "stranded_inventory",
    "removal_orders_90d",
    "removal_quantity_reconciliation",
    "catalog_offer_health",
    "variation_integrity",
    "brand_assets",
    "inventory_fulfillment",
    "shipment_exceptions",
    "fee_alerts",
    "returns_voc",
    "ads_readiness",
    "reporting_readiness",
    "monitoring_integrations",
    "promotion_stack",
    "btp_eligibility",
}

CRITICAL_CHECK_IDS = {
    "account_identity",
    "account_health",
    "recall_product_safety",
    "automated_unfulfillable_settings",
    "automated_stranded_settings",
    "unfulfillable_inventory",
    "stranded_inventory",
    "removal_orders_90d",
    "removal_quantity_reconciliation",
}

RESULT_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "NOT_APPLICABLE"}
RUN_STATES = {
    "access_blocked",
    "assessment_in_progress",
    "approval_pending",
    "approved",
    "executing",
    "verification_pending",
    "signed_off",
}
ACTION_STATUSES = {
    "STAGED",
    "APPROVED",
    "EXECUTED",
    "VERIFIED",
    "DEFERRED",
    "REJECTED",
    "EXECUTION_FAILED",
}


class ManifestError(ValueError):
    """Raised when a manifest cannot be loaded."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(str(exc)) from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be an object")
    return data


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_datetime(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: timestamp is required")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}: invalid ISO-8601 timestamp {value!r}")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label}: timestamp must include a timezone")
    return parsed


def parse_date(value: Any, label: str, errors: list[str]) -> date | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: date is required")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: invalid ISO date {value!r}")
        return None


def require_text(obj: dict[str, Any], key: str, label: str, errors: list[str]) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}.{key}: non-empty text is required")
        return ""
    return value.strip()


def unique_by_id(
    rows: Any,
    required_ids: set[str],
    label: str,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        errors.append(f"{label}: must be an array")
        return {}
    found: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{index}]: must be an object")
            continue
        row_id = require_text(row, "id", f"{label}[{index}]", errors)
        if not row_id:
            continue
        if row_id in found:
            errors.append(f"{label}: duplicate id {row_id!r}")
            continue
        found[row_id] = row
        status = row.get("status")
        if status not in RESULT_STATUSES:
            errors.append(f"{label}.{row_id}: invalid status {status!r}")
        parse_datetime(row.get("observed_at"), f"{label}.{row_id}.observed_at", errors)
        require_text(row, "evidence_ref", f"{label}.{row_id}", errors)
        if status == "WARN":
            follow_up = row.get("follow_up")
            if not isinstance(follow_up, dict):
                errors.append(f"{label}.{row_id}: WARN requires follow_up")
            else:
                require_text(follow_up, "owner", f"{label}.{row_id}.follow_up", errors)
                parse_date(follow_up.get("due_date"), f"{label}.{row_id}.follow_up.due_date", errors)
                require_text(follow_up, "task_url", f"{label}.{row_id}.follow_up", errors)
    missing = required_ids - set(found)
    extra = set(found) - required_ids
    if missing:
        errors.append(f"{label}: missing ids {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{label}: unknown ids {', '.join(sorted(extra))}")
    return found


def canonical_fingerprint_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    scope = manifest.get("scope", {})
    access = manifest.get("access", [])
    checks = manifest.get("checks", [])
    audiences = manifest.get("promotion_audiences", [])
    batch = manifest.get("change_batch", {})
    return {
        "schema_version": manifest.get("schema_version"),
        "scope": scope,
        "access": access,
        "checks": checks,
        "red_conditions": manifest.get("red_conditions", []),
        "promotion_inventory": manifest.get("promotion_inventory"),
        "promotion_audiences": audiences,
        "actions": [
            {
                key: action.get(key)
                for key in (
                    "action_id",
                    "category",
                    "before",
                    "after",
                    "risk",
                    "approval_required",
                )
            }
            for action in batch.get("actions", [])
            if isinstance(action, dict)
        ],
    }


def compute_fingerprint(manifest: dict[str, Any]) -> str:
    raw = json.dumps(
        canonical_fingerprint_payload(manifest),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def validate_promotions(manifest: dict[str, Any], errors: list[str]) -> None:
    state = manifest.get("run", {}).get("state")
    inventory = manifest.get("promotion_inventory")
    rows = manifest.get("promotion_audiences")
    if not isinstance(rows, list):
        errors.append("promotion_audiences: must be an array")
        return
    if state == "access_blocked":
        if inventory is not None:
            errors.append("promotion_inventory must be null when access is blocked")
        if rows:
            errors.append("promotion_audiences must be empty when access is blocked")
        return
    if not isinstance(inventory, dict):
        errors.append("promotion_inventory: must be an object")
        return
    parse_datetime(inventory.get("observed_at"), "promotion_inventory.observed_at", errors)
    require_text(inventory, "evidence_ref", "promotion_inventory", errors)
    live_ids = inventory.get("live_eligible_audience_ids")
    if not isinstance(live_ids, list) or not all(
        isinstance(value, str) and value.strip() for value in live_ids
    ):
        errors.append("promotion_inventory.live_eligible_audience_ids must be a text array")
        live_ids = []
    if len(live_ids) != len(set(live_ids)):
        errors.append("promotion_inventory.live_eligible_audience_ids must be unique")

    seen: set[str] = set()
    eligible_seen: set[str] = set()
    managed_asins = manifest.get("scope", {}).get("managed_asins", [])
    managed_asin_set = set(managed_asins) if isinstance(managed_asins, list) else set()
    for index, row in enumerate(rows):
        label = f"promotion_audiences[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: must be an object")
            continue
        audience_id = require_text(row, "audience_id", label, errors)
        require_text(row, "audience_name", label, errors)
        if audience_id in seen:
            errors.append(f"promotion_audiences: duplicate audience_id {audience_id!r}")
        seen.add(audience_id)
        eligibility = row.get("eligibility")
        if eligibility not in {"ELIGIBLE", "NOT_ELIGIBLE", "UNAVAILABLE"}:
            errors.append(f"{label}: invalid eligibility {eligibility!r}")
        if eligibility == "ELIGIBLE" and audience_id:
            eligible_seen.add(audience_id)
        parse_datetime(row.get("observed_at"), f"{label}.observed_at", errors)
        require_text(row, "evidence_ref", label, errors)
        proposal = row.get("proposal")
        exclusion = row.get("exclusion")
        if eligibility == "ELIGIBLE":
            if bool(proposal) == bool(exclusion):
                errors.append(f"{label}: eligible audience needs exactly one proposal or exclusion")
                continue
            if exclusion:
                if not isinstance(exclusion, dict):
                    errors.append(f"{label}.exclusion: must be an object")
                else:
                    require_text(exclusion, "reason", f"{label}.exclusion", errors)
                continue
            if not isinstance(proposal, dict):
                errors.append(f"{label}.proposal: must be an object")
                continue
            if proposal.get("discount_percent") != 15:
                errors.append(f"{label}.proposal: discount_percent must be 15")
            duration = proposal.get("duration_days")
            if not isinstance(duration, int) or duration < 1 or duration > 90:
                errors.append(f"{label}.proposal: duration_days must be 1..90")
            platform_max = proposal.get("platform_max_duration_days")
            if not isinstance(platform_max, int) or platform_max < 1:
                errors.append(f"{label}.proposal: platform_max_duration_days must be positive")
            elif isinstance(duration, int) and duration != min(platform_max, 90):
                errors.append(
                    f"{label}.proposal: duration_days must equal the live maximum capped at 90"
                )
            start = parse_date(proposal.get("start_date"), f"{label}.proposal.start_date", errors)
            if start and start.weekday() not in {0, 1, 2}:
                errors.append(f"{label}.proposal: start_date must be Monday, Tuesday, or Wednesday")
            if start and state in {"approved", "executing", "verification_pending", "signed_off"}:
                approved_value = manifest.get("change_batch", {}).get("approved_at")
                if isinstance(approved_value, str):
                    try:
                        approved_date = datetime.fromisoformat(
                            approved_value.replace("Z", "+00:00")
                        ).date()
                    except ValueError:
                        approved_date = None
                    if approved_date and start < approved_date:
                        errors.append(f"{label}.proposal: start_date cannot precede approval")
            budget_source = proposal.get("budget_source")
            if budget_source not in {"PLATFORM_MINIMUM", "APPROVED_CEILING"}:
                errors.append(f"{label}.proposal: invalid budget_source {budget_source!r}")
            budget = proposal.get("budget_amount")
            if not isinstance(budget, (int, float)) or budget <= 0:
                errors.append(f"{label}.proposal: budget_amount must be positive")
            platform_minimum = proposal.get("platform_minimum_budget")
            if not isinstance(platform_minimum, (int, float)) or platform_minimum <= 0:
                errors.append(f"{label}.proposal: platform_minimum_budget must be positive")
            elif isinstance(budget, (int, float)):
                if budget_source == "PLATFORM_MINIMUM" and budget != platform_minimum:
                    errors.append(
                        f"{label}.proposal: budget_amount must equal platform_minimum_budget"
                    )
                if budget < platform_minimum:
                    errors.append(f"{label}.proposal: budget_amount cannot be below the live minimum")
            ceiling = proposal.get("approved_budget_ceiling")
            if budget_source == "APPROVED_CEILING":
                if not isinstance(ceiling, (int, float)) or ceiling <= 0:
                    errors.append(
                        f"{label}.proposal: APPROVED_CEILING requires approved_budget_ceiling"
                    )
                elif isinstance(budget, (int, float)) and budget > ceiling:
                    errors.append(f"{label}.proposal: budget_amount exceeds approved_budget_ceiling")
            require_text(proposal, "currency", f"{label}.proposal", errors)
            asins = proposal.get("asins")
            if not isinstance(asins, list) or not asins:
                errors.append(f"{label}.proposal: at least one safe ASIN is required")
                continue
            asin_seen: set[str] = set()
            for asin_index, asin in enumerate(asins):
                asin_label = f"{label}.proposal.asins[{asin_index}]"
                if not isinstance(asin, dict):
                    errors.append(f"{asin_label}: must be an object")
                    continue
                asin_id = require_text(asin, "asin", asin_label, errors)
                if asin_id in asin_seen:
                    errors.append(f"{label}.proposal: duplicate ASIN {asin_id!r}")
                asin_seen.add(asin_id)
                for flag in (
                    "active",
                    "in_stock",
                    "economically_eligible",
                    "featured_offer",
                    "stacking_safe",
                ):
                    if asin.get(flag) is not True:
                        errors.append(f"{asin_label}: {flag} must be true for an included ASIN")
                worst_case = asin.get("worst_case_discount_percent")
                if not isinstance(worst_case, (int, float)) or worst_case > 15:
                    errors.append(f"{asin_label}: worst_case_discount_percent must be <= 15")
            exclusions = proposal.get("asin_exclusions")
            if not isinstance(exclusions, list):
                errors.append(f"{label}.proposal.asin_exclusions: must be an array")
                exclusions = []
            excluded_seen: set[str] = set()
            for exclusion_index, exclusion_row in enumerate(exclusions):
                exclusion_label = f"{label}.proposal.asin_exclusions[{exclusion_index}]"
                if not isinstance(exclusion_row, dict):
                    errors.append(f"{exclusion_label}: must be an object")
                    continue
                excluded_asin = require_text(exclusion_row, "asin", exclusion_label, errors)
                require_text(exclusion_row, "reason", exclusion_label, errors)
                if excluded_asin in excluded_seen:
                    errors.append(f"{label}.proposal: duplicate excluded ASIN {excluded_asin!r}")
                excluded_seen.add(excluded_asin)
            overlap = asin_seen & excluded_seen
            if overlap:
                errors.append(
                    f"{label}.proposal: ASINs cannot be both included and excluded: "
                    + ", ".join(sorted(overlap))
                )
            accounted = asin_seen | excluded_seen
            missing = managed_asin_set - accounted
            extra = accounted - managed_asin_set
            if missing:
                errors.append(
                    f"{label}.proposal: managed ASINs need inclusion or exclusion: "
                    + ", ".join(sorted(missing))
                )
            if extra:
                errors.append(
                    f"{label}.proposal: ASINs outside managed scope: "
                    + ", ".join(sorted(extra))
                )
        elif proposal:
            errors.append(f"{label}: ineligible/unavailable audience cannot have a proposal")

    missing_audiences = set(live_ids) - eligible_seen
    extra_audiences = eligible_seen - set(live_ids)
    if missing_audiences:
        errors.append(
            "promotion_audiences: missing live eligible audiences "
            + ", ".join(sorted(missing_audiences))
        )
    if extra_audiences:
        errors.append(
            "promotion_audiences: ELIGIBLE rows absent from live inventory "
            + ", ".join(sorted(extra_audiences))
        )


def validate_actions(
    manifest: dict[str, Any],
    fingerprint: str,
    errors: list[str],
) -> list[dict[str, Any]]:
    batch = manifest.get("change_batch")
    if not isinstance(batch, dict):
        errors.append("change_batch: must be an object")
        return []
    actions = batch.get("actions")
    if not isinstance(actions, list):
        errors.append("change_batch.actions: must be an array")
        return []
    seen: set[str] = set()
    valid_actions: list[dict[str, Any]] = []
    for index, action in enumerate(actions):
        label = f"change_batch.actions[{index}]"
        if not isinstance(action, dict):
            errors.append(f"{label}: must be an object")
            continue
        action_id = require_text(action, "action_id", label, errors)
        if action_id in seen:
            errors.append(f"change_batch.actions: duplicate action_id {action_id!r}")
        seen.add(action_id)
        for key in ("category", "before", "after", "risk"):
            require_text(action, key, label, errors)
        if action.get("approval_required") is not True:
            errors.append(f"{label}: approval_required must be true")
        status = action.get("status")
        if status not in ACTION_STATUSES:
            errors.append(f"{label}: invalid status {status!r}")
        if status in {"EXECUTED", "VERIFIED", "EXECUTION_FAILED"}:
            require_text(action, "executed_by", label, errors)
            parse_datetime(action.get("executed_at"), f"{label}.executed_at", errors)
        if status == "VERIFIED":
            require_text(action, "verification_evidence_ref", label, errors)
        if status == "DEFERRED":
            follow_up = action.get("follow_up")
            if not isinstance(follow_up, dict):
                errors.append(f"{label}: DEFERRED requires follow_up")
            else:
                require_text(follow_up, "owner", f"{label}.follow_up", errors)
                parse_date(follow_up.get("due_date"), f"{label}.follow_up.due_date", errors)
                require_text(follow_up, "task_url", f"{label}.follow_up", errors)
        valid_actions.append(action)

    state = manifest.get("run", {}).get("state")
    batch_fingerprint = batch.get("fingerprint")
    if state in {"approval_pending", "approved", "executing", "verification_pending", "signed_off"}:
        if batch_fingerprint != fingerprint:
            errors.append("change_batch.fingerprint: missing or stale")
    if state in {"approved", "executing", "verification_pending", "signed_off"}:
        if batch.get("approved_fingerprint") != fingerprint:
            errors.append("change_batch.approved_fingerprint: missing or stale")
        task_owner = manifest.get("run", {}).get("task_owner")
        if batch.get("approved_by") != task_owner:
            errors.append("change_batch.approved_by must equal run.task_owner")
        parse_datetime(batch.get("approved_at"), "change_batch.approved_at", errors)
    return valid_actions


def computed_rag(
    state: str,
    access: dict[str, dict[str, Any]],
    checks: dict[str, dict[str, Any]],
    red_conditions: list[Any],
    actions: list[dict[str, Any]],
) -> str:
    if any(row.get("status") in {"FAIL", "BLOCKED"} for row in access.values()):
        return "RED"
    if any(
        checks.get(check_id, {}).get("status") in {"FAIL", "BLOCKED"}
        for check_id in CRITICAL_CHECK_IDS
    ):
        return "RED"
    if any(isinstance(row, dict) and row.get("active") is True for row in red_conditions):
        return "RED"
    if state == "signed_off":
        if any(row.get("status") in {"WARN", "FAIL", "BLOCKED"} for row in checks.values()):
            return "AMBER"
        if any(action.get("status") not in {"VERIFIED", "DEFERRED", "REJECTED"} for action in actions):
            return "AMBER"
        return "GREEN"
    return "AMBER"


def validate_peer_and_monitoring(
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    run = manifest.get("run", {})
    if run.get("state") != "signed_off":
        return
    review = manifest.get("inventory_peer_review")
    if not isinstance(review, dict):
        errors.append("inventory_peer_review: must be an object")
    else:
        reviewer = require_text(review, "reviewed_by", "inventory_peer_review", errors)
        if reviewer and reviewer in {run.get("task_owner"), run.get("executor")}:
            errors.append("inventory_peer_review.reviewed_by must differ from task owner/executor")
        if reviewer and reviewer != run.get("inventory_reviewer"):
            errors.append("inventory_peer_review.reviewed_by must equal run.inventory_reviewer")
        parse_datetime(review.get("reviewed_at"), "inventory_peer_review.reviewed_at", errors)
        for flag in (
            "unfulfillable_setting_verified",
            "stranded_settings_verified",
            "return_destination_verified",
            "removal_orders_rechecked",
            "quantities_reconciled",
            "recall_notices_rechecked",
        ):
            if review.get(flag) is not True:
                errors.append(f"inventory_peer_review.{flag} must be true for signoff")
        require_text(review, "evidence_ref", "inventory_peer_review", errors)

    monitoring = manifest.get("monitoring_handoff")
    if not isinstance(monitoring, dict):
        errors.append("monitoring_handoff: must be an object")
        return
    watch = monitoring.get("seven_day_watch")
    if not isinstance(watch, dict) or watch.get("scheduled") is not True:
        errors.append("monitoring_handoff.seven_day_watch must be scheduled for signoff")
        return
    require_text(watch, "owner", "monitoring_handoff.seven_day_watch", errors)
    require_text(watch, "task_url", "monitoring_handoff.seven_day_watch", errors)
    start = parse_date(watch.get("start_date"), "monitoring_handoff.seven_day_watch.start_date", errors)
    end = parse_date(watch.get("end_date"), "monitoring_handoff.seven_day_watch.end_date", errors)
    if start and end and end != start + timedelta(days=6):
        errors.append("monitoring_handoff.seven_day_watch must cover seven calendar days inclusive")


def validate_manifest(manifest: dict[str, Any]) -> tuple[list[str], str, str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    run = manifest.get("run")
    if not isinstance(run, dict):
        errors.append("run: must be an object")
        run = {}
    run_id = require_text(run, "run_id", "run", errors)
    if run_id and not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{7,127}", run_id):
        errors.append("run.run_id: use 8..128 letters, digits, dots, underscores, or hyphens")
    state = run.get("state")
    if state not in RUN_STATES:
        errors.append(f"run.state: invalid value {state!r}")
        state = "assessment_in_progress"
    mode = run.get("mode")
    if mode not in {"TEMPLATE", "SYNTHETIC", "LIVE"}:
        errors.append(f"run.mode: invalid value {mode!r}")
    if mode == "TEMPLATE" and state in {
        "approval_pending",
        "approved",
        "executing",
        "verification_pending",
        "signed_off",
    }:
        errors.append("run.mode TEMPLATE cannot enter approval or execution")
    rag = run.get("overall_rag")
    if rag not in {"RED", "AMBER", "GREEN"}:
        errors.append(f"run.overall_rag: invalid value {rag!r}")
    task_owner = require_text(run, "task_owner", "run", errors)
    reviewer = require_text(run, "inventory_reviewer", "run", errors)
    if task_owner and reviewer and task_owner == reviewer:
        errors.append("run.inventory_reviewer must differ from run.task_owner")
    parse_datetime(run.get("started_at"), "run.started_at", errors)
    if state == "signed_off":
        parse_datetime(run.get("completed_at"), "run.completed_at", errors)

    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope: must be an object")
        scope = {}
    for key in (
        "client_name",
        "client_slug",
        "profile_key",
        "seller_account_label",
        "marketplace",
    ):
        require_text(scope, key, "scope", errors)
    if scope.get("fulfillment_model") not in {"FBA", "FBM", "MIXED"}:
        errors.append("scope.fulfillment_model must be FBA, FBM, or MIXED")
    brands = scope.get("managed_brands")
    if not isinstance(brands, list) or not brands or not all(isinstance(v, str) and v.strip() for v in brands):
        errors.append("scope.managed_brands must contain at least one brand")
    access = unique_by_id(manifest.get("access"), ACCESS_IDS, "access", errors)
    raw_checks = manifest.get("checks")
    if state == "access_blocked":
        if raw_checks != []:
            errors.append("checks must be empty when access is blocked; do not start Day 0")
        checks = {}
    else:
        checks = unique_by_id(raw_checks, CHECK_IDS, "checks", errors)

    if scope.get("fulfillment_model") in {"FBA", "MIXED"}:
        for surface in ("inventory_settings", "removal_reports"):
            if access.get(surface, {}).get("status") == "NOT_APPLICABLE":
                errors.append(f"access.{surface}: cannot be NOT_APPLICABLE for FBA/MIXED")

    access_blocked = any(row.get("status") in {"FAIL", "BLOCKED"} for row in access.values())
    if access_blocked and state != "access_blocked":
        errors.append("run.state must be access_blocked when required access fails")
    if not access_blocked and state == "access_blocked":
        errors.append("run.state access_blocked requires a failed/blocked access surface")

    if not isinstance(scope.get("managed_asins"), list):
        errors.append("scope.managed_asins must be an array")
    elif not scope.get("managed_asins"):
        errors.append("scope.managed_asins must contain the explicit managed scope")
    elif len(scope["managed_asins"]) != len(set(scope["managed_asins"])):
        errors.append("scope.managed_asins must be unique")

    red_conditions = manifest.get("red_conditions")
    if not isinstance(red_conditions, list):
        errors.append("red_conditions: must be an array")
        red_conditions = []
    for index, condition in enumerate(red_conditions):
        if not isinstance(condition, dict):
            errors.append(f"red_conditions[{index}]: must be an object")
            continue
        require_text(condition, "type", f"red_conditions[{index}]", errors)
        require_text(condition, "details", f"red_conditions[{index}]", errors)
        if condition.get("active") is not True:
            errors.append(f"red_conditions[{index}].active must be true; remove resolved conditions")
        require_text(condition, "evidence_ref", f"red_conditions[{index}]", errors)

    validate_promotions(manifest, errors)
    fingerprint = compute_fingerprint(manifest)
    actions = validate_actions(manifest, fingerprint, errors)
    expected_rag = computed_rag(state, access, checks, red_conditions, actions)
    if rag != expected_rag:
        errors.append(f"run.overall_rag must be {expected_rag} for the current manifest")
    if expected_rag == "RED" and state in {
        "approval_pending",
        "approved",
        "executing",
        "verification_pending",
        "signed_off",
    }:
        errors.append("RED run cannot enter approval or execution")
    if rag == "GREEN" and state != "signed_off":
        errors.append("GREEN is allowed only for signed_off runs")
    if state == "signed_off" and any(
        action.get("status") not in {"VERIFIED", "DEFERRED", "REJECTED"}
        for action in actions
    ):
        errors.append("signed_off requires verified, deferred, or rejected actions")
    validate_peer_and_monitoring(manifest, errors)
    return errors, fingerprint, expected_rag


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    parser.add_argument(
        "--stamp-fingerprint",
        action="store_true",
        help="write the computed fingerprint when an approval-pending manifest is otherwise valid",
    )
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except ManifestError as exc:
        print(f"[onboarding-validator] ERROR: {exc}", file=sys.stderr)
        return 2
    errors, fingerprint, expected_rag = validate_manifest(manifest)
    if args.stamp_fingerprint:
        allowed_errors = {"change_batch.fingerprint: missing or stale"}
        if manifest.get("run", {}).get("state") != "approval_pending":
            errors.append("--stamp-fingerprint requires run.state approval_pending")
        elif manifest.get("run", {}).get("mode") != "LIVE":
            errors.append("--stamp-fingerprint requires run.mode LIVE")
        elif set(errors) - allowed_errors:
            errors.append("--stamp-fingerprint refused because other validation problems remain")
        else:
            manifest["change_batch"]["fingerprint"] = fingerprint
            write_manifest(args.manifest, manifest)
            errors, fingerprint, expected_rag = validate_manifest(manifest)
    result = {
        "valid": not errors,
        "fingerprint": fingerprint,
        "expected_rag": expected_rag,
        "operational_approval_allowed": (
            not errors
            and manifest.get("run", {}).get("mode") == "LIVE"
            and manifest.get("run", {}).get("state") == "approval_pending"
        ),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Fingerprint: {fingerprint}")
        print(f"Expected RAG: {expected_rag}")
        print(
            "Operational approval: "
            + ("ALLOWED" if result["operational_approval_allowed"] else "NOT ALLOWED")
        )
        if errors:
            print(f"Validation: FAIL ({len(errors)} problem(s))")
            for error in errors:
                print(f"- {error}")
        else:
            print("Validation: PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

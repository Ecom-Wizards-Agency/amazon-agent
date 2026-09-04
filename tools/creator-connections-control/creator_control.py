#!/usr/bin/env python3
"""Deterministic identity, gate, queue, and MCF preflight controls.

The tool has no Amazon, Google, browser, Slack, or network dependency. It emits
JSON evidence so an executor can prove it acted on one resolved creator record.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class Hold(Exception):
    """A controlled stop. The caller must not continue the external action."""


def read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = handle.name
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, target)
        temporary_path = None
        try:
            directory_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            # Directory fsync is not available on every supported platform.
            pass
    finally:
        if temporary_path and Path(temporary_path).exists():
            os.unlink(temporary_path)


@contextmanager
def registry_lock(path: str, timeout_seconds: float = 5.0):
    """Hold a cross-process lock for one registry mutation."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(target.name + ".lock")
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise Hold(f"Registry is locked by another process: {lock_path}")
            time.sleep(0.02)
    try:
        os.write(descriptor, f"pid={os.getpid()} acquired={datetime.now(timezone.utc).isoformat()}\n".encode("utf-8"))
        os.fsync(descriptor)
        yield
    finally:
        os.close(descriptor)
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass


def mutate_registry(path: str, operation) -> Any:
    """Reread, mutate, and atomically persist a registry under one lock."""
    with registry_lock(path):
        registry = load_registry(path)
        before = json.dumps(registry, sort_keys=True, separators=(",", ":"))
        try:
            result = operation(registry)
        except Hold:
            after = json.dumps(registry, sort_keys=True, separators=(",", ":"))
            if after != before:
                write_json(path, registry)
            raise
        after = json.dumps(registry, sort_keys=True, separators=(",", ":"))
        if after != before:
            write_json(path, registry)
        return result


def normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def normalize_email(value: Any) -> str:
    return normalized(value)


def normalize_phone(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def normalize_address(record: dict[str, Any]) -> str:
    address = record.get("address") or {}
    required = ("street", "city", "state", "postal_code")
    if not all(normalized(address.get(part)) for part in required):
        return ""
    return "|".join(
        normalized(address.get(part))
        for part in (*required, "country")
    )


def canonical_storefront(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", parsed.path.rstrip("/").lower())
    return host + path


def get_secret(name: str) -> bytes:
    secret = os.environ.get(name, "")
    if len(secret) < 16:
        raise Hold(f"Configuration error: set {name} to a local secret of at least 16 characters.")
    return secret.encode("utf-8")


def fingerprint(secret: bytes, label: str, value: str) -> str:
    if not value:
        return ""
    payload = f"{label}:{value}".encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def record_fingerprints(record: dict[str, Any], secret: bytes) -> dict[str, str]:
    return {
        "storefront_key": fingerprint(secret, "storefront", canonical_storefront(record.get("storefront_url"))),
        "thread_key": fingerprint(secret, "thread", normalized(record.get("thread_key"))),
        "full_name_fp": fingerprint(secret, "full_name", normalized(record.get("full_name"))),
        "email_fp": fingerprint(secret, "email", normalize_email(record.get("email"))),
        "phone_fp": fingerprint(secret, "phone", normalize_phone(record.get("phone"))),
        "address_fp": fingerprint(secret, "address", normalize_address(record)),
    }


def new_registry() -> dict[str, Any]:
    return {"schema_version": 1, "sequence_by_brand": {}, "records": []}


def load_registry(path: str) -> dict[str, Any]:
    if not Path(path).exists():
        return new_registry()
    registry = read_json(path)
    if registry.get("schema_version") != 1 or not isinstance(registry.get("records"), list):
        raise Hold("Registry schema is invalid. Do not use it for operational work.")
    registry.setdefault("sequence_by_brand", {})
    return registry


def active_records(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in registry["records"] if item.get("record_state", "Active") == "Active"]


def resolve_record(registry: dict[str, Any], record: dict[str, Any], secret: bytes) -> dict[str, Any]:
    """Resolve without guessing. Ambiguity and conflicting evidence always hold."""
    fingerprints = record_fingerprints(record, secret)
    campaign_id = normalized(record.get("campaign_id"))
    candidates: dict[str, set[str]] = {"storefront": set(), "thread": set(), "contacts": set()}
    known = {entry["creator_record_id"]: entry for entry in active_records(registry)}

    for entry in known.values():
        identifier = entry["creator_record_id"]
        if fingerprints["storefront_key"] and fingerprints["storefront_key"] == entry.get("storefront_key"):
            candidates["storefront"].add(identifier)
        if (
            fingerprints["thread_key"]
            and fingerprints["thread_key"] == entry.get("thread_key")
            and campaign_id
            and campaign_id == normalized(entry.get("campaign_id"))
        ):
            candidates["thread"].add(identifier)
        matches = sum(
            bool(fingerprints[key] and fingerprints[key] == entry.get(key))
            for key in ("full_name_fp", "email_fp", "phone_fp", "address_fp")
        )
        if matches >= 2:
            candidates["contacts"].add(identifier)

    all_matches = set().union(*candidates.values())
    if len(all_matches) > 1:
        return {"result": "CONFLICT", "reason": "multiple_active_records_match", "matches": sorted(all_matches)}

    if all_matches:
        identifier = next(iter(all_matches))
        existing = known[identifier]
        if normalized(existing.get("lock_state")) not in {"", "unlocked"}:
            return {"result": "HOLD", "reason": "record_is_locked", "matches": [identifier]}
        conflicts = []
        for key in ("storefront_key", "email_fp", "phone_fp", "address_fp"):
            if fingerprints[key] and existing.get(key) and fingerprints[key] != existing.get(key):
                conflicts.append(key)
        if conflicts:
            return {
                "result": "CONFLICT",
                "reason": "resolved_record_has_conflicting_identifier",
                "matches": [identifier],
                "conflicting_fields": conflicts,
            }
        return {"result": "RESOLVED", "creator_record_id": identifier, "match_method": next(k for k, v in candidates.items() if v)}

    if not fingerprints["thread_key"] or not campaign_id:
        return {"result": "HOLD", "reason": "new_record_requires_thread_key_and_campaign_id"}
    return {"result": "NEW", "fingerprints": fingerprints}


def lock_conflicting_records(registry: dict[str, Any], resolution: dict[str, Any]) -> None:
    """Persist a conflict lock on every active record implicated by resolution."""
    identifiers = set(resolution.get("matches") or [])
    if not identifiers:
        return
    for entry in registry["records"]:
        if entry.get("creator_record_id") not in identifiers:
            continue
        entry["lock_state"] = "Conflict"
        entry["escalation_reason"] = resolution.get("reason") or "identity_conflict"
        entry["version"] = int(entry.get("version") or 0) + 1
        entry["last_verified_at"] = date.today().isoformat()


def refresh_registry_entry(registry: dict[str, Any], identifier: str, record: dict[str, Any], secret: bytes) -> None:
    """Add newly verified fingerprints without replacing an existing identity value."""
    fingerprints = record_fingerprints(record, secret)
    for entry in registry["records"]:
        if entry.get("creator_record_id") != identifier:
            continue
        changed = False
        for key, value in fingerprints.items():
            if value and not entry.get(key):
                entry[key] = value
                changed = True
        if changed:
            entry["version"] = int(entry.get("version") or 0) + 1
            entry["last_verified_at"] = date.today().isoformat()
        return
    raise Hold("Resolved record disappeared from registry during refresh.")


def issue_record_id(registry: dict[str, Any], record: dict[str, Any], secret: bytes, today: date) -> str:
    result = resolve_record(registry, record, secret)
    if result["result"] == "RESOLVED":
        refresh_registry_entry(registry, result["creator_record_id"], record, secret)
        return result["creator_record_id"]
    if result["result"] == "CONFLICT":
        lock_conflicting_records(registry, result)
    if result["result"] != "NEW":
        raise Hold(f"Identity {result['result'].lower()}: {result['reason']}")
    brand_code = re.sub(r"[^A-Z0-9]", "", str(record.get("brand_code", ""))).upper()
    if not brand_code:
        raise Hold("New creator record requires brand_code.")
    sequence_key = f"{brand_code}-{today:%y}"
    id_pattern = re.compile(rf"^CCR-{re.escape(brand_code)}-{today:%y}-(\d+)$")
    existing_numbers = [
        int(match.group(1))
        for entry in registry["records"]
        if (match := id_pattern.fullmatch(str(entry.get("creator_record_id", "")).upper()))
    ]
    persisted_sequence = int(registry["sequence_by_brand"].get(sequence_key, 0))
    next_number = max([persisted_sequence, *existing_numbers], default=0) + 1
    existing_ids = {str(entry.get("creator_record_id", "")).upper() for entry in registry["records"]}
    identifier = f"CCR-{brand_code}-{today:%y}-{next_number:04d}"
    while identifier in existing_ids:
        next_number += 1
        identifier = f"CCR-{brand_code}-{today:%y}-{next_number:04d}"
    registry["sequence_by_brand"][sequence_key] = next_number
    registry["records"].append(
        {
            "creator_record_id": identifier,
            "brand": str(record.get("brand", "")).strip(),
            "campaign_id": normalized(record.get("campaign_id")),
            "thread_key": result["fingerprints"]["thread_key"],
            "storefront_key": result["fingerprints"]["storefront_key"],
            "full_name_fp": result["fingerprints"]["full_name_fp"],
            "email_fp": result["fingerprints"]["email_fp"],
            "phone_fp": result["fingerprints"]["phone_fp"],
            "address_fp": result["fingerprints"]["address_fp"],
            "record_state": "Active",
            "lock_state": "Unlocked",
            "version": 1,
            "created_at": today.isoformat(),
        }
    )
    return identifier


def is_truthy(value: Any) -> bool:
    return value is True or normalized(value) in {"yes", "true", "verified", "pass", "passed"}


def strong(value: Any) -> bool:
    return normalized(value) in {"strong", "high", "excellent", "verified"}


def score_record(record: dict[str, Any]) -> dict[str, Any]:
    address = record.get("address") or {}
    checks = {
        "complete_fulfillment_details": bool(
            normalized(record.get("full_name"))
            and normalize_email(record.get("email"))
            and normalize_phone(record.get("phone"))
            and all(normalized(address.get(field)) for field in ("street", "city", "state", "postal_code"))
        ),
        "requested_asin": bool(normalized(record.get("requested_asin"))),
        "exact_product_match": normalized(record.get("product_match_status")) == "exact match",
        "storefront_visible": bool(canonical_storefront(record.get("storefront_url"))),
        "recent_post_verified": is_truthy(record.get("recent_post_verified")),
        "content_quality": strong(record.get("content_quality_rating")),
        "category_fit": strong(record.get("category_fit")),
        "performance_or_revenue": is_truthy(record.get("performance_evidence_available")) or is_truthy(record.get("earns_revenue_badge")),
        "specific_asin_mentioned": is_truthy(record.get("specific_asin_mentioned")),
        "low_spam_risk": normalized(record.get("spam_risk")) == "low",
    }
    missing = [label for label, passed in checks.items() if not passed]
    return {"score": sum(checks.values()), "checks": checks, "missing": missing}


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise Hold(f"Invalid ISO date: {value}") from exc


def queue_item(record: dict[str, Any], today: date) -> dict[str, Any] | None:
    score = score_record(record)
    status = normalized(record.get("status"))
    identifier = record.get("creator_record_id") or "UNRESOLVED"
    attempts = int(record.get("follow_up_attempts") or 0)
    last_outbound = parse_date(record.get("last_outbound_date"))
    due = parse_date(record.get("follow_up_date")) or (last_outbound + timedelta(days=2) if last_outbound else today)
    base = {
        "queue_id": f"{today:%Y%m%d}-{identifier}",
        "run_date": today.isoformat(),
        "creator_record_id": identifier,
        "brand": record.get("brand", ""),
        "campaign_tab": record.get("campaign_tab", ""),
        "current_status": record.get("status", ""),
        "computed_score": score["score"],
        "missing": score["missing"],
        "due_date": due.isoformat(),
    }
    if identifier == "UNRESOLVED":
        return base | {"action_type": "IDENTITY_RESOLUTION", "gate_result": "BLOCKED", "queue_state": "Escalated", "reason": "missing_creator_record_id"}
    if status in {"new inquiry", "inquiry received"}:
        return base | {"action_type": "BACKGROUND_CHECK", "gate_result": "HOLD", "queue_state": "Queued", "reason": "new_inquiry_requires_visible_evidence"}
    if status in {"first-base pass", "manager review", "verification sent", "proof requested", "address verification"}:
        if attempts >= 3:
            return base | {"action_type": "ESCALATE_UNRESPONSIVE", "gate_result": "BLOCKED", "queue_state": "Escalated", "reason": "three_follow_up_attempts_without_required_reply"}
        if due <= today:
            return base | {"action_type": "SEND_TAILORED_VERIFICATION_FOLLOW_UP", "gate_result": "PENDING_APPROVAL", "queue_state": "Queued", "reason": "message_send_requires_current_approval;missing_" + ",".join(score["missing"])}
        return None
    if status in {"verification confirmed", "approved for sample"}:
        if score["score"] != 10:
            return base | {"action_type": "RECONCILE_QUALIFICATION", "gate_result": "BLOCKED", "queue_state": "Escalated", "reason": "status_score_drift"}
        return base | {"action_type": "MCF_PREFLIGHT", "gate_result": "HOLD", "queue_state": "Queued", "reason": "paid_order_requires_preflight_and_authorized_executor"}
    if status == "product switch pending":
        alternate_asin = normalized(record.get("proposed_alternate_asin")).upper()
        if not alternate_asin:
            return base | {"action_type": "RECONCILE_PRODUCT_SWITCH", "gate_result": "BLOCKED", "queue_state": "Escalated", "reason": "missing_verified_alternate_asin"}
        if attempts >= 3:
            return base | {"action_type": "ESCALATE_PRODUCT_SWITCH_UNRESPONSIVE", "gate_result": "BLOCKED", "queue_state": "Escalated", "reason": "three_product_switch_follow_ups_without_exact_asin_confirmation"}
        if due <= today:
            return base | {"action_type": "SEND_PRODUCT_SWITCH_FOLLOW_UP", "gate_result": "PENDING_APPROVAL", "queue_state": "Queued", "reason": f"message_send_requires_current_approval;await_exact_confirmation_{alternate_asin}"}
        return None
    if status in {"sample sent", "delivered", "awaiting content", "delivered / awaiting content", "follow up"}:
        expected = parse_date(record.get("expected_delivery_date"))
        content_due = (expected + timedelta(days=3)) if expected else due
        if attempts >= 3:
            return base | {"action_type": "ESCALATE_CONTENT_UNRESPONSIVE", "gate_result": "BLOCKED", "queue_state": "Escalated", "reason": "three_content_follow_ups_without_reply"}
        if today >= content_due and due <= today:
            return base | {"action_type": "SEND_CONTENT_FOLLOW_UP", "gate_result": "PENDING_APPROVAL", "queue_state": "Queued", "reason": "message_send_requires_current_approval;track_performance_and_request_video_link"}
    return None


def mcf_inventory_errors(catalog_item: dict[str, Any], quantity: int) -> list[str]:
    errors: list[str] = []
    channel = normalized(catalog_item.get("fulfillment_channel"))
    if channel not in {"fba", "afn", "amazon", "amazon fulfilled", "mcf"}:
        errors.append("selected_sku_not_fba_fulfilled")
    if catalog_item.get("mcf_fulfillable") is not True:
        errors.append("selected_sku_not_mcf_fulfillable")
    try:
        fulfillable_quantity = int(catalog_item.get("fulfillable_quantity"))
    except (TypeError, ValueError):
        fulfillable_quantity = -1
    if fulfillable_quantity < quantity:
        errors.append("insufficient_mcf_fulfillable_quantity")
    if not normalized(catalog_item.get("inventory_checked_at")):
        errors.append("mcf_inventory_check_missing")
    if not normalized(catalog_item.get("fulfillment_evidence_reference")):
        errors.append("mcf_inventory_evidence_missing")
    return errors


def product_switch_preflight(registry: dict[str, Any], proposal: dict[str, Any], secret: bytes) -> dict[str, Any]:
    record = proposal.get("creator") or {}
    identity = resolve_record(registry, record, secret)
    errors: list[str] = []
    if identity.get("result") == "CONFLICT":
        lock_conflicting_records(registry, identity)
    if identity.get("result") != "RESOLVED":
        errors.append("identity_not_resolved")
    resolved = next((item for item in registry["records"] if item.get("creator_record_id") == identity.get("creator_record_id")), {})
    if normalized(resolved.get("lock_state")) not in {"", "unlocked"}:
        errors.append("record_not_unlocked_for_product_switch")

    phase = normalized(proposal.get("phase"))
    if phase not in {"offer", "confirm"}:
        errors.append("invalid_product_switch_phase")
    original_asin = normalized(proposal.get("original_asin")).upper()
    current_requested_asin = normalized(record.get("requested_asin")).upper()
    tracker_asin = normalized(proposal.get("tracker_asin")).upper()
    alternate_asin = normalized(proposal.get("alternate_asin")).upper()
    campaign_asins = {normalized(value).upper() for value in (proposal.get("campaign_asins") or []) if normalized(value)}
    if not original_asin or len({original_asin, current_requested_asin, tracker_asin}) != 1:
        errors.append("original_asin_mismatch")
    if not alternate_asin or alternate_asin == original_asin:
        errors.append("alternate_asin_not_distinct")
    if alternate_asin not in campaign_asins:
        errors.append("alternate_asin_not_in_campaign")
    if normalized(proposal.get("original_unavailable_reason")) not in {
        "not mcf fulfillable",
        "not_mcf_fulfillable",
        "out of stock",
        "out_of_stock",
        "not found",
        "not_found",
    }:
        errors.append("original_mcf_blocker_not_verified")
    if not normalized(proposal.get("original_blocker_evidence_reference")):
        errors.append("original_mcf_blocker_evidence_missing")

    catalog = proposal.get("product_catalog") or {}
    catalog_item = catalog.get(alternate_asin, {})
    selected_sku = normalized(proposal.get("alternate_sku")).upper()
    if normalized(catalog_item.get("asin")).upper() != alternate_asin:
        errors.append("alternate_catalog_asin_mismatch")
    if not selected_sku or normalized(catalog_item.get("sku")).upper() != selected_sku:
        errors.append("alternate_sku_not_mapped_to_asin")
    errors.extend(mcf_inventory_errors(catalog_item, 1))

    if phase == "confirm":
        if normalized(proposal.get("creator_confirmed_asin")).upper() != alternate_asin:
            errors.append("creator_confirmation_asin_mismatch")
        if not normalized(proposal.get("creator_confirmation_evidence_reference")):
            errors.append("creator_confirmation_evidence_missing")

    if errors:
        required_next_state = "Conflict or Held"
    elif phase == "offer":
        required_next_state = "Product Switch Pending"
    else:
        required_next_state = "Approved for Sample"
    return {
        "result": "PASS" if not errors else "HOLD",
        "phase": phase,
        "creator_record_id": identity.get("creator_record_id"),
        "errors": errors,
        "required_next_state": required_next_state,
        "original_asin": original_asin,
        "alternate_asin": alternate_asin,
        "alternate_sku": selected_sku,
    }


def mcf_preflight(registry: dict[str, Any], proposal: dict[str, Any], secret: bytes) -> dict[str, Any]:
    record = proposal.get("creator") or {}
    identity = resolve_record(registry, record, secret)
    errors: list[str] = []
    if identity.get("result") == "CONFLICT":
        lock_conflicting_records(registry, identity)
    if identity.get("result") != "RESOLVED":
        errors.append("identity_not_resolved")
    resolved = next((item for item in registry["records"] if item.get("creator_record_id") == identity.get("creator_record_id")), {})
    if normalized(resolved.get("lock_state")) not in {"", "unlocked"}:
        errors.append("record_not_unlocked_for_preflight")
    requested = normalized(record.get("requested_asin")).upper()
    tracker_asin = normalized(proposal.get("tracker_asin")).upper()
    selected_asin = normalized(proposal.get("selected_asin")).upper()
    catalog = proposal.get("product_catalog") or {}
    selected_sku = normalized(proposal.get("selected_sku")).upper()
    catalog_item = catalog.get(selected_asin, {})
    score = score_record(record)
    if normalized(record.get("status")) != "approved for sample": errors.append("status_not_approved_for_sample")
    if score["score"] != 10: errors.append("qualification_not_10_of_10")
    if normalized(record.get("sample_decision")) != "send": errors.append("sample_decision_not_send")
    if not requested or len({requested, tracker_asin, selected_asin}) != 1: errors.append("asin_mismatch")
    if normalized(catalog_item.get("asin")).upper() != selected_asin: errors.append("catalog_asin_mismatch")
    if not selected_sku or normalized(catalog_item.get("sku")).upper() != selected_sku:
        errors.append("sku_not_mapped_to_selected_asin")
    try:
        quantity = int(proposal.get("quantity") or 0)
    except (TypeError, ValueError):
        quantity = 0
        errors.append("quantity_invalid")
    if quantity != 1: errors.append("quantity_must_equal_1")
    errors.extend(mcf_inventory_errors(catalog_item, max(quantity, 1)))
    if normalized(proposal.get("shipping_speed")) != "standard": errors.append("shipping_must_be_standard")
    fee = int(proposal.get("visible_fee_cents") or 0)
    cap = int(proposal.get("approved_fee_cap_cents") or -1)
    if cap < 0 or fee > cap: errors.append("fee_exceeds_approved_cap")
    registry_history = resolved.get("sample_history") or []
    proposal_history = proposal.get("sample_history") or []
    duplicate_registry_history = any(
        normalized(entry.get("asin")).upper() == selected_asin
        and normalized(entry.get("status")) not in {"cancelled", "failed"}
        for entry in registry_history
    )
    duplicate_proposal_history = any(
        entry.get("creator_record_id") == identity.get("creator_record_id")
        and normalized(entry.get("asin")).upper() == selected_asin
        and normalized(entry.get("status")) not in {"cancelled", "failed"}
        for entry in proposal_history
    )
    if (
        proposal.get("prior_sample_same_creator_asin")
        or duplicate_registry_history
        or duplicate_proposal_history
    ):
        errors.append("duplicate_sample_risk")
    if proposal.get("page_errors"): errors.append("page_validation_error")
    if proposal.get("field_truncated"): errors.append("field_truncation_detected")
    if not score["checks"]["complete_fulfillment_details"]: errors.append("incomplete_fulfillment_details")
    return {
        "result": "PASS" if not errors else "HOLD",
        "creator_record_id": identity.get("creator_record_id"),
        "computed_score": score["score"],
        "errors": errors,
        "required_next_state": "Locked for MCF" if not errors else "Conflict or Held",
        "quantity": proposal.get("quantity"),
        "visible_fee_cents": fee,
        "approved_fee_cap_cents": cap,
        "selected_asin": selected_asin,
        "selected_sku": selected_sku,
    }


def reserve_mcf(registry: dict[str, Any], proposal: dict[str, Any], secret: bytes) -> dict[str, Any]:
    """Atomically reserve a passing creator/ASIN pair for a future API worker."""
    result = mcf_preflight(registry, proposal, secret)
    if result["result"] != "PASS":
        return result
    identifier, asin = result["creator_record_id"], result["selected_asin"]
    for entry in registry["records"]:
        if entry.get("creator_record_id") == identifier:
            entry["lock_state"] = "Locked for MCF"
            entry["mcf_reservation"] = {"asin": asin, "reserved_at": datetime.now(timezone.utc).isoformat()}
            entry["version"] = int(entry.get("version") or 0) + 1
            return result | {"reservation": "LOCKED_FOR_MCF"}
    raise Hold("Resolved record vanished before MCF reservation.")


def confirm_mcf(registry: dict[str, Any], identifier: str, asin: str, order_id: str, evidence_reference: str) -> dict[str, Any]:
    if not identifier or not asin or not order_id or not evidence_reference:
        raise Hold("Confirmation requires Creator Record ID, ASIN, order ID, and evidence reference.")
    for entry in registry["records"]:
        if entry.get("creator_record_id") != identifier:
            continue
        reservation = entry.get("mcf_reservation") or {}
        if normalized(entry.get("lock_state")) != "locked for mcf" or normalized(reservation.get("asin")).upper() != normalized(asin).upper():
            raise Hold("MCF confirmation does not match an active reservation.")
        entry["sample_history"] = entry.get("sample_history", []) + [{"asin": asin.upper(), "order_id": order_id, "evidence_reference": evidence_reference, "confirmed_at": datetime.now(timezone.utc).isoformat()}]
        entry["lock_state"] = "Unlocked"
        entry.pop("mcf_reservation", None)
        entry["version"] = int(entry.get("version") or 0) + 1
        return {"result": "PASS", "creator_record_id": identifier, "order_id": order_id, "state": "sample_confirmed"}
    raise Hold("Creator Record ID does not exist in the registry.")


def migrate_legacy(registry: dict[str, Any], payload: dict[str, Any], secret: bytes, today: date) -> dict[str, Any]:
    """Convert only provenance-backed legacy rows. It never guesses an identity."""
    rows = payload.get("records")
    if not isinstance(rows, list):
        raise Hold("Legacy migration input requires a records list.")
    results = []
    for row in rows:
        source_ref = row.get("source_ref") or "unknown-source"
        try:
            identifier = issue_record_id(registry, row, secret, today)
            results.append({"source_ref": source_ref, "result": "READY_TO_SYNC", "creator_record_id": identifier})
        except Hold as exc:
            results.append({"source_ref": source_ref, "result": "HELD", "reason": str(exc)})
    return {
        "run_date": today.isoformat(),
        "results": results,
        "counts": {"ready_to_sync": sum(x["result"] == "READY_TO_SYNC" for x in results), "held": sum(x["result"] == "HELD" for x in results)},
    }


def emit(value: Any, exit_code: int = 0) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secret-env", default="CREATOR_CONTROL_HMAC_KEY")
    sub = parser.add_subparsers(dest="command", required=True)
    register = sub.add_parser("register")
    register.add_argument("--registry", required=True)
    register.add_argument("--record", required=True)
    score = sub.add_parser("score")
    score.add_argument("--record", required=True)
    queue = sub.add_parser("queue")
    queue.add_argument("--input", required=True)
    queue.add_argument("--output", required=True)
    queue.add_argument("--date", default=date.today().isoformat())
    preflight = sub.add_parser("preflight")
    preflight.add_argument("--registry", required=True)
    preflight.add_argument("--input", required=True)
    switch = sub.add_parser("preflight-switch")
    switch.add_argument("--registry", required=True)
    switch.add_argument("--input", required=True)
    reserve = sub.add_parser("reserve-mcf")
    reserve.add_argument("--registry", required=True)
    reserve.add_argument("--input", required=True)
    confirm = sub.add_parser("confirm-mcf")
    confirm.add_argument("--registry", required=True)
    confirm.add_argument("--creator-record-id", required=True)
    confirm.add_argument("--asin", required=True)
    confirm.add_argument("--order-id", required=True)
    confirm.add_argument("--evidence-reference", required=True)
    migrate = sub.add_parser("migrate-legacy")
    migrate.add_argument("--registry", required=True)
    migrate.add_argument("--input", required=True)
    migrate.add_argument("--output", required=True)
    migrate.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    try:
        secret = get_secret(args.secret_env)
        if args.command == "register":
            record = read_json(args.record)
            identifier = mutate_registry(
                args.registry,
                lambda registry: issue_record_id(registry, record, secret, date.today()),
            )
            emit({"result": "PASS", "creator_record_id": identifier, "registry": args.registry})
        if args.command == "score":
            emit(score_record(read_json(args.record)))
        if args.command == "queue":
            sweep, today = read_json(args.input), parse_date(args.date)
            if not today or not isinstance(sweep.get("records"), list): raise Hold("Queue input requires a records list and valid date.")
            items = [item for record in sweep["records"] if (item := queue_item(record, today))]
            output = {"run_date": today.isoformat(), "items": items, "counts": {"queued": sum(x["queue_state"] == "Queued" for x in items), "escalated": sum(x["queue_state"] == "Escalated" for x in items)}}
            write_json(args.output, output)
            emit(output)
        if args.command == "preflight":
            proposal = read_json(args.input)
            result = mutate_registry(
                args.registry,
                lambda registry: mcf_preflight(registry, proposal, secret),
            )
            emit(result, 0 if result["result"] == "PASS" else 2)
        if args.command == "preflight-switch":
            proposal = read_json(args.input)
            result = mutate_registry(
                args.registry,
                lambda registry: product_switch_preflight(registry, proposal, secret),
            )
            emit(result, 0 if result["result"] == "PASS" else 2)
        if args.command == "reserve-mcf":
            proposal = read_json(args.input)
            result = mutate_registry(
                args.registry,
                lambda registry: reserve_mcf(registry, proposal, secret),
            )
            emit(result, 0 if result["result"] == "PASS" else 2)
        if args.command == "confirm-mcf":
            result = mutate_registry(
                args.registry,
                lambda registry: confirm_mcf(
                    registry,
                    args.creator_record_id,
                    args.asin,
                    args.order_id,
                    args.evidence_reference,
                ),
            )
            emit(result)
        if args.command == "migrate-legacy":
            today = parse_date(args.date)
            if not today: raise Hold("Legacy migration date is invalid.")
            payload = read_json(args.input)
            result = mutate_registry(
                args.registry,
                lambda registry: migrate_legacy(registry, payload, secret, today),
            )
            write_json(args.output, result)
            emit(result)
    except Hold as exc:
        emit({"result": "HOLD", "reason": str(exc)}, 2)


if __name__ == "__main__":
    main()

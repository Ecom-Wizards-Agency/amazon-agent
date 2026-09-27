import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


MODULE = Path(__file__).parents[1] / "creator_control.py"
SPEC = importlib.util.spec_from_file_location("creator_control", MODULE)
cc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cc)

# Synthetic order keys in the form creators.preflight_result returns.
KEY = "CCS-" + "0123456789abcdef" * 2
OTHER_KEY = "CCS-" + "fedcba9876543210" * 2


def creator(**overrides):
    record = {
        "brand": "Example", "brand_code": "EX", "campaign_id": "campaign-1", "thread_key": "thread-1",
        "full_name": "Example Creator", "email": "creator@example.test", "phone": "555-010-2000",
        "address": {"street": "100 Example Road", "city": "Austin", "state": "TX", "postal_code": "78701", "country": "US"},
        "storefront_url": "https://www.amazon.com/shop/examplecreator?ref=abc", "requested_asin": "B0EXAMPLE1",
        "product_match_status": "Exact Match", "recent_post_verified": True, "content_quality_rating": "Strong",
        "category_fit": "Strong", "performance_evidence_available": True, "specific_asin_mentioned": True,
        "spam_risk": "Low", "status": "Approved for Sample", "sample_decision": "Send",
    }
    record.update(overrides)
    return record


def proposal(**overrides):
    value = {
        "creator_record_id": "CCR-EX-26-0001",
        "creator": creator(),
        "tracker_campaign_id": "campaign-1",
        "tracker_source_ref": "tracker/campaign-1/row-2",
        "thread_evidence_reference": "private-evidence/thread-1.json",
        "preflight_evidence_reference": "private-evidence/preflight-1.json",
        "tracker_asin": "B0EXAMPLE1",
        "selected_asin": "B0EXAMPLE1",
        "selected_sku": "SKU-1",
        "product_catalog": {
            "B0EXAMPLE1": {
                "asin": "B0EXAMPLE1",
                "sku": "SKU-1",
                "product_title": "Example Product",
                "campaign_id": "campaign-1",
                "fulfillment_channel": "FBA",
                "mcf_fulfillable": True,
                "fulfillable_quantity": 10,
                "inventory_checked_at": "2026-08-05T10:00:00Z",
                "fulfillment_evidence_reference": "private-evidence/mcf-search.json",
            }
        },
        "quantity": 1,
        "shipping_speed": "Standard",
        "visible_fee_cents": 799,
        "approved_fee_cap_cents": 800,
        "derived_order_key": KEY,
    }
    value.update(overrides)
    return value


def verification(reservation_id, **overrides):
    value = {
        "creator_record_id": "CCR-EX-26-0001",
        "reservation_id": reservation_id,
        "campaign_id": "campaign-1",
        "tracker_source_ref": "tracker/campaign-1/row-2",
        "screen_asin": "B0EXAMPLE1",
        "screen_sku": "SKU-1",
        "product_title": "Example Product",
        "quantity": 1,
        "recipient": creator(),
        "shipping_speed": "Standard",
        "visible_fee_cents": 799,
        "evidence_reference": "private-evidence/mcf-screen.png",
        "order_id": KEY,
    }
    value.update(overrides)
    return value


def reconciliation(reserved_id, **overrides):
    value = {
        "creator_record_id": "CCR-EX-26-0001",
        "reservation_id": reserved_id,
        "campaign_id": "campaign-1",
        "tracker_source_ref": "tracker/campaign-1/row-2",
        "asin": "B0EXAMPLE1",
        "sku": "SKU-1",
        "product_title": "Example Product",
        "quantity": 1,
        "recipient": creator(),
        "order_id": KEY,
        "evidence_reference": "private-evidence/order-history.png",
    }
    value.update(overrides)
    return value


def switch_proposal(**overrides):
    alternate = "B0ALTERNATE"
    value = {
        "phase": "offer",
        "creator": creator(),
        "original_asin": "B0EXAMPLE1",
        "tracker_asin": "B0EXAMPLE1",
        "alternate_asin": alternate,
        "alternate_sku": "SKU-ALT",
        "campaign_asins": ["B0EXAMPLE1", alternate],
        "original_unavailable_reason": "not_mcf_fulfillable",
        "original_blocker_evidence_reference": "private-evidence/original-search.json",
        "product_catalog": {
            alternate: {
                "asin": alternate,
                "sku": "SKU-ALT",
                "fulfillment_channel": "FBA",
                "mcf_fulfillable": True,
                "fulfillable_quantity": 6,
                "inventory_checked_at": "2026-08-05T10:05:00Z",
                "fulfillment_evidence_reference": "private-evidence/alternate-search.json",
            }
        },
    }
    value.update(overrides)
    return value


class CreatorControlTests(unittest.TestCase):
    def setUp(self):
        self.secret = b"this-is-a-test-secret-at-least-16"
        self.registry = cc.new_registry()

    def test_record_id_is_reused_for_same_thread_and_identity(self):
        first = creator()
        identifier = cc.issue_record_id(self.registry, first, self.secret, date(2026, 8, 5))
        self.assertEqual(identifier, "CCR-EX-26-0001")
        self.assertEqual(cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5)), identifier)

    def test_new_contact_fingerprint_is_added_after_thread_resolution(self):
        initial = creator(email="", phone="", address={"street": "", "city": "", "state": "", "postal_code": "", "country": "US"})
        identifier = cc.issue_record_id(self.registry, initial, self.secret, date(2026, 8, 5))
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        entry = next(x for x in self.registry["records"] if x["creator_record_id"] == identifier)
        self.assertTrue(entry["email_fp"])

    def test_conflicting_contact_blocks_resolved_thread(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        changed = creator(email="different@example.test")
        result = cc.resolve_record(self.registry, changed, self.secret)
        self.assertEqual(result["result"], "CONFLICT")
        self.assertIn("email_fp", result["conflicting_fields"])

    def test_conflicting_register_persists_record_lock(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        with self.assertRaises(cc.Hold):
            cc.issue_record_id(
                self.registry,
                creator(email="different@example.test"),
                self.secret,
                date(2026, 8, 5),
            )
        entry = next(item for item in self.registry["records"] if item["creator_record_id"] == identifier)
        self.assertEqual(entry["lock_state"], "Conflict")
        self.assertEqual(entry["escalation_reason"], "resolved_record_has_conflicting_identifier")

    def test_record_id_sequence_recovers_from_existing_records(self):
        self.assertEqual(
            cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5)),
            "CCR-EX-26-0001",
        )
        self.registry["sequence_by_brand"] = {}
        second = creator(
            thread_key="thread-2",
            storefront_url="https://www.amazon.com/shop/secondcreator",
            full_name="Second Creator",
            email="second@example.test",
            phone="555-010-3000",
            address={"street": "200 Example Road", "city": "Dallas", "state": "TX", "postal_code": "75001", "country": "US"},
        )
        self.assertEqual(
            cc.issue_record_id(self.registry, second, self.secret, date(2026, 8, 5)),
            "CCR-EX-26-0002",
        )

    def test_score_requires_all_ten_checks(self):
        scored = cc.score_record(creator())
        self.assertEqual(scored["score"], 10)
        self.assertEqual(cc.score_record(creator(phone=""))["score"], 9)

    def test_queue_escalates_after_three_verification_attempts(self):
        item = cc.queue_item(creator(creator_record_id="CCR-EX-26-0001", status="Verification Sent", follow_up_attempts=3), date(2026, 8, 5))
        self.assertEqual(item["action_type"], "ESCALATE_UNRESPONSIVE")

    def test_message_queue_items_require_current_approval(self):
        verification = cc.queue_item(
            creator(
                creator_record_id="CCR-EX-26-0001",
                status="Verification Sent",
                phone="",
                follow_up_date="2026-08-05",
            ),
            date(2026, 8, 5),
        )
        content = cc.queue_item(
            creator(
                creator_record_id="CCR-EX-26-0001",
                status="Awaiting Content",
                expected_delivery_date="2026-08-01",
                follow_up_date="2026-08-05",
            ),
            date(2026, 8, 5),
        )
        self.assertEqual(verification["gate_result"], "PENDING_APPROVAL")
        self.assertEqual(content["gate_result"], "PENDING_APPROVAL")

    def test_product_switch_queue_requires_exact_alternate_and_schedules_follow_up(self):
        missing = cc.queue_item(
            creator(
                creator_record_id="CCR-EX-26-0001",
                status="Product Switch Pending",
                proposed_alternate_asin="",
            ),
            date(2026, 8, 5),
        )
        self.assertEqual(missing["action_type"], "RECONCILE_PRODUCT_SWITCH")
        follow_up = cc.queue_item(
            creator(
                creator_record_id="CCR-EX-26-0001",
                status="Product Switch Pending",
                proposed_alternate_asin="B0ALTERNATE",
                follow_up_date="2026-08-05",
            ),
            date(2026, 8, 5),
        )
        self.assertEqual(follow_up["action_type"], "SEND_PRODUCT_SWITCH_FOLLOW_UP")
        self.assertEqual(follow_up["gate_result"], "PENDING_APPROVAL")

    def test_preflight_rejects_wrong_quantity_and_asin(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        proposed = {"creator": creator(), "tracker_asin": "B0EXAMPLE1", "selected_asin": "B0OTHER", "selected_sku": "SKU-1", "product_catalog": {"B0OTHER": {"sku": "SKU-1"}}, "quantity": 2, "shipping_speed": "Standard", "visible_fee_cents": 799, "approved_fee_cap_cents": 800}
        result = cc.mcf_preflight(self.registry, proposed, self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("asin_mismatch", result["errors"])
        self.assertIn("quantity_must_equal_1", result["errors"])

    def test_preflight_requires_explicit_catalog_asin_and_sku_mapping(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        result = cc.mcf_preflight(
            self.registry,
            proposal(selected_sku="", product_catalog={"B0EXAMPLE1": {"sku": ""}}),
            self.secret,
        )
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("catalog_asin_mismatch", result["errors"])
        self.assertIn("sku_not_mapped_to_selected_asin", result["errors"])

    def test_preflight_holds_when_fee_is_missing_or_invalid(self):
        missing = proposal()
        missing.pop("visible_fee_cents")
        result = cc.mcf_preflight(self.registry, missing, self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("fee_missing_or_invalid", result["errors"])
        result = cc.mcf_preflight(self.registry, proposal(visible_fee_cents="abc"), self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("fee_missing_or_invalid", result["errors"])

    def test_preflight_holds_instead_of_crashing_on_invalid_quantity(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        result = cc.mcf_preflight(self.registry, proposal(quantity="one"), self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("quantity_invalid", result["errors"])
        self.assertIn("quantity_must_equal_1", result["errors"])

    def test_preflight_rejects_fbm_inventory_even_when_units_exist(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        item = proposal()["product_catalog"]["B0EXAMPLE1"] | {
            "fulfillment_channel": "FBM",
            "mcf_fulfillable": False,
            "fulfillable_quantity": 85,
        }
        result = cc.mcf_preflight(
            self.registry,
            proposal(product_catalog={"B0EXAMPLE1": item}),
            self.secret,
        )
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("selected_sku_not_fba_fulfilled", result["errors"])
        self.assertIn("selected_sku_not_mcf_fulfillable", result["errors"])

    def test_preflight_requires_fresh_inventory_evidence_and_enough_units(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        item = proposal()["product_catalog"]["B0EXAMPLE1"] | {
            "fulfillable_quantity": 0,
            "inventory_checked_at": "",
            "fulfillment_evidence_reference": "",
        }
        result = cc.mcf_preflight(
            self.registry,
            proposal(product_catalog={"B0EXAMPLE1": item}),
            self.secret,
        )
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("insufficient_mcf_fulfillable_quantity", result["errors"])
        self.assertIn("mcf_inventory_check_missing", result["errors"])
        self.assertIn("mcf_inventory_evidence_missing", result["errors"])

    def test_product_switch_offer_requires_campaign_membership_and_mcf_stock(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        passing = cc.product_switch_preflight(self.registry, switch_proposal(), self.secret)
        self.assertEqual(passing["result"], "PASS")
        self.assertEqual(passing["required_next_state"], "Product Switch Pending")
        held = cc.product_switch_preflight(
            self.registry,
            switch_proposal(campaign_asins=["B0EXAMPLE1"]),
            self.secret,
        )
        self.assertEqual(held["result"], "HOLD")
        self.assertIn("alternate_asin_not_in_campaign", held["errors"])

    def test_product_switch_confirmation_must_name_the_verified_alternate(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        missing = cc.product_switch_preflight(
            self.registry,
            switch_proposal(phase="confirm"),
            self.secret,
        )
        self.assertEqual(missing["result"], "HOLD")
        self.assertIn("creator_confirmation_asin_mismatch", missing["errors"])
        self.assertIn("creator_confirmation_evidence_missing", missing["errors"])
        passing = cc.product_switch_preflight(
            self.registry,
            switch_proposal(
                phase="confirm",
                creator_confirmed_asin="B0ALTERNATE",
                creator_confirmation_evidence_reference="private-evidence/creator-thread.json",
            ),
            self.secret,
        )
        self.assertEqual(passing["result"], "PASS")
        self.assertEqual(passing["required_next_state"], "Approved for Sample")

    def test_reservation_blocks_a_second_mcf_preflight(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        proposed = proposal()
        self.assertEqual(cc.reserve_mcf(self.registry, proposed, self.secret)["reservation"], "LOCKED_FOR_MCF")
        self.assertEqual(cc.mcf_preflight(self.registry, proposed, self.secret)["result"], "HOLD")

    def test_preflight_binds_creator_campaign_tracker_product_and_recipient(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        wrong = proposal(
            creator_record_id="CCR-EX-26-9999",
            tracker_campaign_id="campaign-2",
            creator=creator(email="other@example.test"),
        )
        result = cc.mcf_preflight(self.registry, wrong, self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("creator_record_id_mismatch", result["errors"])
        self.assertIn("campaign_id_mismatch", result["errors"])
        self.assertIn("recipient_email_fp_missing", result["errors"])

    def test_populated_mcf_screen_must_match_locked_manifest(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reserved = cc.reserve_mcf(self.registry, proposal(), self.secret)
        held = cc.verify_mcf(
            self.registry,
            verification(
                reserved["reservation_id"],
                screen_sku="SKU-WRONG",
                product_title="Wrong Product",
                recipient=creator(phone="555-999-9999"),
            ),
            self.secret,
        )
        self.assertEqual(held["result"], "HOLD")
        self.assertIn("screen_sku_mismatch", held["errors"])
        self.assertIn("screen_product_title_mismatch", held["errors"])
        self.assertIn("screen_recipient_mismatch", held["errors"])
        self.assertEqual(self.registry["records"][0]["lock_state"], "Locked for MCF")

    def test_confirmation_requires_verified_screen_and_exact_reservation(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reserved = cc.reserve_mcf(self.registry, proposal(), self.secret)
        reservation_id = reserved["reservation_id"]
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(
                self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1,
                KEY, "private-evidence/order.png",
            )
        verified = cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        self.assertEqual(verified["reservation_state"], "Verified for Submit")
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(
                self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-WRONG", 1,
                KEY, "private-evidence/order.png",
            )
        confirmed = cc.confirm_mcf(
            self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1,
            KEY, "private-evidence/order.png",
        )
        self.assertEqual(confirmed["state"], "sample_confirmed")
        self.assertEqual(self.registry["records"][0]["lock_state"], "Unlocked")
        self.assertEqual(self.registry["records"][0]["sample_history"][0]["quantity"], 1)

    def test_definitive_cancellation_releases_reservation_and_is_idempotent(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reserved = cc.reserve_mcf(self.registry, proposal(), self.secret)
        reservation_id = reserved["reservation_id"]
        cancelled = cc.cancel_mcf(
            self.registry, identifier, reservation_id, "amazon_rejected", "private-evidence/rejected.png",
        )
        self.assertEqual(cancelled["state"], "reservation_cancelled_and_released")
        self.assertEqual(self.registry["records"][0]["lock_state"], "Unlocked")
        repeated = cc.cancel_mcf(
            self.registry, identifier, reservation_id, "amazon_rejected", "private-evidence/rejected.png",
        )
        self.assertEqual(repeated["state"], "already_released")

    def reserved_creator(self, uncertain=False):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reservation_id = cc.reserve_mcf(self.registry, proposal(), self.secret)["reservation_id"]
        cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        if uncertain:
            with self.assertRaises(cc.Hold):
                cc.cancel_mcf(self.registry, identifier, reservation_id, "request_timeout", "private-evidence/timeout.json")
        return identifier, reservation_id

    def test_failed_current_screen_recheck_revokes_approval_and_can_be_repaired(self):
        identifier, reservation_id = self.reserved_creator()
        held = cc.verify_mcf(self.registry, verification(reservation_id, recipient=creator(email="wrong@example.test")), self.secret)
        self.assertEqual(held["result"], "HOLD")
        entry = self.registry["records"][0]
        self.assertEqual(entry["lock_state"], "Locked for MCF")
        self.assertEqual(entry["mcf_reservation"]["state"], "Reserved")
        self.assertNotIn("verified_at", entry["mcf_reservation"])
        self.assertNotIn("verification_evidence_reference", entry["mcf_reservation"])
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1, KEY, "evidence")
        self.assertEqual(cc.verify_mcf(self.registry, verification(reservation_id), self.secret)["result"], "PASS")

    def test_stale_reservation_recheck_cannot_revoke_current_approval(self):
        self.reserved_creator()
        before = copy.deepcopy(self.registry)
        result = cc.verify_mcf(self.registry, verification("MCFR-OLD"), self.secret)
        self.assertIn("reservation_id_mismatch", result["errors"])
        self.assertEqual(self.registry, before)

    def test_reconciliation_records_existing_order_and_replay_is_idempotent(self):
        _, reservation_id = self.reserved_creator(uncertain=True)
        payload = reconciliation(reservation_id)
        self.assertEqual(cc.reconcile_mcf(self.registry, payload, self.secret)["state"], "existing_order_reconciled")
        entry = self.registry["records"][0]
        self.assertEqual(entry["lock_state"], "Unlocked")
        self.assertNotIn("mcf_reservation", entry)
        self.assertEqual(entry["sample_history"][0]["status"], "Confirmed")
        self.assertIn("duplicate_sample_risk", cc.mcf_preflight(self.registry, proposal(), self.secret)["errors"])
        before = copy.deepcopy(self.registry)
        self.assertEqual(cc.reconcile_mcf(self.registry, payload, self.secret)["state"], "already_reconciled")
        self.assertEqual(self.registry, before)
        persisted = json.dumps(self.registry)
        for private in ("creator@example.test", "100 Example Road", "555-010-2000", "Example Creator"):
            self.assertNotIn(private, persisted)

    def test_reconciliation_mismatch_and_conflicting_replay_preserve_registry(self):
        _, reservation_id = self.reserved_creator(uncertain=True)
        mismatches = {
            "creator_record_id": "CCR-EX-26-9999", "reservation_id": "MCFR-OTHER",
            "campaign_id": "other", "tracker_source_ref": "tracker/other/row-2",
            "asin": "B0OTHER", "sku": "WRONG", "product_title": "Wrong Product",
            "quantity": 2, "recipient": creator(email="wrong@example.test"),
            "order_id": "", "evidence_reference": "",
        }
        before = copy.deepcopy(self.registry)
        for key, value in mismatches.items():
            with self.subTest(field=key):
                with self.assertRaises(cc.Hold):
                    cc.reconcile_mcf(self.registry, reconciliation(reservation_id, **{key: value}), self.secret)
                self.assertEqual(self.registry, before)
        cc.reconcile_mcf(self.registry, reconciliation(reservation_id), self.secret)
        before = copy.deepcopy(self.registry)
        for changes in ({"order_id": "OTHER-ORDER"}, {"evidence_reference": "different-evidence"}, {"recipient": creator(phone="555-999-9999")}):
            with self.subTest(changes=changes):
                with self.assertRaises(cc.Hold):
                    cc.reconcile_mcf(self.registry, reconciliation(reservation_id, **changes), self.secret)
                self.assertEqual(self.registry, before)

    def test_reconciliation_requires_uncertain_state_and_strict_one_unit(self):
        identifier, reservation_id = self.reserved_creator()
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.reconcile_mcf(self.registry, reconciliation(reservation_id), self.secret)
        self.assertEqual(self.registry, before)
        with self.assertRaises(cc.Hold):
            cc.cancel_mcf(self.registry, identifier, reservation_id, "outcome_unknown", "evidence")
        before = copy.deepcopy(self.registry)
        for quantity in (True, 1.0, 1.5, "1", None):
            with self.subTest(quantity=quantity):
                with self.assertRaises(cc.Hold):
                    cc.reconcile_mcf(self.registry, reconciliation(reservation_id, quantity=quantity), self.secret)
                self.assertEqual(self.registry, before)

    def test_reconciliation_rejects_order_already_recorded_elsewhere(self):
        _, reservation_id = self.reserved_creator(uncertain=True)
        self.registry["records"].append({"creator_record_id": "CCR-EX-26-9999", "sample_history": [{"order_id": KEY}]})
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.reconcile_mcf(self.registry, reconciliation(reservation_id), self.secret)
        self.assertEqual(self.registry, before)

    def test_cli_failed_verification_and_reconciliation_persist_safely(self):
        identifier, reservation_id = self.reserved_creator()
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry.json"
            input_path = Path(directory) / "input.json"
            cc.write_json(str(registry_path), self.registry)
            environment = os.environ.copy()
            environment["CREATOR_CONTROL_HMAC_KEY"] = self.secret.decode("utf-8")

            def run(command, payload=None, extra=(), expected=0):
                args = [sys.executable, str(MODULE), command, "--registry", str(registry_path)]
                if payload is not None:
                    cc.write_json(str(input_path), payload)
                    args += ["--input", str(input_path)]
                result = subprocess.run(args + list(extra), capture_output=True, text=True, env=environment, timeout=10)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                return json.loads(result.stdout)

            before = registry_path.read_bytes()
            run("verify-mcf", verification("MCFR-OLD"), expected=2)
            self.assertEqual(registry_path.read_bytes(), before)
            run("verify-mcf", verification(reservation_id, screen_sku="WRONG"), expected=2)
            self.assertEqual(cc.read_json(str(registry_path))["records"][0]["mcf_reservation"]["state"], "Reserved")
            run("confirm-mcf", extra=("--creator-record-id", identifier, "--reservation-id", reservation_id, "--asin", "B0EXAMPLE1", "--sku", "SKU-1", "--quantity", "1", "--order-id", KEY, "--evidence-reference", "evidence"), expected=2)
            run("verify-mcf", verification(reservation_id))
            run("cancel-mcf", extra=("--creator-record-id", identifier, "--reservation-id", reservation_id, "--reason-code", "request_timeout", "--evidence-reference", "evidence"), expected=2)
            before = registry_path.read_bytes()
            self.assertEqual(cc.read_json(str(registry_path))["records"][0]["mcf_reservation"]["state"], "Reconciliation Required")
            run("reconcile-mcf", reconciliation(reservation_id, sku="WRONG"), expected=2)
            self.assertEqual(registry_path.read_bytes(), before)
            self.assertEqual(run("reconcile-mcf", reconciliation(reservation_id))["state"], "existing_order_reconciled")
            before = registry_path.read_bytes()
            self.assertEqual(run("reconcile-mcf", reconciliation(reservation_id))["state"], "already_reconciled")
            run("reconcile-mcf", reconciliation(reservation_id, order_id="OTHER"), expected=2)
            self.assertEqual(registry_path.read_bytes(), before)
            self.assertEqual(len(cc.read_json(str(registry_path))["records"][0]["sample_history"]), 1)

    def test_uncertain_cancellation_keeps_lock_for_reconciliation(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reserved = cc.reserve_mcf(self.registry, proposal(), self.secret)
        with self.assertRaises(cc.Hold):
            cc.cancel_mcf(
                self.registry, identifier, reserved["reservation_id"], "request_timeout", "private-evidence/timeout.json",
            )
        entry = self.registry["records"][0]
        self.assertEqual(entry["lock_state"], "Locked for MCF")
        self.assertEqual(entry["mcf_reservation"]["state"], "Reconciliation Required")

    def test_legacy_reservation_can_be_listed_and_definitively_cancelled(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        entry = self.registry["records"][0]
        entry["lock_state"] = "Locked for MCF"
        entry["mcf_reservation"] = {"asin": "B0EXAMPLE1", "reserved_at": "2026-08-05T10:00:00Z"}
        listed = cc.list_mcf_reservations(self.registry)
        legacy_id = listed["active_reservations"][0]["reservation_id"]
        self.assertTrue(legacy_id.startswith("MCFR-LEGACY-"))
        result = cc.cancel_mcf(
            self.registry, identifier, legacy_id, "definitive_not_created", "private-evidence/order-history.png",
        )
        self.assertEqual(result["state"], "reservation_cancelled_and_released")
        self.assertEqual(entry["lock_state"], "Unlocked")

    def test_registry_sample_history_blocks_duplicate_proposal(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        entry = next(item for item in self.registry["records"] if item["creator_record_id"] == identifier)
        entry["sample_history"] = [{"asin": "B0EXAMPLE1", "order_id": "ORDER-1"}]
        result = cc.mcf_preflight(self.registry, proposal(sample_history=[]), self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("duplicate_sample_risk", result["errors"])

    def test_two_processes_cannot_reserve_the_same_mcf_order(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry.json"
            proposal_path = Path(directory) / "proposal.json"
            cc.write_json(str(registry_path), self.registry)
            cc.write_json(str(proposal_path), proposal())
            environment = os.environ.copy()
            environment["CREATOR_CONTROL_HMAC_KEY"] = self.secret.decode("utf-8")
            command = [
                sys.executable,
                str(MODULE),
                "reserve-mcf",
                "--registry",
                str(registry_path),
                "--input",
                str(proposal_path),
            ]
            processes = [
                subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
                for _ in range(2)
            ]
            completed = [process.communicate(timeout=10) + (process.returncode,) for process in processes]
            self.assertEqual(sorted(item[2] for item in completed), [0, 2])
            results = [json.loads(item[0]) for item in completed]
            self.assertEqual(sum(item["result"] == "PASS" for item in results), 1)
            persisted = cc.read_json(str(registry_path))
            self.assertEqual(persisted["records"][0]["lock_state"], "Locked for MCF")

    def test_legacy_migration_holds_row_without_thread_provenance(self):
        results = cc.migrate_legacy(self.registry, {"records": [creator(source_ref="Heavy Duty!B11", thread_key="")]}, self.secret, date(2026, 8, 5))
        self.assertEqual(results["results"][0]["result"], "HELD")


def arcana_proposal(**overrides):
    value = proposal(order_owner="arcana")
    value.pop("visible_fee_cents")
    value.update(overrides)
    return value


def placed_outcome(reservation_id, **overrides):
    value = {
        "derivedOrderKey": KEY, "state": "placed", "class": "placed", "escalated": False,
        "mcfStatus": "Received", "acceptedAt": "2026-09-28T10:00:00.000Z",
        "placedAt": "2026-09-28T10:02:00.000Z", "reservationId": reservation_id,
    }
    value.update(overrides)
    return value


def api_order(reservation_id, outcome=None, **overrides):
    value = {
        "creator_record_id": "CCR-EX-26-0001", "reservation_id": reservation_id, "asin": "B0EXAMPLE1",
        "sku": "SKU-1", "quantity": 1, "derived_order_key": KEY,
        "outcome": outcome if outcome is not None else placed_outcome(reservation_id),
    }
    value.update(overrides)
    return value


class ArcanaHandoverTests(unittest.TestCase):
    """WP-338l: lanes handed to Arcana, the stored derived key and record-api-order."""

    def setUp(self):
        self.secret = b"this-is-a-test-secret-at-least-16"
        self.registry = cc.new_registry()

    def arcana_reserved(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reserved = cc.reserve_mcf(self.registry, arcana_proposal(), self.secret)
        self.assertEqual(reserved["reservation"], "LOCKED_FOR_MCF")
        return identifier, reserved["reservation_id"]

    def assert_held_unchanged(self, payload):
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.record_api_order(self.registry, payload)
        self.assertEqual(self.registry, before)

    def test_reservation_stores_derived_key_unchanged_and_requires_it(self):
        _, reservation_id = self.arcana_reserved()
        reservation = self.registry["records"][0]["mcf_reservation"]
        self.assertEqual(reservation["derived_order_key"], KEY)
        self.assertEqual(reservation["order_owner"], "arcana")
        self.assertNotIn("visible_fee_cents", reservation)
        self.assertEqual(reservation["approved_fee_cap_cents"], 800)
        other = cc.new_registry()
        cc.issue_record_id(other, creator(), self.secret, date(2026, 8, 5))
        runner_lane = cc.new_registry()
        cc.issue_record_id(runner_lane, creator(), self.secret, date(2026, 8, 5))
        cc.reserve_mcf(runner_lane, proposal(), self.secret)
        self.assertEqual(runner_lane["records"][0]["mcf_reservation"]["derived_order_key"], KEY)
        self.assertNotIn("order_owner", runner_lane["records"][0]["mcf_reservation"])
        for key in (None, "", KEY.upper(), KEY[:-1], "CC-EX-B0EXAMPLE1-260928", " " + KEY):
            with self.subTest(key=key):
                before = copy.deepcopy(other)
                with self.assertRaises(cc.Hold):
                    cc.reserve_mcf(other, proposal(derived_order_key=key), self.secret)
                self.assertEqual(other, before)
        with self.assertRaises(cc.Hold):
            cc.reserve_mcf(other, proposal(order_owner="seller_central"), self.secret)

    def test_reserve_refuses_a_key_held_or_recorded_by_another_reservation(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        self.registry["records"].append({"creator_record_id": "CCR-EX-26-9999", "sample_history": [{"reservation_id": "MCFR-0000000000000001", "order_id": KEY}]})
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.reserve_mcf(self.registry, proposal(), self.secret)
        self.assertEqual(self.registry, before)
        self.registry["records"][1] = {"creator_record_id": "CCR-EX-26-9999", "lock_state": "Locked for MCF", "mcf_reservation": {"reservation_id": "MCFR-0000000000000002", "asin": "B0OTHER0001", "derived_order_key": KEY}}
        with self.assertRaises(cc.Hold):
            cc.reserve_mcf(self.registry, proposal(), self.secret)

    def test_arcana_lane_fee_check_is_cap_only(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        passing = cc.mcf_preflight(self.registry, arcana_proposal(), self.secret)
        self.assertEqual(passing["result"], "PASS")
        self.assertIsNone(passing["visible_fee_cents"])
        self.assertEqual(passing["approved_fee_cap_cents"], 800)
        browser = cc.mcf_preflight(self.registry, arcana_proposal(order_owner="runner"), self.secret)
        self.assertEqual(browser["errors"], ["fee_missing_or_invalid"])
        no_cap = arcana_proposal()
        no_cap.pop("approved_fee_cap_cents")
        self.assertEqual(cc.mcf_preflight(self.registry, no_cap, self.secret)["errors"], ["fee_missing_or_invalid"])
        self.assertEqual(cc.mcf_preflight(self.registry, arcana_proposal(approved_fee_cap_cents="n/a"), self.secret)["errors"], ["fee_missing_or_invalid"])
        self.assertEqual(cc.mcf_preflight(self.registry, arcana_proposal(approved_fee_cap_cents=-1), self.secret)["errors"], ["fee_exceeds_approved_cap"])
        self.assertEqual(cc.mcf_preflight(self.registry, arcana_proposal(visible_fee_cents=900), self.secret)["errors"], ["fee_exceeds_approved_cap"])

    def test_preflight_output_keeps_the_arcana_preflight_result_shape(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        expected = {
            "result", "creator_record_id", "computed_score", "errors", "required_next_state", "quantity",
            "visible_fee_cents", "approved_fee_cap_cents", "selected_asin", "selected_sku", "product_title",
            "campaign_id", "tracker_source_ref", "recipient_binding",
        }
        for built in (proposal(), arcana_proposal()):
            with self.subTest(owner=built.get("order_owner", "runner")):
                self.assertEqual(set(cc.mcf_preflight(self.registry, built, self.secret)), expected)

    def test_record_api_order_records_placed_order_with_binding_unverified_note(self):
        _, reservation_id = self.arcana_reserved()
        result = cc.record_api_order(self.registry, api_order(reservation_id))
        self.assertEqual(result["state"], "api_order_recorded")
        entry = self.registry["records"][0]
        self.assertEqual(entry["lock_state"], "Unlocked")
        self.assertNotIn("mcf_reservation", entry)
        self.assertEqual(len(entry["sample_history"]), 1)
        history = entry["sample_history"][0]
        self.assertEqual(history["order_id"], KEY)
        self.assertEqual(history["recipient_note"], "recipient: operator-entered in Arcana, binding unverified")
        self.assertEqual(history["status"], "Confirmed")
        self.assertEqual(history["quantity"], 1)
        self.assertNotIn("recipient_binding", history)
        self.assertRegex(history["evidence_reference"], r"^arcana:send:CCS-[0-9a-f]{32}:[0-9a-f]{64}$")
        self.assertEqual(history["evidence_reference"], cc.arcana_outcome(placed_outcome(reservation_id))["evidence_reference"])
        self.assertIn("duplicate_sample_risk", cc.mcf_preflight(self.registry, proposal(), self.secret)["errors"])
        persisted = json.dumps(self.registry)
        for private in ("creator@example.test", "100 Example Road", "555-010-2000", "Example Creator"):
            self.assertNotIn(private, persisted)

    def test_record_api_order_replay_is_idempotent(self):
        _, reservation_id = self.arcana_reserved()
        payload = api_order(reservation_id)
        cc.record_api_order(self.registry, payload)
        before = copy.deepcopy(self.registry)
        self.assertEqual(cc.record_api_order(self.registry, payload)["state"], "already_recorded")
        later_read = api_order(reservation_id, placed_outcome(reservation_id, mcfStatus="Processing"))
        self.assertEqual(cc.record_api_order(self.registry, later_read)["state"], "already_recorded")
        self.assertEqual(self.registry, before)
        self.assertEqual(len(self.registry["records"][0]["sample_history"]), 1)

    def test_record_api_order_refuses_a_malformed_key(self):
        _, reservation_id = self.arcana_reserved()
        for key in (None, "", KEY.upper(), KEY[:-1], KEY + "0", "CCS-" + "g" * 32, "CC-EX-B0EXAMPLE1-260928", KEY + " "):
            with self.subTest(key=key):
                self.assert_held_unchanged(api_order(reservation_id, placed_outcome(reservation_id, derivedOrderKey=key), derived_order_key=key))

    def test_record_api_order_refuses_quantity_other_than_one(self):
        _, reservation_id = self.arcana_reserved()
        for quantity in (0, 2, True, 1.0, "1", None):
            with self.subTest(quantity=quantity):
                self.assert_held_unchanged(api_order(reservation_id, quantity=quantity))

    def test_record_api_order_refuses_a_reservation_mismatch(self):
        _, reservation_id = self.arcana_reserved()
        for field, value in (
            ("reservation_id", "MCFR-0000000000000009"), ("creator_record_id", "CCR-EX-26-9999"),
            ("asin", "B0OTHER0001"), ("sku", "SKU-WRONG"),
        ):
            with self.subTest(field=field):
                self.assert_held_unchanged(api_order(reservation_id) | {field: value})
        with self.subTest(field="outcome.reservationId"):
            self.assert_held_unchanged(api_order(reservation_id, placed_outcome("MCFR-0000000000000009")))
        with self.subTest(field="reservation_id and outcome"):
            other = "MCFR-0000000000000009"
            self.assert_held_unchanged(api_order(other, placed_outcome(other)))

    def test_record_api_order_refuses_a_key_other_than_the_stored_key(self):
        _, reservation_id = self.arcana_reserved()
        self.assert_held_unchanged(api_order(reservation_id, placed_outcome(reservation_id, derivedOrderKey=OTHER_KEY), derived_order_key=OTHER_KEY))
        self.assert_held_unchanged(api_order(reservation_id, derived_order_key=OTHER_KEY))

    def test_record_api_order_refuses_a_key_recorded_on_another_reservation(self):
        _, reservation_id = self.arcana_reserved()
        self.registry["records"].append({"creator_record_id": "CCR-EX-26-9999", "sample_history": [{"reservation_id": "MCFR-0000000000000001", "order_id": KEY}]})
        self.assert_held_unchanged(api_order(reservation_id))

    def test_record_api_order_refuses_every_outcome_but_placed(self):
        _, reservation_id = self.arcana_reserved()
        for state, outcome_class in (
            ("sealed", "pending"), ("accepted", "pending"), ("uncertain", "uncertain"), ("conflict", "uncertain"),
            ("rejected", "failed"), ("failed_after_placement", "failed"), ("withdrawn", "failed"), ("cancelled", "cancelled"),
            ("placed", "pending"), ("accepted", "placed"),
        ):
            with self.subTest(state=state, outcome_class=outcome_class):
                self.assert_held_unchanged(api_order(reservation_id, placed_outcome(reservation_id, state=state, **{"class": outcome_class})))
        for overrides in ({"escalated": True}, {"escalated": "false"}, {"placedAt": None}):
            with self.subTest(overrides=overrides):
                self.assert_held_unchanged(api_order(reservation_id, placed_outcome(reservation_id, **overrides)))
        with self.subTest(outcome="extra field"):
            self.assert_held_unchanged(api_order(reservation_id, placed_outcome(reservation_id, address="synthetic")))
        with self.subTest(outcome="missing"):
            self.assert_held_unchanged(api_order(reservation_id, outcome={}))

    def test_record_api_order_runs_only_from_a_reserved_arcana_lane(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reservation_id = cc.reserve_mcf(self.registry, proposal(), self.secret)["reservation_id"]
        self.assert_held_unchanged(api_order(reservation_id))
        cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        self.assert_held_unchanged(api_order(reservation_id))
        cc.cancel_mcf(self.registry, identifier, reservation_id, "operator_aborted_before_submit", "evidence")
        arcana_reservation = cc.reserve_mcf(self.registry, arcana_proposal(), self.secret)["reservation_id"]
        self.registry["records"][0]["mcf_reservation"]["state"] = "Reconciliation Required"
        self.assert_held_unchanged(api_order(arcana_reservation))

    def test_outcome_classification_names_the_one_permitted_action(self):
        reservation_id = "MCFR-0000000000000001"
        expected = {
            ("placed", "placed", False): "record-api-order",
            ("rejected", "failed", False): "cancel-mcf amazon_rejected",
            ("failed_after_placement", "failed", False): "cancel-mcf amazon_rejected",
            ("approved", "pending", False): "wait",
            ("uncertain", "uncertain", False): "wait",
            ("cancelled", "cancelled", False): "escalate",
            ("placed", "placed", True): "escalate",
            ("uncertain", "uncertain", True): "escalate",
        }
        for (state, outcome_class, escalated), action in expected.items():
            with self.subTest(state=state, escalated=escalated):
                read = placed_outcome(reservation_id, state=state, escalated=escalated, **{"class": outcome_class})
                self.assertEqual(cc.arcana_outcome(read)["next_action"], action)
        self.assertEqual(len(cc.ARCANA_OUTCOME_CLASS), 21)

    def test_browser_fallback_uses_the_stored_derived_key_as_order_id(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reservation_id = cc.reserve_mcf(self.registry, proposal(), self.secret)["reservation_id"]
        stored = self.registry["records"][0]["mcf_reservation"]["derived_order_key"]
        held = cc.verify_mcf(self.registry, verification(reservation_id, order_id="CC-EX-B0EXAMPLE1-260928"), self.secret)
        self.assertIn("screen_order_id_mismatch", held["errors"])
        verified = cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        self.assertEqual(verified["order_id"], stored)
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1, OTHER_KEY, "evidence")
        self.assertEqual(self.registry, before)
        cc.confirm_mcf(self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1, stored, "evidence")
        self.assertEqual(self.registry["records"][0]["sample_history"][0]["order_id"], stored)

    def test_uncertain_browser_order_reconciles_only_under_the_stored_key(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        reservation_id = cc.reserve_mcf(self.registry, proposal(), self.secret)["reservation_id"]
        cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        with self.assertRaises(cc.Hold):
            cc.cancel_mcf(self.registry, identifier, reservation_id, "request_timeout", "evidence")
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.reconcile_mcf(self.registry, reconciliation(reservation_id, order_id=OTHER_KEY), self.secret)
        self.assertEqual(self.registry, before)
        self.assertEqual(cc.reconcile_mcf(self.registry, reconciliation(reservation_id), self.secret)["order_id"], KEY)

    def test_seller_central_path_is_refused_for_a_lane_handed_to_arcana(self):
        identifier, reservation_id = self.arcana_reserved()
        held = cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        self.assertIn("reservation_handed_over_to_arcana", held["errors"])
        self.assertEqual(self.registry["records"][0]["mcf_reservation"]["state"], "Reserved")
        self.registry["records"][0]["mcf_reservation"]["state"] = "Verified for Submit"
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1, KEY, "evidence")
        self.registry["records"][0]["mcf_reservation"]["state"] = "Reconciliation Required"
        with self.assertRaises(cc.Hold):
            cc.reconcile_mcf(self.registry, reconciliation(reservation_id), self.secret)
        self.assertNotIn("sample_history", self.registry["records"][0])

    def assert_release_held(self, identifier, reservation_id, reason, evidence, outcome=None):
        before = copy.deepcopy(self.registry)
        with self.assertRaises(cc.Hold):
            cc.cancel_mcf(self.registry, identifier, reservation_id, reason, evidence, outcome)
        self.assertEqual(self.registry, before)

    def test_failed_arcana_send_releases_with_amazon_rejected_only_from_its_failed_outcome(self):
        identifier, reservation_id = self.arcana_reserved()
        failed_read = placed_outcome(reservation_id, state="rejected", placedAt=None, **{"class": "failed"})
        failed = cc.arcana_outcome(failed_read)
        placed = cc.arcana_outcome(placed_outcome(reservation_id))
        other = "MCFR-0000000000000009"
        for evidence, outcome in (
            (failed["evidence_reference"], None),
            (placed["evidence_reference"], placed_outcome(reservation_id)),
            (failed["evidence_reference"], failed_read | {"escalated": True}),
            ("private-evidence/rejected.png", failed_read),
            (cc.arcana_outcome(failed_read | {"derivedOrderKey": OTHER_KEY})["evidence_reference"], failed_read | {"derivedOrderKey": OTHER_KEY}),
            (cc.arcana_outcome(failed_read | {"reservationId": other})["evidence_reference"], failed_read | {"reservationId": other}),
        ):
            with self.subTest(evidence=evidence, outcome=outcome):
                self.assert_release_held(identifier, reservation_id, "amazon_rejected", evidence, outcome)
        released = cc.cancel_mcf(self.registry, identifier, reservation_id, "amazon_rejected", failed["evidence_reference"], failed_read)
        self.assertEqual(released["state"], "reservation_cancelled_and_released")
        self.assertEqual(self.registry["records"][0]["lock_state"], "Unlocked")
        self.assertEqual(self.registry["records"][0]["mcf_reservation_history"][0]["evidence_reference"], failed["evidence_reference"])
        self.assertNotIn("sample_history", self.registry["records"][0])
        repeated = cc.cancel_mcf(self.registry, identifier, reservation_id, "amazon_rejected", failed["evidence_reference"], failed_read)
        self.assertEqual(repeated["state"], "already_released")

    def test_uncertain_reason_cannot_strand_an_arcana_lane(self):
        identifier, reservation_id = self.arcana_reserved()
        for reason in ("request_timeout", "outcome_unknown", "confirmation_missing"):
            with self.subTest(reason=reason):
                self.assert_release_held(identifier, reservation_id, reason, f"arcana:send:{KEY}:timeout")
        self.assertEqual(self.registry["records"][0]["mcf_reservation"]["state"], "Reserved")
        self.assertEqual(cc.record_api_order(self.registry, api_order(reservation_id))["state"], "api_order_recorded")

    def test_other_release_of_an_arcana_lane_needs_arcana_evidence(self):
        identifier, reservation_id = self.arcana_reserved()
        for evidence in ("private-evidence/operator-note.json", f"arcana:send:{OTHER_KEY}:not_found", f"arcana:send:{KEY}"):
            with self.subTest(evidence=evidence):
                self.assert_release_held(identifier, reservation_id, "operator_aborted_before_submit", evidence)
        released = cc.cancel_mcf(self.registry, identifier, reservation_id, "operator_aborted_before_submit", f"arcana:send:{KEY}:not_found")
        self.assertEqual(released["state"], "reservation_cancelled_and_released")

    def test_evidence_reference_is_reproducible_across_reads_of_one_event(self):
        first = cc.arcana_outcome(placed_outcome("MCFR-0000000000000001"))
        later = cc.arcana_outcome(placed_outcome("MCFR-0000000000000001", mcfStatus="Complete"))
        self.assertEqual(first["evidence_reference"], later["evidence_reference"])
        moved = cc.arcana_outcome(placed_outcome("MCFR-0000000000000001", placedAt="2026-09-28T11:00:00.000Z"))
        self.assertNotEqual(first["evidence_reference"], moved["evidence_reference"])
        for placed_at in ("", "yesterday", "2026-09-28"):
            with self.subTest(placed_at=placed_at):
                with self.assertRaises(cc.Hold):
                    cc.arcana_outcome(placed_outcome("MCFR-0000000000000001", placedAt=placed_at))

    def test_corrupt_reservation_quantity_holds_instead_of_crashing(self):
        identifier, reservation_id = self.arcana_reserved()
        self.registry["records"][0]["mcf_reservation"]["quantity"] = "one"
        self.assert_held_unchanged(api_order(reservation_id))
        runner = cc.new_registry()
        cc.issue_record_id(runner, creator(), self.secret, date(2026, 8, 5))
        runner_reservation = cc.reserve_mcf(runner, proposal(), self.secret)["reservation_id"]
        runner["records"][0]["mcf_reservation"]["quantity"] = "one"
        with self.assertRaises(cc.Hold):
            cc.verify_mcf(runner, verification(runner_reservation), self.secret)
        runner["records"][0]["mcf_reservation"]["state"] = "Verified for Submit"
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(runner, identifier, runner_reservation, "B0EXAMPLE1", "SKU-1", 1, KEY, "evidence")

    def test_cli_record_api_order_and_outcome(self):
        identifier, reservation_id = self.arcana_reserved()
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry.json"
            input_path = Path(directory) / "input.json"
            cc.write_json(str(registry_path), self.registry)
            environment = os.environ.copy()
            environment["CREATOR_CONTROL_HMAC_KEY"] = self.secret.decode("utf-8")

            def run(command, payload, expected=0, registry=True):
                cc.write_json(str(input_path), payload)
                args = [sys.executable, str(MODULE), command, "--input", str(input_path)]
                if registry:
                    args += ["--registry", str(registry_path)]
                result = subprocess.run(args, capture_output=True, text=True, env=environment, timeout=10)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                return json.loads(result.stdout)

            pending = placed_outcome(reservation_id, state="accepted", placedAt=None, **{"class": "pending"})
            self.assertEqual(run("arcana-outcome", pending, registry=False)["next_action"], "wait")
            before = registry_path.read_bytes()
            run("record-api-order", api_order(reservation_id, pending), expected=2)
            self.assertEqual(registry_path.read_bytes(), before)
            self.assertEqual(run("record-api-order", api_order(reservation_id))["state"], "api_order_recorded")
            before = registry_path.read_bytes()
            self.assertEqual(run("record-api-order", api_order(reservation_id))["state"], "already_recorded")
            self.assertEqual(registry_path.read_bytes(), before)
            persisted = cc.read_json(str(registry_path))["records"][0]
            self.assertEqual(persisted["lock_state"], "Unlocked")
            self.assertEqual(persisted["sample_history"][0]["order_id"], KEY)
            self.assertEqual(identifier, persisted["creator_record_id"])

    def test_cli_cancel_releases_an_arcana_lane_only_with_its_failed_outcome(self):
        identifier, reservation_id = self.arcana_reserved()
        failed_read = placed_outcome(reservation_id, state="rejected", placedAt=None, **{"class": "failed"})
        evidence = cc.arcana_outcome(failed_read)["evidence_reference"]
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry.json"
            outcome_path = Path(directory) / "outcome.json"
            cc.write_json(str(registry_path), self.registry)
            cc.write_json(str(outcome_path), failed_read)
            environment = os.environ.copy()
            environment["CREATOR_CONTROL_HMAC_KEY"] = self.secret.decode("utf-8")
            base = [sys.executable, str(MODULE), "cancel-mcf", "--registry", str(registry_path), "--creator-record-id", identifier,
                    "--reservation-id", reservation_id, "--reason-code", "amazon_rejected", "--evidence-reference", evidence]
            before = registry_path.read_bytes()
            held = subprocess.run(base, capture_output=True, text=True, env=environment, timeout=10)
            self.assertEqual(held.returncode, 2, held.stdout + held.stderr)
            self.assertEqual(registry_path.read_bytes(), before)
            released = subprocess.run(base + ["--outcome", str(outcome_path)], capture_output=True, text=True, env=environment, timeout=10)
            self.assertEqual(released.returncode, 0, released.stdout + released.stderr)
            self.assertEqual(json.loads(released.stdout)["state"], "reservation_cancelled_and_released")


def sweep_input(**overrides):
    value = {
        "run_id": "sweep:EX:2026-09-28", "run_date": "2026-09-28", "brand": "Example",
        "started_at": "2026-09-28T06:00:00Z", "completed_at": "2026-09-28T06:40:00+00:00",
        "evidence_reference": "ev:sweep-2026-09-28",
        "counts": {
            "mounted": 2, "opened": 2, "changed": 1, "messages_examined": 3, "messages_sent": 0,
            "no_action_acknowledgements": 0, "held_or_escalated": 1, "archived_spam": 0, "unmatched": 0,
        },
        "threads": [
            {"thread_key": "thread-1", "creator_record_id": "CCR-EX-26-0001", "sender_role": "creator",
             "amazon_timestamp": "2026-09-27T18:00:00Z", "body": "Synthetic reply from creator@example.test",
             "outcome": "held", "reason": "awaiting_asin_confirmation"},
            {"thread_key": "thread-2", "creator_record_id": None, "sender_role": "brand",
             "amazon_timestamp": None, "body": "Synthetic brand message", "outcome": "unchanged", "reason": None},
        ],
    }
    value.update(overrides)
    return value


class SweepCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.secret = b"this-is-a-test-secret-at-least-16"

    def test_checkpoint_keeps_counts_and_fingerprints_only(self):
        checkpoint = cc.sweep_checkpoint(sweep_input(), self.secret)
        self.assertEqual(checkpoint["schema_version"], 1)
        self.assertEqual(len(checkpoint["threads"]), 2)
        self.assertEqual(sum(checkpoint["counts"].values()), 9)
        registry = cc.new_registry()
        cc.issue_record_id(registry, creator(), self.secret, date(2026, 8, 5))
        self.assertEqual(checkpoint["threads"][0]["thread_key"], registry["records"][0]["thread_key"])
        self.assertRegex(checkpoint["threads"][0]["body_hash"], r"^[0-9a-f]{64}$")
        self.assertEqual(set(checkpoint["threads"][0]), {"thread_key", "creator_record_id", "sender_role", "amazon_timestamp", "body_hash", "outcome", "reason"})
        persisted = json.dumps(checkpoint)
        for private in ("creator@example.test", "Synthetic reply", "thread-1"):
            self.assertNotIn(private, persisted)

    def test_invalid_checkpoint_input_names_fields_not_values(self):
        bad_thread = sweep_input()["threads"][0] | {"outcome": "unmatched", "body": ""}
        for overrides, field in (
            ({"run_id": "has spaces"}, "run_id"),
            ({"counts": sweep_input()["counts"] | {"archived_spam": 2}}, "counts.archived_spam"),
            ({"counts": {"mounted": 1}}, "counts"),
            ({"threads": [bad_thread]}, "threads[0].body"),
            ({"threads": [bad_thread | {"body": "x"}]}, "threads[0].creator_record_id"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(cc.Hold) as held:
                    cc.sweep_checkpoint(sweep_input(**overrides), self.secret)
                self.assertIn(field, str(held.exception))
                self.assertNotIn("creator@example.test", str(held.exception))


if __name__ == "__main__":
    unittest.main()

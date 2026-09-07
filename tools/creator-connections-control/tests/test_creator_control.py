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
        "order_id": "ORDER-EXISTING-1",
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
                "ORDER-1", "private-evidence/order.png",
            )
        verified = cc.verify_mcf(self.registry, verification(reservation_id), self.secret)
        self.assertEqual(verified["reservation_state"], "Verified for Submit")
        with self.assertRaises(cc.Hold):
            cc.confirm_mcf(
                self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-WRONG", 1,
                "ORDER-1", "private-evidence/order.png",
            )
        confirmed = cc.confirm_mcf(
            self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1,
            "ORDER-1", "private-evidence/order.png",
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
            cc.confirm_mcf(self.registry, identifier, reservation_id, "B0EXAMPLE1", "SKU-1", 1, "ORDER-1", "evidence")
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
        self.registry["records"].append({"creator_record_id": "CCR-EX-26-9999", "sample_history": [{"order_id": "ORDER-EXISTING-1"}]})
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
            run("confirm-mcf", extra=("--creator-record-id", identifier, "--reservation-id", reservation_id, "--asin", "B0EXAMPLE1", "--sku", "SKU-1", "--quantity", "1", "--order-id", "ORDER-1", "--evidence-reference", "evidence"), expected=2)
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


if __name__ == "__main__":
    unittest.main()

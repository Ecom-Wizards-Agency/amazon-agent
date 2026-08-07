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
        "creator": creator(),
        "tracker_asin": "B0EXAMPLE1",
        "selected_asin": "B0EXAMPLE1",
        "selected_sku": "SKU-1",
        "product_catalog": {"B0EXAMPLE1": {"asin": "B0EXAMPLE1", "sku": "SKU-1"}},
        "quantity": 1,
        "shipping_speed": "Standard",
        "visible_fee_cents": 799,
        "approved_fee_cap_cents": 800,
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

    def test_preflight_rejects_wrong_quantity_and_asin(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        proposed = {"creator": creator(), "tracker_asin": "B0EXAMPLE1", "selected_asin": "B0OTHER", "selected_sku": "SKU-1", "product_catalog": {"B0OTHER": {"sku": "SKU-1"}}, "quantity": 2, "shipping_speed": "Standard", "visible_fee_cents": 799, "approved_fee_cap_cents": 800}
        result = cc.mcf_preflight(self.registry, proposed, self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("asin_mismatch", result["errors"])
        self.assertIn("quantity_must_equal_1", result["errors"])

    def test_reservation_blocks_a_second_mcf_preflight(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        proposed = proposal()
        self.assertEqual(cc.reserve_mcf(self.registry, proposed, self.secret)["reservation"], "LOCKED_FOR_MCF")
        self.assertEqual(cc.mcf_preflight(self.registry, proposed, self.secret)["result"], "HOLD")

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

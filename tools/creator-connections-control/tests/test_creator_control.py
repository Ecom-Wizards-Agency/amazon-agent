import importlib.util
import json
import os
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

    def test_score_requires_all_ten_checks(self):
        scored = cc.score_record(creator())
        self.assertEqual(scored["score"], 10)
        self.assertEqual(cc.score_record(creator(phone=""))["score"], 9)

    def test_queue_escalates_after_three_verification_attempts(self):
        item = cc.queue_item(creator(creator_record_id="CCR-EX-26-0001", status="Verification Sent", follow_up_attempts=3), date(2026, 8, 5))
        self.assertEqual(item["action_type"], "ESCALATE_UNRESPONSIVE")

    def test_preflight_rejects_wrong_quantity_and_asin(self):
        identifier = cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        proposed = {"creator": creator(), "tracker_asin": "B0EXAMPLE1", "selected_asin": "B0OTHER", "selected_sku": "SKU-1", "product_catalog": {"B0OTHER": {"sku": "SKU-1"}}, "quantity": 2, "shipping_speed": "Standard", "visible_fee_cents": 799, "approved_fee_cap_cents": 800}
        result = cc.mcf_preflight(self.registry, proposed, self.secret)
        self.assertEqual(result["result"], "HOLD")
        self.assertIn("asin_mismatch", result["errors"])
        self.assertIn("quantity_must_equal_1", result["errors"])

    def test_reservation_blocks_a_second_mcf_preflight(self):
        cc.issue_record_id(self.registry, creator(), self.secret, date(2026, 8, 5))
        proposed = {"creator": creator(), "tracker_asin": "B0EXAMPLE1", "selected_asin": "B0EXAMPLE1", "selected_sku": "SKU-1", "product_catalog": {"B0EXAMPLE1": {"asin": "B0EXAMPLE1", "sku": "SKU-1"}}, "quantity": 1, "shipping_speed": "Standard", "visible_fee_cents": 799, "approved_fee_cap_cents": 800}
        self.assertEqual(cc.reserve_mcf(self.registry, proposed, self.secret)["reservation"], "LOCKED_FOR_MCF")
        self.assertEqual(cc.mcf_preflight(self.registry, proposed, self.secret)["result"], "HOLD")

    def test_legacy_migration_holds_row_without_thread_provenance(self):
        results = cc.migrate_legacy(self.registry, {"records": [creator(source_ref="Heavy Duty!B11", thread_key="")]}, self.secret, date(2026, 8, 5))
        self.assertEqual(results["results"][0]["result"], "HELD")


if __name__ == "__main__":
    unittest.main()

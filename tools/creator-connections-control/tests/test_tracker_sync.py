"""Synthetic regression coverage for canonical/overview synchronization."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_creator_control import MODULE, cc, creator, sweep_input


IDENTIFIER = "CCR-EX-26-0001"


def tracker_update():
    previous = {
        "campaign": {
            "Creator Record ID": IDENTIFIER, "Status": "Verification Sent",
            "Product": "Example product B0EXAMPLE1", "Total Qualification Score": 9,
            "Notes": "Earlier verified history.", "Email": "creator@example.test", "Phone": "",
        },
        "registry": {
            "Creator Record ID": IDENTIFIER, "Active Tracker Tab": "Example campaign",
            "Active Campaign ID": "campaign-1", "Record Lock State": "Unlocked",
            "Contact Fingerprint": "synthetic-opaque-fingerprint",
            "Active Product / ASIN": "B0EXAMPLE1",
        },
        "queue": {
            "Creator Record ID": IDENTIFIER, "Campaign Tab": "Example campaign",
            "Queue State": "Scheduled", "Last Updated": "2026-09-27T06:20:30Z",
            "Current Status": "Verification Sent",
        },
        "action_log_ids": ["event-previous"],
    }
    expected = {
        "campaign": {
            "Creator Record ID": IDENTIFIER, "Status": "Verification Confirmed",
            "Notes": "Earlier verified history.\n2026-09-28: Confirmed existing details.",
        },
        "registry": {"Creator Record ID": IDENTIFIER},
        "queue": {
            "Creator Record ID": IDENTIFIER, "Queue State": "Scheduled",
            "Last Updated": "2026-09-28T06:20:30Z",
            "Current Status": "Verification Confirmed",
        },
        "action_log": {
            "Action Log ID": "event-new", "Creator Record ID": IDENTIFIER,
            "Campaign Tab": "Example campaign", "Timestamp": "2026-09-28T06:20:30Z",
            "Evidence Reference": "private-evidence/update-1", "Event Type": "FACT_UPDATED",
        },
        "overview": {"Stage": "Qualification"},
    }
    formulas = {"source": "=SOURCE()", "rows": "=ROWS()", "score": "=SCORE()"}
    return {
        "run_id": "sweep:EX:2026-09-28", "creator_record_id": IDENTIFIER,
        "update_kind": "record_update", "operator_hold": False,
        "spreadsheet_id": "synthetic-workbook", "campaign_tab": "Example campaign",
        "campaign_id": "campaign-1", "source_ref": "tracker/example-campaign/row-11",
        "updated_at": "2026-09-28T06:20:00Z", "evidence_reference": "private-evidence/update-1",
        "before": previous, "expected": expected, "overview_formulas": formulas,
        "readback": {
            "spreadsheet_id": "synthetic-workbook", "campaign_tab": "Example campaign",
            "source_ref": "tracker/example-campaign/row-11", "captured_at": "2026-09-28T06:21:00Z",
            "source_scope": "all_rows_and_tabs", "overview_scope": "complete_projection",
            "campaign": previous["campaign"] | expected["campaign"],
            "registry": copy.deepcopy(previous["registry"]),
            "queue": previous["queue"] | expected["queue"],
            "action_log": [copy.deepcopy(expected["action_log"])],
            "overview_formulas": copy.deepcopy(formulas),
            "overview": [{
                "Creator Record ID": IDENTIFIER, "Campaign Tab": "Example campaign",
                "Source Reference": "tracker/example-campaign/row-11", "Score*": "9/10",
                "Stage": "Qualification",
            }],
        },
    }


def actioned_sweep(receipt=None):
    sweep = sweep_input()
    sweep["threads"][0].update(outcome="actioned", reason=None)
    if receipt is not None:
        sweep["threads"][0]["tracker_update"] = receipt
    return sweep


class TrackerSyncTests(unittest.TestCase):
    def assertHeld(self, payload):
        with self.assertRaises(cc.Hold):
            cc.verify_tracker_update(payload)

    def test_recorded_score_keeps_zero_distinct_from_unknown(self):
        for value in (0, 0.0, "0", "0/10", " 0 / 10 "):
            with self.subTest(value=value):
                self.assertEqual(cc.tracker_score(value), 0)
        for value in (None, "", " ", "Not recorded", "Not verified", "Unknown", "N/A"):
            with self.subTest(value=value):
                self.assertIsNone(cc.tracker_score(value))

    def test_score_aliases_and_qualification_annotation(self):
        for header in cc.SCORE_HEADERS:
            with self.subTest(header=header):
                self.assertEqual(cc.recorded_tracker_score({header: "9/10 qualification only; dispatch held"}), 9)
        for header in ("Score", "Score*"):
            self.assertEqual(cc.recorded_tracker_score({header: "10/10"}, overview=True), 10)

    def test_malformed_out_of_range_boolean_and_ambiguous_scores_hold(self):
        for value in (True, False, -1, 11, 9.5, "11/10", "10/100", "9/5", "9 of 10", "C - Do Not Send", "10/10 qualification; earlier 9/10", [], {}):
            with self.subTest(value=value):
                with self.assertRaises(cc.Hold):
                    cc.tracker_score(value)
        with self.assertRaises(cc.Hold):
            cc.recorded_tracker_score({"Total Qualification Score": 9, "Qualification Score": 10})
        with self.assertRaises(cc.Hold):
            cc.recorded_tracker_score({"Total Score": 9})

    def test_valid_readback_includes_hidden_and_filtered_source_records(self):
        payload = tracker_update()
        payload["readback"]["visibility"] = {"campaign_row_hidden": True, "registry_tab_hidden": True, "filter_active": True}
        result = cc.verify_tracker_update(payload)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["score_label"], "9/10")
        self.assertGreater(result["fields_verified"], 10)
        self.assertRegex(result["readback_digest"], r"^[0-9a-f]{64}$")
        self.assertNotIn("send_authorized", result)
        for private in ("creator@example.test", "Earlier verified history", "synthetic-workbook"):
            self.assertNotIn(private, json.dumps(result))

    def test_unknown_score_display_does_not_equal_zero(self):
        for recorded, displayed in (("", "Not recorded"), (0, "0/10")):
            payload = tracker_update()
            payload["before"]["campaign"]["Total Qualification Score"] = recorded
            payload["readback"]["campaign"]["Total Qualification Score"] = recorded
            payload["readback"]["overview"][0]["Score*"] = displayed
            self.assertEqual(cc.verify_tracker_update(payload)["score"], None if recorded == "" else 0)
            payload["readback"]["overview"][0]["Score*"] = "0/10" if recorded == "" else "Not recorded"
            self.assertHeld(payload)

    def test_readback_is_bound_to_original_record_campaign_and_workbook(self):
        mutations = [
            lambda p: p["readback"].update(spreadsheet_id="other-workbook"),
            lambda p: p["readback"].update(source_ref="tracker/other-campaign/row-11"),
            lambda p: p["readback"].update(campaign_tab="Other campaign"),
            lambda p: p["readback"]["campaign"].update({"Creator Record ID": "CCR-EX-26-0002"}),
            lambda p: p["readback"]["registry"].update({"Active Campaign ID": "other-campaign"}),
            lambda p: p["readback"]["registry"].update({"Active Tracker Tab": "Other campaign"}),
            lambda p: p["readback"]["queue"].update({"Campaign Tab": "Other campaign"}),
        ]
        for mutate in mutations:
            payload = tracker_update()
            mutate(payload)
            self.assertHeld(payload)

    def test_partial_backend_update_cannot_pass(self):
        for table in ("campaign", "registry", "queue", "action_log"):
            payload = tracker_update()
            del payload["readback"][table]
            self.assertHeld(payload)
        payload = tracker_update()
        payload["readback"]["campaign"]["Status"] = "Verification Sent"
        self.assertHeld(payload)

    def test_unplanned_source_or_registry_changes_hold(self):
        for table, field in (("campaign", "Email"), ("registry", "Contact Fingerprint"), ("queue", "Campaign Tab")):
            payload = tracker_update()
            payload["readback"][table][field] = "unexpected private replacement"
            self.assertHeld(payload)

    def test_unplanned_new_field_is_rejected_in_each_backend_record(self):
        for table in ("campaign", "registry", "queue"):
            payload = tracker_update()
            payload["readback"][table]["Unexpected Field"] = "unplanned value"
            self.assertHeld(payload)

    def test_queue_cannot_retain_stale_campaign_status(self):
        payload = tracker_update()
        payload["expected"]["queue"]["Current Status"] = "Verification Sent"
        payload["readback"]["queue"]["Current Status"] = "Verification Sent"
        self.assertHeld(payload)

    def test_notes_history_and_append_only_event_are_required(self):
        payload = tracker_update()
        payload["expected"]["campaign"]["Notes"] = "Only the new note; history removed."
        payload["readback"]["campaign"].update(payload["expected"]["campaign"])
        self.assertHeld(payload)
        payload = tracker_update()
        payload["before"]["action_log_ids"].append("event-new")
        self.assertHeld(payload)
        payload = tracker_update()
        payload["readback"]["action_log"].append(copy.deepcopy(payload["expected"]["action_log"]))
        self.assertHeld(payload)

    def test_visible_only_or_filtered_overview_readback_is_insufficient(self):
        for table, scope in (("source_scope", "visible_rows"), ("overview_scope", "current_work"), ("overview_scope", [])):
            payload = tracker_update()
            payload["readback"][table] = scope
            self.assertHeld(payload)

    def test_overview_formulas_cannot_be_replaced_by_typed_values(self):
        for role in ("source", "rows", "score"):
            payload = tracker_update()
            payload["readback"]["overview_formulas"][role] = "9/10"
            self.assertHeld(payload)
        payload = tracker_update()
        del payload["overview_formulas"]["score"]
        self.assertHeld(payload)

    def test_overview_source_must_be_unique_and_identity_matched(self):
        for mutation in ("missing", "duplicate", "wrong_identity", "wrong_campaign"):
            payload = tracker_update()
            rows = payload["readback"]["overview"]
            if mutation == "missing":
                rows.clear()
            elif mutation == "duplicate":
                rows.append(copy.deepcopy(rows[0]))
            elif mutation == "wrong_identity":
                rows[0]["Creator Record ID"] = "CCR-EX-26-0002"
            else:
                rows[0]["Campaign Tab"] = "Other campaign"
            self.assertHeld(payload)

    def test_stale_or_missing_overview_score_holds(self):
        payload = tracker_update()
        payload["readback"]["overview"][0]["Score*"] = "10/10"
        self.assertHeld(payload)
        del payload["readback"]["overview"][0]["Score*"]
        self.assertHeld(payload)

    def test_stale_stage_or_planned_display_fields_hold_even_when_score_matches(self):
        payload = tracker_update()
        payload["expected"]["overview"] = {"Stage": "Content review", "Next step": "Review the recorded link"}
        payload["readback"]["overview"][0]["Next step"] = "Review the recorded link"
        self.assertHeld(payload)
        payload["readback"]["overview"][0]["Stage"] = "Content review"
        self.assertEqual(cc.verify_tracker_update(payload)["result"], "PASS")
        payload["readback"]["overview"][0]["Next step"] = "Ask for the same link again"
        self.assertHeld(payload)

    def test_registry_control_holds_cannot_be_hidden_as_ordinary_qualification(self):
        for field, state in (("Record Lock State", "Conflict"), ("Record Lock State", "Reconciliation Required"),
                             ("Record Lock State", "Locked"), ("Record Lock State", "Reserved"),
                             ("Record State", "Conflict")):
            with self.subTest(field=field, state=state):
                payload = tracker_update()
                payload["before"]["registry"][field] = state
                payload["readback"]["registry"][field] = state
                self.assertHeld(payload)
                payload["expected"]["overview"]["Stage"] = "Your review"
                payload["readback"]["overview"][0]["Stage"] = "Your review"
                self.assertEqual(cc.verify_tracker_update(payload)["result"], "PASS")

    def test_score_write_requires_current_evidence_and_computed_parity(self):
        payload = tracker_update()
        payload["expected"]["campaign"]["Total Qualification Score"] = 9
        self.assertHeld(payload)
        payload["qualification"] = creator(creator_record_id=IDENTIFIER, phone="")
        self.assertEqual(cc.verify_tracker_update(payload)["score"], 9)
        payload["qualification"] = creator(creator_record_id=IDENTIFIER)
        self.assertHeld(payload)

    def test_changed_fulfillment_field_cannot_keep_stale_score_without_evidence(self):
        payload = tracker_update()
        payload["expected"]["campaign"]["Phone"] = "555-010-2000"
        payload["readback"]["campaign"]["Phone"] = "555-010-2000"
        self.assertHeld(payload)
        payload["qualification"] = creator(creator_record_id=IDENTIFIER, phone="")
        self.assertHeld(payload)

    def test_updated_fulfillment_evidence_and_score_reach_the_overview_together(self):
        payload = tracker_update()
        payload["expected"]["campaign"].update({"Phone": "555-010-2000", "Total Qualification Score": 10})
        payload["readback"]["campaign"].update(payload["expected"]["campaign"])
        payload["readback"]["overview"][0]["Score*"] = "10/10"
        payload["qualification"] = creator(creator_record_id=IDENTIFIER)
        result = cc.verify_tracker_update(payload)
        self.assertEqual(result["score"], 10)
        self.assertEqual(result["score_label"], "10/10")

    def test_creator_reply_and_background_check_require_fresh_qualification(self):
        for kind in ("creator_reply", "background_check"):
            payload = tracker_update()
            payload["update_kind"] = kind
            self.assertHeld(payload)
            payload["qualification"] = creator(creator_record_id=IDENTIFIER, phone="")
            self.assertEqual(cc.verify_tracker_update(payload)["result"], "PASS")

    def test_qualification_asin_must_match_source_and_registry(self):
        for mutation in ("wrong_requested_asin", "registry_product_conflict", "ambiguous_source_product"):
            payload = tracker_update()
            payload["qualification"] = creator(creator_record_id=IDENTIFIER, phone="")
            if mutation == "wrong_requested_asin":
                payload["qualification"]["requested_asin"] = "B0EXAMPLE2"
            elif mutation == "registry_product_conflict":
                payload["before"]["registry"]["Active Product / ASIN"] = "B0EXAMPLE2"
                payload["readback"]["registry"]["Active Product / ASIN"] = "B0EXAMPLE2"
            else:
                product = "Example products B0EXAMPLE1 and B0EXAMPLE2"
                payload["before"]["campaign"]["Product"] = product
                payload["readback"]["campaign"]["Product"] = product
            self.assertHeld(payload)

    def test_qualification_evidence_must_match_record_and_campaign(self):
        for changes in ({"creator_record_id": "CCR-EX-26-0002"}, {"campaign_id": "other-campaign"}, {"address": ["invalid"]}):
            payload = tracker_update()
            payload["qualification"] = creator(**({"creator_record_id": IDENTIFIER} | changes))
            self.assertHeld(payload)

    def test_operator_hold_must_survive_in_both_view_and_queue(self):
        payload = tracker_update()
        payload["operator_hold"] = True
        payload["expected"]["queue"]["Queue State"] = "Hold"
        payload["readback"]["queue"]["Queue State"] = "Hold"
        payload["expected"]["overview"]["Stage"] = "On hold"
        payload["readback"]["overview"][0]["Stage"] = "On hold"
        payload["readback"]["overview"][0]["Follow-up*"] = "On hold"
        self.assertEqual(cc.verify_tracker_update(payload)["result"], "PASS")
        for mutate in (
            lambda p: p["readback"]["overview"][0].update(Stage="Qualification"),
            lambda p: p["readback"]["queue"].update({"Queue State": "Scheduled"}),
            lambda p: p["readback"]["overview"][0].update({"Follow-up*": "2026-09-30"}),
            lambda p: p.update(operator_hold="false"),
        ):
            bad = copy.deepcopy(payload)
            mutate(bad)
            self.assertHeld(bad)

    def test_readback_log_and_queue_must_follow_the_update(self):
        payload = tracker_update()
        payload["readback"]["captured_at"] = "2026-09-28T06:19:00Z"
        self.assertHeld(payload)
        for table, field in (("action_log", "Timestamp"), ("queue", "Last Updated")):
            payload = tracker_update()
            payload["expected"][table][field] = "2026-09-27T06:20:30Z"
            actual = payload["readback"][table][0] if table == "action_log" else payload["readback"][table]
            actual[field] = payload["expected"][table][field]
            self.assertHeld(payload)

    def test_actioned_checkpoint_requires_a_full_sync_payload(self):
        for change in ({}, {"tracker_updated": False}, {"tracker_update": {"result": "PASS"}}):
            sweep = actioned_sweep()
            sweep["threads"][0].update(change)
            with self.assertRaises(cc.Hold):
                cc.sweep_checkpoint(sweep, b"synthetic-test-key")

    def test_checkpoint_keeps_existing_arcana_schema_and_private_data_out(self):
        checkpoint = cc.sweep_checkpoint(actioned_sweep(tracker_update()), b"synthetic-test-key")
        self.assertEqual(checkpoint["schema_version"], 1)
        self.assertEqual(set(checkpoint["threads"][0]), {"thread_key", "creator_record_id", "sender_role", "amazon_timestamp", "body_hash", "outcome", "reason"})
        exported = json.dumps(checkpoint)
        for private in ("creator@example.test", "Earlier verified history", "=SOURCE()", "synthetic-workbook", "tracker_update"):
            self.assertNotIn(private, exported)

    def test_checkpoint_rejects_receipts_from_other_runs_records_or_windows(self):
        for change in ({"run_id": "other-run"}, {"creator_record_id": "CCR-EX-26-0002"}, {"updated_at": "2026-09-27T06:20:00Z"}):
            payload = tracker_update()
            if "creator_record_id" in change:
                payload = json.loads(json.dumps(payload).replace(IDENTIFIER, change["creator_record_id"]))
            else:
                payload.update(change)
            self.assertEqual(cc.verify_tracker_update(payload)["result"], "PASS")
            with self.assertRaises(cc.Hold):
                cc.sweep_checkpoint(actioned_sweep(payload), b"synthetic-test-key")

    def test_held_thread_with_tracker_changes_also_requires_sync(self):
        sweep = sweep_input()
        self.assertEqual(cc.sweep_checkpoint(sweep, b"synthetic-test-key")["threads"][0]["outcome"], "held")
        sweep["threads"][0]["tracker_updated"] = True
        with self.assertRaises(cc.Hold):
            cc.sweep_checkpoint(sweep, b"synthetic-test-key")
        sweep["threads"][0]["tracker_update"] = tracker_update()
        self.assertEqual(cc.sweep_checkpoint(sweep, b"synthetic-test-key")["threads"][0]["outcome"], "held")
        sweep["threads"][0]["tracker_updated"] = "true"
        with self.assertRaises(cc.Hold):
            cc.sweep_checkpoint(sweep, b"synthetic-test-key")

    def test_malformed_snapshot_input_holds_without_echoing_private_values(self):
        for payload in (None, [], {}, tracker_update() | {"expected": None}):
            self.assertHeld(payload)
        payload = tracker_update()
        payload["readback"]["campaign"]["Email"] = "private-replacement@example.test"
        with self.assertRaises(cc.Hold) as held:
            cc.verify_tracker_update(payload)
        self.assertNotIn("private-replacement", str(held.exception))
        self.assertNotIn("creator@example.test", str(held.exception))

    def test_update_kind_and_explicit_hold_flag_are_required(self):
        for field in ("update_kind", "operator_hold"):
            payload = tracker_update()
            del payload[field]
            self.assertHeld(payload)

    def test_action_log_evidence_reference_must_be_text(self):
        payload = tracker_update()
        evidence = {"Email": "private-marker@example.test"}
        payload["expected"]["action_log"]["Evidence Reference"] = evidence
        payload["readback"]["action_log"][0]["Evidence Reference"] = evidence
        with self.assertRaises(cc.Hold) as held:
            cc.verify_tracker_update(payload)
        self.assertNotIn("private-marker", str(held.exception))

    def run_cli(self, payload=None, *, raw_text=None, missing=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "captured-update.json"
            if not missing:
                path.write_text(json.dumps(payload) if raw_text is None else raw_text, encoding="utf-8")
            environment = os.environ.copy()
            environment.pop("CREATOR_CONTROL_HMAC_KEY", None)
            return subprocess.run([sys.executable, str(MODULE), "verify-tracker-update", "--input", str(path)],
                                  capture_output=True, text=True, env=environment, timeout=10)

    def test_read_only_cli_needs_no_signing_key(self):
        completed = self.run_cli(tracker_update())
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertEqual(json.loads(completed.stdout)["result"], "PASS")

    def test_cli_failure_is_private_hold_not_a_traceback(self):
        payload = tracker_update()
        payload["readback"]["campaign"]["Email"] = "private-replacement@example.test"
        completed = self.run_cli(payload)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["result"], "HOLD")
        self.assertNotIn("private-replacement", completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_invalid_json_and_unreadable_input_are_private_holds(self):
        for options in ({"raw_text": '{"Email":"private-marker@example.test",}'}, {"missing": True}):
            completed = self.run_cli(**options)
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["result"], "HOLD")
            self.assertNotIn("private-marker", completed.stdout + completed.stderr)
            self.assertNotIn("Traceback", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from template_engine import (
    MarketplacePart,
    MonthlyRunEvidence,
    MonthlySourceRegistry,
    missing_operator_inputs,
    monthly_delivery_directory,
)


class TemplateEngineTests(unittest.TestCase):
    def test_monthly_delivery_directory_uses_required_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = monthly_delivery_directory("July", Path(temp_dir))
            self.assertEqual(destination, Path(temp_dir) / "July Monthly Reports")
            self.assertTrue(destination.is_dir())

    def test_monthly_delivery_directory_rejects_path_input(self) -> None:
        with self.assertRaises(ValueError):
            monthly_delivery_directory("July/Reports", create=False)

    def test_marketplace_part_requires_source_boundaries(self) -> None:
        part = MarketplacePart(
            code="US",
            display_name="United States",
            currency_symbol="$",
            sellerboard_account="Brand US",
            adlabs_profile="Brand US",
            adlabs_dashboard="Brand US",
        )
        part.validate()

        invalid = MarketplacePart(
            code="AU",
            display_name="Australia",
            currency_symbol="A$",
            sellerboard_account="",
            adlabs_profile="Brand AU",
            adlabs_dashboard="Brand AU",
            datadive_supported=False,
        )
        with self.assertRaisesRegex(ValueError, "sellerboard_account"):
            invalid.validate()

    def test_complete_monthly_handoff_requests_nothing(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Example Brand US",
            sellerboard_grouping="parent",
            adlabs_profile="Example Brand US",
            adlabs_dashboard="Example Brand US",
            focus_products=("Product A", "Product B", "Product C"),
            slack_channel="#example-brand-amazon",
        )
        evidence = MonthlyRunEvidence(
            sellerboard_current_month=True,
            sellerboard_previous_month=True,
            sellerboard_parent_grouping_verified=True,
            adlabs_dashboard_current_month=True,
            adlabs_dashboard_previous_month=True,
            rank_radar_products=frozenset(
                {"Product A", "Product B", "Product C"}
            ),
            meeting_notes_status="supplied",
            slack_accessible=True,
        )
        self.assertEqual(missing_operator_inputs(registry, evidence), ())

    def test_saved_slack_channel_is_not_requested_again(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Brand US",
            sellerboard_grouping="parent",
            adlabs_profile="Brand US",
            adlabs_dashboard="Brand US",
            focus_products=("Product",),
            slack_channel="#brand-amazon-ew",
        )
        evidence = MonthlyRunEvidence(
            sellerboard_current_month=True,
            sellerboard_previous_month=True,
            sellerboard_parent_grouping_verified=True,
            adlabs_dashboard_current_month=True,
            adlabs_dashboard_previous_month=True,
            rank_radar_products=frozenset({"Product"}),
            meeting_notes_status="none_confirmed",
        )
        requests = missing_operator_inputs(registry, evidence)
        self.assertFalse(any("Slack" in request for request in requests))

    def test_missing_monthly_evidence_returns_only_missing_inputs(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Brand US",
            sellerboard_grouping="parent",
            adlabs_profile="Brand US",
            adlabs_dashboard="Brand US",
            focus_products=("Product A", "Product B"),
            slack_channel="#brand-amazon-ew",
        )
        evidence = MonthlyRunEvidence(
            sellerboard_current_month=True,
            sellerboard_parent_grouping_verified=True,
            adlabs_dashboard_current_month=True,
            rank_radar_products=frozenset({"Product A"}),
        )
        requests = missing_operator_inputs(registry, evidence)
        self.assertEqual(len(requests), 4)
        self.assertTrue(any("comparison month" in request for request in requests))
        self.assertTrue(any("Product B" in request for request in requests))
        self.assertTrue(any("Meeting notes" in request for request in requests))
        self.assertFalse(any("Slack" in request for request in requests))

    def test_unsupported_datadive_marketplace_skips_rank_radar(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Example Brand AU",
            sellerboard_grouping="parent",
            adlabs_profile="Example Brand AU",
            adlabs_dashboard="Example Brand AU",
            focus_products=("Cream", "Balm"),
            slack_channel="#example-brand-au-amazon",
            datadive_supported=False,
        )
        evidence = MonthlyRunEvidence(
            sellerboard_current_month=True,
            sellerboard_previous_month=True,
            sellerboard_parent_grouping_verified=True,
            adlabs_dashboard_current_month=True,
            adlabs_dashboard_previous_month=True,
            meeting_notes_status="supplied",
        )
        self.assertEqual(missing_operator_inputs(registry, evidence), ())

    def test_source_registry_requires_parent_grouping(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Brand",
            sellerboard_grouping="asin",
            adlabs_profile="Brand",
            adlabs_dashboard="Brand",
            focus_products=("Product",),
        )
        with self.assertRaisesRegex(ValueError, "grouping must be 'parent'"):
            registry.validate()


if __name__ == "__main__":
    unittest.main()

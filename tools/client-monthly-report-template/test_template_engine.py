from __future__ import annotations

import unittest
from pathlib import Path

from template_engine import (
    CoverItem,
    CoverSpec,
    MarketplacePart,
    MonthlyRunEvidence,
    MonthlySourceRegistry,
    OptionalSection,
    PageModule,
    ReportDefinition,
    compose_report,
    missing_operator_inputs,
)


def _page(key: str, label: str | None = None) -> PageModule:
    return PageModule(key=key, toc_label=label or key, renderer=lambda backend, n: None)


def _definition(**overrides: object) -> ReportDefinition:
    base = dict(
        brand_slug="example-us",
        title="Example Monthly Report",
        output_path=Path("output/example-us/reporting/example.docx"),
        cover_spec=CoverSpec(
            report_label="PERFORMANCE REPORT - JULY 2026",
            period_line="July 1 - July 31, 2026",
            title="Example Monthly Report",
            overview="Monthly performance overview.",
            contents=(
                CoverItem("KPI overview and break-even ACOS guardrail"),
                CoverItem("Root-cause package", requires_optional_section="root_cause"),
            ),
        ),
        cover_renderer=lambda backend, pages, total, enabled: None,
        base_pages=(
            _page("kpi_overview"),
            _page("break_even_guardrail"),
            _page("traffic_segments"),
            _page("top_search_terms"),
            _page("placements"),
            _page("product_focus"),
            _page("sqp_product_view"),
        ),
        closing_pages=(_page("goals_priorities"),),
    )
    base.update(overrides)
    return ReportDefinition(**base)  # type: ignore[arg-type]


class TemplateEngineTests(unittest.TestCase):
    def test_compose_report_orders_pages_and_reports_total(self) -> None:
        totals: list[int] = []
        definition = _definition(configure_page_total=totals.append)
        pages = compose_report(definition)
        self.assertEqual(pages[-1].key, "goals_priorities")
        self.assertEqual(totals, [len(pages)])

    def test_compose_report_rejects_missing_required_page(self) -> None:
        definition = _definition(base_pages=(_page("kpi_overview"),))
        with self.assertRaisesRegex(ValueError, "Missing required base pages"):
            compose_report(definition)

    def test_optional_section_is_blocked_for_other_brands(self) -> None:
        section = OptionalSection(
            key="root_cause",
            toc_label="Root-cause package",
            pages=(_page("root_cause_overview", "Root-cause package"),),
            allowed_brands=frozenset({"other-brand-de"}),
        )
        definition = _definition(
            optional_sections={"root_cause": section},
            enabled_optional_sections=("root_cause",),
        )
        with self.assertRaisesRegex(ValueError, "restricted to"):
            compose_report(definition)

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

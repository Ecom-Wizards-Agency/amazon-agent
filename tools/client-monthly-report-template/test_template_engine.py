from __future__ import annotations

import json
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
    rank_tracker_marketplace_supported,
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
        # AU is covered by the SoldScope rank tracker; the legacy DataDive
        # flag no longer decides once the marketplace code is known.
        self.assertTrue(invalid.rank_tracking_supported)
        japan = MarketplacePart(
            code="JP",
            display_name="Japan",
            currency_symbol="¥",
            sellerboard_account="Brand JP",
            adlabs_profile="Brand JP",
            adlabs_dashboard="Brand JP",
        )
        self.assertFalse(japan.rank_tracking_supported)

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
            rank_tracker_products=frozenset(
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
            rank_tracker_products=frozenset({"Product"}),
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
            rank_tracker_products=frozenset({"Product A"}),
        )
        requests = missing_operator_inputs(registry, evidence)
        self.assertEqual(len(requests), 4)
        self.assertTrue(any("comparison month" in request for request in requests))
        self.assertTrue(any("Product B" in request for request in requests))
        self.assertTrue(
            any("SoldScope rank tracker" in request for request in requests)
        )
        self.assertTrue(any("Meeting notes" in request for request in requests))
        self.assertFalse(any("Slack" in request for request in requests))

    @staticmethod
    def _complete_evidence_without_rank() -> MonthlyRunEvidence:
        return MonthlyRunEvidence(
            sellerboard_current_month=True,
            sellerboard_previous_month=True,
            sellerboard_parent_grouping_verified=True,
            adlabs_dashboard_current_month=True,
            adlabs_dashboard_previous_month=True,
            meeting_notes_status="supplied",
        )

    def test_rank_tracker_marketplace_list(self) -> None:
        supported = (
            "US", "CA", "MX", "BR", "DE", "ES", "FR", "IT",
            "UK", "NL", "SE", "IN", "TR", "AE", "SA", "AU",
        )
        for code in supported:
            self.assertTrue(rank_tracker_marketplace_supported(code), code)
        self.assertTrue(rank_tracker_marketplace_supported("gb"))
        for code in ("JP", "PL", "BE", "SG", ""):
            self.assertFalse(rank_tracker_marketplace_supported(code), code)

    def test_unsupported_rank_tracker_marketplace_skips_rank_screenshot(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Example Brand JP",
            sellerboard_grouping="parent",
            adlabs_profile="Example Brand JP",
            adlabs_dashboard="Example Brand JP",
            focus_products=("Cream", "Balm"),
            slack_channel="#example-brand-jp-amazon",
            marketplace="JP",
        )
        self.assertFalse(registry.rank_tracking_supported)
        self.assertEqual(
            missing_operator_inputs(registry, self._complete_evidence_without_rank()),
            (),
        )

    def test_au_is_supported_by_rank_tracker(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Example Brand AU",
            sellerboard_grouping="parent",
            adlabs_profile="Example Brand AU",
            adlabs_dashboard="Example Brand AU",
            focus_products=("Cream", "Balm"),
            slack_channel="#example-brand-au-amazon",
            marketplace="AU",
            datadive_supported=False,
        )
        requests = missing_operator_inputs(
            registry, self._complete_evidence_without_rank()
        )
        self.assertEqual(len(requests), 1)
        self.assertIn("SoldScope rank tracker", requests[0])
        self.assertIn("Cream, Balm", requests[0])

    def test_legacy_datadive_flag_applies_without_marketplace(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Example Brand",
            sellerboard_grouping="parent",
            adlabs_profile="Example Brand",
            adlabs_dashboard="Example Brand",
            focus_products=("Cream",),
            slack_channel="#example-brand-amazon",
            datadive_supported=False,
        )
        self.assertEqual(
            missing_operator_inputs(registry, self._complete_evidence_without_rank()),
            (),
        )

    def test_legacy_rank_radar_products_still_count(self) -> None:
        registry = MonthlySourceRegistry(
            sellerboard_account="Example Brand",
            sellerboard_grouping="parent",
            adlabs_profile="Example Brand",
            adlabs_dashboard="Example Brand",
            focus_products=("Cream",),
            slack_channel="#example-brand-amazon",
            marketplace="US",
        )
        evidence = MonthlyRunEvidence(
            sellerboard_current_month=True,
            sellerboard_previous_month=True,
            sellerboard_parent_grouping_verified=True,
            adlabs_dashboard_current_month=True,
            adlabs_dashboard_previous_month=True,
            rank_radar_products=frozenset({"Cream"}),
            meeting_notes_status="supplied",
        )
        self.assertEqual(missing_operator_inputs(registry, evidence), ())

    def test_brand_config_reads_rank_tracker_keys(self) -> None:
        config = json.loads(
            (Path(__file__).parent / "brand-config.example.json").read_text(
                encoding="utf-8"
            )
        )
        config["focus_products"][0]["rank_tracker_group_id"] = "9000"
        config["focus_products"][0].pop("rank_tracker_url")
        registry = MonthlySourceRegistry.from_brand_config(config)
        registry.validate()
        self.assertEqual(registry.marketplace, "US")
        self.assertTrue(registry.rank_tracking_supported)
        self.assertEqual(registry.rank_tracker_group_ids, {"Focus Product": "9000"})
        self.assertEqual(
            registry.rank_tracker_urls,
            {"Focus Product": "https://app.soldscope.com/rank-tracker/9000"},
        )

    def test_brand_config_falls_back_to_legacy_rank_radar_keys(self) -> None:
        config = {
            "brand": {},
            "sources": {
                "sellerboard_account": "Legacy Brand",
                "sellerboard_grouping": "parent",
                "adlabs_profile": "Legacy Brand",
                "adlabs_dashboard": "Legacy Brand",
                "slack_channel": "#legacy-brand-amazon",
                "datadive_marketplace_supported": False,
            },
            "focus_products": [
                {
                    "name": "Legacy Product",
                    "rank_radar_id": "rr-1",
                    "rank_radar_url": "https://example.invalid/rank-radar/rr-1",
                }
            ],
        }
        registry = MonthlySourceRegistry.from_brand_config(config)
        self.assertEqual(registry.rank_tracker_group_ids, {"Legacy Product": "rr-1"})
        self.assertEqual(
            registry.rank_tracker_urls,
            {"Legacy Product": "https://example.invalid/rank-radar/rr-1"},
        )
        self.assertFalse(registry.rank_tracking_supported)

        config["sources"].pop("datadive_marketplace_supported")
        config["sources"]["datadive_supported"] = False
        self.assertFalse(
            MonthlySourceRegistry.from_brand_config(config).rank_tracking_supported
        )

        config["sources"]["rank_tracker_marketplace_supported"] = True
        self.assertTrue(
            MonthlySourceRegistry.from_brand_config(config).rank_tracking_supported
        )

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

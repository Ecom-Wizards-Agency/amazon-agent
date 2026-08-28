from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from launch_model import break_even_acos, build_model, contribution_per_unit, validate_config  # noqa: E402


class LaunchModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = Path(__file__).parent / "fixtures" / "generic.json"
        cls.base = json.loads(fixture.read_text(encoding="utf-8"))

    def test_revenue_ppc_and_acos(self):
        model = build_model(copy.deepcopy(self.base))
        row = next(r for r in model["rows"] if r["scenario_id"] == "base" and r["week"] == 1)
        self.assertAlmostEqual(row["ad_spend"], 80.0)
        self.assertAlmostEqual(row["ad_orders"], 4.0)
        self.assertAlmostEqual(row["ad_sales"], 179.96)
        self.assertAlmostEqual(row["revenue"], 359.92)
        self.assertAlmostEqual(row["ad_spend"] / row["ad_sales"], 80.0 / 179.96)

    def test_break_even_acos_uses_unit_economics(self):
        product = self.base["products"][0]
        self.assertAlmostEqual(contribution_per_unit(product), 19.99)
        self.assertAlmostEqual(break_even_acos(product), 19.99 / 44.99)

    def test_external_halo_is_separate(self):
        model = build_model(copy.deepcopy(self.base))
        row = next(r for r in model["rows"] if r["scenario_id"] == "base" and r["week"] == 1)
        self.assertEqual(row["external_halo_units"], 2)
        self.assertAlmostEqual(row["unconstrained_demand"], row["ad_orders"] + row["organic_units"] + 2)
        self.assertAlmostEqual(row["ad_sales"], row["ad_orders"] * row["effective_price"])

    def test_vine_allocation_and_stock_depletion(self):
        model = build_model(copy.deepcopy(self.base))
        week1 = next(r for r in model["rows"] if r["scenario_id"] == "base" and r["week"] == 1)
        self.assertEqual(week1["vine_units"], 30)
        self.assertAlmostEqual(week1["closing_stock"], 500 - 30 - week1["fulfilled_units"])
        week2 = next(r for r in model["rows"] if r["scenario_id"] == "base" and r["week"] == 2)
        self.assertAlmostEqual(week2["opening_stock"], week1["closing_stock"])

    def test_reorder_calculation_uses_confirmed_lead_time_and_moq(self):
        model = build_model(copy.deepcopy(self.base))
        summary = next(s for s in model["stock_summary"] if s["scenario_id"] == "high")
        self.assertEqual(summary["lead_time_weeks"], 10)
        self.assertIsNotNone(summary["reorder_week"])
        self.assertEqual(summary["recommended_reorder_units"] % 500, 0)

    def test_missing_inputs_produce_directional_status(self):
        config = copy.deepcopy(self.base)
        config["products"][0]["unit_economics"]["landed_cogs"] = None
        config["products"][0]["inventory"]["opening_stock"] = None
        result = validate_config(config)
        self.assertEqual(result["status"], "DIRECTIONAL")
        labels = {item["label"] for item in result["missing"]}
        self.assertIn("Daily Greens: landed COGS", labels)
        self.assertIn("Daily Greens: available US stock", labels)

    def test_zero_sales_does_not_divide_by_zero(self):
        config = copy.deepcopy(self.base)
        for scenario in config["scenarios"]:
            values = scenario["products"]["daily-greens"]
            for field in ("paid_clicks_per_week", "organic_units_per_week", "external_halo_units_per_week"):
                values[field] = {phase: 0 for phase in ("launch", "scale", "stabilize")}
        model = build_model(config)
        summary = next(s for s in model["scenario_summary"] if s["scenario_id"] == "base")
        self.assertEqual(summary["revenue"], 0)
        self.assertIsNone(summary["acos"])

    def test_unavailable_margin_remains_none(self):
        config = copy.deepcopy(self.base)
        config["products"][0]["unit_economics"]["amazon_fees"] = None
        model = build_model(config)
        pricing = next(p for p in model["pricing_summary"] if p["product_id"] == "daily-greens")
        self.assertIsNone(pricing["contribution_per_unit_before_ads"])
        self.assertIsNone(pricing["break_even_acos"])

    def test_delayed_inbound_and_demand_above_stock(self):
        config = copy.deepcopy(self.base)
        config["products"][0]["inventory"]["opening_stock"] = 5
        config["products"][0]["inventory"]["inbound"] = [{"week": 10, "units": 20}]
        config["products"][0]["reviews"]["vine_units"] = 0
        model = build_model(config)
        week1 = next(r for r in model["rows"] if r["scenario_id"] == "high" and r["week"] == 1)
        self.assertGreater(week1["unmet_demand"], 0)
        self.assertEqual(week1["closing_stock"], 0)
        week10 = next(r for r in model["rows"] if r["scenario_id"] == "high" and r["week"] == 10)
        self.assertEqual(week10["inbound_units"], 20)

    def test_no_external_channel_data_means_zero_halo(self):
        config = copy.deepcopy(self.base)
        config["external_channels"] = {"current_meta_spend": None, "current_google_spend": None, "branded_search_contribution": None, "planned_launch_support": None}
        for scenario in config["scenarios"]:
            values = scenario["products"]["daily-greens"]
            values["external_halo_units_per_week"] = {phase: 0 for phase in ("launch", "scale", "stabilize")}
            values["halo_basis"] = "No external halo assumed"
        model = build_model(config)
        self.assertEqual(sum(r["external_halo_units"] for r in model["rows"]), 0)

    def test_incentivized_review_strategy_fails(self):
        config = copy.deepcopy(self.base)
        config["reviews"]["methods"].append("creator_purchase_for_review")
        result = validate_config(config)
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(any("Prohibited review methods" in error for error in result["errors"]))

    def test_duplicate_review_request_strategy_fails(self):
        config = copy.deepcopy(self.base)
        helium = config["reviews"]["helium10_follow_up"]
        helium["enabled"] = True
        helium["deduplicate_with_seller_central"] = False
        result = validate_config(config)
        self.assertEqual(result["status"], "ERROR")
        self.assertTrue(any("deduplicate" in error.lower() for error in result["errors"]))

    def _tmrw_commercial_config(self):
        config = copy.deepcopy(self.base)
        first = config["products"][0]
        starter = copy.deepcopy(first)
        starter.update({"id": "starter-kit", "name": "TMRW Starter Kit", "list_price": 104.99, "launch_price": 104.99})
        refill = copy.deepcopy(first)
        refill.update({"id": "refill-pouch", "name": "TMRW Refill Pouch", "list_price": 99.99, "launch_price": 99.99})
        starter["reviews"]["vine_units"] = 0
        refill["reviews"]["vine_units"] = 0
        config["products"] = [starter, refill]
        for scenario in config["scenarios"]:
            assumptions = copy.deepcopy(scenario["products"]["daily-greens"])
            scenario["products"] = {"starter-kit": copy.deepcopy(assumptions), "refill-pouch": copy.deepcopy(assumptions)}
        allocations = {
            "month_1": {"high_intent_non_branded": 0.45, "discovery": 0.25, "competitor_keywords": 0.15, "competitor_product_targeting": 0.10, "branded_defense": 0.05},
            "month_2": {"high_intent_non_branded": 0.50, "discovery": 0.15, "competitor_keywords": 0.15, "competitor_product_targeting": 0.15, "branded_defense": 0.05},
            "month_3": {"high_intent_non_branded": 0.55, "discovery": 0.10, "competitor_keywords": 0.15, "competitor_product_targeting": 0.15, "branded_defense": 0.05},
        }
        config["commercial_targets"] = {
            "daily_revenue_milestones": {"month_1_exit": 300, "month_2_exit": 1000, "month_3_committed": 1000, "month_3_stretch": 2000},
            "stock_safety_buffer_pct": 0.20,
            "stock_rounding_increment": 25,
            "product_mix_by_month": {
                "month_1": {"starter-kit": 0.85, "refill-pouch": 0.15},
                "month_2": {"starter-kit": 0.75, "refill-pouch": 0.25},
                "month_3": {"starter-kit": 0.65, "refill-pouch": 0.35},
            },
            "ppc_plan": {
                "month_1": {"label": "Month 1", "planned_spend": 2000, "spend_ceiling": 3000, "planning_cpc": 2, "planning_cvr": 0.04, "campaign_allocation": allocations["month_1"]},
                "month_2": {"label": "Month 2", "planned_spend": 4500, "spend_ceiling": 6000, "planning_cpc": 2, "planning_cvr": 0.08, "campaign_allocation": allocations["month_2"]},
                "month_3_committed": {"label": "Month 3 committed", "planned_spend": 6500, "spend_ceiling": 9000, "planning_cpc": 2, "planning_cvr": 0.10, "campaign_allocation": allocations["month_3"]},
                "month_3_stretch": {"label": "Month 3 stretch", "planned_spend": 10000, "spend_ceiling": 12000, "planning_cpc": 2, "planning_cvr": 0.10, "campaign_allocation": allocations["month_3"]},
            },
            "keywords": {},
        }
        return config

    def test_commercial_revenue_paths_units_mix_and_stock_buffer(self):
        model = build_model(self._tmrw_commercial_config())
        commercial = model["commercial"]
        summaries = {item["path_id"]: item for item in commercial["summaries"]}
        self.assertAlmostEqual(summaries["committed"]["target_revenue"], 57400)
        self.assertAlmostEqual(summaries["stretch"]["target_revenue"], 74900)
        self.assertAlmostEqual(summaries["capacity"]["target_revenue"], 92400)
        self.assertEqual(round(summaries["committed"]["forecast_units"]), 555)
        self.assertEqual(round(summaries["stretch"]["forecast_units"]), 724)
        self.assertEqual(summaries["committed"]["customer_sale_inventory_required"], 675)
        self.assertEqual(summaries["stretch"]["customer_sale_inventory_required"], 875)
        self.assertEqual(summaries["capacity"]["customer_sale_inventory_required"], 1075)
        committed_units = summaries["committed"]["product_units"]
        starter_mix = committed_units["starter-kit"] / summaries["committed"]["forecast_units"]
        self.assertAlmostEqual(starter_mix, 0.696, places=2)

    def test_commercial_ppc_allocations_and_ceilings(self):
        config = self._tmrw_commercial_config()
        result = validate_config(config)
        self.assertEqual(result["errors"], [])
        for plan in config["commercial_targets"]["ppc_plan"].values():
            self.assertLessEqual(plan["planned_spend"], plan["spend_ceiling"])
            self.assertAlmostEqual(sum(plan["campaign_allocation"].values()), 1.0)
            self.assertEqual(plan["campaign_allocation"]["branded_defense"], 0.05)

    def test_commercial_ppc_validation_rejects_overspend(self):
        config = self._tmrw_commercial_config()
        config["commercial_targets"]["ppc_plan"]["month_1"]["planned_spend"] = 4000
        result = validate_config(config)
        self.assertTrue(any("cannot exceed" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

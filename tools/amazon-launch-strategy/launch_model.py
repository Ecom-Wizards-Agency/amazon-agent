"""Deterministic 13-week Amazon launch forecast model."""

from __future__ import annotations

import math
from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from typing import Any


SCHEMA_VERSION = "amazon-launch-strategy.v1"
MONTHS = {
    "Month 1": range(1, 5),
    "Month 2": range(5, 9),
    "Month 3": range(9, 14),
}
SCENARIO_IDS = ("low", "base", "high")
PROHIBITED_REVIEW_TYPES = {
    "incentivized_review",
    "review_gating",
    "creator_purchase_for_review",
    "disguised_compensation",
}
COMMERCIAL_MONTHS = (
    ("month_1", "Month 1", 28),
    ("month_2", "Month 2", 28),
    ("month_3", "Month 3", 35),
)
CAMPAIGN_PURPOSES = (
    "high_intent_non_branded",
    "discovery",
    "competitor_keywords",
    "competitor_product_targeting",
    "branded_defense",
)


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _phase_value(values: dict[str, Any], phase_id: str, default: Any = 0) -> Any:
    value = values.get(phase_id, default)
    return default if value is None else value


def launch_products(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [p for p in config.get("products", []) if p.get("phase") == "launch"]


def effective_price(product: dict[str, Any]) -> float:
    launch_price = _num(product.get("launch_price"))
    if launch_price is not None:
        return launch_price
    list_price = _num(product.get("list_price")) or 0.0
    coupon_pct = _num(product.get("coupon_pct")) or 0.0
    return list_price * (1.0 - coupon_pct)


def contribution_per_unit(product: dict[str, Any]) -> float | None:
    economics = product.get("unit_economics", {})
    required = [
        economics.get("landed_cogs"),
        economics.get("amazon_fees"),
        economics.get("other_variable_costs"),
    ]
    if any(v is None or v == "" for v in required):
        return None
    coupon_fee = _num(economics.get("coupon_fee_per_redemption")) or 0.0
    return effective_price(product) - sum(float(v) for v in required) - coupon_fee


def break_even_acos(product: dict[str, Any]) -> float | None:
    price = effective_price(product)
    contribution = contribution_per_unit(product)
    if contribution is None or price <= 0:
        return None
    return max(0.0, contribution / price)


def phases_by_week(config: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for phase in config.get("ppc", {}).get("phases", []):
        for week in range(int(phase["start_week"]), int(phase["end_week"]) + 1):
            result[week] = phase
    return result


def validate_review_policy(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    reviews = config.get("reviews", {})
    methods = set(reviews.get("methods", []))
    forbidden = sorted(methods & PROHIBITED_REVIEW_TYPES)
    if forbidden:
        errors.append("Prohibited review methods: " + ", ".join(forbidden))

    helium = reviews.get("helium10_follow_up", {})
    if helium.get("enabled"):
        if not helium.get("amazon_standard_template_only"):
            errors.append("Helium 10 Follow-Up must use Amazon's standard template only.")
        if helium.get("max_requests_per_order") != 1:
            errors.append("Helium 10 Follow-Up must send no more than one request per order.")
        if not helium.get("deduplicate_with_seller_central"):
            errors.append("Helium 10 Follow-Up must deduplicate against Seller Central requests.")
        if helium.get("incentive_or_custom_review_language"):
            errors.append("Helium 10 Follow-Up cannot contain incentives or custom review language.")
    return errors


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing: list[dict[str, str]] = []

    if config.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}.")

    client = config.get("client", {})
    for key in ("name", "brand", "account", "marketplace", "currency", "output_dir"):
        if not client.get(key):
            errors.append(f"client.{key} is required.")

    products = launch_products(config)
    if not products:
        errors.append("At least one product with phase=launch is required.")
    ids = [p.get("id") for p in config.get("products", [])]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        errors.append("Every product needs a unique non-empty id.")
    for product in products:
        if effective_price(product) <= 0:
            errors.append(f"{product.get('id')}: list_price or launch_price must be positive.")

    phase_map = phases_by_week(config)
    if set(phase_map) != set(range(1, 14)):
        errors.append("ppc.phases must cover every week from 1 through 13 exactly once.")

    scenarios = {s.get("id"): s for s in config.get("scenarios", [])}
    if set(scenarios) != set(SCENARIO_IDS):
        errors.append("scenarios must contain exactly low, base, and high ids.")
    for scenario_id, scenario in scenarios.items():
        scenario_products = scenario.get("products", {})
        for product in products:
            product_id = product["id"]
            if product_id not in scenario_products:
                errors.append(f"{scenario_id}: missing scenario inputs for {product_id}.")
                continue
            values = scenario_products[product_id]
            for phase in config.get("ppc", {}).get("phases", []):
                phase_id = phase["id"]
                for field in ("cpc", "cvr", "paid_clicks_per_week", "organic_units_per_week", "external_halo_units_per_week"):
                    if phase_id not in values.get(field, {}):
                        errors.append(f"{scenario_id}/{product_id}: missing {field}.{phase_id}.")
                halo = _num(_phase_value(values.get("external_halo_units_per_week", {}), phase_id, 0)) or 0
                if halo > 0 and not values.get("halo_basis"):
                    errors.append(f"{scenario_id}/{product_id}: halo units require a non-empty halo_basis.")

    errors.extend(validate_review_policy(config))

    commercial = config.get("commercial_targets")
    if commercial:
        milestones = commercial.get("daily_revenue_milestones", {})
        for key in ("month_1_exit", "month_2_exit", "month_3_committed", "month_3_stretch"):
            value = _num(milestones.get(key))
            if value is None or value < 0:
                errors.append(f"commercial_targets.daily_revenue_milestones.{key} must be zero or positive.")
        buffer_pct = _num(commercial.get("stock_safety_buffer_pct"))
        if buffer_pct is None or buffer_pct < 0:
            errors.append("commercial_targets.stock_safety_buffer_pct must be zero or positive.")
        increment = _num(commercial.get("stock_rounding_increment"))
        if increment is None or increment <= 0:
            errors.append("commercial_targets.stock_rounding_increment must be positive.")

        launch_ids = {product["id"] for product in products}
        mixes = commercial.get("product_mix_by_month", {})
        for month_key, _, _ in COMMERCIAL_MONTHS:
            mix = mixes.get(month_key, {})
            if set(mix) != launch_ids:
                errors.append(f"commercial_targets.product_mix_by_month.{month_key} must contain every launch product exactly once.")
            elif not math.isclose(sum(float(value) for value in mix.values()), 1.0, abs_tol=1e-9):
                errors.append(f"commercial_targets.product_mix_by_month.{month_key} must total 100%.")

        ppc_plan = commercial.get("ppc_plan", {})
        for plan_id in ("month_1", "month_2", "month_3_committed", "month_3_stretch"):
            plan = ppc_plan.get(plan_id, {})
            planned = _num(plan.get("planned_spend"))
            ceiling = _num(plan.get("spend_ceiling"))
            if planned is None or ceiling is None or planned < 0 or ceiling < 0:
                errors.append(f"commercial_targets.ppc_plan.{plan_id} needs non-negative planned_spend and spend_ceiling.")
            elif planned > ceiling:
                errors.append(f"commercial_targets.ppc_plan.{plan_id}.planned_spend cannot exceed its ceiling.")
            allocation = plan.get("campaign_allocation", {})
            if set(allocation) != set(CAMPAIGN_PURPOSES):
                errors.append(f"commercial_targets.ppc_plan.{plan_id}.campaign_allocation must contain the five campaign purposes.")
            elif not math.isclose(sum(float(value) for value in allocation.values()), 1.0, abs_tol=1e-9):
                errors.append(f"commercial_targets.ppc_plan.{plan_id}.campaign_allocation must total 100%.")
            elif not math.isclose(float(allocation["branded_defense"]), 0.05, abs_tol=1e-9):
                errors.append(f"commercial_targets.ppc_plan.{plan_id}.branded_defense must remain 5%.")

    baseline = config.get("baseline", {})
    if baseline.get("current_revenue") is None:
        missing.append({"field": "baseline.current_revenue", "label": "Current marketplace revenue"})
    if not baseline.get("orders_by_product"):
        missing.append({"field": "baseline.orders_by_product", "label": "Current orders by product"})

    external = config.get("external_channels", {})
    for key, label in (
        ("current_meta_spend", "Current Meta spend"),
        ("current_google_spend", "Current Google spend"),
        ("branded_search_contribution", "Branded-search contribution"),
        ("planned_launch_support", "Planned Meta and Google launch support"),
    ):
        if external.get(key) is None:
            missing.append({"field": f"external_channels.{key}", "label": label})

    if not client.get("launch_date"):
        missing.append({"field": "client.launch_date", "label": "Confirmed launch date"})

    for product in products:
        pid = product["id"]
        economics = product.get("unit_economics", {})
        for key, label in (
            ("landed_cogs", "landed COGS"),
            ("amazon_fees", "Amazon fees"),
            ("other_variable_costs", "other variable costs"),
            ("discount_floor", "discount floor"),
        ):
            if economics.get(key) is None:
                missing.append({"field": f"products.{pid}.unit_economics.{key}", "label": f"{product['name']}: {label}"})
        inventory = product.get("inventory", {})
        if inventory.get("opening_stock") is None:
            missing.append({"field": f"products.{pid}.inventory.opening_stock", "label": f"{product['name']}: available US stock"})
        if inventory.get("inbound") is None:
            missing.append({"field": f"products.{pid}.inventory.inbound", "label": f"{product['name']}: inbound US stock"})
        if inventory.get("moq") is None:
            missing.append({"field": f"products.{pid}.inventory.moq", "label": f"{product['name']}: production MOQ"})
        for key, label in (
            ("production_weeks", "production time"),
            ("freight_weeks", "freight time"),
            ("fba_checkin_weeks", "FBA receiving buffer"),
        ):
            if inventory.get("lead_times", {}).get(key) is None:
                missing.append({"field": f"products.{pid}.inventory.lead_times.{key}", "label": f"{product['name']}: {label}"})
        if product.get("reviews", {}).get("vine_eligible") is None:
            missing.append({"field": f"products.{pid}.reviews.vine_eligible", "label": f"{product['name']}: Vine eligibility"})

    if missing:
        warnings.append("The plan is directional until the listed confirmations are supplied.")
    return {
        "status": "ERROR" if errors else ("DIRECTIONAL" if missing else "READY"),
        "errors": errors,
        "warnings": warnings,
        "missing": missing,
    }


def _lead_time_weeks(product: dict[str, Any]) -> float | None:
    lead = product.get("inventory", {}).get("lead_times", {})
    values = [lead.get("production_weeks"), lead.get("freight_weeks"), lead.get("fba_checkin_weeks")]
    if any(v is None for v in values):
        return None
    return sum(float(v) for v in values)


def _inbound_by_week(product: dict[str, Any]) -> dict[int, float] | None:
    inbound = product.get("inventory", {}).get("inbound")
    if inbound is None:
        return None
    result: dict[int, float] = defaultdict(float)
    for item in inbound:
        result[int(item["week"])] += float(item["units"])
    return dict(result)


def _launch_date(config: dict[str, Any]) -> date | None:
    raw = config.get("client", {}).get("launch_date")
    return date.fromisoformat(raw) if raw else None


def _reorder_label(config: dict[str, Any], week_offset: int | None) -> str:
    if week_offset is None:
        return "Unconfirmed"
    launch = _launch_date(config)
    if launch:
        return (launch + timedelta(weeks=week_offset - 1)).isoformat()
    if week_offset <= 0:
        return f"Day 0 minus {abs(week_offset) + 1} week(s)"
    return f"Week {week_offset}"


def _round_up(value: float, increment: int) -> int:
    return int(math.ceil(value / increment) * increment)


def _daily_ramp(start: float, end: float, days: int) -> list[float]:
    if days <= 1:
        return [end]
    return [start + (end - start) * day / (days - 1) for day in range(days)]


def _allocate_rounded_total(total: int, raw_weights: dict[str, float], increment: int) -> dict[str, int]:
    """Allocate an already rounded stock total without changing the total."""
    product_ids = list(raw_weights)
    remaining = total
    result: dict[str, int] = {}
    for product_id in product_ids[:-1]:
        value = int(round((total * raw_weights[product_id]) / increment) * increment)
        value = max(0, min(value, remaining))
        result[product_id] = value
        remaining -= value
    if product_ids:
        result[product_ids[-1]] = remaining
    return result


def build_commercial_model(config: dict[str, Any]) -> dict[str, Any] | None:
    commercial = config.get("commercial_targets")
    if not commercial:
        return None

    products = {product["id"]: product for product in launch_products(config)}
    milestones = commercial["daily_revenue_milestones"]
    paths = {
        "committed": {
            "label": "Committed",
            "month_3_label": "Maintain $1,000/day",
            "month_3_start": float(milestones["month_3_committed"]),
            "month_3_end": float(milestones["month_3_committed"]),
        },
        "stretch": {
            "label": "Stretch",
            "month_3_label": "Reach $2,000/day",
            "month_3_start": float(milestones["month_3_committed"]),
            "month_3_end": float(milestones["month_3_stretch"]),
        },
        "capacity": {
            "label": "Capacity ceiling",
            "month_3_label": "Hold $2,000/day",
            "month_3_start": float(milestones["month_3_stretch"]),
            "month_3_end": float(milestones["month_3_stretch"]),
        },
    }
    safety_buffer = float(commercial["stock_safety_buffer_pct"])
    stock_increment = int(commercial["stock_rounding_increment"])
    vine_by_product = {
        product_id: int(_num(product.get("reviews", {}).get("vine_units")) or 0)
        for product_id, product in products.items()
    }

    summaries: list[dict[str, Any]] = []
    weekly_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []
    for path_id, path in paths.items():
        daily_by_month = {
            "month_1": _daily_ramp(0.0, float(milestones["month_1_exit"]), 28),
            "month_2": _daily_ramp(float(milestones["month_1_exit"]), float(milestones["month_2_exit"]), 28),
            "month_3": _daily_ramp(path["month_3_start"], path["month_3_end"], 35),
        }
        path_units_by_product: dict[str, float] = defaultdict(float)
        total_revenue = 0.0
        total_units = 0.0
        week_number = 1
        for month_key, month_label, days in COMMERCIAL_MONTHS:
            daily_values = daily_by_month[month_key]
            month_revenue = sum(daily_values)
            mix = commercial["product_mix_by_month"][month_key]
            blended_asp = sum(float(mix[product_id]) * effective_price(products[product_id]) for product_id in products)
            month_units = month_revenue / blended_asp if blended_asp else 0.0
            ppc_plan_id = month_key if month_key != "month_3" else ("month_3_stretch" if path_id in {"stretch", "capacity"} else "month_3_committed")
            ppc = commercial["ppc_plan"][ppc_plan_id]
            planning_cpc = _num(ppc.get("planning_cpc"))
            planning_cvr = _num(ppc.get("planning_cvr"))
            spend_supported_ad_units = None
            if planning_cpc and planning_cvr is not None:
                spend_supported_ad_units = float(ppc["planned_spend"]) / planning_cpc * planning_cvr
            required_non_ad_units = None if spend_supported_ad_units is None else max(0.0, month_units - spend_supported_ad_units)
            monthly_rows.append({
                "path_id": path_id,
                "path": path["label"],
                "month_id": month_key,
                "month": month_label,
                "days": days,
                "start_daily_revenue": daily_values[0],
                "exit_daily_revenue": daily_values[-1],
                "target_revenue": month_revenue,
                "blended_asp": blended_asp,
                "required_units": month_units,
                "planned_ppc": float(ppc["planned_spend"]),
                "ppc_ceiling": float(ppc["spend_ceiling"]),
                "spend_supported_ad_units": spend_supported_ad_units,
                "required_non_ad_units": required_non_ad_units,
                "external_halo_units": 0.0,
                "product_mix": deepcopy(mix),
                "campaign_allocation": deepcopy(ppc["campaign_allocation"]),
            })
            total_revenue += month_revenue
            total_units += month_units
            for product_id, share in mix.items():
                path_units_by_product[product_id] += month_units * float(share)
            for offset in range(0, days, 7):
                weekly_revenue = sum(daily_values[offset:offset + 7])
                weekly_units = weekly_revenue / blended_asp if blended_asp else 0.0
                for product_id, share in mix.items():
                    product_units = weekly_units * float(share)
                    weekly_rows.append({
                        "path_id": path_id,
                        "path": path["label"],
                        "week": week_number,
                        "month": month_label,
                        "product_id": product_id,
                        "product": products[product_id]["name"],
                        "mix": float(share),
                        "effective_price": effective_price(products[product_id]),
                        "target_revenue": product_units * effective_price(products[product_id]),
                        "forecast_units": product_units,
                        "external_halo_units": 0.0,
                    })
                week_number += 1

        customer_stock = _round_up(total_units * (1.0 + safety_buffer), stock_increment)
        mix_weights = {product_id: units / total_units if total_units else 0.0 for product_id, units in path_units_by_product.items()}
        stock_by_product = _allocate_rounded_total(customer_stock, mix_weights, 5)
        vine_total = sum(vine_by_product.values())
        summaries.append({
            "path_id": path_id,
            "path": path["label"],
            "month_3_objective": path["month_3_label"],
            "target_revenue": total_revenue,
            "forecast_units": total_units,
            "customer_sale_inventory_required": customer_stock,
            "vine_units": vine_total,
            "total_inventory_required": customer_stock + vine_total,
            "product_units": dict(path_units_by_product),
            "customer_stock_by_product": stock_by_product,
            "total_stock_by_product": {
                product_id: stock_by_product[product_id] + vine_by_product[product_id]
                for product_id in stock_by_product
            },
        })

    return {
        "daily_revenue_milestones": deepcopy(milestones),
        "stock_safety_buffer_pct": safety_buffer,
        "stock_rounding_increment": stock_increment,
        "summaries": summaries,
        "monthly": monthly_rows,
        "weekly": weekly_rows,
        "ppc_plan": deepcopy(commercial["ppc_plan"]),
        "keywords": deepcopy(commercial.get("keywords", {})),
    }


def build_model(config: dict[str, Any]) -> dict[str, Any]:
    validation = validate_config(config)
    if validation["errors"]:
        raise ValueError("; ".join(validation["errors"]))

    config = deepcopy(config)
    phase_map = phases_by_week(config)
    products = {p["id"]: p for p in launch_products(config)}
    rows: list[dict[str, Any]] = []
    stock_summaries: list[dict[str, Any]] = []

    for scenario in config["scenarios"]:
        sid = scenario["id"]
        for pid, product in products.items():
            values = scenario["products"][pid]
            price = effective_price(product)
            opening_stock = _num(product.get("inventory", {}).get("opening_stock"))
            inbound_by_week = _inbound_by_week(product)
            stock_known = opening_stock is not None and inbound_by_week is not None
            current_stock = opening_stock if stock_known else None
            safety_stock = _num(product.get("inventory", {}).get("safety_stock")) or 0.0
            vine_units = _num(product.get("reviews", {}).get("vine_units")) or 0.0
            demand_history: list[float] = []
            first_stockout: int | None = None
            first_safety_breach: int | None = None

            for week in range(1, 14):
                phase = phase_map[week]
                phase_id = phase["id"]
                clicks = float(_phase_value(values["paid_clicks_per_week"], phase_id, 0))
                cpc = float(_phase_value(values["cpc"], phase_id, 0))
                cvr = float(_phase_value(values["cvr"], phase_id, 0))
                organic = float(_phase_value(values["organic_units_per_week"], phase_id, 0))
                halo = float(_phase_value(values["external_halo_units_per_week"], phase_id, 0))
                ad_orders = clicks * cvr
                ad_spend = clicks * cpc
                demand = ad_orders + organic + halo
                demand_history.append(demand)
                inbound = (inbound_by_week or {}).get(week, 0.0)
                vine = vine_units if week == 1 else 0.0
                beginning = current_stock
                fulfilled = None
                closing = None
                unmet = None
                if stock_known:
                    available = max(0.0, float(current_stock) + inbound - vine)
                    fulfilled = min(demand, available)
                    unmet = max(0.0, demand - fulfilled)
                    closing = max(0.0, available - fulfilled)
                    current_stock = closing
                    if first_stockout is None and (unmet > 1e-9 or closing <= 1e-9):
                        first_stockout = week
                    if first_safety_breach is None and closing < safety_stock:
                        first_safety_breach = week

                revenue_units = fulfilled if fulfilled is not None else demand
                ad_sales = ad_orders * price
                contribution = contribution_per_unit(product)
                rows.append({
                    "scenario_id": sid,
                    "scenario": scenario.get("label", sid.title()),
                    "week": week,
                    "month": next(name for name, weeks in MONTHS.items() if week in weeks),
                    "product_id": pid,
                    "product": product["name"],
                    "phase_id": phase_id,
                    "phase": phase.get("name", phase_id),
                    "effective_price": price,
                    "paid_clicks": clicks,
                    "cpc": cpc,
                    "cvr": cvr,
                    "ad_spend": ad_spend,
                    "ad_orders": ad_orders,
                    "ad_sales": ad_sales,
                    "organic_units": organic,
                    "external_halo_units": halo,
                    "halo_basis": values.get("halo_basis") or "No external halo assumed",
                    "unconstrained_demand": demand,
                    "fulfilled_units": fulfilled,
                    "forecast_units": revenue_units,
                    "revenue": revenue_units * price,
                    "opening_stock": beginning,
                    "inbound_units": inbound if inbound_by_week is not None else None,
                    "vine_units": vine,
                    "closing_stock": closing,
                    "unmet_demand": unmet,
                    "contribution_per_unit_before_ads": contribution,
                    "break_even_acos": break_even_acos(product),
                    "daily_budget_cap": _num(phase.get("daily_budget_cap")),
                })

            projected_stockout = first_stockout
            if stock_known and projected_stockout is None:
                recent_rate = sum(demand_history[-4:]) / 4.0
                if recent_rate > 0:
                    projected_stockout = 13 + math.ceil(float(current_stock) / recent_rate)
            lead_weeks = _lead_time_weeks(product)
            reorder_week = None if projected_stockout is None or lead_weeks is None else math.floor(projected_stockout - lead_weeks)
            recent_rate = sum(demand_history[-4:]) / 4.0
            reorder_qty = None
            moq = _num(product.get("inventory", {}).get("moq"))
            if stock_known and lead_weeks is not None and recent_rate > 0:
                needed = max(0.0, recent_rate * (lead_weeks + 4) + safety_stock - float(current_stock))
                if moq and moq > 0:
                    reorder_qty = math.ceil(needed / moq) * moq
                else:
                    reorder_qty = math.ceil(needed)
            stock_summaries.append({
                "scenario_id": sid,
                "scenario": scenario.get("label", sid.title()),
                "product_id": pid,
                "product": product["name"],
                "opening_stock": opening_stock,
                "vine_units": vine_units,
                "safety_stock": safety_stock if stock_known else None,
                "closing_stock_week_13": current_stock,
                "safety_breach_week": first_safety_breach,
                "projected_stockout_week": projected_stockout,
                "lead_time_weeks": lead_weeks,
                "reorder_week": reorder_week,
                "reorder_label": _reorder_label(config, reorder_week),
                "recommended_reorder_units": reorder_qty,
                "stock_confirmed": stock_known,
            })

    month_summary: list[dict[str, Any]] = []
    for scenario in config["scenarios"]:
        sid = scenario["id"]
        for month, weeks in MONTHS.items():
            selected = [r for r in rows if r["scenario_id"] == sid and r["week"] in weeks]
            ad_spend = sum(r["ad_spend"] for r in selected)
            ad_sales = sum(r["ad_sales"] for r in selected)
            total_revenue = sum(r["revenue"] for r in selected)
            month_summary.append({
                "scenario_id": sid,
                "scenario": scenario.get("label", sid.title()),
                "month": month,
                "weeks": f"{min(weeks)}-{max(weeks)}",
                "ppc_spend": ad_spend,
                "ad_sales": ad_sales,
                "acos": (ad_spend / ad_sales) if ad_sales else None,
                "forecast_units": sum(r["forecast_units"] for r in selected),
                "ad_units": sum(r["ad_orders"] for r in selected),
                "organic_units": sum(r["organic_units"] for r in selected),
                "external_halo_units": sum(r["external_halo_units"] for r in selected),
                "revenue": total_revenue,
                "daily_ppc_average": ad_spend / len(list(weeks)) / 7,
            })

    annual_summary = []
    for scenario in config["scenarios"]:
        sid = scenario["id"]
        selected = [r for r in rows if r["scenario_id"] == sid]
        ad_spend = sum(r["ad_spend"] for r in selected)
        ad_sales = sum(r["ad_sales"] for r in selected)
        annual_summary.append({
            "scenario_id": sid,
            "scenario": scenario.get("label", sid.title()),
            "ppc_spend": ad_spend,
            "ad_sales": ad_sales,
            "acos": ad_spend / ad_sales if ad_sales else None,
            "forecast_units": sum(r["forecast_units"] for r in selected),
            "revenue": sum(r["revenue"] for r in selected),
            "external_halo_units": sum(r["external_halo_units"] for r in selected),
        })

    cap_breaches = []
    for sid in SCENARIO_IDS:
        for week in range(1, 14):
            selected = [r for r in rows if r["scenario_id"] == sid and r["week"] == week]
            total = sum(r["ad_spend"] for r in selected)
            caps = {r["daily_budget_cap"] for r in selected if r["daily_budget_cap"] is not None}
            cap = max(caps) if caps else None
            if cap is not None and total > cap * 7 + 1e-9:
                cap_breaches.append({"scenario_id": sid, "week": week, "weekly_spend": total, "weekly_cap": cap * 7})

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_from": config,
        "validation": validation,
        "rows": rows,
        "month_summary": month_summary,
        "scenario_summary": annual_summary,
        "stock_summary": stock_summaries,
        "pricing_summary": [
            {
                "product_id": p["id"],
                "product": p["name"],
                "phase": p.get("phase"),
                "list_price": _num(p.get("list_price")),
                "launch_price": effective_price(p) if p.get("launch_price") is not None or p.get("list_price") is not None else None,
                "discount_pct": (1 - effective_price(p) / float(p["list_price"])) if _num(p.get("list_price")) else None,
                "contribution_per_unit_before_ads": contribution_per_unit(p),
                "break_even_acos": break_even_acos(p),
                "discount_floor": _num(p.get("unit_economics", {}).get("discount_floor")),
            }
            for p in config.get("products", [])
        ],
        "review_policy": {
            "status": "PASS",
            "methods": config.get("reviews", {}).get("methods", []),
            "vine": config.get("reviews", {}).get("vine", {}),
            "request_a_review": config.get("reviews", {}).get("request_a_review", {}),
            "helium10_follow_up": config.get("reviews", {}).get("helium10_follow_up", {}),
        },
        "cap_breaches": cap_breaches,
        "commercial": build_commercial_model(config),
    }

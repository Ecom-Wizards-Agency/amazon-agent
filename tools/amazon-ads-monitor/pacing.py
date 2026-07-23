"""pacing.py -- month-to-date run-rate pacing vs a monthly ad budget.

Run rate is a PORTFOLIO-LEVEL GOVERNOR on top of the rank engine, not the
strategy itself (per `_local/ads-strategy/strategy.md` v3, "Run-rate
governor"). This module answers one question: are we pacing over or under
the month's ad budget, and if over, what gets cut first?

The cut order is FIXED doctrine, not per-client judgment:

    1. waste     -- high-spend-no-sales targets
    2. discovery -- bids down, then budgets (share must stay <= ~20% anyway)
    3. profit    -- bid trims toward target ACOS, never pauses of converting targets
    4. rank      -- LAST, and only by explicit operator/client decision;
                    a mid-flight rank push is never cut silently

Pure functions over Sellerboard-style DailyRow lists (same discipline as
analyze.py: no I/O, no MCP). The monthly budget comes from the caller
(CLI flag or per-client config in `_local/ads-monitor/`); where no
explicit budget exists, the caller may derive one from the TACOS ceiling
x trailing total sales before calling in.
"""

from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from flags import Flag, SEVERITY_ALERT, SEVERITY_INFO, SEVERITY_WARN, CATEGORY_UNKNOWN

DEFAULT_PACING_THRESHOLDS = {
    "warn_above": 1.10,   # pace > this = warn (watch, no action yet)
    "act_above": 1.25,    # pace > this = act (apply the cut order)
    "underpace_below": 0.75,  # pace < this = under-pace (push, mirror order)
}

CUT_ORDER = ("waste", "discovery", "profit", "rank")

CUT_ORDER_GUIDANCE = (
    "1. Waste first: high-spend-no-sales targets (the optimizer's own bucket).",
    "2. Discovery: bids down, then budgets (share of spend must stay <= ~20% anyway).",
    "3. Profit: bid trims toward target ACOS; never pause converting targets for pacing.",
    "4. Rank LAST, and ONLY by explicit operator/client decision -- a mid-flight rank "
    "push is never cut silently by the governor.",
)

UNDERPACE_GUIDANCE = (
    "1. Fund unfunded demand first (SUPA O1 flags).",
    "2. Scale proven winners (SUPA E1 / the weekly PUSH list).",
    "3. Raise budget-capped Rank/SKW campaigns.",
)

STATUS_ON_PACE = "on_pace"
STATUS_WARN = "warn"
STATUS_ACT = "act"
STATUS_UNDERPACE = "underpace"


@dataclass
class PacingResult:
    as_of: dt.date
    month_start: dt.date
    day_of_month: int
    days_in_month: int
    monthly_budget: float
    mtd_spend: float
    budget_to_date: float  # monthly_budget * day_of_month / days_in_month
    pace: Optional[float]  # mtd_spend / budget_to_date
    status: str
    days_with_data: int
    coverage_complete: bool  # every day from month start through as_of had a spend figure
    guidance: tuple = ()
    notes: list = field(default_factory=list)


def _pacing_thresholds(lens: Optional[dict] = None, config: Optional[dict] = None) -> dict:
    """Same layering as flags._thresholds: toolkit defaults -> goal-lens
    `pacing_overrides` -> explicit per-account config `pacing` overrides
    (config always wins)."""
    merged = dict(DEFAULT_PACING_THRESHOLDS)
    if lens and lens.get("pacing_overrides"):
        merged.update({k: v for k, v in lens["pacing_overrides"].items() if k in DEFAULT_PACING_THRESHOLDS})
    if config and "pacing" in config:
        merged.update({k: v for k, v in config["pacing"].items() if k in DEFAULT_PACING_THRESHOLDS})
    return merged


def compute_pacing(
    account_rows: list,
    as_of: dt.date,
    monthly_budget: Optional[float],
    lens: Optional[dict] = None,
    config: Optional[dict] = None,
) -> Optional[PacingResult]:
    """Month-to-date pace as of `as_of` (inclusive). Returns None when no
    monthly budget is known -- pacing simply doesn't apply, which the
    report states rather than inventing a budget.

    `account_rows`: Sellerboard-style DailyRow list (needs `.date` and
    `.spend`). Rows outside `as_of`'s month are ignored. Missing days make
    `coverage_complete` False and add a note -- the pace is then
    UNDERSTATED, never silently corrected.
    """
    if not monthly_budget or monthly_budget <= 0:
        return None

    thresholds = _pacing_thresholds(lens, config)
    month_start = as_of.replace(day=1)
    days_in_month = calendar.monthrange(as_of.year, as_of.month)[1]
    day_of_month = as_of.day

    mtd_spend = 0.0
    days_with_data = 0
    seen_dates = set()
    for row in account_rows:
        date = getattr(row, "date", None)
        spend = getattr(row, "spend", None)
        if date is None or spend is None:
            continue
        if not (month_start <= date <= as_of) or date in seen_dates:
            continue
        seen_dates.add(date)
        mtd_spend += spend
        days_with_data += 1

    budget_to_date = monthly_budget * day_of_month / days_in_month
    pace = (mtd_spend / budget_to_date) if budget_to_date > 0 else None
    coverage_complete = days_with_data >= day_of_month

    notes = []
    if not coverage_complete:
        notes.append(
            f"Only {days_with_data} of {day_of_month} month-to-date days have a spend figure -- "
            "the pace is understated; widen the Sellerboard window before acting on an under-pace read."
        )

    status = STATUS_ON_PACE
    guidance: tuple = ()
    if pace is not None:
        if pace > thresholds["act_above"]:
            status = STATUS_ACT
            guidance = CUT_ORDER_GUIDANCE
        elif pace > thresholds["warn_above"]:
            status = STATUS_WARN
        elif pace < thresholds["underpace_below"] and coverage_complete:
            status = STATUS_UNDERPACE
            guidance = UNDERPACE_GUIDANCE

    return PacingResult(
        as_of=as_of,
        month_start=month_start,
        day_of_month=day_of_month,
        days_in_month=days_in_month,
        monthly_budget=monthly_budget,
        mtd_spend=mtd_spend,
        budget_to_date=budget_to_date,
        pace=pace,
        status=status,
        days_with_data=days_with_data,
        coverage_complete=coverage_complete,
        guidance=guidance,
        notes=notes,
    )


def pacing_flag(pacing: Optional[PacingResult], lens: Optional[dict] = None) -> Optional[Flag]:
    """A single account-level Flag for the daily/weekly flag sections.
    on_pace -> no flag. warn/underpace -> WARN. act -> ALERT (the governor
    says apply the cut order)."""
    if pacing is None or pacing.pace is None or pacing.status == STATUS_ON_PACE:
        return None
    label = (lens or {}).get("label")
    if pacing.status == STATUS_ACT:
        severity = SEVERITY_ALERT
        cause = (
            "Over pace: apply the fixed cut order (waste -> discovery -> profit; Rank last and only "
            "by explicit operator decision)."
        )
    elif pacing.status == STATUS_WARN:
        severity = SEVERITY_WARN
        cause = "Slightly over pace: watch, no action yet. Check for event days (deal/holiday) before reading it as drift."
    else:  # underpace
        severity = SEVERITY_WARN if pacing.coverage_complete else SEVERITY_INFO
        cause = "Under pace: fund unfunded demand (O1), scale winners (E1), raise capped Rank budgets."
    if label and label != "Neutral":
        cause += f" (Read under the '{label}' goal lens.)"
    return Flag(
        severity=severity,
        metric="run_rate_pace",
        threshold=f"pace {pacing.pace:.2f} vs budget-to-date",
        message=(
            f"MTD ad spend ${pacing.mtd_spend:,.2f} vs ${pacing.budget_to_date:,.2f} budget-to-date "
            f"(day {pacing.day_of_month}/{pacing.days_in_month}, monthly budget ${pacing.monthly_budget:,.2f}) "
            f"-- pace {pacing.pace:.2f}."
        ),
        likely_cause=cause,
        scope="account",
        category=CATEGORY_UNKNOWN,
    )

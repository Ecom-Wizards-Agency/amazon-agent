"""analyze.py -- trend + delta computation for amazon-ads-monitor.

Pure functions over DailyRow lists: no I/O, no MCP, fully unit-testable.
For the report date (default = yesterday, decided by the CLI), computes
each metric's value plus its change vs the prior day and vs the trailing
7-day average (absolute + %), and classifies a simple up/down/flat trend
over the trailing 7 days. Metric set is pluggable (`metrics=`) so the
same math covers both the SP-Ads/mock metric set and the Sellerboard
account-total metric set (total_sales, real_acos, margin, ...); see
`datasource.METRICS` / `datasource.SELLERBOARD_METRICS`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from datasource import METRICS, CATEGORY_UNKNOWN, DailyRow, metric_value

TREND_UP = "up"
TREND_DOWN = "down"
TREND_FLAT = "flat"

# A first-half-vs-second-half average change smaller than this counts as flat.
TREND_TOLERANCE = 0.05


@dataclass
class MetricDelta:
    metric: str
    value: Optional[float]
    prior_value: Optional[float]
    prior_abs_change: Optional[float]
    prior_pct_change: Optional[float]
    trailing7_avg: Optional[float]
    trailing7_abs_change: Optional[float]
    trailing7_pct_change: Optional[float]
    trend: str


@dataclass
class SeriesAnalysis:
    """Analysis for one series: the account overall, or a single campaign."""

    label: str
    campaign_id: Optional[str]
    category: str
    report_row: Optional[DailyRow]
    deltas: dict = field(default_factory=dict)  # metric -> MetricDelta


@dataclass
class AnalysisResult:
    account: str
    report_date: dt.date
    account_series: SeriesAnalysis
    campaign_series: list


def _pct_change(new: Optional[float], old: Optional[float]) -> Optional[float]:
    if new is None or old is None or old == 0:
        return None
    return (new - old) / abs(old)


def _abs_change(new: Optional[float], old: Optional[float]) -> Optional[float]:
    if new is None or old is None:
        return None
    return new - old


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def classify_trend(values_oldest_to_newest: list, tolerance: float = TREND_TOLERANCE) -> str:
    """Classify a trend using first-half vs second-half average.

    `values_oldest_to_newest` should be the trailing window (typically the
    7 days before the report date), ordered oldest first. Missing (None)
    points are dropped before averaging.
    """
    clean = [v for v in values_oldest_to_newest if v is not None]
    if len(clean) < 2:
        return TREND_FLAT
    mid = len(clean) // 2
    first_half = clean[:mid] or clean[:1]
    second_half = clean[mid:] or clean[-1:]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    if avg_first == 0:
        return TREND_FLAT if avg_second == 0 else TREND_UP
    change = (avg_second - avg_first) / abs(avg_first)
    if change > tolerance:
        return TREND_UP
    if change < -tolerance:
        return TREND_DOWN
    return TREND_FLAT


def analyze_series(
    rows_by_date: dict,
    report_date: dt.date,
    label: str,
    campaign_id: Optional[str] = None,
    category: str = CATEGORY_UNKNOWN,
    metrics: Optional[tuple] = None,
) -> SeriesAnalysis:
    """`rows_by_date`: date -> DailyRow for one series. Should cover at
    least the report date, the prior day, and the 7 days before that for
    full trailing-average/trend coverage; missing dates degrade gracefully
    to None deltas rather than raising.

    `metrics`: which metric names to compute deltas for (default: the
    SP-Ads/mock metric set `datasource.METRICS`). Pass
    `datasource.SELLERBOARD_METRICS` for a Sellerboard account series so
    the day-over-day / trailing-7-avg math covers total_sales, real_acos,
    margin, etc. instead of the click-level metrics Sellerboard doesn't
    report."""

    report_row = rows_by_date.get(report_date)
    prior_row = rows_by_date.get(report_date - dt.timedelta(days=1))
    trailing_dates_newest_first = [report_date - dt.timedelta(days=d) for d in range(1, 8)]
    trailing_rows_newest_first = [rows_by_date.get(d) for d in trailing_dates_newest_first]

    deltas = {}
    for metric in (metrics or METRICS):
        value = metric_value(report_row, metric)
        prior_value = metric_value(prior_row, metric)
        trailing_values_newest_first = [metric_value(r, metric) for r in trailing_rows_newest_first]
        trailing_clean = [v for v in trailing_values_newest_first if v is not None]
        trailing_avg = sum(trailing_clean) / len(trailing_clean) if trailing_clean else None
        trailing_oldest_first = list(reversed(trailing_values_newest_first))
        deltas[metric] = MetricDelta(
            metric=metric,
            value=value,
            prior_value=prior_value,
            prior_abs_change=_abs_change(value, prior_value),
            prior_pct_change=_pct_change(value, prior_value),
            trailing7_avg=trailing_avg,
            trailing7_abs_change=_abs_change(value, trailing_avg),
            trailing7_pct_change=_pct_change(value, trailing_avg),
            trend=classify_trend(trailing_oldest_first),
        )
    return SeriesAnalysis(label=label, campaign_id=campaign_id, category=category, report_row=report_row, deltas=deltas)


def analyze_account(
    account: str,
    report_date: dt.date,
    account_rows: list,
    campaign_rows: list,
    metrics: Optional[tuple] = None,
) -> AnalysisResult:
    """`metrics`: see `analyze_series`; applied to both the account series
    and every campaign series (campaign rows from an AdLabs adapter still
    use the default SP-Ads metric set unless overridden explicitly)."""
    by_date = {r.date: r for r in account_rows}
    account_series = analyze_series(by_date, report_date, label=account, category=CATEGORY_UNKNOWN, metrics=metrics)

    per_campaign: dict = {}
    for r in campaign_rows:
        per_campaign.setdefault(r.campaign_id, {})[r.date] = r

    campaign_series = []
    for cid, by_date_c in per_campaign.items():
        any_row = next(iter(by_date_c.values()))
        campaign_series.append(
            analyze_series(
                by_date_c,
                report_date,
                label=any_row.campaign_name or cid,
                campaign_id=cid,
                category=any_row.category,
                metrics=metrics,
            )
        )
    campaign_series.sort(key=lambda s: s.label)
    return AnalysisResult(
        account=account,
        report_date=report_date,
        account_series=account_series,
        campaign_series=campaign_series,
    )


# ---------------------------------------------------------------------------
# Weekly (WoW) aggregation -- the weekly brief's account-level headline.
#
# Additive metrics are SUMMED over each 7-day window (this week vs last
# week); ratio metrics are RECOMPUTED from the summed components of each
# window (e.g. tacos = sum(spend) / sum(total_sales)) rather than averaged
# day-by-day, so one unusually large/small day doesn't get equal weight to
# a near-zero day. `real_acos` is the one exception: it's Sellerboard's own
# computed figure (may fold in costs this toolkit doesn't see), so its
# weekly figure is a simple mean of the days that reported a value, not a
# recomputation.

WEEKLY_SUM_METRICS = (
    "total_sales", "sales", "spend", "orders", "units_organic", "units_ppc",
    "refunds", "gross_profit", "net_profit", "sessions",
)
WEEKLY_AVG_METRICS = ("real_acos",)
WEEKLY_RATIO_METRICS = ("acos", "tacos", "margin")
# Display/report order for the weekly headline table.
WEEKLY_METRICS = (
    "total_sales", "sales", "spend", "tacos", "real_acos", "acos", "orders",
    "units_organic", "units_ppc", "refunds", "gross_profit", "net_profit",
    "margin", "sessions",
)


@dataclass
class WeeklyMetricDelta:
    metric: str
    this_week: Optional[float]
    last_week: Optional[float]
    abs_change: Optional[float]
    pct_change: Optional[float]


@dataclass
class WeeklyAnalysis:
    """WoW analysis for one account's Sellerboard-style daily rows.

    `week_end` is the report date (last day of "this week", typically
    yesterday -- see run_weekly.py's note on Sellerboard's total_* columns
    reading 0 for the very latest/in-progress day; prefer a `week_end` that
    is a fully-completed day). "This week" = the 7 days ending `week_end`
    inclusive; "last week" = the 7 days immediately before that.
    """

    account: str
    week_end: dt.date
    this_week_start: dt.date
    last_week_start: dt.date
    last_week_end: dt.date
    deltas: dict  # metric -> WeeklyMetricDelta
    this_week_rows: list
    last_week_rows: list


def _sum_metric(rows: list, metric: str) -> Optional[float]:
    values = [v for v in (getattr(r, metric, None) for r in rows) if v is not None]
    return sum(values) if values else None


def _avg_metric(rows: list, metric: str) -> Optional[float]:
    values = [v for v in (getattr(r, metric, None) for r in rows) if v is not None]
    return (sum(values) / len(values)) if values else None


def aggregate_week(account_rows: list, week_end: dt.date) -> WeeklyAnalysis:
    """Aggregate Sellerboard account-level `DailyRow`s into THIS-week vs
    LAST-week (7-day) totals and week-over-week absolute + % change for
    each metric in `WEEKLY_METRICS`. Missing days/metrics degrade
    gracefully to `None` rather than raising (same contract as
    `analyze_series`)."""
    rows_by_date = {r.date: r for r in account_rows}
    this_week_start = week_end - dt.timedelta(days=6)
    last_week_end = this_week_start - dt.timedelta(days=1)
    last_week_start = last_week_end - dt.timedelta(days=6)

    this_week_rows = [rows_by_date[d] for d in sorted(rows_by_date) if this_week_start <= d <= week_end]
    last_week_rows = [rows_by_date[d] for d in sorted(rows_by_date) if last_week_start <= d <= last_week_end]

    deltas: dict = {}

    def _add(metric: str, this_val: Optional[float], last_val: Optional[float]) -> None:
        deltas[metric] = WeeklyMetricDelta(
            metric=metric,
            this_week=this_val,
            last_week=last_val,
            abs_change=_abs_change(this_val, last_val),
            pct_change=_pct_change(this_val, last_val),
        )

    for metric in WEEKLY_SUM_METRICS:
        _add(metric, _sum_metric(this_week_rows, metric), _sum_metric(last_week_rows, metric))
    for metric in WEEKLY_AVG_METRICS:
        _add(metric, _avg_metric(this_week_rows, metric), _avg_metric(last_week_rows, metric))

    # Ratio metrics recomputed from the summed components above (falls
    # back to None if a required component metric wasn't summed, e.g. a
    # non-Sellerboard row set missing total_sales/net_profit).
    def _get(metric: str, which: str) -> Optional[float]:
        d = deltas.get(metric)
        return getattr(d, which) if d else None

    _add("acos", _safe_div(_get("spend", "this_week"), _get("sales", "this_week")),
         _safe_div(_get("spend", "last_week"), _get("sales", "last_week")))
    _add("tacos", _safe_div(_get("spend", "this_week"), _get("total_sales", "this_week")),
         _safe_div(_get("spend", "last_week"), _get("total_sales", "last_week")))
    _add("margin", _safe_div(_get("net_profit", "this_week"), _get("total_sales", "this_week")),
         _safe_div(_get("net_profit", "last_week"), _get("total_sales", "last_week")))

    return WeeklyAnalysis(
        account=account_rows[0].account if account_rows else "unknown",
        week_end=week_end,
        this_week_start=this_week_start,
        last_week_start=last_week_start,
        last_week_end=last_week_end,
        deltas=deltas,
        this_week_rows=this_week_rows,
        last_week_rows=last_week_rows,
    )

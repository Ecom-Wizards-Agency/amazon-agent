"""report.py -- markdown report + Slack payload rendering.

Pure formatting: takes an AnalysisResult plus the active/suppressed Flag
lists and renders (a) a markdown daily report and (b) a compact Slack
message (mrkdwn text + Block Kit JSON). No file I/O and no Slack posting
here -- the CLI writes the markdown to disk, and the *skill* (runtime
layer, via the Slack MCP connector) is what actually posts the Slack
payload this module returns.
"""

from __future__ import annotations

import datetime as dt
import json as _json
from pathlib import Path as _Path
from typing import Optional

from analyze import AnalysisResult, SeriesAnalysis, WeeklyAnalysis
from flags import Flag, SEVERITY_CRITICAL, SEVERITY_ALERT, SEVERITY_WARN, SEVERITY_INFO
from datasource import CATEGORY_UNKNOWN
from crosscheck import render_verdict_emoji_line
from recommendations import RecommendationsResult

SLACK_CHANNEL_NAME = "#amazon-daily-report"


def default_slack_channel() -> str:
    """Channel for Slack payloads. The real workspace channel ID lives only
    in gitignored `_local/ads-monitor/config.json` (`slack_channel_id`);
    without it, fall back to the channel NAME and let the poster resolve
    it. No workspace ID may appear as a literal in this repo."""
    cfg = _Path(__file__).resolve().parents[2] / "_local" / "ads-monitor" / "config.json"
    try:
        channel = _json.loads(cfg.read_text(encoding="utf-8")).get("slack_channel_id")
    except (OSError, ValueError):
        channel = None
    return channel or SLACK_CHANNEL_NAME


HEADLINE_METRICS = ("spend", "sales", "orders", "acos", "roas", "tacos", "impressions", "clicks", "ctr", "cvr", "cpc")
SLACK_HEADLINE_METRICS = ("spend", "sales", "acos", "tacos", "orders")

# Sellerboard account-level rows carry whole-account totals, not
# click-level metrics (no impressions/clicks/CTR/CVR/CPC/ROAS -- see
# datasource.SELLERBOARD_METRICS). `run_monitor.py` passes this set via
# `meta["headline_metrics"]` for `--source sellerboard` runs so the
# report leads with what Sellerboard actually reports: total sales, ad
# sales, ad spend, TACOS, Real ACOS, orders, margin.
SELLERBOARD_HEADLINE_METRICS = ("total_sales", "sales", "spend", "tacos", "real_acos", "orders", "margin")
SELLERBOARD_SLACK_HEADLINE_METRICS = ("total_sales", "sales", "spend", "tacos", "real_acos", "orders")

_CURRENCY = {"spend", "sales", "cpc", "total_sales", "gross_profit", "net_profit"}
_PERCENT = {"ctr", "cvr", "acos", "tacos", "real_acos", "margin", "unit_session_pct"}
_MULTIPLIER = {"roas"}
_INT = {"impressions", "clicks", "orders", "units_organic", "units_ppc", "refunds", "sessions"}

METRIC_LABELS = {
    "impressions": "Impressions",
    "clicks": "Clicks",
    "spend": "Spend",
    "sales": "Sales",
    "orders": "Orders",
    "ctr": "CTR",
    "cvr": "CVR",
    "cpc": "CPC",
    "acos": "ACOS",
    "roas": "ROAS",
    "tacos": "TACOS",
    "total_sales": "Total Sales",
    "real_acos": "Real ACOS",
    "margin": "Margin",
    "units_organic": "Units (organic)",
    "units_ppc": "Units (PPC)",
    "refunds": "Refunds",
    "gross_profit": "Gross Profit",
    "net_profit": "Net Profit",
    "sessions": "Sessions",
    "unit_session_pct": "Unit Session %",
}

SEVERITY_LABELS = {SEVERITY_CRITICAL: "Critical", SEVERITY_ALERT: "Alert", SEVERITY_WARN: "Warn", SEVERITY_INFO: "Info"}
SEVERITY_EMOJI = {
    SEVERITY_CRITICAL: ":red_circle:",
    SEVERITY_ALERT: ":rotating_light:",
    SEVERITY_WARN: ":warning:",
    SEVERITY_INFO: ":information_source:",
}

# Metric-name overrides for the Sellerboard headline context, where
# "spend"/"sales" mean whole-account ad spend/ad sales (not a single
# campaign's), sitting alongside "Total Sales" -- spelling that out avoids
# ambiguity in the table. Passed as `labels=` to the headline renderers;
# falls back to `METRIC_LABELS` for anything not overridden here.
SELLERBOARD_METRIC_LABEL_OVERRIDES = {"spend": "Ad Spend", "sales": "Ad Sales"}

# ---------------------------------------------------------------------------
# Weekly (WoW) headline metric set/order, mirroring the daily Sellerboard
# set (see analyze.WEEKLY_METRICS) plus the same label overrides ("spend"/
# "sales" mean whole-account ad spend/ad sales in this context).
WEEKLY_HEADLINE_METRICS = (
    "total_sales", "sales", "spend", "tacos", "real_acos", "acos", "orders",
    "units_organic", "units_ppc", "refunds", "gross_profit", "net_profit",
    "margin", "sessions",
)
WEEKLY_SLACK_HEADLINE_METRICS = ("total_sales", "sales", "spend", "tacos", "real_acos", "orders", "margin")


def _fmt_value(metric: str, value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    if metric in _CURRENCY:
        return f"${value:,.2f}"
    if metric in _PERCENT:
        return f"{value * 100:.1f}%"
    if metric in _MULTIPLIER:
        return f"{value:.2f}x"
    if metric in _INT:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def _fmt_pct_change(pct: Optional[float]) -> str:
    if pct is None:
        return "n/a"
    return f"{pct * 100:+.0f}%"


def _arrow(pct: Optional[float], tolerance: float = 0.02) -> str:
    if pct is None:
        return "–"  # en dash: no comparable prior value
    if pct > tolerance:
        return "▲"  # ▲
    if pct < -tolerance:
        return "▼"  # ▼
    return "–"


def _trend_word(trend: str) -> str:
    return {"up": "trending up", "down": "trending down", "flat": "flat"}.get(trend, trend)


# ---------------------------------------------------------------------------
# Markdown

def _markdown_headline_table(series: SeriesAnalysis, metrics: Optional[tuple] = None, labels: Optional[dict] = None) -> str:
    lines = [
        "| Metric | Value | vs Prior Day | vs Trailing-7 Avg | 7d Trend |",
        "|---|---|---|---|---|",
    ]
    label_map = {**METRIC_LABELS, **(labels or {})}
    for metric in (metrics or HEADLINE_METRICS):
        d = series.deltas.get(metric)
        if d is None:
            continue
        value_s = _fmt_value(metric, d.value)
        prior_s = f"{_arrow(d.prior_pct_change)} {_fmt_pct_change(d.prior_pct_change)}"
        trailing_s = f"{_arrow(d.trailing7_pct_change)} {_fmt_pct_change(d.trailing7_pct_change)} (avg {_fmt_value(metric, d.trailing7_avg)})"
        lines.append(f"| {label_map.get(metric, metric)} | {value_s} | {prior_s} | {trailing_s} | {_trend_word(d.trend)} |")
    return "\n".join(lines)


def _markdown_campaign_table(campaign_series: list) -> str:
    if not campaign_series:
        return (
            "_No campaign-level detail this run._ Sellerboard's Dashboard Totals feed is "
            "account-level only; campaign/keyword detail comes from AdLabs (see "
            "`crosscheck.py` and the skill's AdLabs pull step).\n"
        )
    lines = [
        "| Campaign | Category | Spend | Sales | ACOS | Spend vs Trailing-7 | Trend |",
        "|---|---|---|---|---|---|---|",
    ]
    for series in campaign_series:
        spend_d = series.deltas.get("spend")
        sales_d = series.deltas.get("sales")
        acos_d = series.deltas.get("acos")
        spend_change = f"{_arrow(spend_d.trailing7_pct_change)} {_fmt_pct_change(spend_d.trailing7_pct_change)}" if spend_d else "n/a"
        lines.append(
            f"| {series.label} | {series.category} | "
            f"{_fmt_value('spend', spend_d.value if spend_d else None)} | "
            f"{_fmt_value('sales', sales_d.value if sales_d else None)} | "
            f"{_fmt_value('acos', acos_d.value if acos_d else None)} | "
            f"{spend_change} | {_trend_word(spend_d.trend) if spend_d else 'n/a'} |"
        )
    return "\n".join(lines)


def _markdown_flag_section(title: str, flags: list) -> str:
    if not flags:
        return f"### {title}\n\nNone.\n"
    lines = [f"### {title}\n"]
    for f in flags:
        lines.append(
            f"- **[{SEVERITY_LABELS.get(f.severity, f.severity).upper()}] {f.scope}** "
            f"({f.category}) -- {f.metric}: {f.message} "
            f"Threshold: {f.threshold}. Likely cause: {f.likely_cause}"
        )
    return "\n".join(lines) + "\n"


def _one_line_trend_summary(analysis: AnalysisResult, active_flags: list) -> str:
    acos_d = analysis.account_series.deltas.get("acos")
    tacos_d = analysis.account_series.deltas.get("tacos")
    spend_d = analysis.account_series.deltas.get("spend")
    margin_d = analysis.account_series.deltas.get("margin")
    n_critical = sum(1 for f in active_flags if f.severity == SEVERITY_CRITICAL)
    n_alert = sum(1 for f in active_flags if f.severity == SEVERITY_ALERT)
    n_warn = sum(1 for f in active_flags if f.severity == SEVERITY_WARN)
    trend_bits = []
    if spend_d:
        trend_bits.append(f"spend {_trend_word(spend_d.trend)}")
    if acos_d:
        trend_bits.append(f"ACOS {_trend_word(acos_d.trend)}")
    if tacos_d and tacos_d.value is not None:
        trend_bits.append(f"TACOS {_fmt_value('tacos', tacos_d.value)}")
    if margin_d and margin_d.value is not None:
        trend_bits.append(f"margin {_fmt_value('margin', margin_d.value)} ({_trend_word(margin_d.trend)})")
    status_bits = []
    if n_critical:
        status_bits.append(f"{n_critical} critical")
    if n_alert:
        status_bits.append(f"{n_alert} alert(s)")
    if n_warn:
        status_bits.append(f"{n_warn} warn(s)")
    status = ", ".join(status_bits) if status_bits else "no active flags"
    bits = ", ".join(trend_bits) if trend_bits else "insufficient trailing data"
    return f"{bits} over the trailing week; {status} today."


def render_markdown(
    analysis: AnalysisResult,
    active_flags: list,
    suppressed_flags: list,
    meta: dict,
) -> str:
    account = analysis.account
    date_s = analysis.report_date.isoformat()
    lines = [f"# Amazon Ads Daily Monitor -- {account} -- {date_s}", ""]

    if meta.get("preview"):
        lines += [
            "> **PREVIEW -- mock data.** No live Amazon Ads API credentials are configured for this "
            "account yet; this report is generated from synthetic data (`--source mock`) so the format "
            "can be reviewed before real credentials exist. See `_local/ads-monitor/README.md`.",
            "",
        ]

    headline_metrics = meta.get("headline_metrics") or HEADLINE_METRICS
    headline_labels = meta.get("headline_labels")

    lines += [
        f"**Data source:** {meta.get('source_label', meta.get('source', 'unknown'))}  ",
        f"**Attribution window:** {meta.get('attribution_window', 'n/a')}  ",
        f"**Generated:** {meta.get('generated_at', dt.datetime.utcnow().isoformat() + 'Z')}",
    ]

    goal_lens = meta.get("goal_lens")
    if goal_lens:
        lines.append(f"**Goal lens:** {goal_lens.get('label')} -- {goal_lens.get('description')}  ")

    crosscheck_result = meta.get("crosscheck")
    if crosscheck_result is not None:
        lines.append(f"**Cross-check:** {render_verdict_emoji_line(crosscheck_result)}  ")

    lines += [
        "",
        "## Headline metrics (vs prior day / trailing-7-day avg)",
        "",
        _markdown_headline_table(analysis.account_series, headline_metrics, headline_labels),
        "",
        "## Trend summary",
        "",
        _one_line_trend_summary(analysis, active_flags),
        "",
        "## Flags",
        "",
        _markdown_flag_section("Critical", [f for f in active_flags if f.severity == SEVERITY_CRITICAL]),
        _markdown_flag_section("Alert", [f for f in active_flags if f.severity == SEVERITY_ALERT]),
        _markdown_flag_section("Warn", [f for f in active_flags if f.severity == SEVERITY_WARN]),
        _markdown_flag_section("Info", [f for f in active_flags if f.severity == SEVERITY_INFO]),
        "## Suppressed (philosophy-aware, not flagged)",
        "",
    ]
    if not suppressed_flags:
        lines.append("None.\n")
    else:
        for f in suppressed_flags:
            lines.append(f"- **{f.scope}** ({f.category}) -- {f.metric}: {f.message} {f.suppressed_reason}")
        lines.append("")

    lines += [
        "## Campaign detail",
        "",
        _markdown_campaign_table(analysis.campaign_series),
        "",
    ]

    notes = meta.get("notes") or []
    if notes:
        lines.append("## Notes")
        lines.append("")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Slack (mrkdwn + Block Kit)

def _slack_headline_line(series: SeriesAnalysis, metrics: Optional[tuple] = None, labels: Optional[dict] = None) -> str:
    label_map = {**METRIC_LABELS, **(labels or {})}
    parts = []
    for metric in (metrics or SLACK_HEADLINE_METRICS):
        d = series.deltas.get(metric)
        if d is None or d.value is None:
            continue
        parts.append(f"{label_map.get(metric, metric)} {_fmt_value(metric, d.value)} {_arrow(d.trailing7_pct_change)}{_fmt_pct_change(d.trailing7_pct_change)}")
    return " • ".join(parts)


def render_slack(
    analysis: AnalysisResult,
    active_flags: list,
    suppressed_flags: list,
    meta: dict,
    max_flags: int = 5,
) -> dict:
    account = analysis.account
    date_s = analysis.report_date.isoformat()
    preview_tag = " [PREVIEW - mock data]" if meta.get("preview") else ""
    header_text = f"Amazon Ads Daily Monitor -- {account} -- {date_s}{preview_tag}"

    slack_metrics = meta.get("slack_headline_metrics")
    headline_labels = meta.get("headline_labels")
    headline_line = _slack_headline_line(analysis.account_series, slack_metrics, headline_labels)
    trend_line = _one_line_trend_summary(analysis, active_flags)

    crosscheck_result = meta.get("crosscheck")
    crosscheck_line = render_verdict_emoji_line(crosscheck_result) if crosscheck_result is not None else None

    top_flags = active_flags[:max_flags]
    if top_flags:
        flag_lines = [
            f"{SEVERITY_EMOJI.get(f.severity, '')} *{f.scope}* ({f.category}) -- {f.metric}: {f.message}"
            for f in top_flags
        ]
    else:
        flag_lines = ["No active flags today."]
    remaining = len(active_flags) - len(top_flags)
    if remaining > 0:
        flag_lines.append(f"...and {remaining} more (see the full report).")

    suppressed_note = f"{len(suppressed_flags)} suppressed (philosophy-aware, not flagged)." if suppressed_flags else ""

    text_fallback = "\n".join(
        [header_text, headline_line] + ([crosscheck_line] if crosscheck_line else []) + [trend_line, *flag_lines]
    )

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": header_text[:150], "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": headline_line or "No headline data."}},
    ]
    if crosscheck_line:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": crosscheck_line}})
    blocks += [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"_{trend_line}_"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Top flags*\n" + "\n".join(flag_lines)}},
    ]
    context_elements = [{"type": "mrkdwn", "text": f"Source: {meta.get('source_label', meta.get('source'))}"}]
    goal_lens = meta.get("goal_lens")
    if goal_lens:
        context_elements.append({"type": "mrkdwn", "text": f"Goal lens: {goal_lens.get('label')}"})
    if suppressed_note:
        context_elements.append({"type": "mrkdwn", "text": suppressed_note})
    blocks.append({"type": "context", "elements": context_elements})

    return {
        "channel": meta.get("slack_channel_id") or default_slack_channel(),
        "text": text_fallback,
        "blocks": blocks,
    }


# ---------------------------------------------------------------------------
# Weekly (WoW) brief -- headline table over analyze.WeeklyAnalysis.deltas
# plus the three PROPOSAL lists from recommendations.RecommendationsResult
# (PUSH / PAUSE-OPTIMIZE / TEST). Read-only: every section is a proposal
# for operator approval, never an executed change (see the closing note
# `render_weekly_markdown` always appends).

def _markdown_weekly_headline_table(weekly: WeeklyAnalysis, metrics: Optional[tuple] = None, labels: Optional[dict] = None) -> str:
    lines = [
        "| Metric | This Week | Last Week | Change | % Change |",
        "|---|---|---|---|---|",
    ]
    label_map = {**METRIC_LABELS, **(labels or {})}
    for metric in (metrics or WEEKLY_HEADLINE_METRICS):
        d = weekly.deltas.get(metric)
        if d is None:
            continue
        this_s = _fmt_value(metric, d.this_week)
        last_s = _fmt_value(metric, d.last_week)
        abs_s = _fmt_value(metric, d.abs_change)
        pct_s = f"{_arrow(d.pct_change)} {_fmt_pct_change(d.pct_change)}"
        lines.append(f"| {label_map.get(metric, metric)} | {this_s} | {last_s} | {abs_s} | {pct_s} |")
    return "\n".join(lines)


def _slack_weekly_headline_line(weekly: WeeklyAnalysis, metrics: Optional[tuple] = None, labels: Optional[dict] = None) -> str:
    label_map = {**METRIC_LABELS, **(labels or {})}
    parts = []
    for metric in (metrics or WEEKLY_SLACK_HEADLINE_METRICS):
        d = weekly.deltas.get(metric)
        if d is None or d.this_week is None:
            continue
        parts.append(f"{label_map.get(metric, metric)} {_fmt_value(metric, d.this_week)} {_arrow(d.pct_change)}{_fmt_pct_change(d.pct_change)}")
    return " • ".join(parts)


def _markdown_push_section(push: list) -> str:
    if not push:
        return "_No push candidates this week._\n"
    lines = []
    for item in push:
        lines.append(
            f"- **{item.entity}** ({item.scope}, {item.category}) -- {item.why}\n"
            f"  **Action:** {item.action}  \n"
            f"  **Expected impact:** {item.expected_impact}"
        )
    return "\n".join(lines) + "\n"


def _markdown_pause_optimize_section(items: list) -> str:
    if not items:
        return "_No pause/optimize candidates this week._\n"
    lines = []
    for item in items:
        lines.append(
            f"- **{item.entity}** ({item.scope}, {item.category}) -- {item.why}\n"
            f"  **Action:** {item.action}"
        )
    return "\n".join(lines) + "\n"


def _markdown_test_section(tests: list) -> str:
    """Only rendered by the caller when `tests` is non-empty -- a "New
    ideas & tests" block never appears just to say there's nothing new
    (see recommendations.select_tests/build_recommendations)."""
    if not tests:
        return ""
    lines = ["## New ideas & tests", ""]
    for t in tests:
        status_label = "vetted backlog" if t.status == "vetted_backlog" else "external signal hypothesis"
        lines.append(f"- **{t.hypothesis}** (priority: {t.priority}; {status_label}; source: {t.source})")
        lines.append(f"  - Method: {t.method}")
        lines.append(f"  - Success metric: {t.success_metric}")
    lines.append("")
    return "\n".join(lines)


def _slack_weekly_item_lines(items: list, empty_label: str, max_items: int = 5) -> list:
    if not items:
        return [empty_label]
    lines = []
    for item in items[:max_items]:
        action = getattr(item, "action", "")
        lines.append(f"- *{item.entity}* ({item.scope}) -- {item.why} -> {action}")
    remaining = len(items) - max_items
    if remaining > 0:
        lines.append(f"...and {remaining} more (see the full report).")
    return lines


PROPOSAL_DISCLAIMER = (
    "These are PROPOSALS for operator approval, not executed changes. This brief is read-only: any "
    "resulting bid, budget, keyword, or campaign change requires the operator's explicit go-ahead in "
    "`amazon-ads` (interactive Console work) or `amazon-campaign-builder` (bulk create/update)."
)


def render_weekly_markdown(
    weekly_analysis: WeeklyAnalysis,
    recommendations: RecommendationsResult,
    meta: dict,
    flags: Optional[tuple] = None,
) -> str:
    """`flags`: optional `(active_flags, suppressed_flags)` tuple (see
    `flags.evaluate`) -- the weekly brief's WoW headline is the primary
    read, but a brand can optionally also carry today's day-level
    goal-aware flags (same rules as the daily brief) for one combined
    weekly artifact. Omit to render the WoW headline + proposals only.
    """
    account = weekly_analysis.account
    week_end_s = weekly_analysis.week_end.isoformat()
    this_week_start_s = weekly_analysis.this_week_start.isoformat()
    last_week_start_s = weekly_analysis.last_week_start.isoformat()
    last_week_end_s = weekly_analysis.last_week_end.isoformat()

    lines = [f"# Amazon Ads Weekly Brief -- {account} -- week ending {week_end_s}", ""]

    if meta.get("preview"):
        lines += [
            "> **PREVIEW -- mock data.** No live Amazon Ads/Sellerboard/AdLabs data is wired up for "
            "this account yet; this brief is generated from synthetic data so the format can be "
            "reviewed before real data exists.",
            "",
        ]

    lines += [
        f"**This week:** {this_week_start_s} to {week_end_s}  ",
        f"**Last week:** {last_week_start_s} to {last_week_end_s}  ",
        f"**Data source:** {meta.get('source_label', meta.get('source', 'unknown'))}  ",
        f"**Generated:** {meta.get('generated_at', dt.datetime.utcnow().isoformat() + 'Z')}",
    ]

    goal_lens = meta.get("goal_lens")
    if goal_lens:
        lines.append(f"**Goal lens:** {goal_lens.get('label')} -- {goal_lens.get('description')}  ")

    headline_metrics = meta.get("weekly_headline_metrics") or WEEKLY_HEADLINE_METRICS
    headline_labels = meta.get("headline_labels")

    lines += [
        "",
        "## Week-over-week headline",
        "",
        _markdown_weekly_headline_table(weekly_analysis, headline_metrics, headline_labels),
        "",
    ]

    if flags:
        active_flags, suppressed_flags = flags
        lines += [
            "## Flags (today, goal-aware)",
            "",
            _markdown_flag_section("Critical", [f for f in active_flags if f.severity == SEVERITY_CRITICAL]),
            _markdown_flag_section("Alert", [f for f in active_flags if f.severity == SEVERITY_ALERT]),
            _markdown_flag_section("Warn", [f for f in active_flags if f.severity == SEVERITY_WARN]),
            _markdown_flag_section("Info", [f for f in active_flags if f.severity == SEVERITY_INFO]),
        ]
        if suppressed_flags:
            lines.append("### Suppressed (philosophy-aware, not flagged)\n")
            for f in suppressed_flags:
                lines.append(f"- **{f.scope}** ({f.category}) -- {f.metric}: {f.message} {f.suppressed_reason}")
            lines.append("")

    lines += [
        "## PUSH -- scale these",
        "",
        _markdown_push_section(recommendations.push),
        "",
        "## PAUSE / OPTIMIZE -- fix these",
        "",
        _markdown_pause_optimize_section(recommendations.pause_optimize),
        "",
    ]

    test_section = _markdown_test_section(recommendations.tests)
    if test_section:
        lines.append(test_section)

    if recommendations.notes:
        lines.append("## Notes")
        lines.append("")
        for n in recommendations.notes:
            lines.append(f"- {n}")
        lines.append("")

    lines += ["---", "", f"_{PROPOSAL_DISCLAIMER}_", ""]

    return "\n".join(lines)


def render_weekly_slack(
    weekly_analysis: WeeklyAnalysis,
    recommendations: RecommendationsResult,
    meta: dict,
    flags: Optional[tuple] = None,
    max_items: int = 5,
) -> dict:
    account = weekly_analysis.account
    week_end_s = weekly_analysis.week_end.isoformat()
    preview_tag = " [PREVIEW - mock data]" if meta.get("preview") else ""
    goal_lens = meta.get("goal_lens")
    lens_label = goal_lens.get("label") if goal_lens else "Neutral"
    header_text = f"Amazon Ads Weekly Brief -- {account} -- week ending {week_end_s}{preview_tag}"

    slack_metrics = meta.get("weekly_slack_headline_metrics")
    headline_labels = meta.get("headline_labels")
    headline_line = _slack_weekly_headline_line(weekly_analysis, slack_metrics, headline_labels)

    push_lines = _slack_weekly_item_lines(recommendations.push, "No push candidates this week.", max_items)
    pause_lines = _slack_weekly_item_lines(recommendations.pause_optimize, "No pause/optimize candidates this week.", max_items)

    test_lines = []
    for t in recommendations.tests[:max_items]:
        test_lines.append(f"- *{t.hypothesis}* (priority: {t.priority})")
    remaining_tests = len(recommendations.tests) - max_items
    if remaining_tests > 0:
        test_lines.append(f"...and {remaining_tests} more (see the full report).")

    flag_summary_line = None
    if flags:
        active_flags, _ = flags
        n_critical = sum(1 for f in active_flags if f.severity == SEVERITY_CRITICAL)
        n_alert = sum(1 for f in active_flags if f.severity == SEVERITY_ALERT)
        n_warn = sum(1 for f in active_flags if f.severity == SEVERITY_WARN)
        bits = []
        if n_critical:
            bits.append(f"{n_critical} critical")
        if n_alert:
            bits.append(f"{n_alert} alert(s)")
        if n_warn:
            bits.append(f"{n_warn} warn(s)")
        flag_summary_line = ", ".join(bits) if bits else "no active flags today"

    text_fallback_parts = [header_text, f"Goal lens: {lens_label}"]
    if headline_line:
        text_fallback_parts.append(headline_line)
    if flag_summary_line:
        text_fallback_parts.append(f"Today's flags: {flag_summary_line}")
    text_fallback_parts += ["PUSH:"] + push_lines + ["PAUSE / OPTIMIZE:"] + pause_lines
    if test_lines:
        text_fallback_parts += ["New ideas & tests:"] + test_lines
    text_fallback = "\n".join(text_fallback_parts)

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": header_text[:150], "emoji": True}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Goal lens: *{lens_label}*"}]},
        {"type": "section", "text": {"type": "mrkdwn", "text": headline_line or "No headline data."}},
    ]
    if flag_summary_line:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"_Today's flags: {flag_summary_line}_"}})
    blocks += [
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*PUSH*\n" + "\n".join(push_lines)}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*PAUSE / OPTIMIZE*\n" + "\n".join(pause_lines)}},
    ]
    if test_lines:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*New ideas & tests*\n" + "\n".join(test_lines)}})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"Source: {meta.get('source_label', meta.get('source'))}"},
            {"type": "mrkdwn", "text": "Proposals for operator approval -- not executed changes."},
        ],
    })

    return {
        "channel": meta.get("slack_channel_id") or default_slack_channel(),
        "text": text_fallback,
        "blocks": blocks,
    }

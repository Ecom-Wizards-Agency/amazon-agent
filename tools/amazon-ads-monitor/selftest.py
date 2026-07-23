#!/usr/bin/env python3
"""selftest.py -- regression suite for the amazon-ads-monitor toolkit.

Synthetic fixtures only, no network access. Run after any change:

    python3 tools/amazon-ads-monitor/selftest.py

Covers:
- analyze.py: exact delta/trend arithmetic on a hand-built fixture.
- flags.py: a suppressed false-alarm (Rank/SKW ACOS swing) does NOT appear
  in active flags, and each real-anomaly rule (CVR drop w/ stable clicks,
  near-zero Rank impressions, zero-sales-spend, budget-capped, discovery
  bloat) DOES fire, both on a hand-built fixture and on the real
  MockDataSource's scripted scenarios.
- report.py: markdown + Slack payload render without error and contain
  the expected sections/keys.
- run_monitor.py: a full `--source mock` CLI run writes per-account
  markdown files and a valid Slack JSON payload, with no credentials.
- datasource.py `parse_sellerboard_csv`/`SellerboardDataSource`: delimiter
  auto-detection (synthetic semicolon CSV, values never committed as real
  brand financials) and column-name mapping against the REAL gitignored
  sample `_local/ads-monitor/samples/sample_dashboardtotals_7d.csv` (read
  only if present; the expected figures are recomputed from the CSV's own
  raw columns at test time, not hardcoded, so no real financial numbers
  ever land in this committed file).
- crosscheck.py: verified vs mismatch vs no_data verdicts.
- flags.py goal lenses: the same underlying metrics produce different
  flag severities under different `goal=` lenses (rank-launch vs
  profit-maintain vs neutral).
"""

from __future__ import annotations

import datetime as dt
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from analyze import analyze_account, classify_trend, TREND_UP, TREND_DOWN, TREND_FLAT, aggregate_week
from datasource import (
    CATEGORY_DISCOVERY, CATEGORY_RANK, DailyRow, MockDataSource,
    SellerboardDataSource, parse_sellerboard_csv, SELLERBOARD_METRICS,
)
from flags import evaluate, resolve_goal_lens, SEVERITY_CRITICAL, SEVERITY_ALERT, SEVERITY_INFO, SEVERITY_WARN
from crosscheck import cross_check, render_verdict_line, render_verdict_emoji_line, VERIFIED, MISMATCH, NO_DATA
from pacing import compute_pacing, pacing_flag, CUT_ORDER_GUIDANCE, UNDERPACE_GUIDANCE
from recommendations import build_recommendations, parse_signal_digest_markdown
from report import render_markdown, render_slack, render_weekly_markdown, render_weekly_slack
import run_monitor
import run_weekly

FAILURES = []
PASSES = []

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_SAMPLE_PATH = REPO_ROOT / "_local" / "ads-monitor" / "samples" / "sample_dashboardtotals_7d.csv"


def check(name, condition, detail=""):
    if condition:
        PASSES.append(name)
    else:
        FAILURES.append(f"{name}: {detail}")


# ---------------------------------------------------------------------------
# Hand-built fixture: five campaigns, each engineered to trip exactly one
# rule (plus one deliberate cross-campaign discovery-bloat trigger).

REPORT_DATE = dt.date(2026, 7, 12)

_SPECS = {
    "A": {  # Rank/SKW: wide ACOS swing -> must be SUPPRESSED, not active.
        "name": "Rank | SP | Exact | widget | ACME-WID | EW",
        "category": CATEGORY_RANK,
        "baseline": dict(impressions=1000, clicks=40, spend=50.0, sales=100.0, orders=4),
        "day0": dict(sales=25.0),  # ACOS 50% -> 200%
    },
    "B": {  # Discovery: CVR collapse with stable clicks -> real anomaly, warn.
        "name": "Discovery Auto | SP | Auto | widget | ACME | EW",
        "category": CATEGORY_DISCOVERY,
        "baseline": dict(impressions=2000, clicks=100, spend=49.0, sales=224.0, orders=8),
        "day0": dict(clicks=98, orders=1, sales=28.0),
    },
    "C": {  # Rank/SKW: near-zero impressions -> real anomaly, alert.
        "name": "Rank | SP | Exact | gadget | ACME-GAD | EW",
        "category": CATEGORY_RANK,
        "baseline": dict(impressions=800, clicks=32, spend=40.0, sales=80.0, orders=3),
        "day0": dict(impressions=5, clicks=1, spend=2.0, sales=0.0, orders=0),
    },
    "D": {  # Discovery: real spend, persistently zero orders -> real anomaly, alert.
        "name": "Discovery Phrase | SP | Phrase | thing | ACME | EW",
        "category": CATEGORY_DISCOVERY,
        "baseline": dict(impressions=1500, clicks=15, spend=30.0, sales=0.0, orders=0),
        "day0": {},
    },
    "E": {  # Rank/SKW: budget-capped on the report day -> real anomaly, warn.
        "name": "Rank | SP | Exact | thingy | ACME-THY | EW",
        "category": CATEGORY_RANK,
        "baseline": dict(impressions=900, clicks=36, spend=35.0, sales=70.0, orders=3, budget=40.0, budget_capped=False),
        "day0": dict(spend=39.5, budget_capped=True),
    },
}


def build_fixture():
    campaign_rows = []
    per_day_totals = {}
    for cid, spec in _SPECS.items():
        for offset in range(0, 8):
            date = REPORT_DATE - dt.timedelta(days=offset)
            values = dict(spec["baseline"])
            if offset == 0:
                values.update(spec["day0"])
            row = DailyRow(
                account="test-acct",
                date=date,
                level="campaign",
                impressions=values.get("impressions", 0),
                clicks=values.get("clicks", 0),
                spend=values.get("spend", 0.0),
                sales=values.get("sales", 0.0),
                orders=values.get("orders", 0),
                campaign_id=cid,
                campaign_name=spec["name"],
                category=spec["category"],
                budget=values.get("budget"),
                budget_capped=values.get("budget_capped", False),
            )
            campaign_rows.append(row)
            totals = per_day_totals.setdefault(date, {"impressions": 0, "clicks": 0, "spend": 0.0, "sales": 0.0, "orders": 0})
            totals["impressions"] += row.impressions
            totals["clicks"] += row.clicks
            totals["spend"] += row.spend
            totals["sales"] += row.sales
            totals["orders"] += row.orders

    account_rows = [DailyRow(account="test-acct", date=d, level="account", **t) for d, t in per_day_totals.items()]
    return account_rows, campaign_rows


def find(flags, metric, name_substr):
    return [f for f in flags if f.metric == metric and name_substr in f.scope]


def test_trend_classification():
    check("trend_up", classify_trend([1, 1, 1, 2, 2, 2]) == TREND_UP)
    check("trend_down", classify_trend([2, 2, 2, 1, 1, 1]) == TREND_DOWN)
    check("trend_flat", classify_trend([10, 10.2, 9.9, 10.1, 10, 9.95]) == TREND_FLAT)
    check("trend_insufficient_data", classify_trend([None, None, 5]) == TREND_FLAT)


def test_deltas_exact_arithmetic(analysis):
    e_series = next(s for s in analysis.campaign_series if s.label == _SPECS["E"]["name"])
    spend_d = e_series.deltas["spend"]
    check("delta_value", spend_d.value == 39.5, spend_d.value)
    check("delta_prior_value", spend_d.prior_value == 35.0, spend_d.prior_value)
    check("delta_prior_abs_change", abs(spend_d.prior_abs_change - 4.5) < 1e-9, spend_d.prior_abs_change)
    check("delta_prior_pct_change", abs(spend_d.prior_pct_change - (4.5 / 35.0)) < 1e-9, spend_d.prior_pct_change)
    check("delta_trailing7_avg", spend_d.trailing7_avg == 35.0, spend_d.trailing7_avg)
    check("delta_trailing7_pct_change", abs(spend_d.trailing7_pct_change - (4.5 / 35.0)) < 1e-9, spend_d.trailing7_pct_change)


def test_flags_fixture(analysis):
    active, suppressed = evaluate(analysis)

    check(
        "suppressed_rank_acos_not_active",
        find(active, "acos", _SPECS["A"]["name"]) == [],
        "Rank/SKW ACOS swing leaked into active flags",
    )
    check(
        "suppressed_rank_acos_in_suppressed",
        bool(find(suppressed, "acos", _SPECS["A"]["name"])),
        "Rank/SKW ACOS swing missing from suppressed list",
    )
    cvr_flags = find(active, "cvr", _SPECS["B"]["name"])
    check("cvr_drop_stable_clicks_fires", bool(cvr_flags) and cvr_flags[0].severity == "warn", cvr_flags)

    impr_flags = find(active, "impressions", _SPECS["C"]["name"])
    check("near_zero_impressions_rank_fires", bool(impr_flags) and impr_flags[0].severity == "alert", impr_flags)

    orders_flags = find(active, "orders", _SPECS["D"]["name"])
    check("zero_sales_spend_fires", bool(orders_flags) and orders_flags[0].severity == "alert", orders_flags)

    budget_flags = [f for f in active if f.metric == "spend" and _SPECS["E"]["name"] in f.scope and "budget" in f.likely_cause.lower()]
    check("budget_capped_fires", bool(budget_flags) and budget_flags[0].severity == "warn", budget_flags)

    discovery_flags = [f for f in active if f.metric == "discovery_share_of_spend" and f.scope == "account"]
    check("discovery_share_fires", bool(discovery_flags), discovery_flags)

    return active, suppressed


def test_report_rendering(analysis, active, suppressed):
    meta = {
        "source": "mock",
        "source_label": "MOCK (synthetic data, no live credentials)",
        "preview": True,
        "attribution_window": "7d (synthetic)",
        "generated_at": "2026-07-13T00:00:00Z",
        "slack_channel_id": "C000000000",
        "notes": [],
    }
    md = render_markdown(analysis, active, suppressed, meta)
    check("markdown_has_title", "Amazon Ads Daily Monitor" in md)
    check("markdown_has_preview_banner", "PREVIEW" in md)
    check("markdown_has_suppressed_section", "Suppressed" in md and _SPECS["A"]["name"] in md)
    check("markdown_has_arrow_symbol", ("▲" in md) or ("▼" in md))
    check("markdown_suppressed_not_in_active_sections", _count_flag_mentions(md, _SPECS["A"]["name"], "acos") <= 1)

    slack = render_slack(analysis, active, suppressed, meta)
    check("slack_has_blocks", "blocks" in slack and isinstance(slack["blocks"], list) and len(slack["blocks"]) > 0)
    check("slack_channel_default", slack["channel"] == "C000000000", slack["channel"])
    check("slack_text_nonempty", bool(slack.get("text")))
    check("slack_preview_tag", "PREVIEW" in slack["text"])


def _count_flag_mentions(markdown_text: str, name: str, metric: str) -> int:
    # Suppressed section legitimately mentions the campaign once; active
    # Flags sections must not mention it a second time for this metric.
    count = 0
    for line in markdown_text.splitlines():
        if name in line and metric in line:
            count += 1
    return count


def test_mock_datasource_scenarios():
    ds = MockDataSource()
    report_date = dt.date(2026, 3, 15)  # arbitrary: scenarios anchor to "end date", not a calendar date
    start = report_date - dt.timedelta(days=14)
    account = "acme-us"
    account_rows = ds.get_account_daily(account, start, report_date)
    campaign_rows = ds.get_campaign_daily(account, start, report_date)
    analysis = analyze_account(account, report_date, account_rows, campaign_rows)
    active, suppressed = evaluate(analysis)

    check(
        "mock_suppressed_rank_acos_not_active",
        find(active, "acos", "bamboo cutting board") == [],
        find(active, "acos", "bamboo cutting board"),
    )
    check(
        "mock_suppressed_rank_acos_in_suppressed",
        bool(find(suppressed, "acos", "bamboo cutting board")),
    )
    check("mock_near_zero_impressions_fires", bool(find(active, "impressions", "bamboo salad bowl")))
    check("mock_cvr_drop_fires", bool(find(active, "cvr", "bamboo cheese board")))
    check("mock_zero_sales_spend_fires", bool(find(active, "orders", "new arrivals scavenger")))
    check("mock_discovery_share_fires", any(f.metric == "discovery_share_of_spend" for f in active))
    check(
        "mock_budget_capped_fires",
        any(f.metric == "spend" and "bamboo cutting board" in f.scope and "budget" in f.likely_cause.lower() for f in active),
    )


def test_cli_end_to_end_mock():
    with tempfile.TemporaryDirectory() as tmp:
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = run_monitor.main([
                "--source", "mock",
                "--date", "2026-05-01",
                "--out", tmp,
                "--slack-json", "-",
            ])
        stdout = buf.getvalue()
        check("cli_exit_zero", exit_code == 0, exit_code)

        acme_md = Path(tmp, "acme-us", "ads-monitor", "2026-05-01_daily.md")
        globex_md = Path(tmp, "globex-us", "ads-monitor", "2026-05-01_daily.md")
        check("cli_writes_acme_md", acme_md.exists())
        check("cli_writes_globex_md", globex_md.exists())
        if acme_md.exists():
            check("cli_md_has_title", "Amazon Ads Daily Monitor" in acme_md.read_text(encoding="utf-8"))

        # Slack payload is the only JSON object printed after the per-account
        # summary lines; find the line starting the JSON blob.
        json_start = stdout.find("{")
        check("cli_prints_slack_json", json_start != -1)
        if json_start != -1:
            payload = json.loads(stdout[json_start:])
            check("cli_slack_json_has_both_accounts", "acme-us" in payload and "globex-us" in payload, list(payload))


# ---------------------------------------------------------------------------
# Sellerboard CSV parsing: synthetic delimiter-detection fixture + a real
# sample used only to compute expectations dynamically (never hardcoded).

def test_sellerboard_semicolon_delimiter_autodetect():
    """Synthetic values only -- proves comma vs semicolon auto-detection
    and column-name mapping (not position), independent of any real
    account's numbers."""
    header = (
        '"Date";"SalesOrganic";"SalesPPC";"SalesSponsoredProducts";"SalesSponsoredDisplay";'
        '"UnitsOrganic";"UnitsPPC";"Orders";"Refunds";"SponsoredProducts";"SponsoredDisplay";'
        '"SponsoredBrands";"SponsoredBrandsVideo";"GrossProfit";"NetProfit";"Margin";"Real ACOS";'
        '"Sessions";"Unit Session Percentage"'
    )
    row = (
        '"01/06/2026";"1000.00";"500.00";"400.00";"100.00";"10";"5";"15";"1";'
        '"-150.00";"-20.00";"0.00";"0.00";"300.00";"280.00";"18.67";"34.00";"200";"7.50"'
    )
    synthetic_semicolon_csv = header + "\n" + row + "\n"

    rows = parse_sellerboard_csv(synthetic_semicolon_csv, "synth-acct")
    check("semicolon_parses_one_row", len(rows) == 1, len(rows))
    if rows:
        r = rows[0]
        check("semicolon_date", r.date == dt.date(2026, 6, 1), r.date)
        check("semicolon_total_sales", abs(r.total_sales - 1500.0) < 1e-6, r.total_sales)
        check("semicolon_ad_spend_abs_and_summed", abs(r.spend - 170.0) < 1e-6, r.spend)  # abs(-150)+abs(-20)
        check("semicolon_ad_sales", abs(r.sales - 500.0) < 1e-6, r.sales)
        check("semicolon_orders", r.orders == 15, r.orders)
        check("semicolon_real_acos_pct_to_fraction", abs(r.real_acos - 0.34) < 1e-6, r.real_acos)
        check("semicolon_margin_pct_to_fraction", abs(r.margin - 0.1867) < 1e-6, r.margin)

    # The identical logical row, comma-delimited, must parse to the same
    # values -- proves the difference is genuinely delimiter detection,
    # not some semicolon-specific code path.
    comma_csv = synthetic_semicolon_csv.replace(";", ",")
    comma_rows = parse_sellerboard_csv(comma_csv, "synth-acct")
    check(
        "comma_variant_matches_semicolon_variant",
        bool(comma_rows) and abs(comma_rows[0].spend - 170.0) < 1e-6 and abs(comma_rows[0].total_sales - 1500.0) < 1e-6,
        comma_rows,
    )

    # Blank feed -> [] (not an error): signals "fall back to AdLabs".
    check("blank_feed_returns_empty_list", parse_sellerboard_csv("", "synth-acct") == [])
    check("header_only_feed_returns_empty_list", parse_sellerboard_csv(header + "\n", "synth-acct") == [])


def test_real_sellerboard_sample():
    """Parses the REAL gitignored sample and checks the parser's output
    against expectations recomputed independently from the CSV's own raw
    columns at test time -- so this committed file never hardcodes a real
    brand's financial figures. Skips (not a failure) if the gitignored
    sample isn't present in this checkout."""
    if not REAL_SAMPLE_PATH.exists():
        PASSES.append("real_sample_skipped (gitignored sample not present in this checkout)")
        return

    import csv as _csv

    with REAL_SAMPLE_PATH.open(encoding="utf-8-sig") as fh:
        raw_by_date = {}
        for raw in _csv.DictReader(fh):
            d = dt.datetime.strptime(raw["Date"].strip(), "%d/%m/%Y").date()
            raw_by_date[d] = raw

    def expected(d):
        raw = raw_by_date[d]
        sales_organic = float(raw["SalesOrganic"])
        sales_ppc = float(raw["SalesPPC"])
        total_sales = sales_organic + sales_ppc
        ad_spend = sum(
            abs(float(raw[c])) for c in ("SponsoredProducts", "SponsoredDisplay", "SponsoredBrands", "SponsoredBrandsVideo")
        )
        real_acos = float(raw["Real ACOS"]) / 100.0
        tacos = (ad_spend / total_sales) if total_sales else None
        return total_sales, ad_spend, tacos, real_acos

    d12 = dt.date(2026, 7, 12)
    d13 = dt.date(2026, 7, 13)
    check("real_sample_has_12_and_13_july", d12 in raw_by_date and d13 in raw_by_date, sorted(raw_by_date))
    if d12 not in raw_by_date or d13 not in raw_by_date:
        return

    exp_total_12, exp_spend_12, exp_tacos_12, exp_real_acos_12 = expected(d12)
    exp_total_13, exp_spend_13, exp_tacos_13, exp_real_acos_13 = expected(d13)

    ds = SellerboardDataSource.from_paths({"acme": [str(REAL_SAMPLE_PATH)]})
    rows = ds.get_account_daily("acme", d12 - dt.timedelta(days=7), d13)
    by_date = {r.date: r for r in rows}
    r12, r13 = by_date.get(d12), by_date.get(d13)
    check("real_sample_parses_12_and_13", r12 is not None and r13 is not None)
    if not (r12 and r13):
        return

    check("real_sample_total_sales_12", abs(r12.total_sales - exp_total_12) < 1e-6, (r12.total_sales, exp_total_12))
    check("real_sample_ad_spend_12", abs(r12.spend - exp_spend_12) < 1e-6, (r12.spend, exp_spend_12))
    check("real_sample_tacos_12", abs(r12.tacos - exp_tacos_12) < 1e-6, (r12.tacos, exp_tacos_12))
    check("real_sample_real_acos_12", abs(r12.real_acos - exp_real_acos_12) < 1e-6, (r12.real_acos, exp_real_acos_12))
    check("real_sample_total_sales_13", abs(r13.total_sales - exp_total_13) < 1e-6, (r13.total_sales, exp_total_13))
    check("real_sample_ad_spend_13", abs(r13.spend - exp_spend_13) < 1e-6, (r13.spend, exp_spend_13))
    check("real_sample_tacos_13", abs(r13.tacos - exp_tacos_13) < 1e-6, (r13.tacos, exp_tacos_13))
    check("real_sample_real_acos_13", abs(r13.real_acos - exp_real_acos_13) < 1e-6, (r13.real_acos, exp_real_acos_13))

    # Day-over-day (13/07 vs 12/07), via analyze.py, checked against the
    # same independently-recomputed expected values -- not the parser's
    # own numbers, so this actually exercises the delta math too.
    analysis = analyze_account("acme", d13, rows, [], metrics=SELLERBOARD_METRICS)
    total_sales_d = analysis.account_series.deltas["total_sales"]
    spend_d = analysis.account_series.deltas["spend"]
    exp_total_delta = exp_total_13 - exp_total_12
    exp_spend_delta = exp_spend_13 - exp_spend_12
    check(
        "real_sample_dod_total_sales_abs_change",
        abs(total_sales_d.prior_abs_change - exp_total_delta) < 1e-6,
        (total_sales_d.prior_abs_change, exp_total_delta),
    )
    check(
        "real_sample_dod_ad_spend_abs_change",
        abs(spend_d.prior_abs_change - exp_spend_delta) < 1e-6,
        (spend_d.prior_abs_change, exp_spend_delta),
    )
    check(
        "real_sample_dod_total_sales_pct_change",
        abs(total_sales_d.prior_pct_change - (exp_total_delta / exp_total_12)) < 1e-6,
        (total_sales_d.prior_pct_change, exp_total_delta / exp_total_12),
    )
    check(
        "real_sample_dod_ad_spend_pct_change",
        abs(spend_d.prior_pct_change - (exp_spend_delta / exp_spend_12)) < 1e-6,
        (spend_d.prior_pct_change, exp_spend_delta / exp_spend_12),
    )


# ---------------------------------------------------------------------------
# crosscheck.py: verified / mismatch / no_data verdicts.

def test_crosscheck_verdicts():
    sb = {"ad_spend": 100.0, "ad_sales": 500.0, "total_sales": 2000.0}
    al_close = {"ad_spend": 104.0, "ad_sales": 480.0, "total_sales": 2050.0}  # all within +/-7%
    verified = cross_check(sb, al_close)
    check("crosscheck_verified_headline", verified.headline_verdict == VERIFIED, verified.headline_verdict)
    check("crosscheck_verified_all_figures", all(f.verdict == VERIFIED for f in verified.figures))
    check("crosscheck_verified_emoji_line", render_verdict_emoji_line(verified).startswith("✅"))

    al_far = {"ad_spend": 160.0, "ad_sales": 480.0, "total_sales": 2050.0}  # ad_spend +60%
    mismatch = cross_check(sb, al_far)
    check("crosscheck_mismatch_headline", mismatch.headline_verdict == MISMATCH, mismatch.headline_verdict)
    mismatches = mismatch.mismatches()
    check("crosscheck_mismatch_isolates_ad_spend", len(mismatches) == 1 and mismatches[0].figure == "ad_spend", mismatches)
    line = render_verdict_line(mismatch)
    check("crosscheck_mismatch_line_names_figure_and_pct", "ad spend" in line and "+60%" in line, line)

    no_data = cross_check({}, {})
    check("crosscheck_no_data_headline", no_data.headline_verdict == NO_DATA, no_data.headline_verdict)

    tolerance_result = cross_check(sb, {"ad_spend": 106.0}, tolerance=0.10)
    check(
        "crosscheck_custom_tolerance_respected",
        [f for f in tolerance_result.figures if f.figure == "ad_spend"][0].verdict == VERIFIED,
    )


# ---------------------------------------------------------------------------
# flags.py goal lenses: same metrics, different severities per lens.

def test_goal_lens_severity_differences(campaign_analysis):
    # Campaign C (Rank/SKW near-zero impressions) is an ALERT under the
    # neutral lens; rank-launch's `impression_rank_critical` must escalate
    # it to CRITICAL, since losing the keyword we're trying to rank is the
    # single worst outcome under that goal.
    active_neutral, _ = evaluate(campaign_analysis, goal=None)
    active_rank_launch, _ = evaluate(campaign_analysis, goal="rank-launch")

    c_neutral = find(active_neutral, "impressions", _SPECS["C"]["name"])
    c_rank_launch = find(active_rank_launch, "impressions", _SPECS["C"]["name"])
    check(
        "goal_neutral_near_zero_impressions_is_alert",
        bool(c_neutral) and c_neutral[0].severity == SEVERITY_ALERT,
        c_neutral,
    )
    check(
        "goal_rank_launch_near_zero_impressions_escalated_to_critical",
        bool(c_rank_launch) and c_rank_launch[0].severity == SEVERITY_CRITICAL,
        c_rank_launch,
    )

    # Account-level goal-aware TACOS/margin read: build a small
    # Sellerboard-style account series with a sharp TACOS rise + margin
    # drop on the report day vs a flat trailing week, and confirm the two
    # lenses treat the identical numbers oppositely (expected_high/
    # suppressed under rank-launch vs alert_on_rise/active under
    # profit-maintain).
    report_date = dt.date(2026, 7, 13)
    account_rows = []
    for offset in range(0, 8):
        d = report_date - dt.timedelta(days=offset)
        if offset == 0:
            spend, total_sales, margin = 60.0, 300.0, 0.05  # TACOS 20%, margin 5%
        else:
            spend, total_sales, margin = 30.0, 300.0, 0.20  # TACOS 10%, margin 20%
        account_rows.append(DailyRow(
            account="lens-test", date=d, level="account",
            impressions=0, clicks=0, spend=spend, sales=spend, orders=5,
            total_sales=total_sales, margin=margin, real_acos=0.1,
        ))
    lens_analysis = analyze_account("lens-test", report_date, account_rows, [], metrics=SELLERBOARD_METRICS)

    active_profit, _ = evaluate(lens_analysis, goal="profit-maintain")
    active_launch, suppressed_launch = evaluate(lens_analysis, goal="rank-launch")
    active_neutral_acct, suppressed_neutral_acct = evaluate(lens_analysis, goal=None)

    profit_tm = [f for f in active_profit if f.metric == "tacos_margin"]
    check(
        "goal_profit_maintain_tacos_margin_is_active_alert",
        bool(profit_tm) and profit_tm[0].severity == SEVERITY_ALERT,
        profit_tm,
    )

    launch_tm_active = [f for f in active_launch if f.metric == "tacos_margin"]
    launch_tm_suppressed = [f for f in suppressed_launch if f.metric == "tacos_margin"]
    check("goal_rank_launch_tacos_margin_not_active", launch_tm_active == [], launch_tm_active)
    check(
        "goal_rank_launch_tacos_margin_suppressed_as_info",
        bool(launch_tm_suppressed) and launch_tm_suppressed[0].severity == SEVERITY_INFO,
        launch_tm_suppressed,
    )

    # Neutral lens ("ignore" behavior): no goal-aware tacos/margin flag at
    # all, active or suppressed -- confirms the check is opt-in per lens,
    # not always-on.
    neutral_tm_any = [f for f in (active_neutral_acct + suppressed_neutral_acct) if f.metric == "tacos_margin"]
    check("goal_neutral_tacos_margin_check_is_off", neutral_tm_any == [], neutral_tm_any)


# ---------------------------------------------------------------------------
# Weekly brief: analyze.aggregate_week arithmetic on a synthetic ~14-day
# Sellerboard-style series (distinct this-week vs last-week values on
# every summed metric, exact expectations computed by hand).

WEEK_END = dt.date(2026, 7, 12)  # this week: 07-06..07-12; last week: 06-29..07-05


def build_weekly_fixture_rows(account: str = "weekly-test") -> list:
    rows = []
    this_week_start = WEEK_END - dt.timedelta(days=6)
    last_week_end = this_week_start - dt.timedelta(days=1)
    last_week_start = last_week_end - dt.timedelta(days=6)
    for offset in range(14):
        d = last_week_start + dt.timedelta(days=offset)
        in_this_week = d >= this_week_start
        if in_this_week:
            total_sales, spend, sales, orders, net_profit = 1200.0, 150.0, 400.0, 12, 250.0
        else:
            total_sales, spend, sales, orders, net_profit = 1000.0, 100.0, 300.0, 10, 200.0
        rows.append(DailyRow(
            account=account, date=d, level="account",
            impressions=0, clicks=0, spend=spend, sales=sales, orders=orders,
            total_sales=total_sales, net_profit=net_profit, real_acos=0.15,
        ))
    return rows


def test_aggregate_week_math():
    rows = build_weekly_fixture_rows()
    weekly = aggregate_week(rows, WEEK_END)

    check("weekly_week_end", weekly.week_end == WEEK_END, weekly.week_end)
    check("weekly_this_week_start", weekly.this_week_start == WEEK_END - dt.timedelta(days=6))
    check("weekly_this_week_row_count", len(weekly.this_week_rows) == 7, len(weekly.this_week_rows))
    check("weekly_last_week_row_count", len(weekly.last_week_rows) == 7, len(weekly.last_week_rows))

    ts = weekly.deltas["total_sales"]
    check("weekly_total_sales_this_week_sum", ts.this_week == 8400.0, ts.this_week)
    check("weekly_total_sales_last_week_sum", ts.last_week == 7000.0, ts.last_week)
    check("weekly_total_sales_abs_change", abs(ts.abs_change - 1400.0) < 1e-9, ts.abs_change)
    check("weekly_total_sales_pct_change", abs(ts.pct_change - (1400.0 / 7000.0)) < 1e-9, ts.pct_change)

    spend_d = weekly.deltas["spend"]
    check("weekly_spend_this_week_sum", spend_d.this_week == 1050.0, spend_d.this_week)
    check("weekly_spend_last_week_sum", spend_d.last_week == 700.0, spend_d.last_week)
    check("weekly_spend_pct_change", abs(spend_d.pct_change - 0.5) < 1e-9, spend_d.pct_change)

    sales_d = weekly.deltas["sales"]
    check("weekly_sales_this_week_sum", sales_d.this_week == 2800.0, sales_d.this_week)
    check("weekly_sales_last_week_sum", sales_d.last_week == 2100.0, sales_d.last_week)

    orders_d = weekly.deltas["orders"]
    check("weekly_orders_this_week_sum", orders_d.this_week == 84, orders_d.this_week)
    check("weekly_orders_last_week_sum", orders_d.last_week == 70, orders_d.last_week)
    check("weekly_orders_pct_change", abs(orders_d.pct_change - 0.2) < 1e-9, orders_d.pct_change)

    net_profit_d = weekly.deltas["net_profit"]
    check("weekly_net_profit_pct_change", abs(net_profit_d.pct_change - 0.25) < 1e-9, net_profit_d.pct_change)

    # Ratio metrics recomputed from the summed components, not averaged day-by-day.
    acos_d = weekly.deltas["acos"]
    check("weekly_acos_this_week", abs(acos_d.this_week - (1050.0 / 2800.0)) < 1e-9, acos_d.this_week)
    check("weekly_acos_last_week", abs(acos_d.last_week - (700.0 / 2100.0)) < 1e-9, acos_d.last_week)

    tacos_d = weekly.deltas["tacos"]
    check("weekly_tacos_this_week", abs(tacos_d.this_week - (1050.0 / 8400.0)) < 1e-9, tacos_d.this_week)
    check("weekly_tacos_last_week", abs(tacos_d.last_week - (700.0 / 7000.0)) < 1e-9, tacos_d.last_week)

    margin_d = weekly.deltas["margin"]
    check("weekly_margin_this_week", abs(margin_d.this_week - (1750.0 / 8400.0)) < 1e-9, margin_d.this_week)
    check("weekly_margin_last_week", abs(margin_d.last_week - (1400.0 / 7000.0)) < 1e-9, margin_d.last_week)

    # real_acos is a simple mean of the days reporting a value (not resummed).
    real_acos_d = weekly.deltas["real_acos"]
    check("weekly_real_acos_this_week", abs(real_acos_d.this_week - 0.15) < 1e-9, real_acos_d.this_week)
    check("weekly_real_acos_abs_change", abs(real_acos_d.abs_change - 0.0) < 1e-9, real_acos_d.abs_change)

    return weekly


# ---------------------------------------------------------------------------
# recommendations.py: goal-differentiated Push/Pause-Optimize on synthetic
# AdLabs-style entities. A Halo/Profit target at 30% ACOS should be a
# Pause/Optimize candidate under the strict profit-maintain ceiling (25%)
# but NOT under the looser rank-launch ceiling (45%); a Rank/SKW keyword
# converting at a much worse ACOS must never be proposed for a cut on ACOS
# grounds under either goal (ACOS is an indicator, not a decision factor).

_PROFIT_ENTITY = {
    "entity_type": "target", "name": "mid acos halo target",
    "campaign_name": "Halo | SP | Exact | widget long tail | ACME | EW",
    "match_type": "exact", "impressions": 2000, "clicks": 100,
    "spend": 90.0, "sales": 300.0, "orders": 5,
}
_RANK_ENTITY = {
    "entity_type": "target", "name": "high acos rank keyword",
    "campaign_name": "Rank | SP | Exact | widget | ACME-WID | EW",
    "match_type": "exact", "impressions": 3000, "clicks": 150,
    "spend": 150.0, "sales": 100.0, "orders": 5,
}


def _pause_names(result):
    return [item.entity for item in result.pause_optimize]


def _push_names(result):
    return [item.entity for item in result.push]


def test_build_recommendations_goal_differentiated():
    entities = [dict(_PROFIT_ENTITY), dict(_RANK_ENTITY)]

    profit_maintain = build_recommendations(entities, goal="profit-maintain")
    rank_launch = build_recommendations(entities, goal="rank-launch")

    check(
        "rec_profit_entity_paused_under_profit_maintain",
        _PROFIT_ENTITY["name"] in _pause_names(profit_maintain),
        _pause_names(profit_maintain),
    )
    check(
        "rec_profit_entity_not_paused_under_rank_launch",
        _PROFIT_ENTITY["name"] not in _pause_names(rank_launch),
        _pause_names(rank_launch),
    )
    check(
        "rec_rank_entity_never_paused_profit_maintain",
        _RANK_ENTITY["name"] not in _pause_names(profit_maintain),
        _pause_names(profit_maintain),
    )
    check(
        "rec_rank_entity_never_paused_rank_launch",
        _RANK_ENTITY["name"] not in _pause_names(rank_launch),
        _pause_names(rank_launch),
    )
    check(
        "rec_rank_entity_pushed_despite_high_acos",
        _RANK_ENTITY["name"] in _push_names(profit_maintain) and _RANK_ENTITY["name"] in _push_names(rank_launch),
        (_push_names(profit_maintain), _push_names(rank_launch)),
    )
    return profit_maintain, rank_launch


def test_select_tests_empty_and_signal_driven():
    # A single healthy Rank entity, no goal, no situation, no signals ->
    # nothing in the vetted backlog is pertinent -> tests == [] (not a
    # fabricated filler test), and a note says so explicitly.
    healthy_rank_only = [dict(
        entity_type="target", name="healthy rank keyword",
        campaign_name="Rank | SP | Exact | gizmo | ACME-GIZ | EW",
        match_type="exact", impressions=5000, clicks=200, spend=40.0, sales=200.0, orders=8,
    )]
    empty_result = build_recommendations(healthy_rank_only, goal=None)
    check("rec_tests_empty_when_nothing_pertinent", empty_result.tests == [], empty_result.tests)
    check(
        "rec_notes_say_no_new_tests",
        any("no new tests" in n.lower() for n in empty_result.notes),
        empty_result.notes,
    )

    # The same brand this week, but an external-signal digest bullet whose
    # tag ("rank_present") matches this week's actual signals -> a
    # non-fabricated, digest-sourced test idea should surface.
    digest_text = (
        "- **Test broad-match variants alongside the exact Rank keyword.** "
        "Tags: rank_present. Source: PPC Newsletter #42. Confidence: unverified."
    )
    signal_items = parse_signal_digest_markdown(digest_text)
    check("rec_digest_parses_one_item", len(signal_items) == 1, signal_items)

    signal_driven_result = build_recommendations(healthy_rank_only, goal=None, signal_items=signal_items)
    check("rec_tests_nonempty_with_matching_signal", len(signal_driven_result.tests) == 1, signal_driven_result.tests)
    if signal_driven_result.tests:
        t = signal_driven_result.tests[0]
        check("rec_test_status_is_external_signal", t.status == "external_signal_hypothesis", t.status)
        check("rec_test_hypothesis_from_digest", "broad-match variants" in t.hypothesis, t.hypothesis)

    return empty_result, signal_driven_result


# ---------------------------------------------------------------------------
# report.py weekly renderers: non-empty markdown with the right sections,
# and a Slack payload dict with the expected shape, for both an
# empty-tests and a non-empty-tests RecommendationsResult.

def test_weekly_report_rendering(weekly, active_flags, suppressed_flags, empty_tests_result, signal_driven_result):
    base_meta = {
        "source": "sellerboard",
        "source_label": "Sellerboard 'Dashboard Totals' (PRIMARY, whole-account truth)",
        "preview": False,
        "generated_at": "2026-07-13T00:00:00Z",
        "slack_channel_id": "C000000000",
        "goal_lens": {"label": "Profit / Maintain", "description": "Mature ASIN, defending margin."},
    }

    md_no_tests = render_weekly_markdown(weekly, empty_tests_result, base_meta)
    check("weekly_md_nonempty_no_tests", bool(md_no_tests.strip()))
    check("weekly_md_has_title", "Amazon Ads Weekly Brief" in md_no_tests)
    check("weekly_md_has_wow_headline", "Week-over-week headline" in md_no_tests)
    check("weekly_md_has_push_section", "PUSH" in md_no_tests)
    check("weekly_md_has_pause_section", "PAUSE / OPTIMIZE" in md_no_tests)
    check("weekly_md_has_proposal_disclaimer", "PROPOSALS for operator approval" in md_no_tests)
    check("weekly_md_no_test_section_when_empty", "New ideas & tests" not in md_no_tests)
    check("weekly_md_no_flags_section_when_omitted", "Flags (today" not in md_no_tests)

    md_with_tests = render_weekly_markdown(weekly, signal_driven_result, base_meta, flags=(active_flags, suppressed_flags))
    check("weekly_md_test_section_when_nonempty", "New ideas & tests" in md_with_tests)
    check("weekly_md_flags_section_when_given", "Flags (today" in md_with_tests)
    check("weekly_md_arrow_symbol", ("▲" in md_with_tests) or ("▼" in md_with_tests) or ("–" in md_with_tests))

    slack_no_tests = render_weekly_slack(weekly, empty_tests_result, base_meta)
    check("weekly_slack_is_dict", isinstance(slack_no_tests, dict))
    check("weekly_slack_has_channel", slack_no_tests.get("channel") == "C000000000", slack_no_tests.get("channel"))
    check("weekly_slack_has_blocks", isinstance(slack_no_tests.get("blocks"), list) and len(slack_no_tests["blocks"]) > 0)
    check("weekly_slack_text_nonempty", bool(slack_no_tests.get("text")))
    check("weekly_slack_goal_lens_label", "Profit / Maintain" in slack_no_tests["text"])

    slack_with_tests = render_weekly_slack(weekly, signal_driven_result, base_meta, flags=(active_flags, suppressed_flags))
    check(
        "weekly_slack_has_test_block",
        any("New ideas & tests" in (b.get("text", {}).get("text", "")) for b in slack_with_tests["blocks"] if b.get("type") == "section"),
    )


# ---------------------------------------------------------------------------
# run_weekly.py CLI: a full end-to-end run from a synthetic Sellerboard CSV
# alone (no AdLabs), plus a run WITH an AdLabs entities file + a signal
# digest, proving the CLI's argument wiring (not just the library calls).

def _build_synthetic_weekly_csv(days: int = 21) -> str:
    header = [
        "Date", "SalesOrganic", "SalesPPC", "SalesSponsoredProducts", "SalesSponsoredDisplay",
        "UnitsOrganic", "UnitsPPC", "Orders", "Refunds", "SponsoredProducts", "SponsoredDisplay",
        "SponsoredBrands", "SponsoredBrandsVideo", "GrossProfit", "NetProfit", "Margin", "Real ACOS",
        "Sessions", "Unit Session Percentage",
    ]
    start = dt.date(2026, 6, 20)
    lines = [",".join(header)]
    for i in range(days):
        d = start + dt.timedelta(days=i)
        lines.append(",".join([
            d.strftime("%d/%m/%Y"), "700.00", "300.00", "250.00", "50.00", "20", "8", "15", "1",
            "-150.00", "-20.00", "0.00", "0.00", "300.00", "250.00", "20.00", "15.00", "500", "3.00",
        ]))
    return "\n".join(lines) + "\n"


def test_cli_end_to_end_weekly():
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp, "acme-us_dashboardtotals_30d.csv")
        csv_path.write_text(_build_synthetic_weekly_csv(), encoding="utf-8")

        adlabs_path = Path(tmp, "adlabs_weekly.json")
        adlabs_path.write_text(json.dumps([dict(_PROFIT_ENTITY), dict(_RANK_ENTITY)]), encoding="utf-8")

        digest_path = Path(tmp, "digest.md")
        digest_path.write_text(
            "- **Test broad-match variants alongside the exact Rank keyword.** "
            "Tags: rank_present. Source: PPC Newsletter #42. Confidence: unverified.\n",
            encoding="utf-8",
        )

        radar_path = Path(tmp, "rank_radar.json")
        radar_path.write_text(json.dumps([
            {"keyword": _RANK_ENTITY["name"], "rank_now": 1, "rank_prev": 2, "weeks_stable": 4},
        ]), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = run_weekly.main([
                "--csv", str(csv_path),
                "--account", "acme-us",
                "--date", "2026-07-10",
                "--goal", "profit-maintain",
                "--situation", "recurring acos spike on broad match",
                "--adlabs-json", str(adlabs_path),
                "--signal-digest", str(digest_path),
                "--rank-radar-json", str(radar_path),
                "--monthly-budget", "4000",
                "--out", tmp,
                "--slack-json", "-",
            ])
        stdout = buf.getvalue()
        check("weekly_cli_exit_zero", exit_code == 0, exit_code)

        out_md = Path(tmp, "acme-us", "ads-monitor", "2026-07-10_weekly.md")
        check("weekly_cli_writes_md", out_md.exists())
        if out_md.exists():
            text = out_md.read_text(encoding="utf-8")
            check("weekly_cli_md_has_title", "Amazon Ads Weekly Brief" in text)
            check("weekly_cli_md_has_push_or_pause_entity", (_PROFIT_ENTITY["name"] in text) or (_RANK_ENTITY["name"] in text))
            check("weekly_cli_md_has_pacing_section", "Run-rate pacing" in text)
            check("weekly_cli_md_has_graduate_section", "GRADUATE -- rank achieved" in text)

        json_start = stdout.find("{")
        check("weekly_cli_prints_slack_json", json_start != -1)
        if json_start != -1:
            payload = json.loads(stdout[json_start:])
            check("weekly_cli_slack_json_has_channel", bool(payload.get("channel")), payload.get("channel"))


def test_cli_end_to_end_weekly_csv_only():
    """The weekly CLI must run end-to-end from a Sellerboard CSV alone
    (no --adlabs-json, no --signal-digest) -- Push/Pause-Optimize come
    back empty with a note, not an error."""
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp, "globex-us_dashboardtotals_30d.csv")
        csv_path.write_text(_build_synthetic_weekly_csv(), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = run_weekly.main([
                "--csv", str(csv_path),
                "--account", "globex-us",
                "--date", "2026-07-10",
                "--out", tmp,
            ])
        check("weekly_csv_only_cli_exit_zero", exit_code == 0, exit_code)
        out_md = Path(tmp, "globex-us", "ads-monitor", "2026-07-10_weekly.md")
        check("weekly_csv_only_cli_writes_md", out_md.exists())
        if out_md.exists():
            text = out_md.read_text(encoding="utf-8")
            check("weekly_csv_only_no_adlabs_note_present", "No AdLabs campaign/target-level rows supplied" in text)


# ---------------------------------------------------------------------------
# pacing.py: month-to-date run-rate governor math, goal-lens threshold
# layering, coverage honesty, and the flag severities.

class _SpendDay:
    """Minimal row for compute_pacing (needs only .date and .spend)."""

    def __init__(self, date, spend):
        self.date = date
        self.spend = spend


def _spend_days(start: dt.date, days: int, spend_per_day: float):
    return [_SpendDay(start + dt.timedelta(days=i), spend_per_day) for i in range(days)]


def test_pacing_math():
    as_of = dt.date(2026, 7, 10)  # day 10 of a 31-day month
    july1 = dt.date(2026, 7, 1)

    # No budget -> pacing does not apply (None), never a fabricated read.
    check("pacing_none_without_budget", compute_pacing(_spend_days(july1, 10, 130.0), as_of, None) is None)

    # 10 days x $130 = $1,300 MTD vs $1,000 budget-to-date (3,100 * 10/31) -> pace 1.30 -> ACT.
    over = compute_pacing(_spend_days(july1, 10, 130.0), as_of, 3100.0)
    check("pacing_budget_to_date_exact", abs(over.budget_to_date - 1000.0) < 1e-9, over.budget_to_date)
    check("pacing_pace_exact", abs(over.pace - 1.30) < 1e-9, over.pace)
    check("pacing_act_status", over.status == "act", over.status)
    check("pacing_act_guidance_is_cut_order", over.guidance == CUT_ORDER_GUIDANCE)
    check("pacing_act_coverage_complete", over.coverage_complete)

    # Pace 1.15 -> WARN under the neutral lens, ACT under profit-maintain
    # (its pacing_overrides pull act_above down to 1.15 exclusive... 1.20 > 1.15 -> act).
    warn = compute_pacing(_spend_days(july1, 10, 115.0), as_of, 3100.0)
    check("pacing_warn_status_neutral", warn.status == "warn", warn.status)
    pm_lens = resolve_goal_lens("profit-maintain")
    pm = compute_pacing(_spend_days(july1, 10, 120.0), as_of, 3100.0, lens=pm_lens)
    check("pacing_act_under_profit_maintain", pm.status == "act", (pm.status, pm.pace))
    rl_lens = resolve_goal_lens("rank-launch")
    rl = compute_pacing(_spend_days(july1, 10, 130.0), as_of, 3100.0, lens=rl_lens)
    check("pacing_rank_launch_tolerates_130", rl.status == "warn", (rl.status, rl.pace))

    # Under-pace with full coverage -> underpace + the push-order guidance.
    under = compute_pacing(_spend_days(july1, 10, 50.0), as_of, 3100.0)
    check("pacing_underpace_status", under.status == "underpace", under.status)
    check("pacing_underpace_guidance", under.guidance == UNDERPACE_GUIDANCE)

    # Missing days: pace is understated -> NEVER an under-pace verdict on
    # partial coverage; a note states the gap instead.
    partial = compute_pacing(_spend_days(dt.date(2026, 7, 6), 5, 100.0), as_of, 3100.0)
    check("pacing_partial_coverage_flagged", not partial.coverage_complete, partial.days_with_data)
    check("pacing_partial_no_underpace", partial.status == "on_pace", partial.status)
    check("pacing_partial_has_note", any("understated" in n for n in partial.notes), partial.notes)

    # Flag severities: act -> ALERT, warn -> WARN, on_pace -> no flag.
    check("pacing_flag_act_is_alert", pacing_flag(over).severity == SEVERITY_ALERT)
    check("pacing_flag_warn_is_warn", pacing_flag(warn).severity == SEVERITY_WARN)
    on_pace = compute_pacing(_spend_days(july1, 10, 100.0), as_of, 3100.0)
    check("pacing_flag_none_on_pace", pacing_flag(on_pace) is None, on_pace.status)

    return over


# ---------------------------------------------------------------------------
# recommendations.py rank-radar wiring: GRADUATE proposals for rank 1-3
# stable 2+ weeks, data-backed cut protection for keywords whose organic
# rank is improving, and the no-radar note when Rank entities are present.

def test_rank_radar_graduation_and_protection():
    entities = [dict(_PROFIT_ENTITY), dict(_RANK_ENTITY)]

    radar = [
        # The Rank keyword has DONE ITS JOB: rank 1, four stable weeks ->
        # GRADUATE, and no longer a push candidate.
        {"keyword": _RANK_ENTITY["name"], "rank_now": 1, "rank_prev": 1, "weeks_stable": 4},
        # The Halo target is over the profit-maintain ACOS ceiling BUT its
        # organic rank is improving (15 -> 8): buying position -> protected
        # from the cut, surfaced as a note instead.
        {"keyword": _PROFIT_ENTITY["name"], "rank_now": 8, "rank_prev": 15, "weeks_stable": 0},
        # Rank 2 but only 1 stable week -> NOT graduating yet.
        {"keyword": "almost there keyword", "rank_now": 2, "rank_prev": 4, "weeks_stable": 1},
    ]

    result = build_recommendations(entities, goal="profit-maintain", rank_radar=radar)

    grads = [g.keyword for g in result.graduate]
    check("radar_graduates_stable_top3", _RANK_ENTITY["name"] in grads, grads)
    check("radar_no_premature_graduation", "almost there keyword" not in grads, grads)
    check("radar_graduated_keyword_not_pushed", _RANK_ENTITY["name"] not in _push_names(result), _push_names(result))
    if result.graduate:
        g = result.graduate[0]
        check("radar_graduate_action_steps_down", "2-3 optimizer" in g.action and "cliff-drop" in g.action, g.action)

    check(
        "radar_improving_rank_protected_from_cut",
        _PROFIT_ENTITY["name"] not in _pause_names(result),
        _pause_names(result),
    )
    check(
        "radar_protection_noted_not_silent",
        any(_PROFIT_ENTITY["name"] in n and "rank improving" in n for n in result.notes),
        result.notes,
    )

    # Without radar, the same profit entity IS cut (the baseline rule) and
    # the missing-radar gap is stated in a note, never silent.
    no_radar = build_recommendations(entities, goal="profit-maintain")
    check("radar_baseline_cut_without_radar", _PROFIT_ENTITY["name"] in _pause_names(no_radar), _pause_names(no_radar))
    check("radar_missing_noted", any("No Rank Radar rows supplied" in n for n in no_radar.notes), no_radar.notes)
    check("radar_none_graduate_without_radar", no_radar.graduate == [], no_radar.graduate)

    return result


def test_pacing_and_graduate_rendering(weekly, over_pacing, radar_result):
    meta = {
        "source": "sellerboard",
        "source_label": "Sellerboard 'Dashboard Totals' (PRIMARY, whole-account truth)",
        "preview": False,
        "generated_at": "2026-07-13T00:00:00Z",
        "slack_channel_id": "C000000000",
        "goal_lens": {"label": "Profit / Maintain", "description": "Mature ASIN, defending margin."},
        "pacing": over_pacing,
    }
    md = render_weekly_markdown(weekly, radar_result, meta)
    check("render_md_has_pacing_section", "Run-rate pacing" in md)
    check("render_md_pacing_shows_act", "OVER PACE (act)" in md)
    check("render_md_pacing_cut_order", "Rank LAST" in md or "Waste first" in md)
    check("render_md_has_graduate_section", "GRADUATE -- rank achieved" in md)
    check("render_md_graduate_names_keyword", _RANK_ENTITY["name"] in md)

    slack = render_weekly_slack(weekly, radar_result, meta)
    check("render_slack_pacing_line", "Run-rate:" in slack["text"], slack["text"][:200])
    check(
        "render_slack_graduate_block",
        any("GRADUATE" in (b.get("text", {}).get("text", "")) for b in slack["blocks"] if b.get("type") == "section"),
    )

    # No pacing (no budget on file) and no graduates -> neither section appears.
    meta_no_pacing = dict(meta, pacing=None)
    empty_result = build_recommendations([], goal=None)
    md_plain = render_weekly_markdown(weekly, empty_result, meta_no_pacing)
    check("render_md_no_pacing_when_absent", "Run-rate pacing" not in md_plain)
    check("render_md_no_graduate_when_empty", "GRADUATE" not in md_plain)


def main() -> int:
    account_rows, campaign_rows = build_fixture()
    analysis = analyze_account("test-acct", REPORT_DATE, account_rows, campaign_rows)

    test_trend_classification()
    test_deltas_exact_arithmetic(analysis)
    active, suppressed = test_flags_fixture(analysis)
    test_report_rendering(analysis, active, suppressed)
    test_mock_datasource_scenarios()
    test_cli_end_to_end_mock()
    test_sellerboard_semicolon_delimiter_autodetect()
    test_real_sellerboard_sample()
    test_crosscheck_verdicts()
    test_goal_lens_severity_differences(analysis)

    weekly = test_aggregate_week_math()
    test_build_recommendations_goal_differentiated()
    empty_tests_result, signal_driven_result = test_select_tests_empty_and_signal_driven()
    test_weekly_report_rendering(weekly, active, suppressed, empty_tests_result, signal_driven_result)
    over_pacing = test_pacing_math()
    radar_result = test_rank_radar_graduation_and_protection()
    test_pacing_and_graduate_rendering(weekly, over_pacing, radar_result)
    test_cli_end_to_end_weekly()
    test_cli_end_to_end_weekly_csv_only()

    print(f"\n{len(PASSES)} passed, {len(FAILURES)} failed")
    if FAILURES:
        print("\nFAILURES:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("selftest: all green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

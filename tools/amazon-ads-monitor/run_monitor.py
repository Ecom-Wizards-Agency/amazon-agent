#!/usr/bin/env python3
"""run_monitor.py -- CLI for the amazon-ads-monitor toolkit.

Read-only. Never touches campaigns. Produces a markdown report per
account under `output/{account}/ads-monitor/{date}_daily.md` and,
optionally, a Slack payload (mrkdwn + Block Kit JSON) written to a file
or printed to stdout for the runtime/skill layer to post via the Slack
MCP connector (this CLI never posts to Slack itself).

Examples
--------
Mock mode, no credentials needed, all sample accounts, yesterday's date:

    python3 tools/amazon-ads-monitor/run_monitor.py --source mock

Sellerboard CSV (PRIMARY real source, as of 2026-07-14) -- one brand at a
time, a delivered or firecrawl-fetched Dashboard Totals CSV (see
_local/ads-monitor/SELLERBOARD-FORMAT.md and the amazon-ads-monitor skill
for the file-first/firecrawl-fallback flow):

    python3 tools/amazon-ads-monitor/run_monitor.py --source sellerboard \\
        --csv _local/ads-monitor/inbox/sondur/dashboardtotals_7d.csv \\
        --accounts sondur --goal rank-launch --date 2026-07-13

Pass a same-day AdLabs figure file (fetched via the AdLabs MCP at the
skill layer -- this CLI makes no MCP/network calls itself) to also run
the Sellerboard-vs-AdLabs cross-check:

    python3 tools/amazon-ads-monitor/run_monitor.py --source sellerboard \\
        --csv <path> --accounts sondur --adlabs-json <path to {"ad_spend":..,"ad_sales":..,"total_sales":..}>

Real Amazon Ads API (secondary source, once _local/ads-monitor/config.json
has credentials):

    python3 tools/amazon-ads-monitor/run_monitor.py --source spads \\
        --config _local/ads-monitor/config.json --date 2026-07-12
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from analyze import analyze_account
from datasource import DATASOURCES, SPAdsApiConfigError, SELLERBOARD_METRICS
from flags import evaluate, resolve_goal_lens, GOAL_LENSES
from report import render_markdown, render_slack, SELLERBOARD_HEADLINE_METRICS, SELLERBOARD_SLACK_HEADLINE_METRICS, SELLERBOARD_METRIC_LABEL_OVERRIDES
from crosscheck import cross_check

DEFAULT_SLACK_CHANNEL_ID = "C0BGWLFMW3V"  # #amazon-daily-report


def _yesterday() -> dt.date:
    return dt.date.today() - dt.timedelta(days=1)


def _parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="amazon-ads-monitor: daily previous-day Amazon Ads report")
    p.add_argument("--date", type=str, default=None, help="Report date YYYY-MM-DD (default: yesterday)")
    p.add_argument("--source", choices=sorted(DATASOURCES), default="mock", help="Data source adapter (default: mock)")
    p.add_argument("--accounts", type=str, default=None, help="Comma-separated account list (default: all accounts the source knows about; for --source sellerboard with --csv, names the single account the CSV belongs to -- inferred from the filename if omitted)")
    p.add_argument("--config", type=str, default="_local/ads-monitor/config.json", help="Config path (used by --source spads; ignored by mock/sellerboard)")
    p.add_argument(
        "--csv", type=str, default=None,
        help="Comma-separated Sellerboard 'Dashboard Totals' CSV file path(s) for --source sellerboard "
             "(pass both the ~7d and ~30d feed for one brand if you have them; the shorter/fresher one "
             "should come first -- it wins on any overlapping date). See _local/ads-monitor/SELLERBOARD-FORMAT.md.",
    )
    p.add_argument(
        "--goal", type=str, default=None,
        help=f"Brand goal/stage lens from its Notion 'Amazon Agent Ops Profiles' row, one of: {', '.join(sorted(GOAL_LENSES))}. "
             "Adjusts flag thresholds/severity/wording (see flags.py GOAL_LENSES). Unknown/omitted -> neutral lens (unchanged behavior).",
    )
    p.add_argument(
        "--adlabs-json", type=str, default=None,
        help="Path to a JSON file with same-report-day AdLabs figures {\"ad_spend\":.., \"ad_sales\":.., "
             "\"total_sales\":..} (fetched via the AdLabs MCP at the skill layer -- this CLI makes no "
             "MCP/network calls itself). When given, runs the Sellerboard-vs-AdLabs cross-check "
             "(crosscheck.py) and includes the verdict in the report.",
    )
    p.add_argument("--tolerance", type=float, default=None, help="Cross-check tolerance as a fraction (default: crosscheck.DEFAULT_TOLERANCE, +/-7%%)")
    p.add_argument("--out", type=str, default="output", help="Base output directory (default: output)")
    p.add_argument("--window-days", type=int, default=14, help="Days of history to fetch before the report date for trailing calcs (default: 14)")
    p.add_argument("--slack-json", type=str, default=None, help="Write the Slack payload here ('-' for stdout); one payload per account")
    p.add_argument("--quiet", action="store_true", help="Suppress the per-account console summary")
    return p.parse_args(argv)


def _load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def _infer_account_from_csv_path(path: str) -> str:
    """Best-effort account slug from a Sellerboard export filename, e.g.
    'sondur_dashboardtotals_7d.csv' -> 'sondur'. Falls back to the whole
    stem if no recognized marker is found."""
    stem = Path(path).stem
    lower = stem.lower()
    for marker in ("_dashboardtotals", "-dashboardtotals", "_dashboard_totals", "-dashboard_totals"):
        idx = lower.find(marker)
        if idx != -1:
            return stem[:idx]
    return stem


def _build_datasource(source: str, config: dict, csv_paths: list = None, account_hint: str = None):
    cls = DATASOURCES[source]
    if source == "mock":
        return cls()
    if source == "spads":
        if not config or "lwa" not in config or "accounts" not in config:
            raise SPAdsApiConfigError(
                "SP Ads API config is missing/incomplete. Copy "
                "_local/ads-monitor/config.TEMPLATE.json to config.json, fill in LWA "
                "credentials + accounts[], or run with --source mock instead."
            )
        return cls(config)
    if source == "sellerboard":
        if not csv_paths:
            raise SPAdsApiConfigError(
                "--source sellerboard requires --csv <path[,path...]> pointing at the delivered "
                "Sellerboard 'Dashboard Totals' CSV (file-first) or the firecrawl-fetched copy saved "
                "to _local/ads-monitor/inbox/<brand>/ (fallback) -- see the amazon-ads-monitor skill "
                "and _local/ads-monitor/SELLERBOARD-FORMAT.md."
            )
        account = account_hint or _infer_account_from_csv_path(csv_paths[0])
        return cls.from_paths({account: csv_paths})
    # adlabs / marketplaceadpros: documented stubs, instantiate to surface
    # the clear NotImplementedError from their constructors/methods.
    return cls()


def run_account(
    ds, account: str, report_date: dt.date, window_days: int, config: dict, source: str,
    goal: str = None, adlabs_figures: dict = None, tolerance: float = None,
):
    start = report_date - dt.timedelta(days=window_days)
    account_rows = ds.get_account_daily(account, start, report_date)
    campaign_rows = ds.get_campaign_daily(account, start, report_date)

    metrics = SELLERBOARD_METRICS if source == "sellerboard" else None
    analysis = analyze_account(account, report_date, account_rows, campaign_rows, metrics=metrics)
    active_flags, suppressed_flags = evaluate(analysis, config, goal=goal)

    thresholds_note = None
    if config and config.get("thresholds"):
        thresholds_note = "Using config-overridden thresholds (see _local/ads-monitor/config.json)."

    notes = [n for n in [thresholds_note] if n]
    if source == "sellerboard" and not account_rows:
        notes.append(
            "Sellerboard feed returned no rows for this window (blank/just-requested report or no "
            "delivered file yet) -- per SELLERBOARD-FORMAT.md, fall back to AdLabs for this brand/day "
            "at the skill layer; this CLI run has no account-level figures to report."
        )

    crosscheck_result = None
    if adlabs_figures is not None:
        report_row = analysis.account_series.report_row
        sb_figures = {
            "ad_spend": report_row.spend if report_row else None,
            "ad_sales": report_row.sales if report_row else None,
            "total_sales": report_row.total_sales if report_row else None,
        }
        kwargs = {} if tolerance is None else {"tolerance": tolerance}
        crosscheck_result = cross_check(sb_figures, adlabs_figures, **kwargs)

    lens = resolve_goal_lens(goal)

    meta = {
        "source": source,
        "source_label": {
            "mock": "MOCK (synthetic data, no live credentials)",
            "sellerboard": "Sellerboard 'Dashboard Totals' (PRIMARY, whole-account truth)",
            "spads": "Amazon Ads API v3 (SP, secondary)",
            "adlabs": "AdLabs (ad-granular cross-check, same-day figure corrects tomorrow)",
            "marketplaceadpros": "MarketplaceAdPros (secondary/cross-check)",
        }.get(source, source),
        "preview": source == "mock",
        "attribution_window": config.get("attribution_window", "7d") if source == "spads" else "7d",
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "slack_channel_id": config.get("slack_channel_id", DEFAULT_SLACK_CHANNEL_ID),
        "notes": notes,
        "goal_lens": {"label": lens["label"], "description": lens["description"]},
        "crosscheck": crosscheck_result,
    }
    if source == "sellerboard":
        meta["headline_metrics"] = SELLERBOARD_HEADLINE_METRICS
        meta["slack_headline_metrics"] = SELLERBOARD_SLACK_HEADLINE_METRICS
        meta["headline_labels"] = SELLERBOARD_METRIC_LABEL_OVERRIDES

    markdown = render_markdown(analysis, active_flags, suppressed_flags, meta)
    slack_payload = render_slack(analysis, active_flags, suppressed_flags, meta)
    return analysis, active_flags, suppressed_flags, markdown, slack_payload


def main(argv=None) -> int:
    args = _parse_args(argv)
    report_date = dt.date.fromisoformat(args.date) if args.date else _yesterday()
    config = _load_config(args.config)

    csv_paths = [p.strip() for p in args.csv.split(",") if p.strip()] if args.csv else None
    account_hint = args.accounts.split(",")[0].strip() if args.accounts else None

    try:
        ds = _build_datasource(args.source, config, csv_paths=csv_paths, account_hint=account_hint)
    except SPAdsApiConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    adlabs_figures = None
    if args.adlabs_json:
        adlabs_figures = json.loads(Path(args.adlabs_json).read_text(encoding="utf-8"))

    accounts = args.accounts.split(",") if args.accounts else ds.list_accounts()
    out_base = Path(args.out)
    exit_code = 0
    slack_payloads = []

    for account in accounts:
        account = account.strip()
        try:
            analysis, active_flags, suppressed_flags, markdown, slack_payload = run_account(
                ds, account, report_date, args.window_days, config, args.source,
                goal=args.goal, adlabs_figures=adlabs_figures, tolerance=args.tolerance,
            )
        except Exception as exc:  # noqa: BLE001 -- surface per-account errors, keep going
            print(f"ERROR [{account}]: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        out_dir = out_base / account / "ads-monitor"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{report_date.isoformat()}_daily.md"
        out_path.write_text(markdown, encoding="utf-8")

        slack_payloads.append((account, slack_payload))

        if not args.quiet:
            n_critical = sum(1 for f in active_flags if f.severity == "critical")
            n_alert = sum(1 for f in active_flags if f.severity == "alert")
            n_warn = sum(1 for f in active_flags if f.severity == "warn")
            n_info = sum(1 for f in active_flags if f.severity == "info")
            print(
                f"[{account}] {report_date.isoformat()} -> {out_path} "
                f"(critical={n_critical} alert={n_alert} warn={n_warn} info={n_info} suppressed={len(suppressed_flags)})"
            )

    if args.slack_json:
        payload_out = slack_payloads[0][1] if len(slack_payloads) == 1 else {
            account: payload for account, payload in slack_payloads
        }
        rendered = json.dumps(payload_out, indent=2)
        if args.slack_json == "-":
            print(rendered)
        else:
            Path(args.slack_json).write_text(rendered, encoding="utf-8")
            if not args.quiet:
                print(f"Slack payload written to {args.slack_json}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

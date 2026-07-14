#!/usr/bin/env python3
"""run_weekly.py -- CLI for the amazon-ads-monitor toolkit's WEEKLY brief.

Read-only. Never touches campaigns. Produces a markdown weekly brief per
account under `output/{account}/ads-monitor/{week_end}_weekly.md` and,
optionally, a Slack payload (mrkdwn + Block Kit JSON) written to a file or
printed to stdout for the runtime/skill layer to post via the Slack MCP
connector (this CLI never posts to Slack itself).

Flow
----
1. Parse the brand's Sellerboard "Dashboard Totals" CSV(s) via
   `SellerboardDataSource` (same file-first/firecrawl-fallback convention
   as the daily CLI -- see run_monitor.py and
   _local/ads-monitor/SELLERBOARD-FORMAT.md).
2. `analyze.aggregate_week(account_rows, week_end)` -- this-week vs
   last-week (7-day) totals and WoW deltas. `week_end` defaults to
   yesterday (the same "latest complete day" convention as the daily
   brief); Sellerboard's total_* columns can read 0 for the still-in-
   progress current day, so never anchor the week on today -- pass an
   earlier `--date` if yesterday itself isn't a fully-completed day yet.
3. Load the week's normalized AdLabs campaign/target-level rows (already
   filtered/shaped by the skill layer -- see
   `recommendations.normalize_entities` and the two AdLabs quirks
   documented in the amazon-ads-monitor SKILL.md) from `--adlabs-json`;
   omitted/empty is fine -- Push/Pause-Optimize come back empty with a
   note, not an error.
4. Parse the week's external-signal digest (`--signal-digest`, see
   `_local/ads-signals/<ISO-year>-W<week>/digest.md` and
   `recommendations.parse_signal_digest_markdown`) if given.
5. `recommendations.build_recommendations(...)` -- the three PROPOSAL
   lists (Push / Pause-Optimize / Test), goal-and-situation-aware.
6. Also runs the same day-level goal-aware flags as the daily brief
   (`analyze.analyze_account` + `flags.evaluate`, anchored on `week_end`)
   so the weekly artifact can optionally carry "today's" flags alongside
   the WoW headline -- additive, not a replacement for the daily brief
   (skip with `--no-daily-flags`).
7. Render the weekly markdown + Slack payload (`report.render_weekly_markdown`
   / `report.render_weekly_slack`) and write them out.

Examples
--------
Sellerboard CSV alone (no AdLabs yet -- Push/Pause-Optimize come back
empty with a note; that's a valid, complete weekly run):

    python3 tools/amazon-ads-monitor/run_weekly.py \\
        --csv _local/ads-monitor/inbox/sondur/dashboardtotals_30d.csv \\
        --account sondur --goal rank-launch --date 2026-07-13

Full weekly run with AdLabs weekly entities + a signal digest:

    python3 tools/amazon-ads-monitor/run_weekly.py \\
        --csv <7d path>,<30d path> --account sondur --goal rank-launch \\
        --situation "recurring ACOS spikes on broad match" \\
        --adlabs-json _local/ads-monitor/inbox/sondur/adlabs_weekly.json \\
        --signal-digest _local/ads-signals/2026-W28/digest.md \\
        --out output --slack-json -
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from analyze import aggregate_week, analyze_account
from datasource import SellerboardDataSource, SELLERBOARD_METRICS
from flags import evaluate, resolve_goal_lens, GOAL_LENSES
from recommendations import build_recommendations, parse_signal_digest_markdown
from report import (
    render_weekly_markdown, render_weekly_slack,
    WEEKLY_HEADLINE_METRICS, WEEKLY_SLACK_HEADLINE_METRICS,
    SELLERBOARD_METRIC_LABEL_OVERRIDES,
)

DEFAULT_SLACK_CHANNEL_ID = "C0BGWLFMW3V"  # #amazon-daily-report


def _yesterday() -> dt.date:
    return dt.date.today() - dt.timedelta(days=1)


def _parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="amazon-ads-monitor: weekly WoW Amazon Ads brief (Push/Pause-Optimize/Test proposals). Read-only."
    )
    p.add_argument("--date", type=str, default=None, help="Week-end report date YYYY-MM-DD; must be a fully-completed day (default: yesterday)")
    p.add_argument(
        "--csv", type=str, required=True,
        help="Comma-separated Sellerboard 'Dashboard Totals' CSV file path(s) covering >=14 days "
             "(this week + prior week) for the account. See _local/ads-monitor/SELLERBOARD-FORMAT.md.",
    )
    p.add_argument("--account", type=str, default=None, help="Account slug (default: inferred from the first --csv filename)")
    p.add_argument(
        "--adlabs-json", type=str, default=None,
        help="Path to a JSON file: a list of normalized AdLabs weekly campaign/target rows "
             "(see recommendations.normalize_entities for the expected shape). Omit for an "
             "AdLabs-free run -- Push/Pause-Optimize come back empty with a note, not an error.",
    )
    p.add_argument(
        "--goal", type=str, default=None,
        help=f"Brand goal/stage lens from its Notion 'Amazon Agent Ops Profiles' row, one of: {', '.join(sorted(GOAL_LENSES))}.",
    )
    p.add_argument("--situation", type=str, default=None, help="Free-text brand situation this week (feeds TEST selection's light keyword tagging, e.g. mentions of a hijacker or a recurring ACOS spike)")
    p.add_argument(
        "--signal-digest", type=str, default=None,
        help="Path to this week's _local/ads-signals/<ISO-year>-W<week>/digest.md; parsed via "
             "recommendations.parse_signal_digest_markdown and folded into TEST selection.",
    )
    p.add_argument("--out", type=str, default="output", help="Base output directory (default: output)")
    p.add_argument("--window-days", type=int, default=21, help="Days of Sellerboard history to fetch before week_end (default: 21 -- covers this+last week plus a daily-flag trailing-7 average)")
    p.add_argument("--slack-json", type=str, default=None, help="Write the Slack payload here ('-' for stdout)")
    p.add_argument("--no-daily-flags", action="store_true", help="Skip the optional day-level goal-aware flags section (included by default)")
    p.add_argument("--quiet", action="store_true", help="Suppress the console summary")
    return p.parse_args(argv)


def _infer_account_from_csv_path(path: str) -> str:
    """Same convention as run_monitor.py's helper: best-effort account
    slug from a Sellerboard export filename."""
    stem = Path(path).stem
    lower = stem.lower()
    for marker in ("_dashboardtotals", "-dashboardtotals", "_dashboard_totals", "-dashboard_totals"):
        idx = lower.find(marker)
        if idx != -1:
            return stem[:idx]
    return stem


def run_account(
    account: str,
    csv_paths: list,
    week_end: dt.date,
    window_days: int,
    goal: str = None,
    raw_entities: list = None,
    signal_items: list = None,
    situation: str = None,
    include_daily_flags: bool = True,
):
    ds = SellerboardDataSource.from_paths({account: csv_paths})
    start = week_end - dt.timedelta(days=window_days)
    account_rows = ds.get_account_daily(account, start, week_end)

    notes = []
    if not account_rows:
        notes.append(
            "Sellerboard feed returned no rows for this window -- per SELLERBOARD-FORMAT.md, fall back to "
            "AdLabs for this brand/week at the skill layer; this CLI run has no account-level figures to report."
        )

    weekly_analysis = aggregate_week(account_rows, week_end)
    recommendations = build_recommendations(
        raw_entities or [], goal=goal, situation=situation, signal_items=signal_items,
    )

    flags_tuple = None
    if include_daily_flags and account_rows:
        daily_analysis = analyze_account(account, week_end, account_rows, [], metrics=SELLERBOARD_METRICS)
        active_flags, suppressed_flags = evaluate(daily_analysis, goal=goal)
        flags_tuple = (active_flags, suppressed_flags)

    lens = resolve_goal_lens(goal)
    meta = {
        "source": "sellerboard",
        "source_label": "Sellerboard 'Dashboard Totals' (PRIMARY, whole-account truth)",
        "preview": False,
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "slack_channel_id": DEFAULT_SLACK_CHANNEL_ID,
        "goal_lens": {"label": lens["label"], "description": lens["description"]},
        "weekly_headline_metrics": WEEKLY_HEADLINE_METRICS,
        "weekly_slack_headline_metrics": WEEKLY_SLACK_HEADLINE_METRICS,
        "headline_labels": SELLERBOARD_METRIC_LABEL_OVERRIDES,
    }
    if notes:
        meta["notes"] = notes

    markdown = render_weekly_markdown(weekly_analysis, recommendations, meta, flags=flags_tuple)
    slack_payload = render_weekly_slack(weekly_analysis, recommendations, meta, flags=flags_tuple)
    return weekly_analysis, recommendations, markdown, slack_payload


def main(argv=None) -> int:
    args = _parse_args(argv)
    week_end = dt.date.fromisoformat(args.date) if args.date else _yesterday()
    csv_paths = [p.strip() for p in args.csv.split(",") if p.strip()]
    if not csv_paths:
        print("ERROR: --csv must name at least one Sellerboard CSV path", file=sys.stderr)
        return 2
    account = args.account or _infer_account_from_csv_path(csv_paths[0])

    raw_entities = []
    if args.adlabs_json:
        raw_entities = json.loads(Path(args.adlabs_json).read_text(encoding="utf-8"))

    signal_items = []
    if args.signal_digest:
        digest_path = Path(args.signal_digest)
        if digest_path.exists():
            signal_items = parse_signal_digest_markdown(digest_path.read_text(encoding="utf-8"))

    try:
        weekly_analysis, recommendations, markdown, slack_payload = run_account(
            account, csv_paths, week_end, args.window_days,
            goal=args.goal, raw_entities=raw_entities, signal_items=signal_items,
            situation=args.situation, include_daily_flags=not args.no_daily_flags,
        )
    except Exception as exc:  # noqa: BLE001 -- surface the error, exit non-zero
        print(f"ERROR [{account}]: {exc}", file=sys.stderr)
        return 2

    out_dir = Path(args.out) / account / "ads-monitor"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{week_end.isoformat()}_weekly.md"
    out_path.write_text(markdown, encoding="utf-8")

    if not args.quiet:
        print(
            f"[{account}] week ending {week_end.isoformat()} -> {out_path} "
            f"(push={len(recommendations.push)} pause_optimize={len(recommendations.pause_optimize)} tests={len(recommendations.tests)})"
        )

    if args.slack_json:
        rendered = json.dumps(slack_payload, indent=2)
        if args.slack_json == "-":
            print(rendered)
        else:
            Path(args.slack_json).write_text(rendered, encoding="utf-8")
            if not args.quiet:
                print(f"Slack payload written to {args.slack_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

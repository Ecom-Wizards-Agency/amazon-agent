---
name: amazon-dayparting
description: "Analyze Sponsored Products hourly campaign reports and prepare confidence-gated 7 by 24 bid schedules for Amazon-native rules or AdLabs dayparting."
---

# Amazon Dayparting

Browser: Mixed (local analysis; AdLabs MCP for schedule reads and operator-approved writes; CDP only when an hourly Amazon Ads report must be downloaded).

Use this skill when the operator asks for hourly performance analysis, dayparting, schedule bid rules, or an AdLabs hourly bid grid.

## Choose The Surface

- **Analysis only:** build a read-only hourly report and proposed grid locally.
- **Amazon-native schedule rule:** Amazon's native rule increases bids during selected times. Do not translate a negative recommendation into a native bid decrease.
- **AdLabs schedule:** AdLabs accepts a complete 7 by 24 grid with whole percentages from -99 to 300 and can boost or throttle. It reasserts the stored base bid on its hourly run.

Never blur these surfaces in the operator note.

## Analyze

1. Verify the advertiser, marketplace, report date range, and account timezone. Amazon's hourly report uses the advertising account timezone.
2. Use at least two fully settled weeks, preferably four. The local analyzer excludes the newest two report days by default because sales attribution is still filling in.
3. Run:

   ```bash
   python3 tools/amazon-dayparting/analyze_dayparting.py \
     --input <hourly-campaign-report.csv-or-xlsx> \
     --timezone <account-timezone> \
     --out-dir output/<client>/ads/dayparting
   ```

4. Read [references/analysis-method.md](references/analysis-method.md) before interpreting the output. Do not average rate columns from the source report.
5. Review `summary.json`, `by_day.csv`, `by_hour.csv`, `by_4hour.csv`, `grid.csv`, and `adlabs_grid.tsv`. The proposed grid uses `0` for missing or low-confidence cells, meaning the base bid.

## Operate An AdLabs Schedule

Read [references/adlabs-execution.md](references/adlabs-execution.md) before creating, editing, cloning, assigning, pausing, or deleting a schedule.

Schedule creation, editing, assignment, pausing, and deletion are live advertising writes. Render a dry run first, summarize the affected schedule, campaigns, timezone, and changed cells, then obtain explicit operator approval for the exact write. A request to analyze hourly data does not authorize schedule creation.

## Output

State the source rows, settled date coverage, timezone, currency, campaigns, confidence threshold, trusted-cell count, strongest and weakest trusted windows, and any thin-data or attribution caveat. Recommendations are starting points for review, not guaranteed performance improvements.

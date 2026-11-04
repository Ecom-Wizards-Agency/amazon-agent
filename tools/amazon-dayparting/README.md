# Amazon dayparting analyzer

**Retired 03.11.2026.** The `amazon-dayparting` skill was deleted when ads data and PPC execution moved to SYNQ. The AdLabs carve-out account (US and CA) keeps their live AdLabs dayparting schedules, operated from the AdLabs carve-out section of the PPC skill: `skills/amazon-ppc-weekly-management/references/adlabs-carve-out.md`. This analyzer and its selftest stay so an AdLabs carve-out schedule proposal can still be computed. Do not start dayparting for any other client.

## Run

```bash
python3 tools/amazon-dayparting/analyze_dayparting.py \
  --input <hourly-campaign-report.csv-or-xlsx> \
  --timezone <account-timezone> \
  --out-dir output/<client>/ads/dayparting
python3 tools/amazon-dayparting/selftest.py
```

The input is an Amazon Sponsored Products Campaign report at hourly time unit, in the advertising account timezone. Use at least two fully settled weeks, preferably four. The analyzer excludes the newest two report days by default because attribution is still filling in, and disables recommendations below fourteen settled dates unless `--allow-thin-data` is passed.

It writes `summary.json`, `by_day.csv`, `by_hour.csv`, `by_4hour.csv`, `grid.csv` and `adlabs_grid.tsv`. The grid uses `0` (base bid) for missing or low-confidence cells. Output is a proposed grid only; it writes nothing to any ads account.

## Method

- Aggregate impressions, clicks, orders, spend and attributed sales from raw rows, then recompute CTR, CVR, CPC, ACOS, ROAS, RPC and aCTC. Never average the report's rate cells.
- One currency per run (`--currency` when the source has more than one).
- Confidence gate: minimum clicks per cell is `ceiling(account aCTC x 5)` (multiplier configurable, `--min-clicks` overrides).
- Starting point for a trusted cell: `round((cell RPC / account RPC - 1) x 100)`, clamped only to AdLabs' accepted -99 to 300.
- Day, hour and 168-cell grid tables reconcile back to the same totals. A strong hourly pattern does not prove causality: promotions, budget exhaustion, campaign mix and stock can create the same shape.

# Dayparting Analysis Method

## Required Source

Use an Amazon Sponsored Products Campaign report at hourly time unit. The parser requires date, start time, campaign, currency, impressions, clicks, spend, orders, and attributed sales. It accepts common Amazon header variants but fails when the required fingerprint is missing.

Do not combine currencies. Filter to one currency before calculating revenue per click or bid changes.

## Additive Measures First

Aggregate these fields from raw rows:

- impressions;
- clicks;
- orders;
- spend;
- attributed sales.

Then recompute every rate:

```text
CTR  = clicks / impressions
CVR  = orders / clicks
CPC  = spend / clicks
ACOS = spend / sales
ROAS = sales / spend
RPC  = sales / clicks
aCTC = clicks / orders
```

Never average the source report's CTR, CPC, CVR, ACOS, or ROAS cells.

## Confidence Gate

The default minimum clicks for a segment is:

```text
minimum clicks = ceiling(account aCTC × 5)
```

The multiplier is configurable. A cell below the threshold receives no recommendation and is written as `0` in the complete AdLabs grid, which means base bid. If the account has no orders, aCTC cannot be estimated and recommendations remain unavailable unless the operator supplies a deliberate minimum-click threshold.

## Bid Starting Point

For a trusted segment:

```text
change percent = round((segment RPC / account RPC - 1) × 100)
```

The local analyzer clamps the value only to AdLabs' accepted bounds, -99 to 300. It does not apply the grid. Review practical bid ceilings, campaign purpose, stock, profitability, and placement strategy before any write.

RPC is the default because it compares revenue produced by a click with the cost of buying that click. ACOS can look favorable merely because CPC changed, so read CPC beside RPC.

## Coverage And Reconciliation

- Use the account timezone, not the operator's timezone or UTC.
- Exclude unsettled recent days before recommendations.
- Prefer four weeks. Fewer than fourteen distinct settled dates is thin data and disables recommendations by default.
- Compare distinct dates represented by weekday. Partial weeks can overweight a weekday.
- Sum the day table, hour table, and 168-cell grid back to the same scope totals.
- Missing hours are explicit zero-data cells, never silently dropped.
- A strong hourly pattern does not prove causality. Promotions, budget exhaustion, campaign mix, and stock can create the same shape.

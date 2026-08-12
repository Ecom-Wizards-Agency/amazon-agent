# Input Contract

Use schema version `amazon-launch-strategy.v1` from `tools/amazon-launch-strategy/config.schema.v1.json`.

## Required groups

- `client`: client, brand, account, marketplace, currency, timing label, output directory.
- `products`: launch and later-phase offers, pricing, unit economics, stock, inbound, Vine units, MOQ, and lead times.
- `ppc.phases`: week ranges and optional budget caps.
- `scenarios`: low, base, and high product-level CPC, CVR, paid clicks, organic units, and explicit halo units by phase.
- `reviews`: Request a Review, Vine, Helium 10 Follow-Up, and prohibited-method validation fields.
- `sources`: source locator, status, freshness, and notes.
- `owners`: accountable owner and next confirmation for each launch decision.

## Commercial target layer

Use optional `commercial_targets` when the client has approved operating milestones that should drive the executive plan. It contains:

- `daily_revenue_milestones`: Month 1 exit, Month 2 exit, Month 3 committed, and Month 3 stretch Amazon sales revenue per day.
- `product_mix_by_month`: launch-product unit mix for Months 1-3. Each month must total 100%.
- `stock_safety_buffer_pct` and `stock_rounding_increment`.
- `ppc_plan`: planned spend, available ceiling, optional planning CPC/CVR, and campaign-purpose allocation for Month 1, Month 2, Month 3 committed, and Month 3 stretch.
- `keywords`: approved core, discovery, competitor, and controlled-test targeting direction.

Planned PPC may not exceed its ceiling. Each campaign allocation must total 100%, and branded defense remains 5%. Ceilings are available funding, not forced spend.

The commercial layer produces committed, stretch, and capacity paths. The original low/base/high click, CPC, CVR, organic, and halo scenarios remain supporting sensitivities. They do not overwrite an approved commercial target.

## Missing-input behavior

Leave unavailable values as `null`. Do not use zero for an unknown value. Preflight reports missing high-value inputs and marks the build `DIRECTIONAL`. A directional build remains valid when it includes editable low, base, and high sensitivities and does not present assumptions as confirmed facts.

The following are high-value confirmations:

- Current marketplace revenue and orders by product.
- External-channel spend, branded-search contribution, and planned launch support.
- Landed COGS, Amazon fees, other variable costs, and discount floor.
- Available and inbound stock by configuration.
- MOQ, production time, freight time, and FBA receiving buffer.
- Confirmed launch date and Vine eligibility.

## Scenario inputs

For each launch product and campaign phase provide:

- `cpc`
- `cvr`
- `paid_clicks_per_week`
- `organic_units_per_week`
- `external_halo_units_per_week`
- `halo_basis`

Halo units must be zero when no explicit basis exists. Observed external-channel evidence can be recorded as a source, but causal attribution must remain qualified unless measured.

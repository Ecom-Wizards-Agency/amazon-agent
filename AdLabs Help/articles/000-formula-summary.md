# AdLabs optimizer formulas: operator summary

Captured: 2026-07-26. Distilled from the public AdLabs articles in this library. Rule this exists for: **max-change settings are guardrail ceilings that clamp these formulas; the formula output is the step, never the cap.**

## Bids (weekly, the 4 categories)

Core: **Keyword Bid = Revenue Per Click (RPC) x Target ACOS**, where RPC = Sales / Clicks over the window.

1. **High ACOS**: new bid = RPC x Target ACOS. Almost always a decrease; always below the keyword's current CPC.
2. **High Spend, no sales**: threshold Target CPA = Target ACOS x AOV. Over threshold with zero sales: bid = Anticipated RPC x Target ACOS, where Anticipated RPC = AOV / current clicks. Example: $20 AOV / 10 clicks = $2 anticipated RPC, x 0.30 = $0.60 bid.
3. **Low ACOS** (roughly 20% under target): test a bid increase, 5-25% per iteration, never past the max affordable CPC (RPC x Target ACOS ceiling).
4. **Low Visibility** (clicks below the clicks-to-conversion norm): raise bid to buy data, same ceiling.

## Placements

**Placement Adjustment = (Target ACOS / Current ACOS) - 1**, per placement (ToS, Product Pages, Rest of Search), applied as a relative change to the current modifier.

Example: target 30%, ToS ACOS 45% -> 0.30/0.45 - 1 = -33%: LOWER ToS by 33%. Data window: at least 30 days, ideally 60. A placement raise must be earned by that placement's own ACOS/CVR, never copied from a cap value.

## What this means for /ppc-manage

- The opt-group settings (`bid_max_increase` 25%, `placement_max_increase` 40%, etc.) are clamps. The optimizer proposes formula values anywhere from 1% up to the cap; a written change exactly at the cap means the formula wanted more and got clamped, and must come from a preview, never be authored.
- Validate every batch: `tools/amazon-ppc-management/batches.py validate --rows <rows.json> --max-increase <f> --max-decrease <f> [--tacos <f>]`.
- The in-app optimizer adds weighting on top of these public formulas (outputs "may differ slightly"; placement-modifier weighting is a trade secret), so the preview/UI download stays the source of truth for exact numbers.

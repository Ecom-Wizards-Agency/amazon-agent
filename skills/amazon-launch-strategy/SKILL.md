---
name: amazon-launch-strategy
description: Use for forward-looking Amazon launch plans and launch-readiness decisions covering 13-week sales scenarios, bottom-up PPC budgets, product pricing and discounts, contribution-margin constraints, stock and reorder timing, Vine and review-request policy, and explicit external-channel halo assumptions. Trigger on requests for an Amazon launch plan, 90-day launch strategy, PPC launch budget, launch pricing, launch stock forecast, or review strategy. Read-only planning only; historical performance audits belong to amazon-audit and live execution belongs to the relevant operating skill.
---

# Amazon Launch Strategy

Browser: Mixed (local deterministic build plus narrow connected-source reads when fresh launch inputs are required).

Build a clear Day 0 and Weeks 1-13 launch plan. Keep confirmed facts, editable assumptions, and missing confirmations visibly separate.

## Workflow

1. Confirm the account, marketplace, initial offers, later-phase offers, and launch timing. Use Day 0 when the calendar date is not confirmed.
2. Gather only the sources needed for pricing, demand, margin, inventory, reviews, PPC, and external-channel support. Use current live context when timing or eligibility matters.
3. Copy `tools/amazon-launch-strategy/config.TEMPLATE.json` to a client config. Read `references/input-contract.md` before filling it.
4. Run `build_launch_strategy.py --config <config> --preflight`. Resolve fatal errors. Leave unavailable facts empty and label the result directional.
5. Run `--preview`. When approved commercial targets exist, review committed, stretch, and capacity revenue, units, stock, planned PPC, available ceilings, and campaign allocation first. Keep low, base, and high click/CPC/CVR sensitivities as supporting diagnostics.
6. Run `--build` to create the branded client plan and linked workbook. Inspect every document page and populated workbook tab before delivery.
7. Convert reviewed files to native Google Doc and Google Sheet only when delivery is requested. Never post the plan to Slack without a separate explicit instruction.

## Model Rules

- Model 13 weeks and summarize Weeks 1-4, 5-8, and 9-13 as Months 1-3.
- When a commercial target layer exists, use its revenue ramps as the executive operating objective. Do not replace it with the supporting click/CPC/CVR sensitivity model.
- Treat PPC ceilings as available funding, not forced spend. Planned spend may never exceed its ceiling, campaign-purpose allocation must total 100%, and branded defense remains 5% unless the approved contract is intentionally revised.
- Convert target revenue to required units using the phased product mix and blended effective price. Add the configured stock safety buffer, round stock to the configured increment, and add confirmed Vine units above customer-sale inventory.
- Calculate PPC from paid clicks, CPC, CVR, effective price, and campaign phase. Do not use a percentage-of-profit shortcut.
- Keep ad-driven, organic, and external-halo demand separate. Use zero halo unless an explicit assumption or observed evidence is supplied.
- Calculate break-even ACOS only when all required unit-economics inputs exist. Show `N/A` otherwise.
- Track opening stock, inbound units, Vine allocation, safety stock, fulfilled demand, unmet demand, projected stockout, and reorder timing.
- Use confirmed production, freight, and FBA receiving time for reorder timing. Show `Unconfirmed` when any component is missing.
- Never invent missing revenue, spend, margin, stock, lead-time, or eligibility inputs.

## Review Policy

Read `references/review-policy.md` before recommending or validating a review plan. Re-check the linked current Amazon Vine and Helium 10 Follow-Up rules at runtime.

## Outputs

Read `references/output-contract.md` when building or reviewing deliverables. The client plan records confirmed decisions, scenario ranges, Month 1-3 PPC, pricing, stock, review policy, owners, and open confirmations. The workbook contains the six required linked tabs.

## Boundaries And Handoffs

- Historical sales or advertising diagnosis: `amazon-audit`.
- Sponsored Products bulk files: `amazon-campaign-builder`.
- Live PPC changes: `amazon-ads` or `amazon-ppc-management`.
- Packaging, variations, UPCs, listing eligibility, or review-history questions: `amazon-catalog`.
- Shipment creation or inbound execution: `amazon-logistics`.

This skill is read-only. A plan is not approval to upload, change campaigns, create shipments, publish listings, or send client communication.

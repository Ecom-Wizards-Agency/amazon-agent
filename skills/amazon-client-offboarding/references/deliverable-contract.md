# Deliverable contract

## Google Doc order

The operator-written narrative uses this order:

1. Executive summary and evidence watermark.
2. Engagement delivery record: what was built, changed, and learned.
3. Account operating model: architecture, naming, ownership, routines, thresholds, stock controls, and decision rules.
4. Advertising change history, including the complete latest material change and its provisional status where applicable.
5. One chapter per included market, covering each supported Amazon area: performance, rank, listings/creative, catalog, inventory, buyability, Account Health, changes, risks, and recommended actions.
6. Non-Brand RPC playbook when advertising data exists.
7. Listing, Creative and POE handover. Lead with asset reuse, image reordering, and localized image text before any redesign recommendation.
8. Open items at handover.
9. Client asset and link index.
10. Supersession and read-only statement.

Start with the executive summary. Do not add a decorative cover. A prior audit, PDF, or tactical snapshot may remain linked as an appendix, but the handover states whether it supersedes that artifact for ongoing decisions.

The narrative must feel like an accountable delivery record. It should distinguish:

- work completed by the engagement;
- current account state at the cutoff;
- evidence-backed learning;
- provisional interpretation;
- successor action;
- unresolved evidence owned by the client or another operator.

Do not force actions into 72-hour, 14-day, and 30-day buckets. Use evidence-led timing and review dates.

## Workbook topology

The workbook contains exactly:

1. `Read Me & Data Watermark`
2. `Market Scoreboard`
3. `Non-Brand RPC Diagnostics`
4. `Rank & Query Tracker`
5. `Action Register`

The advertising change history and client asset/link index belong only in the Doc.

## Non-Brand RPC schema

Include market, ASIN, pack, campaign, query/target, brand classification, spend, clicks, orders, sales, CTR, CPC, CVR, AOV, RPC, ACOS, Top-of-Search share, organic rank, Required RPC, diagnosis, recommendation, owner, and review date.

Workbook formulas:

- CPC: `Spend / Clicks`
- CVR: `Orders / Clicks`
- AOV: `Ad Sales / Orders`
- RPC: `Ad Sales / Clicks`
- ACOS: `Spend / Ad Sales`, equivalent to `CPC / RPC`
- Required RPC: `CPC / Break-even ACOS`, blank unless economics are verified

Keep branded and non-branded traffic separate. Brand misspellings and product-name leakage are branded classification, not generic demand; the public skill must never include client tokens.

## Action register

Each row contains:

- market and Amazon area;
- concrete action;
- owner;
- evidence-led timing;
- trigger;
- expected outcome;
- stop condition;
- review date;
- status and source refs.

Measured expansion tests need predefined spend, order, RPC, and stop thresholds. Do not recommend aggressive scaling where fulfillment, buyability, conversion, or baseline tracking is not ready.

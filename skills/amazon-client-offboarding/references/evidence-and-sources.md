# Evidence and sources

## Evidence hierarchy

Use the narrowest source that can establish the fact. Timestamp every extraction and retain its source ID in each evidence row.

1. Live Amazon reports and account state: Amazon Ads, Seller Central reports, SQP, Account Health, catalog, inventory, and buyability.
2. Managed advertising and rank state: AdLabs and DataDive, including change history, optimization groups, rank tracking, and query intelligence.
3. Customer and creative evidence: POE, listing capture, approved image files, briefs, and client-visible Drive assets.
4. Economics: approved finance source or current client-approved unit economics.
5. Timeline reconciliation: internal Slack, Notion, team-vault run notes, and prior tactical documents. Convert relevant findings into dated client-readable facts. Never expose internal links.

Do not describe a source as current merely because it is the newest file found. Compare its coverage end date with the cutoff and performance windows.

## Required manifest behavior

Start from `tools/amazon-client-offboarding/evidence.TEMPLATE.json`. Include only supported areas, but always include:

- timestamped sources and their coverage;
- one economics status per included market;
- one market-scoreboard row per included market;
- engagement delivery, advertising changes, open gaps, and actions;
- reusable client assets with verified client access;
- rank, query, listing, creative, inventory, buyability, catalog, or Account Health evidence when available.

Every recommendation needs evidence, owner, timing, trigger, expected outcome, stop condition, and review date. A general aspiration is not an action record.

## Comparison and attribution

- Use inclusive day counts. Current and prior windows in one comparison must have equal length.
- Exclude the current day and any future date.
- Do not extend a performance window beyond `attribution_complete_through`.
- Record recent advertising changes in current state but keep their performance attribution `provisional` until the review date.
- Do not credit or blame a change merely because it occurred near a performance movement.

## Economics

Allowed statuses:

- `verified`: current, approved source with source refs and break-even ACOS as a ratio.
- `historical-lead`: useful lead that must be reconfirmed.
- `not-verified`: no approved current value.

For `historical-lead` and `not-verified`, withhold profitability labels and Required RPC. Do not convert a lead into truth through repetition.

## Link and permission gate

Every client-facing link needs:

- an HTTPS URL;
- `client_accessible: true`;
- `status: verified`;
- a timezone-aware `verified_at` timestamp;
- presence in the Doc's asset/link index.

Exclude Slack, Notion, localhost, internal Drive material, broken links, duplicates, and superseded working files. The destination must be an exact existing client-visible Drive folder or folder ID, recorded as `existing: true` and `client_visible: true` after verification.

## Area-specific routing

Load only the specialist skills needed by the evidence that exists:

- advertising history and state: `amazon-ads-console`, `amazon-ppc-weekly-management`, `amazon-reporting`;
- rank and query evidence: `amazon-audit`, `amazon-opportunity-explorer`, DataDive/AdLabs routes;
- listing and creative: `amazon-listing-capture`, `amazon-seo`, `amazon-opportunity-explorer`;
- catalog: `amazon-catalog`;
- inventory and buyability: `amazon-fba-inventory-planning`, `amazon-reporting`;
- Account Health: `amazon-account-health-check`.

These sources are read-only inputs for offboarding. Their action workflows do not grant permission to mutate the account.

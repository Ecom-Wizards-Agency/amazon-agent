---
name: amazon-client-offboarding
description: "Build a branded, read-only Amazon client handover as a native Google Doc and five-tab evidence workbook."
---

# Amazon Client Offboarding

Browser: Mixed

Create a decision-ready handover, not a generic audit and not an archive dump. Show what the engagement delivered, how the account operates, what changed, what was learned, what remains open, and how the successor should verify the next decisions.

## Non-negotiable boundaries

- Stay read-only across Amazon, AdLabs, listings, catalog, inventory, Account Health, and communications.
- Build only for explicitly included markets. Do not mention excluded markets in either client deliverable.
- Use client-specific evidence only in gitignored run folders and client systems. Never commit run configs, manifests, exports, links, or narratives.
- Treat the approved workflow branding as authoritative. Preflight must fail if the approved branding file, black logo, or document font is absent. Never accept the renderer's neutral fallback.
- Deliver only into an existing, verified, client-visible Drive folder. Do not create a folder or guess a destination.
- Do not send messages, schedule meetings, upload campaign files, or change account state.

## Workflow

### 1. Fix scope and evidence watermark

Create the run config from `tools/amazon-client-offboarding/config.TEMPLATE.json`. Record client, successor, audience, included and excluded markets, currency, cutoff timestamp, equal-day comparison windows, attribution-complete date, narrative path, evidence path, approved branding, appendix, and exact existing Drive destination.

Use `references/evidence-and-sources.md` to assemble the evidence manifest. Unsupported areas are disclosed as gaps and omitted from analysis rather than padded with assumptions.

### 2. Build the operating narrative

Write the Markdown narrative yourself. Do not ask the builder to invent findings. Follow the exact order in `references/deliverable-contract.md`.

The document must make the work visible: record what was built, what changed, and what the team learned. The advertising history must include the complete latest material change, while recent changes remain attribution-provisional until their review date.

For listing and creative work, hand over reusable assets and country-specific POE findings. Recommend reordering existing images and localizing their text before proposing a redesign. A new complete redesign is not the default when the current image system can be adapted.

### 3. Preflight before rendering

Run:

```bash
python3 tools/amazon-client-offboarding/build_handover.py \
  --config <run-config.json> \
  --preflight
```

Fix every failure. Never weaken a validator to accommodate incomplete client evidence.

### 4. Build and inspect

Run:

```bash
python3 tools/amazon-client-offboarding/build_handover.py \
  --config <run-config.json>
```

This renders a no-cover A4 DOCX with `doc_label: Amazon Account Handover` through the canonical branded renderer and builds the exact five-tab XLSX through the canonical branding loader and workbook style helpers.

Inspect both files using `references/branding-delivery-and-qa.md`. The Doc owns the change history and client asset/link index. The workbook must contain no change-log or asset-index tab.

### 5. Deliver as native Google files

After local QA, explicitly deliver the validated pair:

```bash
python3 tools/amazon-client-offboarding/build_handover.py \
  --config <run-config.json> \
  --deliver
```

The builder delegates conversion to `tools/gdrive-deliver/deliver.py`. The destination must already exist and have current client-access verification. After first client delivery, edit the native Google Doc or Sheet in place; do not re-import over human comments.

### 6. Close the run

Record a short team-vault run note following repository rules. Include scope, evidence cutoff, material open items, delivered native file links, and the successor. Do not copy raw evidence into the vault.

## Decision rules

- Separate branded from non-branded performance, including misspellings and product-name leakage.
- `RPC = Ad Sales / Clicks = CVR x AOV`.
- `ACOS = CPC / RPC`.
- `Required RPC = CPC / Break-even ACOS`, only when economics are verified.
- A CPC reduction can improve ACOS but cannot improve RPC. RPC recommendations must address CVR, AOV, landing ASIN, pack, offer, stock, Prime eligibility, or query relevance.
- High CTR with low CVR: fix offer, listing, fulfillment, landing ASIN, or pack before bidding higher.
- Low CTR with high CVR: improve the main image, title, query congruence, or Sponsored Brands creative.
- Healthy RPC with limited traffic: isolate and scale through exact, PAT, or controlled Top-of-Search tests.
- Low RPC with low relevance: reduce bids, contain discovery, or add an ad-group negative.
- Strong organic rank: graduate spend gradually instead of switching campaigns off.
- Rank opportunity with weak conversion: listing and fulfillment work precede another rank push.
- Low budget utilization is evidence against budget being the primary constraint.

## References

- `references/evidence-and-sources.md`: evidence hierarchy, source manifest, economics, attribution, and permissions.
- `references/deliverable-contract.md`: exact Doc order, workbook topology, schemas, and narrative standards.
- `references/branding-delivery-and-qa.md`: branding ownership, native delivery, and final QA.

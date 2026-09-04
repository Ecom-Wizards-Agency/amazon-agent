---
name: amazon-client-onboarding
description: "Run and verify a standardized Amazon client Day 0 onboarding: access preflight, read-only account baseline, FBA disposal protection, Brand Tailored Promotion plans, fingerprinted approval, and independent verification."
---

# Amazon Client Onboarding

Browser: Mixed

Run one evidence-backed onboarding per Seller Central account and marketplace. Treat Amazon access as a preflight gate. Assess and stage first; mutate only through the separate approval command.

## Route the command

| Command | Action |
|---|---|
| `Check Amazon onboarding access for <client>` | Read `references/access-preflight.md`. Test required surfaces without changing state. Create one blocking Notion task only when access is missing. |
| `Run Amazon onboarding setup for <client>` | Require a passing access preflight. Read `references/day-zero-assessment.md` and `references/manifest-and-output.md`. Perform the assessment, build the manifest, validate it, and stage a fingerprinted change batch. Do not change Amazon. |
| `Approve Amazon onboarding changes <run_id>` | Read `references/approval-and-verification.md`. Accept only the current displayed fingerprint and execute only the approved batch. |
| `Verify Amazon onboarding <run_id>` | Reopen every changed surface, obtain the independent inventory review, validate the final manifest, schedule the seven-day watch, and close the run only when the signoff rules pass. |

## Core workflow

1. Resolve the client hub and `Amazon Ops.md` profile from the shared team vault. Confirm account label, marketplace, scope, task owner, and a different inventory reviewer.
2. Store run artifacts under `output/{client}/onboarding/{run_id}/` and screenshots under `evidence/{client}/onboarding/{run_id}/`. Register every created path under the run with `tools/artifactctl/artifactctl`; evidence is `preserve`. Never commit client manifests or evidence.
3. Open Seller Central and Amazon Ads through the managed Chrome on port 9222 using `tools/browserctl/task-tabs.mjs` with one task ID per run, and acquire the port's exclusive context claim before any account or marketplace selection. Never repurpose a Seller Central anchor tab. Re-verify the selected account and marketplace on every surface before reading from it.
4. Use live Seller Central as the authority for permissions, settings, promotion eligibility, audience names, limits, and fees. Search first-party Amazon Help when a current rule is needed.
5. Set `run.mode` to `LIVE`, validate the manifest, and stamp its computed fingerprint before showing the change batch:

```bash
python3 tools/amazon-client-onboarding/validate_run.py \
  --manifest <run-manifest.json> \
  --stamp-fingerprint
```

6. Copy the stamped validator fingerprint into the approval preview. Approval becomes stale when the validator returns a different fingerprint. Only `run.mode: LIVE` with `Operational approval: ALLOWED` can authorize Amazon changes. `SYNTHETIC` may simulate later states for self-tests but must never invoke live tools.
7. Record the finished work in `Clients/{Name}/Runs/YYYY-MM-DD-amazon-onboarding.md`. Update `Amazon Ops.md` only with verified durable facts.

## Non-negotiable rules

- Do not start the Day 0 assessment when a critical access surface is unavailable.
- Do not change inventory settings, create promotions, activate monitoring, edit listings or campaigns, submit cases or appeals, or create removal orders during assessment.
- Treat active or unauthorized Disposal/Liquidation orders, recall-required removals, critical Account Health risks, account/marketplace mismatch, and missing inventory-safety access as RED.
- Stage 15% Brand Tailored Promotions for every live eligible audience. Include only active, in-stock, economically eligible ASINs with the Featured Offer and safe worst-case stacking.
- Use the longest live permitted duration up to 90 days and the live platform minimum budget. A larger budget requires an explicit approved ceiling.
- Start promotions Monday through Wednesday. Re-check eligibility, stock, Featured Offer, stacking, dates, and budget immediately before creation.
- Let the task owner approve and execute. Require a different human to verify unfulfillable and stranded settings, return destination, active removal orders, and reconciled quantities.
- Never sign off GREEN until the independent inventory verification and seven-day disposal/recall watch are recorded.
- Route deep audits, catalog edits, campaign changes, appeals, support submissions, shipments, removals, and communications to their owning skills as separate work.

## References

- `references/access-preflight.md`: required Amazon surfaces and conditional blocker task.
- `references/day-zero-assessment.md`: complete read-only assessment and RED rules.
- `references/promotion-plan.md`: 15% all-eligible-audience BTP contract and stacking guards.
- `references/approval-and-verification.md`: fingerprint approval, execution order, peer review, and signoff.
- `references/manifest-and-output.md`: manifest fields, Notion output, vault run note, and recurring handoff.

# SOP Draft: Amazon Client Day 0 Onboarding

Date: 08.08.2026
Status: ready for review
Owner: Amazon Operations
Related workflow: `amazon-client-onboarding`

## Purpose

Start every Amazon engagement from a verified, safe, and measurable account baseline. Prevent silent inventory destruction, surface urgent account risks, document operating readiness, and ensure eligible Brand Tailored Promotion audiences receive an approved 15% setup proposal.

This SOP covers the Amazon module only. Contract, invoice, welcome, asset intake, file-system setup, and roadmap planning remain in the full client onboarding workflow.

## Preconditions

- Contracted Amazon scope and marketplaces are known.
- The client hub and `Amazon Ops.md` profile exist or are ready to be created.
- One task owner and a different inventory verifier are assigned.
- The agency uses an individual secondary-user or authorized-partner account. Shared credentials are forbidden.
- The access preflight passes for the exact Seller Central account and marketplace.

Access is a gate, not a standing onboarding task. When every required surface opens, no access task is created. When access is missing, one blocker task identifies the exact surface, role/permission, marketplace, client action, and evidence.

## Required Inputs

- Client name, canonical slug, Seller Central label, advertiser label, marketplace, and profile key.
- Managed brands and ASIN/SKU scope.
- Fulfillment model: FBA, FBM, or mixed.
- Task owner and independent inventory verifier.
- Client-approved return destination and unfulfillable/stranded schedule or age.
- Verified unit economics for a 15% promotion and any approved budget ceiling above Amazon's live minimum.
- Notion task destination, internal escalation destination, and evidence/run folders.

Do not store a street-level return address, credential, token, cookie, or login email in the vault or GitHub.

## Workflow

### 1. Prove access

Open and verify the exact account/marketplace on:

1. Account selector.
2. Account Health and Performance Notifications.
3. Automated unfulfillable/stranded inventory settings.
4. Removal Order Detail report and order details.
5. Manage All Inventory/catalog.
6. Brand Registry, Brand Analytics, and SQP where available.
7. Brand Tailored Promotions.
8. Advertising Console and reports.
9. Seller Central reporting.

If a critical surface is blocked, create/update one access blocker and stop. Do not partially onboard.

### 2. Run the read-only Day 0 assessment

Confirm account identity, marketplaces, brands, managed ASINs/SKUs, and fulfillment model. Then capture:

- Account Health rating/state, policy issues, notifications, product-safety/recall/required-removal notices, deadlines, and relevant open cases.
- Active, inactive, suppressed, pricing-error, Featured Offer, and variation states.
- Unfulfillable and stranded inventory by ASIN/SKU/FNSKU, reason, quantity, disposition, and auto-removal date.
- Automated unfulfillable setting and both stranded-removal categories, including schedule/age and visible return destination.
- At least 90 days of Removal Order Detail data and every active order.
- Written reconciliation of unfulfillable/stranded quantities against active Return, Disposal, and Liquidation orders.
- FBA/FBM mapping, stock, aged/excess/reserved inventory, shipment exceptions, fee alerts, returns, and Voice of the Customer.
- Advertiser/billing readiness, active campaign/portfolio/budget counts, Seller/Ads reporting, Sellerboard, SellerSonar, TrueOps, review tracking, and monitoring destinations.
- Every active/scheduled coupon, deal, Subscribe & Save offer, promotion, and Brand Tailored Promotion.

Classify every required check as `PASS`, `WARN`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE` with timestamped evidence. A warning requires an owner, due date, and task.

### 3. Stop and escalate RED conditions

Mark RED for:

- active or unauthorized Disposal/Liquidation orders;
- recall-generated or required removals;
- a dangerous order whose cancellation is unavailable or unverified;
- critical Account Health risk;
- account/marketplace mismatch;
- missing inventory-safety access;
- material unreconciled inventory.

Settings changes do not cancel existing orders. A canceled support case or callback is not cancellation proof. Use the removal-order detail page and item totals.

### 4. Stage one change batch

Do not mutate during assessment. Stage:

- unfulfillable inventory toward Return to seller on the approved schedule;
- both stranded-removal categories toward Return to seller at approved ages;
- approved monitoring/integration setup;
- one separate 15% Brand Tailored Promotion for every live eligible audience.

For BTP, use the longest live permitted duration up to 90 days and the live platform minimum budget. Use a Monday–Wednesday start. Include only managed ASINs that are active, in stock, economically eligible, hold the Featured Offer, and remain within the approved worst-case discount after stacking.

Record an explicit exclusion when an eligible audience has no safe ASIN. A larger budget needs a documented client-approved ceiling.

Validate the manifest and present the generated fingerprint with every before/after action.

### 5. Approve and execute

The task owner may approve and execute the current fingerprinted batch. Approval does not extend to appeals, removals, catalog/listing edits, campaign changes, messages, uploads, shipments, or support submissions.

Execution order:

1. Revalidate fingerprint and account/marketplace.
2. Apply inventory-safety settings.
3. Reopen and capture saved settings and visible return destination.
4. Apply explicitly approved monitoring integrations.
5. Refresh BTP eligibility, ASIN stock, Featured Offer, economics, stacking, dates, duration, and budget.
6. Create only unchanged approved promotions; otherwise rebuild the batch.
7. Record execution and verification evidence per action.

### 6. Independent inventory verification

A different person must reopen and verify:

- unfulfillable action and schedule;
- both stranded-removal categories and ages;
- complete visible return destination;
- active removal orders and item totals;
- quantity reconciliation;
- recall and required-removal notices.

### 7. Handoff and signoff

Schedule daily removal-order and recall monitoring for seven calendar days. Hand ongoing checks to the existing daily Account Health and weekly/monthly operations workflows.

Update the single Notion Day 0 task with RAG, clean checks, blockers, change batch, BTP coverage/exclusions, approval, peer review, monitoring, and links. Write a concise team-vault run note; keep raw evidence outside the vault.

Sign off GREEN only when no RED condition remains, approved actions are verified or deliberately deferred with owner/due date, the independent review passes, and the seven-day watch is scheduled.

## Stop-Before-Risk Points

- Stop on login, account, marketplace, brand, ASIN scope, return destination, or economics ambiguity.
- Stop before every account mutation until the exact fingerprinted approval is current.
- Stop and rebuild approval when live state changes.
- Stop before appeals, acknowledgements, support replies/submissions, listing/catalog edits, campaign edits, messages, uploads, shipments, removals, refunds, or other adjacent actions.
- Stop signoff when the task owner and inventory verifier are the same person.

## Evidence And Screenshots Needed

- Account/marketplace and advertiser selection.
- Account Health and relevant notification/case evidence.
- Unfulfillable and stranded settings before and after, including the complete visible return destination.
- Inventory totals and 90-day removal report.
- Detail page for every active removal order and written quantity reconciliation.
- Recall/required-removal review.
- Catalog/offer, inventory, reporting, monitoring, and promotion baselines.
- Live BTP audience eligibility and every proposed/excluded audience.
- Independent inventory-review evidence and seven-day watch task.

## Source Docs/SOPs Used

- First-party Amazon Seller Help and live Seller Central for current UI, eligibility, permissions, settings, limits, and fees.
- The existing automatic FBA disposal-prevention draft and its verified cancellation-proof standard.
- Team-vault client run note documenting a stopped recall disposal and the cancellation-proof standard.
- Amazon Agent skills: account health, logistics, catalog, reporting, operations review, inventory planning, ads, audit, troubleshooting, and communications.
- Amazon announcement: https://sellercentral.amazon.com/seller-forums/discussions/t/ac1edd98-9122-4993-8289-26163ecbd51a/

## Open Questions Or Assumptions

- Live Seller Central is authoritative when a marketplace lacks a program or uses different audience names/limits.
- One manifest covers one seller account-marketplace. Multi-market clients receive separate isolated manifests and one consolidated Notion summary.
- Version one prepares the operational-check handoff but does not activate recurring automations without their existing separate approval flow.

## Promotion Notes

- Agency default: 15% for every live eligible BTP audience.
- Default duration: longest permitted up to 90 days.
- Default budget: live platform minimum.
- Default start days: Monday through Wednesday.
- Every eligible audience requires either a safe proposal or a written exclusion.
- Stacking is evaluated from live behavior; never assume discounts do not combine across consoles.

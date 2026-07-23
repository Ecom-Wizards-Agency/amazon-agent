---
name: amazon-operations-review
description: Run and manage lightweight Amazon weekly and monthly operational checks without duplicating daily Account Health, shipment reconciliation, or full reshipment planning. Use for `Set up the operational checks`, weekly or monthly operations reviews, low-stock and stranded-inventory exceptions, open or received shipment issues, negative-review tracking, SellerSonar fee alerts, returns, Voice of the Customer, overstock checks, and commands to run, show, pause, or resume the operational checks.
---

# Amazon Operations Review

Browser: Mixed (Seller Central and SellerSonar interactive checks; Google Drive, Slack, and task-system connectors for tracking and output).

Keep this skill dormant by default. Loading or installing it must never create an automation, run a check, open Amazon, or write external data.

## Route The Command

| User command | Action |
|---|---|
| `Set up the operational checks` | Read `references/setup-and-activation.md`. Collect configuration and show the activation preview. Do not create or enable an automation. |
| `Approve and activate operational checks` | Activate only when a complete, current preview is awaiting approval. Follow the activation gate in `references/setup-and-activation.md`. Do not run either check immediately. |
| `Run the weekly operational check now` | Require completed setup, then read and run `references/weekly-check.md`. |
| `Run the monthly operational check now` | Require completed setup, then read and run `references/monthly-check.md`. |
| `Pause the operational checks` | Pause both configured schedules through the active automation tool. Preserve configuration and automation IDs. |
| `Resume the operational checks` | Preview both schedules and next-run times, then resume only after explicit confirmation. Do not run immediately. |
| `Show the operational checks setup` | Display state, accounts, destinations, schedules, automation IDs, and next-run times. Do not mutate anything. |

Use the Codex app automation manager for activation, pause, resume, inspection, or deletion. Find the current project ID first and prefer updating a matching automation over creating a duplicate. Do not emulate recurring schedules with local cron files or background processes.

## Run Boundaries

- Daily Account Health owns policy, performance, and listing-blocker alerts. Do not repeat its full sequence.
- Weekly Operations owns lightweight stock exceptions, stranded inventory, shipment exceptions, variation exceptions, negative-review tracking, and SellerSonar fee alerts.
- Monthly Operations owns returns, Voice of the Customer, and overstock review.
- `amazon-inventory-planning` owns full reshipment calculations and requires fresh same-day reports. A stock exception creates or updates a planning task only.
- `amazon-communications` owns any customer outreach or courtesy-refund follow-up.
- `amazon-catalog` owns parentage repairs and listing edits.
- `amazon-logistics` owns shipments, removals, and other inventory actions.

## Hard Rules

- Verify Seller Central account, marketplace, page, and filters before reading data for every account.
- Stop on login, account, marketplace, workbook-tab, configuration, or data-freshness ambiguity.
- Never send a customer message, issue a refund, create a promotion, edit a listing, upload a file, or perform a shipment action without separate approval or a matching local standing permission.
- Never post to a client-facing channel automatically.
- Update existing tasks and review rows instead of creating duplicates.
- Post one compact internal run summary only when the configured internal destination and permission are valid.

## References

- Setup, states, schedules, and activation: `references/setup-and-activation.md`
- Cold-start recurring prompts: `references/automation-prompts.md`
- Weekly procedure: `references/weekly-check.md`
- Shipment-exception rules: `references/shipment-exceptions.md`
- Monthly procedure: `references/monthly-check.md`
- Review workbook contract: `references/review-tracking.md`

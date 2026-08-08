# Approval and Verification

## Approval preview

Show one compact preview containing run ID, client, account, marketplace, RAG status, RED blockers, each proposed before/after value, promotion audience/ASIN/date/discount/budget, stop points, task owner, independent inventory reviewer, and the validator fingerprint.

Accept `Approve Amazon onboarding changes <run_id>` only when:

- `run.mode` is `LIVE` and the validator reports `Operational approval: ALLOWED`;
- the run is `approval_pending`;
- no RED condition is active;
- the displayed fingerprint equals a fresh validator fingerprint;
- the task owner is the approver;
- every financial setting, promotion, and integration activation in the batch is visible;
- return destination, inventory schedule/age, promotion economics, and any budget ceiling are complete.

Approval authorizes only the fingerprinted batch. It does not authorize appeals, removal orders, listing/catalog edits, campaign changes, messages, uploads, support submissions, or other adjacent actions.

## Execution order

1. Revalidate and re-check account/marketplace.
2. Apply approved unfulfillable and stranded removal settings.
3. Reopen the settings and capture the saved values and complete visible return destination.
4. Apply approved monitoring/integration setup that is explicitly included.
5. Refresh every promotion guard from `promotion-plan.md`. If unchanged, create the approved BTPs. If changed, stop and return to approval.
6. Record execution result and evidence per action. Never mark a failed save as executed.

## Independent inventory verification

A person other than the task owner/executor must reopen and verify:

- automated unfulfillable action and schedule;
- both stranded-removal categories and ages;
- complete visible return destination;
- current active removal orders and their item totals;
- unfulfillable/stranded quantity reconciliation;
- recall and required-removal notices.

Record reviewer identity, timestamp, evidence, and explicit booleans for every item. A support case or canceled callback is not proof that a removal stopped. For a canceled dangerous order, require the removal detail to show the merchant-canceled equivalent, canceled quantity equal to ordered, disposed zero, and pending zero.

## Signoff

Schedule a seven-calendar-day daily watch for removal orders and recall/required-removal notices. Hand ongoing account checks to the configured daily/weekly/monthly workflows.

Sign off GREEN only when:

- no RED condition is active;
- required checks are complete;
- all approved actions are verified or deliberately deferred with owner/due date;
- the independent inventory review passes;
- the seven-day watch has an owner, dates, and task URL.

Otherwise leave the run RED or AMBER and keep the Notion task open.

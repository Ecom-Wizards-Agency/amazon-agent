# Manifest and Output Contract

Create the run manifest from `tools/amazon-client-onboarding/manifest.TEMPLATE.json`. Keep client manifests and screenshots in ignored output/evidence folders.

## Manifest ownership

- `run`: ID, state, timestamps, RAG, task owner, executor, and independent reviewer.
- `scope`: client slug, client name, account label, marketplace, brands, managed ASINs, and profile key.
- `access`: one result per required access surface.
- `checks`: one result per required Day 0 check, with evidence and follow-up ownership.
- `red_conditions`: active disposal/recall/health/account mismatch conditions.
- `promotion_inventory`: timestamped live eligible-audience inventory used to prove coverage.
- `promotion_audiences`: every live BTP audience with eligibility, proposal or exclusion.
- `change_batch`: staged before/after actions and approval/execution evidence.
- `inventory_peer_review`: independent settings/order/quantity verification.
- `monitoring_handoff`: seven-day watch and recurring workflow destinations.

Set real runs to `run.mode: LIVE`. Use `tools/amazon-client-onboarding/validate_run.py --manifest <path> --stamp-fingerprint` to validate and write the batch fingerprint. The command refuses non-live manifests and manifests with other validation errors. Only `Operational approval: ALLOWED` can authorize live execution. Synthetic manifests may exercise the state machine in self-tests but never authorize external changes. Do not hand-edit or reuse a fingerprint after account state changes.

## Notion-ready result

Update the single `RUN - Amazon Day 0 Setup - {Client}` task with:

- account/marketplace and evidence timestamp;
- RAG and state;
- clean checks;
- RED blockers and AMBER findings;
- staged/approved/executed changes;
- BTP audience coverage and exclusions;
- approval fingerprint and approver;
- inventory reviewer and verification result;
- seven-day watch and recurring handoff;
- links to evidence and follow-up tasks.

Create or update issue tasks by account, marketplace, issue type, and ASIN/order ID. Do not create duplicates.

## Vault run note

Write `Clients/{Name}/Runs/YYYY-MM-DD-amazon-onboarding.md` with `type: run`. Record scope, RAG, safety findings, approved/executed changes, promotion coverage, unresolved tasks, seven-day watch, and artifact/task links. Do not copy raw reports, screenshots, addresses, or credentials into the vault.

Update `Amazon Ops.md` only when the run verifies a durable account label, marketplace mapping, fulfillment assumption, workflow routing fact, or safety note. Do not store street-level return addresses.

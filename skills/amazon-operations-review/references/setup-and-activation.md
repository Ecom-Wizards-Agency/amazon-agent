# Setup And Activation

## Local State

Store teammate-specific configuration at `_local/amazon-operations-review/config.json`. Never commit this file. Use these states:

- `inactive`: no approved preview and no schedules.
- `preview_pending`: setup is complete and awaiting the exact activation approval.
- `active`: both recurring schedules exist and are enabled.
- `paused`: both schedules exist and are disabled.
- `degraded`: one schedule or required destination is missing or inconsistent.

Installing or loading the skill leaves the state `inactive` and must not create the config file unless the user starts setup.

## Required Configuration

Collect or resolve the following without running an operational check:

- Teammate timezone.
- Active account-profile source.
- For every account: client slug, Seller Central account label, marketplace, Review Management tab, default task owner, and escalation owner.
- Review Management workbook URL: `https://docs.google.com/spreadsheets/d/18otgJNjAKRlpDyTQkcCzhHAqKTxMJc6EgxrQBj8TG_A/edit`
- SellerSonar fee-alert source.
- Follow-up task database or tracker.
- Internal Slack destination and permission to post operational summaries.
- Browser preference and fallback.
- Empty Review Management template tab to copy when a configured client-market tab is missing.

Use the local client-profile cache first, then Notion when the cache is missing, stale, incomplete, or conflicting. Do not silently change shared client facts.

## Setup Command

When the user says `Set up the operational checks`:

1. Read existing local configuration if present.
2. Resolve accounts and marketplaces from the approved profile source.
3. Inspect the Review Management workbook metadata read-only and match configured client-market tabs.
4. Validate SellerSonar, task, Slack, and browser destinations read-only.
5. Record missing values as blockers. Do not guess account labels, marketplace mappings, owners, IDs, or permissions.
6. Prepare the two automation prompts from `automation-prompts.md` with the local config path.
7. Show the activation preview below and set state to `preview_pending` only when there are no blockers.
8. Stop. Do not call an automation-create or automation-enable action.

Activation preview:

```text
Amazon operational checks activation preview
State: preview_pending
Accounts: {account + marketplace + review tab}
Weekly: Tuesday 10:00 {timezone}
Weekly checks: stock, stranded inventory, shipment exceptions, variation exceptions, negative reviews, SellerSonar fee alerts
Monthly: day 2 at 11:00 {timezone}
Monthly checks: returns, Voice of the Customer, overstock
Review workbook: {title + URL}
SellerSonar source: {source}
Tasks: {database + default owners}
Internal output: {Slack destination}
Missing review tabs to create after approval: {tabs or none}
Stop points: messages, refunds, promotions, listing edits, uploads, shipments
First run: next scheduled occurrence; no immediate run

To activate, reply exactly: Approve and activate operational checks
```

## Activation Gate

Accept `Approve and activate operational checks` only when all conditions hold:

- A complete preview is currently pending.
- The approval follows that preview in the same task or is tied to its saved preview fingerprint.
- Accounts, destinations, permissions, timezone, and schedules have not changed since preview.
- The active automation tool can create schedules without triggering an immediate run.

After approval:

1. Copy the configured empty review template tab for each approved missing client-market tab. Do not alter existing tabs.
2. Use the Codex project lookup to resolve the current Amazon Agent project ID.
3. Inspect existing Codex automations for the two names below. Update a matching automation instead of creating a duplicate.
4. Create or update `amazon-operations-review-weekly` for Tuesday at 10:00 in the teammate timezone.
5. Create or update `amazon-operations-review-monthly` for day 2 of each month at 11:00 in the teammate timezone.
6. Use the exact self-contained prompts in `automation-prompts.md` with resolved config paths.
7. Create or update both with the native Codex automation manager. If supported, keep them inactive while verifying both definitions and future next-run times, then activate both. If immediate-run behavior cannot be ruled out, leave both inactive and report the blocker.
8. Save returned automation IDs and activation time locally.
9. Verify that the next runs are in the future and that no operational task started during setup.
10. Set state to `active` only when both schedules are valid and enabled. Otherwise set `degraded` and report the mismatch.

## Pause, Resume, And Inspection

- Pause both IDs as one operation when possible. If only one pauses, set `degraded` and report both states.
- Resume only after showing the two schedules and receiving explicit confirmation. Verify future next-run times and do not trigger a run.
- Show configuration read-only. Never expose secrets or browser-session data.
- Manual weekly or monthly runs require completed configuration. If schedules are paused, state that the manual run is an exception before proceeding.

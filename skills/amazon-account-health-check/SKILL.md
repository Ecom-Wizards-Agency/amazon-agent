---
name: amazon-account-health-check
description: Use for the daily Amazon account health check across Seller Central accounts: re-check open findings from the local findings ledger, read the alert source (such as SellerSonar), verify Account Health in Seller Central, dispose every finding, post the daily action-queue thread with one comment per account, and create or update follow-up tasks.
---

# Amazon Account Health Check

Use this skill for recurring or ad hoc daily account health checks.

Trigger phrases include `daily account health check`, `account health sweep`, `run account health`, `check account health for accounts`, and requests to post a daily account-health thread.

## How To Run

1. First run only: collect the local configuration values and seed the findings ledger — `references/setup.md` (setup keys and account-profile-source rules). Configuration and the ledger are local-only; never commit them to GitHub.
2. Open `{preferred_browser}` and confirm Seller Central is logged in before any account checks — session, tab, and domain rules in `references/browser-rules.md`.
3. Step 0 of every run: re-check open findings from `{findings_ledger_path}` before looking for new issues.
4. Run the per-account check sequence, Europe accounts first, then US, then the rest — `references/check-sequence.md`, including the read-only policy-issue deep dive.
5. Give every finding exactly one disposition (no action / action needed / assigned / waiting / escalate) and write the ledger once at the end of the run — disposition rules, escalation triggers, and the degraded-run procedure in `references/dispositions-and-ledger.md`.
6. Post the Slack action-queue parent post plus one thread comment per account, and create/update follow-up tasks — exact formats and the Notion mapping in `references/output-and-tasks.md`.
7. Finish note: Slack links, queue counts by disposition, tasks created/updated, accounts checked or skipped, ledger written yes/no, browser used, and blockers.

## Hard Rules (always apply)

- Never click `Submit appeal` unless the operator is present and has explicitly approved that exact action.
- Stop before appeals, acknowledgements, support contact or replies, listing edits, shipment actions, messages, uploads, or account-changing actions.
- Freshness guard: if the alert source's latest report is older than the previous business day, never report `No alerts` — report `alert source stale ({report date})`.
- If the queue is empty, post exactly `Action queue: empty` — a missing parent post means the run failed, not that everything was clean.
- Never infer resolved from a missed check; carry skipped accounts' ledger entries forward unchanged.

## References

- `references/setup.md` — first-run setup values and account profile source.
- `references/browser-rules.md` — approved browsers, regional sessions, verification rules.
- `references/check-sequence.md` — per-account check steps and the policy-issue deep dive.
- `references/dispositions-and-ledger.md` — findings ledger schema, dispositions, escalation triggers, degraded runs.
- `references/output-and-tasks.md` — Slack formats, Notion follow-up defaults, finish note.

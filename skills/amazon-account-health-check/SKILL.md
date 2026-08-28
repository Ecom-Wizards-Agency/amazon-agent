---
name: amazon-account-health-check
description: Use for the daily Amazon account health check across Seller Central accounts: re-check open findings from the local findings ledger, read the precomputed Keepa market signals from the state file the caller supplies, verify Account Health in Seller Central, dispose every finding, write the ledger and the run's coverage entry, and create or update follow-up tasks. The run itself posts nothing except an immediate escalation; a separate deterministic pass posts the one daily digest.
---

# Amazon Account Health Check

Browser: CDP (SC Account Health; Review-details clicks + screenshot evidence).

Use this skill for recurring or ad hoc daily account health checks.

Trigger phrases include `daily account health check`, `account health sweep`, `run account health`, `check account health for accounts`, and a scheduled account-health run for one region or one profile.

## How To Run

1. First run only: collect the local configuration values and seed the findings ledger. Setup keys and account-profile-source rules are in `references/setup.md`. Configuration and the ledger are local-only; never commit them to GitHub.
2. Open `{preferred_browser}` and confirm Seller Central is logged in before any account checks. Session, tab, and domain rules are in `references/browser-rules.md`.
3. Step 0 of every run: re-check open findings from `{findings_ledger_path}` before looking for new issues.
4. Run the per-account check sequence, Europe accounts first, then US, then the rest. The sequence, including the read-only policy-issue deep dive, is in `references/check-sequence.md`.
5. Give every finding exactly one disposition (no action / action needed / assigned / waiting / escalate) and write the ledger once at the end of the run. Disposition rules, escalation triggers, and the degraded-run procedure are in `references/dispositions-and-ledger.md`.
6. Post nothing. Write every finding and the run's coverage entry to the ledger, and create or update follow-up tasks. One deterministic pass reads that ledger later and posts the single daily digest for every region together. The only thing this run posts is an immediate one-line escalation for something that cannot wait for the digest. The digest contract, the escalation line, and the Notion mapping are in `references/output-and-tasks.md`.
7. Finish note: return it as the run's structured JSON result. It never goes to Slack. Include counts by disposition, immediate escalations posted, coverage written for the region, tasks created or updated, accounts checked or skipped, ledger written yes/no, browser used, and blockers.

## Hard Rules (always apply)

- Never click `Submit appeal` unless the operator is present and has explicitly approved that exact action.
- Stop before appeals, acknowledgements, support contact or replies, listing edits, shipment actions, messages, uploads, or account-changing actions.
- Market signals are precomputed and read from `{market_signals_state_path}`. Never fetch them during the check.
- Keepa freshness guard: if that state file is missing, or its `generated_at` is not from today, state it as a blocker and carry on. A market-data outage never cancels the account-health check. Do not report an account as clean on market signals you could not read.
- The run's claim is the coverage entry it writes under `coverage[YYYY-MM-DD][<region>]`, not a post. Write it even when the run failed, with `checked: 0`. A region with no entry is reported pending and is never folded into the checked count.
- Never infer resolved from a missed check; carry skipped accounts' ledger entries forward unchanged.

## References

- `references/setup.md`: first-run setup values and account profile source.
- `references/browser-rules.md`: approved browsers, regional sessions, verification rules.
- `references/check-sequence.md`: per-account check steps and the policy-issue deep dive.
- `references/dispositions-and-ledger.md`: findings ledger schema, dispositions, escalation triggers, degraded runs.
- `references/output-and-tasks.md`: the digest contract, the immediate escalation line, Notion follow-up defaults, finish note.

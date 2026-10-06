# First-Run Setup and Account Source

## First-Run Setup

Before creating or running a recurring automation, ask for and record local configuration. Do not commit this configuration to GitHub.

Required setup values:

- `{account_profile_source}`: where active account profiles live, such as Notion, a local CSV, or a local JSON cache.
- `{seller_central_name_field}`: the profile field used to select the Seller Central account. Recommended field name: `Seller Central Name`.
- `{marketplace_field}`: the profile field used to select the country/marketplace. Recommended field name: `Marketplace`.
- `{daily_update_channel}`: the Slack channel the daily digest pass posts to, and the destination for an immediate escalation from a run.
- `{market_signals_state_path}`: local path of the precomputed Keepa market-signal state file. The check reads this file; it never fetches market signals itself. Ask which ASINs each profile registers in its `monitoring` block; an unregistered ASIN gets no market signal.
- `{follow_up_task_database}`: optional task database or tracker for follow-up work.
- `{default_task_type}`: optional task type for follow-ups, such as `Troubleshooting`.
- `{task_priority_rules}`: optional priority mapping for follow-up tasks; `references/output-and-tasks.md` holds the default.
- `{daily_runner}`: the person who works the day's findings and is the default owner of every follow-up task. Record their chat member ID and task-system person ID so mentions and assignments resolve correctly.
- `{escalation_owner}`: the person who receives true escalations only. Record their chat member ID and task-system person ID. Mention them only on escalation lines, never on clean runs.
- `{supervisor}`: optional strategic supervisor who receives a weekly digest instead of daily output. Record their chat member ID.
- `{findings_ledger_path}`: local path of the private findings ledger JSON, stored next to the automation, never in the repo or GitHub.
- `{findings_projection_command}`: the exact command that returns the open findings of one region as a compact JSON array, and the same command's single-finding form. Step 0 reads the ledger only through it. Record both forms, including how the region and the finding key are passed.
- `{preferred_browser}`: not an operator choice. Live runs use the CDP session `browserctl` resolves: `grimoire` on port 9223 for scheduled and Slack runs, the machine's attended default for attended runs (`references/browser-rules.md`). The T3 Code in-app browser and extension-connected browsers are not supported for this check; do not ask the operator to pick one.
- `{first_run_mode}`: whether the first runs are dry runs or post live updates and create live tasks.
- `{schedule}` and `{timezone}`: optional local recurring automation schedule.

Ask which accounts and marketplaces should run before creating a local automation. Account names, marketplace lists, channel IDs, Notion IDs, assignees, schedules, and local paths are runtime configuration, not source-controlled skill content.

### What stays local

GitHub holds the generic skill, setup questions, placeholder templates, stop-before-risk rules and output formats. Never commit:

- seller account names, client names, account lists, client-linked marketplaces or test-run results;
- Slack channel IDs, Notion database IDs, user IDs, assignee names, local workspace paths or local automation files;
- credentials, MFA data, cookies, browser session data, payment or tax details, or downloaded reports;
- copies or exports of shared team-vault profile data. Keep only the local vault path pointer, never a second profile cache.

### Local automation

Create the recurring automation locally only after every value above is recorded, and replace every placeholder before activation. Its prompt names `{workspace_path}`, loads this skill first and passes the setup values. It does not restate the check sequence, dispositions, ledger, output or browser rules: the skill and its references own them, and a copied procedure goes stale.

### Activation checklist

- Run two or three supervised manual runs before enabling the recurring automation.
- Confirm no client or account names, person IDs or the findings ledger are stored in GitHub.
- Confirm every finding carries exactly one disposition, tasks are created or updated without duplicates (matched by ledger key), and the ledger is written once at the end of the run.
- Confirm the configured destination receives the output `references/output-and-tasks.md` defines, with the escalation owner mentioned only on escalation lines.
- Confirm a login or MFA prompt pauses the run safely and the degraded-run path still writes the ledger and escalates the login blocker.
- Confirm no appeals, acknowledgements, support replies, listing edits, shipment actions or account-changing actions are performed.

## Account Source

For automation runs, fetch active profiles from `{account_profile_source}`.

Required profile fields:

- `Profile Name`
- `{seller_central_name_field}`; recommended: `Seller Central Name`
- `{marketplace_field}`; recommended: `Marketplace`
- `Status`

Rules:

- Use `{seller_central_name_field}` as the canonical Seller Central account selector.
- Use `{marketplace_field}` as the canonical country/region selector.
- Group and run profiles by region with Europe first, then US, then any remaining marketplaces.
- Record the country/region on every finding, and use it as the region key of the run's coverage entry, so the digest can group and count by region.
- Do not use or display `Fulfillment Method` in the daily account-health workflow.
- Skip profiles missing `{seller_central_name_field}` or `{marketplace_field}` and list them under blockers.
- Exclude any profile the account source marks as out of scope for scheduled checks. Such a profile is not counted in `in_scope`, is not in the checked list, and is not in `skipped`; its existing findings are carried forward untouched.

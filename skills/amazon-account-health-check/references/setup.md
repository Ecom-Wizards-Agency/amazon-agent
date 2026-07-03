# First-Run Setup and Account Source

## First-Run Setup

Before creating or running a recurring automation, ask for and record local configuration. Do not commit this configuration to GitHub.

Required setup values:

- `{account_profile_source}`: where active account profiles live, such as Notion, a local CSV, or a local JSON cache.
- `{seller_central_name_field}`: the profile field used to select the Seller Central account. Recommended field name: `Seller Central Name`.
- `{marketplace_field}`: the profile field used to select the country/marketplace. Recommended field name: `Marketplace`.
- `{daily_update_channel}`: the Slack channel or other destination for parent posts and account comments.
- `{sellersonar_alert_source}`: the Slack channel, dashboard, CSV, or other alert source used for first-pass alert triage.
- `{follow_up_task_database}`: optional task database or tracker for follow-up work.
- `{default_task_type}`: optional task type for follow-ups, such as `Troubleshooting`.
- `{daily_runner}`: the person who works the daily action queue and is the default owner of every follow-up task. Record their chat member ID and task-system person ID so mentions and assignments resolve correctly.
- `{escalation_owner}`: the person who receives true escalations only. Record their chat member ID and task-system person ID. Mention them only on escalation lines, never on clean runs.
- `{supervisor}`: optional strategic supervisor who receives a weekly digest instead of daily output. Record their chat member ID.
- `{findings_ledger_path}`: local path of the private findings ledger JSON, stored next to the automation, never in the repo or GitHub.
- `{preferred_browser}`: the operator's locally saved browser preference for all live runs - the built-in in-app browser, or a Chromium browser connected through the browser extension (such as Chrome or Brave). The non-preferred approved browser is the fallback.
- `{schedule}` and `{timezone}`: optional local recurring automation schedule.

Ask which accounts and marketplaces should run before creating a local automation. Account names, marketplace lists, channel IDs, Notion IDs, assignees, schedules, and local paths are runtime configuration, not source-controlled skill content.

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
- Show the country/region in all Slack parent and account-comment output.
- Do not use or display `Fulfillment Method` in the daily account-health workflow.
- Skip profiles missing `{seller_central_name_field}` or `{marketplace_field}` and list them under blockers.

# Amazon Agent Client Profiles

The private, Obsidian-synced agency vault is the shared source of truth for durable operational client context. Amazon Agent reads it directly and does not keep a local copy of profile data.

## Canonical Source

Each client has one file:

```text
Clients/{Name}/Amazon Ops.md
```

The note contains exactly one fenced JSON block with `schema_version: 1`, a canonical `client_slug`, and one or more brand-marketplace objects in `profiles`. The surrounding Markdown explains the editing contract to teammates.

Resolve the vault through either:

- `AMAZON_AGENT_TEAM_VAULT`
- The first non-comment line in `_local/team-vault-path.txt`

The environment variable or pointer is machine-local configuration. It stores only the path to the synced vault, not profile facts.

## Core Fields

- `profile_key`, `profile_name`, aliases, status, and marketplace
- Seller Central and Amazon Ads account labels
- Stakeholders, website, listing or storefront URL, and Slack destination
- Fulfillment method, goal/stage, situation, and recurring workflow notes
- Production and shipping timing plus ship-from context
- Reshipment target days, lead-time days, Amazon booking buffer, scaling multiplier, and minimum-volume threshold
- Safety notes and evidence links

Never store credentials, passwords, login emails, cookies, tokens, payment details, tax IDs, private keys, street-level warehouse addresses, browser sessions, raw reports, queues, or machine state.

## Lookup And Validation

```bash
node tools/client-profiles/find-client-profile.mjs alphainfuse
node tools/client-profiles/find-client-profile.mjs "Shaperluv US"
node tools/client-profiles/find-client-profile.mjs --validate
```

For an enabled reshipment profile, the lookup derives:

```text
effective_coverage_days = target_stock_days + lead_time_days + amazon_booking_buffer_days
```

Do not save the derived total in the vault. The validator rejects it so a stale total cannot disagree with its components.

## Agent Lookup Order

1. Read the matching team-vault `Amazon Ops.md` through the lookup tool.
2. Read the client hub for broader durable context.
3. Use Notion for live tasks and meeting notes.
4. Use Slack for recent events and evidence.
5. Use Amazon docs and MAG SOPs for workflow rules and procedures.

If a value conflicts with the user's current evidence, do not silently choose one. In a human-supervised session, update the shared profile with a source link and validate it. Unattended runs must not edit profiles.

# Client Profile Tools

These helpers read shared Amazon operational profiles directly from the team's Obsidian-synced agency vault.

Canonical files:

```text
Clients/{Name}/Amazon Ops.md
```

Resolve the vault with `AMAZON_AGENT_TEAM_VAULT` or the first non-comment line in `_local/team-vault-path.txt`. The pointer is local configuration; the profile data is not copied into this repository.

## Lookup

```bash
node tools/client-profiles/find-client-profile.mjs alphainfuse
node tools/client-profiles/find-client-profile.mjs "Shaperluv US"
node tools/client-profiles/find-client-profile.mjs --validate
```

The lookup parses the fenced JSON block in every `Amazon Ops.md` file. For reshipment-enabled profiles it derives `effective_coverage_days` from target stock days, lead time, and Amazon booking buffer.

Brand-wide work ownership is returned on every matching marketplace profile from the optional root-level `work_owners` object. `design` and `ads` each hold a `primary` and `backup` employee name (or `null`), plus a shared `confirmed_on` date and optional note. Keeping this at the document root avoids copying the same people across every marketplace.

The validator rejects duplicate keys, malformed profiles, malformed work-owner assignments, stored derived totals, sensitive field names, and email addresses. Profile files must not contain credentials, login emails, tokens, cookies, or machine state.

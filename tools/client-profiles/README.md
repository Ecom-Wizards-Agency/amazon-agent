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

The validator rejects duplicate keys, malformed profiles, stored derived totals, sensitive field names, and email addresses. Profile files must not contain credentials, login emails, tokens, cookies, or machine state.

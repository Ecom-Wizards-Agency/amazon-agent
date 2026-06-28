# Client Profile Tools

These helpers work with the local generated cache for Amazon Agent Ops Profiles.

Source of truth:

- Notion database: <notion-database-url>
- Data source: `<notion-data-source>`

Local cache:

```text
_local/client-profiles/profiles.json
```

The cache is ignored by Git and should be regenerated from Notion when client facts change.

## Lookup

```bash
node tools/client-profiles/find-client-profile.mjs acme
node tools/client-profiles/find-client-profile.mjs "Example Brand DE"
```

The lookup script reads local cache only. If it cannot find a profile, check Notion before making client-specific assumptions.

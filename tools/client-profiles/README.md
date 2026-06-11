# Client Profile Tools

These helpers work with the local generated cache for Amazon Agent Ops Profiles.

Source of truth:

- Notion database: https://www.notion.so/b42e52380b874dd5be7c0fba6c0d017e
- Data source: `collection://8e2f0901-3b8e-44ac-8fd6-464f834bd824`

Local cache:

```text
_local/client-profiles/profiles.json
```

The cache is ignored by Git and should be regenerated from Notion when client facts change.

## Lookup

```bash
node tools/client-profiles/find-client-profile.mjs swissker
node tools/client-profiles/find-client-profile.mjs "Piercing XXL DE"
```

The lookup script reads local cache only. If it cannot find a profile, check Notion before making client-specific assumptions.

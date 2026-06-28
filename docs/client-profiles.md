# Amazon Agent Client Profiles

Notion is the shared source of truth for operational client context. Local files are only generated cache for fast agent lookup.

## Notion Source

- Database: Amazon Agent Ops Profiles
- Database URL: <notion-database-url>
- Data source: `<notion-data-source>`
- Parent: Brands
- Linked brand source: Partner Success, `<partner-success-data-source>`

Each ops profile is one brand-marketplace pair, such as `Acme US` or `Example Brand DE`. Keep broad business context in Partner Success. Put agent-operational Amazon details in Amazon Agent Ops Profiles.

## Core Fields

- `Profile Name`
- `Brand`
- `Status`
- `Marketplace`
- `Seller Central Name`
- `Amazon Ads/PPC Name`
- `SellerBoard Email`
- `Main Stakeholders`
- `Website`
- `Live Amazon URL`
- `Fulfillment Method`
- `Production/Shipping Timing`
- `Ship-From Details or Source`
- `Slack Destination`
- `Recurring Workflow Notes`
- `Agent Safety Notes`
- `Local Cache Key`
- `Last Cache Sync`
- `Source Notes`

## Local Cache

Local cache belongs under:

```text
_local/client-profiles/
```

The cache is ignored by Git. It may contain client operational facts pulled from Notion, but it must not contain secrets, passwords, cookies, tokens, payment details, tax IDs, private keys, or browser session data.

Use `_local/client-profiles/profiles.json` as the primary cache file when present. The cache should include:

- Notion database URL and data source ID
- `synced_at`
- `profiles[]`
- Each profile's Notion URL, profile name, local cache key, marketplace, account names, timing notes, workflow notes, and safety notes

## Agent Lookup Order

For client-specific Amazon work:

1. Check `_local/client-profiles/profiles.json`.
2. If the profile is missing or stale, check the Notion `Amazon Agent Ops Profiles` database.
3. Use Partner Success only for broader client/business context.
4. Use Amazon docs and MAG SOPs for current workflow rules and procedure.

Treat local cache as disposable. Notion wins when values conflict.

## Update Flow

The agent should not silently change shared client facts. When it learns a better value, it should draft a proposed update with:

- Profile affected
- Current Notion value
- Proposed replacement
- Evidence/source
- Risk level

A teammate approves the Notion change. Local caches refresh after approval.

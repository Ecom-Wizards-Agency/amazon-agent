# Browser Routing Map

One-page answer to "which browser path does this workflow use". The rule behind the table is in `AGENTS.md` Browser Standard: **if a workflow has a script/CDP runner, use the shared CDP debug Chrome. If it needs eyes or a human-visible UI, it is interactive, and interactive work is Codex's job. If it needs no page at all, use no browser.** Every skill also declares its own path in a standardized `Browser:` line right under its title, enforced by `tools/lint_agent_docs.py`; trust that line when a skill is loaded.

## The Four Paths

| Path | What it is | When |
|---|---|---|
| **CDP debug Chrome** | Dedicated profile `~/.amazon-agent/chrome-debug`, DevTools port 9222 (localhost-only). Launch/reuse: `tools/report-fetcher/launch-chrome-debug.sh`. Logins persist in the profile. | Default for every scripted workflow. Benchmarked ~70x faster per step than driving a browser UI (JS round-trip 0-1 ms; whole jobs run in one call). |
| **Interactive browser (Codex)** | Codex operates the internal browser or the Chrome extension (downloads need the extension + US VPN). Claude hands interactive steps to Codex via the Cross-Agent Handoff unless the operator explicitly asks otherwise. | UI work a script cannot do: clicking, mapping, visual verification, screenshots as evidence. |
| **No browser (MCP)** | DataDive MCP, AdLabs MCP, Notion MCP. | Data that has an API. Always preferred over any browser when it covers the need. |
| **No browser (local)** | Builders and formatters in `tools/`. | File-in/file-out work. |

## Per-Workflow Routing

| Workflow | Skill / command | Path | Runner / route | Notes |
|---|---|---|---|---|
| Seller Central reports (Business, SQP, SCP, TST) | `amazon-reporting` (`/fetch-reports`) | CDP | `tools/report-fetcher/run.mjs` | Fallback: evaluate `fetch-seller-reports.js` in a logged-in tab. |
| POE / Opportunity Explorer exports | `amazon-opportunity-explorer` | CDP | `tools/opportunity-explorer/run-poe.mjs` | Fallback: evaluate `fetch-poe.js` in a logged-in SC page. |
| Listing copy capture (anchor + competitors) | `amazon-listing-capture` | CDP | `extract-amazon-listing-copy.js` evaluated over `cdp.mjs` | PDPs need no login. Fallback: connected-browser evaluate. |
| DataDive roots / Core MKL / competitors / Rank Radar | `amazon-seo-keyword-workflow` | MCP | `datadive` MCP | No browser. |
| DataDive Expanded 1% MKL | `amazon-seo-keyword-workflow` | Interactive (Codex) | DataDive UI download | The one DataDive file the MCP cannot return. Download via the extension browser. |
| Keyword workbook build + SEO writing | `amazon-seo-keyword-workflow`, `amazon-seo` | Local | `build_keyword_workbook.py` | No browser. |
| Health-claims self-check | `amazon-seo` (`/health-claims-check`) | Local | reference + register checks | Listing text comes from listing capture (CDP) when not already on file. |
| Campaign creation from brief | `amazon-campaign-builder` (`/create-campaigns`) | Local | `tools/amazon-campaign-builder/` | File-only output; any upload is a separate operator-confirmed action. |
| Daily/weekly Amazon Ads performance brief | `amazon-ads-monitor` | No browser (MCP) | `tools/amazon-ads-monitor/` (SP Ads API v3), Notion + Slack MCP for brand-context enrichment and delivery | Read-only; never changes campaigns. Falls back to `--source mock` (PREVIEW) with no credentials. |
| Ad/sales audit data pulls | `amazon-ad-audit` (`/amazon-audit`) | Mixed | SQP + Business Report via CDP report fetcher; ads bulk sheet via Ads console download (Codex interactive) | Workbook + narrative build is local. |
| AdLabs audit | `amazon-adlabs-audit` (`/adlabs-audit`) | MCP | AdLabs MCP | Read-only. No browser. |
| FlatFilePro CSV preparation | `amazon-flatfilepro-compliance` (`/flatfilepro-prepare`) | Local | `prepare_flatfilepro_compliance_csv.py` | Label/package evidence comes from the operator. |
| FlatFilePro upload + column mapping | `amazon-flatfilepro-upload-mapper` (`/flatfilepro-upload`) | Interactive (Codex) | logged-in FlatFilePro session | Human-shaped UI; stop before final apply. |
| Creator Connections (inbox, tracker, replies, campaigns) | `amazon-creator-connections` (`/creator-connections`) | Interactive (Codex) | Campaign Manager → Brand content → Creator connections | No MCP exists. Stop before any send/publish. |
| Account health check | `amazon-account-health-check` | Interactive (Codex) | SC Account Health | Needs `Review details` clicks + screenshot evidence. |
| Support cases, buyer messages, refunds | `amazon-communications` | Interactive (Codex) | SC case log / messaging | Stop before send. |
| Shipments, removals, AWD | `amazon-logistics` | Interactive (Codex) | Send to Amazon flows | Stop before creating/confirming shipments. |
| Inventory planning inputs | `amazon-inventory-planning` | Mixed | fresh SC reports via CDP fetcher where covered; other UI exports Codex interactive | Same-day reports rule applies. |
| Catalog / parentage flat files | `amazon-catalog` | Mixed | template downloads + uploads Codex interactive; file builds local | Stop before upload. |
| Ads console operations (bids, budgets, targeting) | `amazon-ads` | Interactive (Codex) | Ads Campaign Manager | Stop before changes. |
| Troubleshooting / suppressed listings | `amazon-troubleshooting` | Interactive (Codex) | wherever the symptom is | Capture exact error text. |

## Constants Across All Paths

- Account/marketplace verification before task work applies to every path, including the CDP profile.
- Logins: the operator logs in; agents never touch credentials. The CDP profile keeps its own logins (one-time per account).
- One login per Seller Central region; switch marketplaces via the in-app switcher, never by changing the domain.
- Stop-before-risk gates are path-independent: a send/upload/publish needs explicit approval no matter which browser executed the steps.

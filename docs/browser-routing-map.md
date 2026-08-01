# Browser Routing Map

One-page answer to "which browser path does this workflow use". The rule behind the table is in `AGENTS.md` Browser Standard: **if a workflow needs no page at all, use no browser. If it needs the operator's own logged-in session, use the Chrome extension. Otherwise use the shared CDP debug Chrome, whether the work is scripted or interactive.** Every skill also declares its own path in a standardized `Browser:` line right under its title, enforced by `tools/lint_agent_docs.py`; trust that line when a skill is loaded.

Routing is by **session**, not by agent. CDP is not limited to scripted fetches: it dispatches real mouse and key events, screenshots, polls for late elements, uploads files and captures downloads. That was verified on 31.07.2026 (team vault run note `Runs/2026-07-31-runtime-consolidation-test.md`), which is why the old "interactive work belongs to a second agent" split is gone.

## The Four Paths

| Path | What it is | When |
|---|---|---|
| **CDP debug Chrome** | Dedicated profile `~/.amazon-agent/chrome-debug`, DevTools port 9222 (localhost-only). Launch/reuse: `tools/report-fetcher/launch-chrome-debug.sh`. Logins persist in the profile. | Default for everything with a page, scripted or interactive. JS round-trip measured at 0.58 ms, so whole jobs run in one call. |
| **Chrome extension** | Drives the operator's *normal* Chrome with their existing logins. | When the task must run in the operator's own session rather than the debug profile. DataDive is the standing case: the debug profile has no DataDive login and creating one risks displacing the operator's. |
| **No browser (MCP)** | DataDive MCP, AdLabs MCP, Notion MCP. | Data that has an API. Always preferred over any browser when it covers the need. |
| **No browser (local)** | Builders and formatters in `tools/`. | File-in/file-out work. |

The two browser profiles hold independent sessions and do not interfere; both can be logged into different accounts at the same time.

## Per-Workflow Routing

| Workflow | Skill / command | Path | Runner / route | Notes |
|---|---|---|---|---|
| Seller Central reports (Business, SQP, SCP, TST) | `amazon-reporting` (`/fetch-reports`) | CDP | `tools/report-fetcher/run.mjs` | Fallback: evaluate `fetch-seller-reports.js` in a logged-in tab. |
| POE / Opportunity Explorer exports | `amazon-opportunity-explorer` | CDP | `tools/opportunity-explorer/run-poe.mjs` | Fallback: evaluate `fetch-poe.js` in a logged-in SC page. |
| Listing copy capture (anchor + competitors) | `amazon-listing-capture` | CDP | `extract-amazon-listing-copy.js` evaluated over `cdp.mjs` | PDPs need no login. |
| DataDive roots / Core MKL / competitors / Rank Radar | `amazon-seo-keyword-workflow` | MCP | `datadive` MCP | No browser. |
| DataDive full keyword pool (the old "Expanded 1% MKL") | `amazon-seo-keyword-workflow` | Extension | three read-only GETs, merged locally | `/mkl/{id}?includeAsinCatalog=true` + `/outlier/{id}` + `/residue-kw-list/{id}`, then filter `relevancy` locally. No settings change, no quota. See the skill. |
| Keyword workbook build + SEO writing | `amazon-seo-keyword-workflow`, `amazon-seo` | Local | `build_keyword_workbook.py` | No browser. |
| Health-claims self-check | `amazon-seo` (`/health-claims-check`) | Local | reference + register checks | Listing text comes from listing capture (CDP) when not already on file. |
| Campaign creation from brief | `amazon-campaign-builder` (`/create-campaigns`) | Local | `tools/amazon-campaign-builder/` | File-only output; any upload is a separate operator-confirmed action. |
| Daily/weekly Amazon Ads performance brief | `amazon-ads-monitor` | No browser (MCP) | `tools/amazon-ads-monitor/` (SP Ads API v3), Notion + Slack MCP | Read-only; never changes campaigns. Falls back to `--source mock` (PREVIEW) with no credentials. |
| Ad/sales audit | `amazon-audit` (`/amazon-audit`, `/adlabs-audit`) | Mixed | AdLabs + DataDive MCP on the managed path; SQP + Business Report + ads bulk over CDP on the prospect path; live creative capture over CDP on both | Read-only. Workbook + narrative build is local. |
| FlatFilePro CSV preparation | `amazon-flatfilepro-prep` (`/flatfilepro-prepare`) | Local | `prepare_flatfilepro_upload.py` | Label/package evidence comes from the operator. |
| FlatFilePro upload + column mapping | `amazon-flatfilepro-upload-mapper` (`/flatfilepro-upload`) | CDP | logged-in FlatFilePro session | Hidden native file input; MUI autocomplete mapping. Stop before **Update Listings**. |
| Creator Connections (inbox, tracker, replies, campaigns) | `amazon-creator-connections` (`/creator-connections`) | CDP | Campaign Manager → Brand content → Creator connections | No MCP exists. Must drain the infinite-scroll thread list. Stop before any send/publish. |
| Account health check | `amazon-account-health-check` | CDP | SC Account Health | Needs `Review details` clicks + screenshot evidence. |
| Weekly/monthly operational checks | `amazon-operations-review` (`/operational-checks`) | Mixed | Seller Central + SellerSonar; Google Drive, Slack, and task connectors | Dormant until explicit setup and activation; shipment checks are exception-only and never submit reconciliation. |
| Support cases, buyer messages, refunds | `amazon-communications` | CDP | SC case log / messaging | Stop before send. |
| Shipments, removals, AWD | `amazon-logistics` | CDP | Send to Amazon flows | Stop before creating/confirming shipments. |
| Inventory planning inputs | `amazon-inventory-planning` | Mixed | fresh SC reports via CDP fetcher where covered; other UI exports over CDP | Same-day reports rule applies. |
| Catalog / parentage flat files | `amazon-catalog` | Mixed | template downloads + uploads over CDP; file builds local | Stop before upload. |
| Ads console operations (bids, budgets, targeting) | `amazon-ads` | CDP | Ads Campaign Manager | Stop before changes. |
| Troubleshooting / suppressed listings | `amazon-troubleshooting` | CDP | wherever the symptom is | Capture exact error text. |
| Serious regulated-product suppression appeal packs | `amazon-regulated-product-suppression-appeals` | Mixed | first-party policy research in Chrome; pack generation and validation local | Victor signoff required; submission remains separate. |

## Constants Across All Paths

- Account/marketplace verification before task work applies to every path, including the CDP profile.
- Logins: the operator logs in; agents never touch credentials. The CDP profile keeps its own logins (one-time per account).
- One login per Seller Central region; switch marketplaces via the in-app switcher, never by changing the domain.
- Stop-before-risk gates are path-independent: a send/upload/publish needs explicit approval no matter which browser executed the steps.
- No VPN is required. The old "US VPN" rule came from the Codex Chrome plugin, not from Amazon (verified 31.07.2026 running US Seller Central and Ads with egress in Seoul, unchallenged).

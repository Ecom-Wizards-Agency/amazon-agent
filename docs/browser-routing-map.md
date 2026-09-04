# Browser Routing Map

One-page answer to "which browser path does this workflow use". The rule behind the table is in `AGENTS.md` Browser Standard: **if a workflow needs no page at all, use no browser. Otherwise use the shared CDP debug Chrome, whether the work is scripted or interactive. Use the Chrome extension only for an explicit extension-only dependency or operator request.** Every skill also declares its own path in a standardized `Browser:` line right under its title, enforced by `tools/lint_agent_docs.py`; trust that line when a skill is loaded.

Routing is by **session**, not by agent. CDP is not limited to scripted fetches: it dispatches real mouse and key events, screenshots, polls for late elements, uploads files and captures downloads. That was verified on 31.07.2026 (team vault run note `Runs/2026-07-31-runtime-consolidation-test.md`), which is why the old "interactive work belongs to a second agent" split is gone.

Port 9222 is the default for Amazon Agent browser work. Port 9223 is the separate
Wizards AI read browser. The T3 Code in-app browser is explicit-only, never a
silent fallback, and is unsuitable when a task depends on the managed profile,
brokered login, or local upload/download handling.

## The Four Paths

| Path | What it is | When |
|---|---|---|
| **CDP debug Chrome** | Port 9222 uses `~/.amazon-agent/chrome-debug`; port 9223 uses the separate Wizards AI profile. Both are localhost-only and controlled by `browserctl`. The standard preset is headless; Evo X1 keeps both headed. | Port 9222 is the normal default. Port 9223 is for Wizards AI read workflows. Mode changes require an explicit `browserctl restart` reason. |
| **Chrome extension** | Drives the operator's *normal* Chrome with their existing logins and extensions. | Only when the required action depends on extension transport, the managed profile lacks the required session, or the operator explicitly requests it. A Data Dive extension action injected into an Amazon retail page is the standing case; DataDive web app work on Evo X1 is not. |
| **No browser (MCP)** | DataDive MCP, AdLabs MCP, Notion MCP. | Data that has an API. Always preferred over any browser when it covers the need. |
| **No browser (local)** | Builders and formatters in `tools/`. | File-in/file-out work. |

On machines with separate profiles, the two hold independent sessions and do not interfere; both can be logged into different accounts at the same time. On the Linux primary (since 25.08.2026) `~/.amazon-agent/chrome-debug` is a symlink to the operator profile `~/.config/google-chrome-amazon-operator`: one merged profile holding Seller Central, DataDive, and the Data Dive extension. Routing by session still applies, but CDP work on that machine runs inside the operator's live session.

## Per-Workflow Routing

| Workflow | Skill / command | Path | Runner / route | Notes |
|---|---|---|---|---|
| Seller Central reports (Business, SQP, SCP, TST) | `amazon-reporting` (`/fetch-reports`) | CDP | `tools/report-fetcher/run.mjs` | Fallback: evaluate `fetch-seller-reports.js` in a logged-in tab. |
| POE / Opportunity Explorer exports | `amazon-opportunity-explorer` | CDP | `tools/opportunity-explorer/run-poe.mjs` | Fallback: evaluate `fetch-poe.js` in a logged-in SC page. |
| Listing copy capture (anchor + competitors) | `amazon-listing-capture` | CDP | `extract-amazon-listing-copy.js` evaluated over `cdp.mjs` | PDPs need no login. |
| Brand surveillance and suspected-product takedown tracking | `tools/amazon-brand-surveillance/monitor.mjs` | CDP | Shared policy-configured port-9222 browser; leased background PDP and search tabs | Public pages need no login. Read-only; never files Brand Registry reports. |
| DataDive roots / Core MKL / competitors / Rank Radar | `amazon-seo` | MCP | `datadive` MCP | No browser. |
| DataDive full keyword pool (the old "Expanded 1% MKL") | `amazon-seo` | CDP (9222) | three read-only GETs in the logged-in DataDive page, merged locally | `/mkl/{id}?includeAsinCatalog=true` + `/outlier/{id}` + `/residue-kw-list/{id}`, then filter `relevancy` locally. No settings change, no quota. See the skill. |
| Data Dive extension actions on Amazon retail pages | `amazon-seo` | Extension | Data Dive extension UI | Use only for an extension-only ASIN-tray or dive-creation action. DataDive app navigation, downloads, and screenshots remain on CDP 9222 on Evo X1. |
| Keyword workbook build + SEO writing | `amazon-seo` | Local | `build_keyword_workbook.py` | Keyword inputs use the skill's MCP and browser routes; the build itself is local. |
| Health-claims self-check | `amazon-seo` (`/health-claims-check`) | Local | reference + register checks | Listing text comes from listing capture (CDP) when not already on file. |
| Campaign creation from brief | `amazon-sponsored-products-bulk-files` (`/create-campaigns`) | Local | `tools/amazon-campaign-builder/` | File-only output; any upload is a separate operator-confirmed action. |
| Amazon Marketing Cloud SQL and audiences | `amazon-amc` | No browser (MCP) | AdLabs AMC plus `tools/amazon-amc/validate_sql.py` | Draft and validation are read-only. Runs, schedules, audiences, updates, and deletions keep separate approval gates. |
| Hourly ads analysis and dayparting | `amazon-dayparting` | Mixed | `tools/amazon-dayparting/analyze_dayparting.py`; AdLabs MCP for schedules; CDP only for an hourly report download | Analysis produces a proposed 7 by 24 grid only. Dry run and explicit approval precede every schedule or assignment write. |
| Daily/weekly Amazon Ads performance brief | `amazon-ads-performance-briefs` | No browser (MCP) | `tools/amazon-ads-monitor/` (SP Ads API v3), Notion + Slack MCP | Read-only; never changes campaigns. Falls back to `--source mock` (PREVIEW) with no credentials. |
| Ad/sales audit | `amazon-audit` (`/amazon-audit`) | Mixed | First-time prospect: SQP + Business Report + ads bulk over CDP, never AdLabs. Monthly/actions: AdLabs + DataDive MCP only. Live creative capture uses CDP on both paths. | Read-only. Actions hand preview/apply work to `amazon-ppc-weekly-management`; workbook + narrative build is local. |
| 90-day Amazon launch strategy | `amazon-launch-strategy` | Mixed | Local deterministic 13-week model and branded builders; narrow Drive, Notion, Slack, DataDive, or CDP reads only when fresh launch inputs require them | Read-only. Historical diagnosis routes to `amazon-audit`; campaign, PPC, catalog, shipment, and communication execution remain separate. |
| Amazon client onboarding | `amazon-client-onboarding` | Mixed | Seller Central and Ads over CDP on port 9222 through the task-tab controller; Notion through its connector; manifest validation local | Access preflight and assessment are read-only. Account changes require the current fingerprinted approval; independent inventory verification gates signoff. |
| Amazon client offboarding handover | `amazon-client-offboarding` | Mixed | Read-only evidence from Amazon reports/UI, AdLabs/DataDive and client systems; local branded Doc/workbook builder; native Drive conversion | No account mutation, folder creation, message, or campaign upload. Unsupported areas are disclosed and omitted. |
| FlatFilePro `.xlsx` preparation | `amazon-flatfilepro` (`/flatfilepro-prepare`) | Local | `prepare_flatfilepro_upload.py` | Label/package evidence comes from the operator. |
| FlatFilePro upload + column mapping | `amazon-flatfilepro` (`/flatfilepro-upload`) | CDP | logged-in FlatFilePro session | Hidden native file input; MUI autocomplete mapping. Stop before **Update Listings**. |
| Creator Connections (inbox, tracker, replies, campaigns) | `amazon-creator-connections` (`/creator-connections`) | CDP | Campaign Manager → Brand content → Creator connections | No MCP exists. Must drain the infinite-scroll thread list. Stop before any send/publish. |
| Account health check | `amazon-account-health-check` | CDP | SC Account Health | Needs `Review details` clicks + screenshot evidence. |
| Weekly/monthly operational checks | `amazon-operational-checks` (`/operational-checks`) | Mixed | Seller Central; Google Drive, Slack, and task connectors. Fee, dimension and weight findings come from the precomputed Keepa market-signals state file, with no browser | Dormant until explicit setup and activation; shipment checks are exception-only and never submit reconciliation. |
| Support cases, buyer messages, refunds | `amazon-communications` | CDP | SC case log / messaging | Stop before send. |
| Shipments, removals, AWD | `amazon-logistics` | CDP | Send to Amazon flows | Exact approval is required before creating/confirming shipments. |
| Inventory planning inputs | `amazon-fba-inventory-planning` | Mixed | fresh SC reports via CDP fetcher where covered; other UI exports over CDP | Same-day reports rule applies. |
| Catalog / parentage flat files | `amazon-catalog` | Mixed | template downloads + uploads over CDP; file builds local | Exact approval is required before upload. |
| Ads console operations (bids, budgets, targeting) | `amazon-ads-console` | CDP | Ads Campaign Manager | Stop before changes. |
| Troubleshooting / suppressed listings | `amazon-troubleshooting` | CDP | wherever the symptom is | Capture exact error text. |
| Serious regulated-product suppression appeal packs | `amazon-regulated-product-appeals` | Mixed | first-party policy research in Chrome; pack generation and validation local | Victor signoff required; submission remains separate. |

## Constants Across All Paths

- Account/marketplace verification before task work applies to every path, including the CDP profile.
- Browser mode comes from the machine policy. Evo X1 keeps ports 9222 and 9223 headed; `ensureChrome()` never changes a running mode.
- Browser priority is port 9222 by default, port 9223 for Wizards AI, and T3 Code in-app only by explicit choice.
- US, DE, and AUS anchors are maintained additively on both Evo X1 ports. A newly discovered unregistered tab receives a two-hour inspection lease before inactivity can authorize cleanup; standard presets continue to preserve unknown tabs.
- Anchors are home-page reserves, never workflow tabs. One stable task ID owns
  one primary target across steps and retries. Extra targets require a named
  slot, a site-created popup, or an explicit operator request.
- Seller Central and FlatFilePro logins may use the exact-origin 1Password broker on ports 9222 and 9223. Human challenges remain operator-only, and no credential enters agent output.
- One login per Seller Central region; switch marketplaces via the in-app switcher, never by changing the domain.
- Stop-before-risk gates are path-independent: a send/upload/publish needs explicit approval no matter which browser executed the steps.
- New local downloads and intermediate files are registered by exact path. The handoff lists their disposition and eligibility date; only unclassified or blocked files need approval.
- No VPN is required. The old "US VPN" rule came from the Codex Chrome plugin, not from Amazon (verified 31.07.2026 running US Seller Central and Ads with egress in Seoul, unchallenged).

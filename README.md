# Amazon Agent

Amazon Agent is Victor's local runtime workspace for operating Amazon workflows with a lightweight source structure. It combines first-party Amazon help captures, Ecom Wizards MAG SOP markdown, and focused Amazon skills for Seller Central, Amazon Ads, Creator Connections, reporting, account health, FBA shipment workflows, troubleshooting, and bulk-file preparation.

## How To Use

Start with `agent.md`. It is the source of truth for assistant behavior, routing, library search order, Chrome browser checkpoints, evidence capture, and stop-before-risk rules.

For most work:

1. Classify the workflow: Seller Central, Amazon Ads, Creator Connections, MAG SOP procedure, reporting, logistics, catalog, inventory, or troubleshooting.
2. Search the local markdown/runtime libraries first.
3. Use Google Chrome with the logged-in Amazon session when browser operation is needed.
4. Stop before externally visible or risky actions unless Victor explicitly approves the specific action.

This project uses one main Codex operator with specialist skills, not separate permanent specialist agents. The dispatcher skill routes work into playbooks like `amazon-seo`, `amazon-catalog`, `amazon-ads`, `amazon-inventory-planning`, `amazon-opportunity-explorer`, and `amazon-communications`.

For inventory/reshipment work, useful trigger phrases are `Weekly FBA Inventory Overview`, `reshipment planning`, `FBA inventory planning`, and `inventory overview`.

For Product Opportunity Explorer work, useful trigger phrases are `Product Opportunity Explorer`, `Opportunity Explorer`, `OEI`, `POE`, `Niche Scout`, `amazon-image-strategy`, and `oei-product-strategy`.

The routing helper can search the local Amazon libraries:

```bash
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "send to amazon shipment create fba shipment" --library mag --limit 5
```

## GitHub Repo

Canonical GitHub repo:

`https://github.com/Ecom-Wizards-Agency/amazon-agent`

The local project should stay aligned with the GitHub repo's lightweight runtime/source structure:

- `AGENTS.md`
- `agent.md`
- `skills/`
- `Amazon Seller Help/`
- `Amazon Ads Help/`
- `Advertising Help After Login/`
- `MAG SOPs/` as markdown-only SOPs
- `docs/`

## Visual MAG SOP Archive

The complete visual MAG SOP archive lives outside the GitHub/runtime project. Victor's current local placeholder path is:

`/Users/victoruhl/Documents/pCloud/Amazon Agent/MAG SOPs`

Use local/GitHub markdown SOPs first for search and routing. Use the pCloud visual archive only when visual confirmation, screenshots, GIFs, or layout references are needed.

Expected pCloud visual archive check:

- 535 Markdown files
- 3,621 assets in `assets/`
- 0 missing local image references

The pCloud folder must be locally available when visual SOPs are needed. This path is user-specific: each team member should download or sync the shared pCloud archive locally and point their setup to their own local path. Do not commit the archive or any personal sync folder into GitHub.

## Opportunity Explorer Extraction

The Product Opportunity Explorer workflow uses repo-native scripts instead of a Chrome extension:

- `tools/opportunity-explorer/extract-opportunity-explorer.js`
- `tools/opportunity-explorer/format-opportunity-explorer-export.mjs`

The scripts scrape the visible Product Opportunity Explorer page in the logged-in Chrome session and save structured JSON plus Markdown for image strategy, product strategy, SEO, and Rufus/Alexa AI workflows.

The original Chrome extension remains in pCloud only as historical/source reference during transition. Once the script is tested, it is not needed as part of the runtime workflow.

## What Does Not Belong In GitHub

Do not commit heavy or local work artifacts to the GitHub repo, including:

- Images and GIFs
- Zip files
- `.final-build/`
- Generated outputs
- Evidence screenshots
- Review tracking files
- Downloads and temporary files

Keep those in pCloud or ignored local-only folders. New work should use lowercase `output/`; uppercase `Output/` remains ignored only as a legacy alias.

## Local Artifact Folders

The base local artifact folders are present after clone through `.gitkeep` files, but real files inside them are ignored and must not sync to GitHub.

Use an ongoing client-first structure for generated work:

```text
output/{client-or-brand}/{workflow}/
downloads/{client-or-brand}/{source}/
evidence/{client-or-brand}/{workflow}/
output/{client-or-brand}/review-management/
```

Dates belong in filenames, not folder names.

Examples:

```text
output/swissker/seo/2026-05-21_keyword-research.md
downloads/swissker/business-reports/2026-05-21_sales-traffic.csv
evidence/swissker/account-check/2026-05-21_account-health.png
output/swissker/review-management/reviews.csv
```

Controlled workflow names:

- `seo`
- `opportunity-data`
- `ads`
- `reporting`
- `inventory`
- `catalog`
- `account-check`
- `support-prep`

Use `output/` for generated analysis and deliverables, `evidence/` for screenshots/UI proof, and `downloads/` for raw Amazon exports before processing. Review management is ongoing, so the operator who starts it should update the same client folder until the workflow is closed. `review-tracking/` remains ignored only as a legacy local folder for old files. If a workflow needs local context, put `README.md` or `operator-note.md` inside the relevant workflow folder. Use Notion for ongoing team status.

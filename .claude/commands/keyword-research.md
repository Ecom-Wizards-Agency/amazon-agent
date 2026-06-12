---
description: Run an Amazon SEO keyword research workbook (DataDive + POE → styled XLSX)
argument-hint: "[brand-product-market] — new run each time, e.g. acme-fiberpowder-it"
---

# Keyword Research

Drive the end-to-end Amazon SEO keyword workbook workflow. Do not duplicate logic here — route into the existing skill and builder.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm the brief — your FIRST action is to ask for it.** Before reading files, scaffolding, or running anything, collect the brief from the user with a single AskUserQuestion (one question per required field, presented as fields they fill in). Only skip a field that `$ARGUMENTS` or the conversation already supplies — never guess, and never pre-fill examples from a previous client (e.g. don't show Sheko as the placeholder for a new product).

   **Required (only the user can give these):**
   - **Brand / client**
   - **Marketplace** (e.g. amazon.it / Italy)
   - **Product** (full product name)
   - **DataDive niche** (URL or ID)
   - **Anchor ASIN** — must be a DataDive-tracked column in the niche, or available via the `datadive` MCP (`get_niche_keywords`) so its rank column can be injected

   **Optional (sensible defaults if unspecified — state the default you used):**
   - Seller Central account (default: same as the client's other runs)
   - PPC / Campaign Structure tab (default: skip — SEO only)
   - Pack size / listing status (else captured from the listing reference)

   Everything else (DataDive CSVs, POE exports, competitor + anchor listing copy) is gathered by Codex via the connected browser — not something the user hand-provides.

2. **Load the workflow.** Use the `amazon-seo-keyword-workflow` skill as the source of truth for load order, data inputs, workbook rules, and QA gates. Pull in `amazon-seo` (writing/compliance), `amazon-opportunity-explorer` (POE/OEI), and `amazon-listing-capture` (live title/bullets/link for anchor + competitors) as that skill directs.

3. **Resolve the config — always scaffold a new product/client.** Every run is a new product/client, so don't offer or auto-pick an existing `config.*.json`. Using the brief from step 1, follow `tools/amazon-seo-keyword-workbook/NEW-CLIENT.md` to scaffold a fresh `config.<brand>-<product>-<market>.json` (from `config.TEMPLATE.json`) plus a matching `seo_content.<brand>-<market>.json` (copied from an existing `seo_content.*.json`). The only exception: if `$ARGUMENTS` explicitly names an existing config to **continue an in-progress run**, reuse `tools/amazon-seo-keyword-workbook/config.<that>.json` instead of scaffolding.

4. **Preflight.** Run the builder with `--preflight`:
   ```bash
   .venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
     --config tools/amazon-seo-keyword-workbook/config.<client>.json --preflight
   ```
   If browser/UI inputs are missing, it prints a copy-ready Codex task (DataDive UI CSVs, POE exports, and the anchor+competitor listing capture). **Stop and hand that to Codex** — Claude writes SEO content and runs the build; Codex gathers the connected-browser inputs to the contract paths. Never substitute the `30%` file for a missing `1%` Expanded MKL. If the anchor isn't a tracked column in the exported MKL, inject its rank column from the `datadive` MCP (`get_niche_keywords`).

5. **Build + QA.** Once inputs are present, run the builder without `--preflight` and require every QA gate in the skill to pass (Core/Expanded row counts match CSVs, distinct source paths, DataDive metadata not placeholder, Never-Ever one-word rows, POE tabs current-source, stale-data guard clean, style preserved). Fix any FAIL before delivery.

6. **Deliver + handoff.** Review the `.xlsx`, then copy **only the final Excel** to the client's Google Drive run-folder `/Users/victoruhl/Library/CloudStorage/GoogleDrive-victor@ecomwizards.agency/Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/<Run Folder>/` and verify a byte-identical MD5. **Google Drive only — do NOT copy to pCloud** (the file becomes a Google Sheet there anyway). POE/DataDive raw files + the manifest stay out (embedded in the sheet / kept local). Surface the auto-generated manifest, Obsidian handoff note, and copy-ready Claude/Codex prompt.

Follow the connected-browser checkpoint, evidence, and stop-before-risk rules from `agent.md` throughout.

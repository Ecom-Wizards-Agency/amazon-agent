---
description: Run an Amazon SEO keyword research workbook (DataDive + POE → styled XLSX)
argument-hint: "[client-product-market | \"new\"] — e.g. sheko-ballastpulver-it"
---

# Keyword Research

Drive the end-to-end Amazon SEO keyword workbook workflow. Do not duplicate logic here — route into the existing skill and builder.

The user's target is: **$ARGUMENTS**

## Steps

1. **Load the workflow.** Use the `amazon-seo-keyword-workflow` skill as the source of truth for load order, data inputs, workbook rules, and QA gates. Pull in `amazon-seo` (writing/compliance) and `amazon-opportunity-explorer` (POE/OEI) as that skill directs.

2. **Resolve the config.**
   - If `$ARGUMENTS` names an existing client/product/market, use `tools/amazon-seo-keyword-workbook/config.<that>.json`.
   - If `$ARGUMENTS` is empty, list the available `config.*.json` files (excluding `config.TEMPLATE.json`) and ask which client to run.
   - If `$ARGUMENTS` is `new` (or no config exists yet), follow `tools/amazon-seo-keyword-workbook/NEW-CLIENT.md` to scaffold a config + SEO content file from the templates first.

3. **Preflight.** Run the builder with `--preflight`:
   ```bash
   .venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
     --config tools/amazon-seo-keyword-workbook/config.<client>.json --preflight
   ```
   If browser/UI inputs are missing, it prints a copy-ready Codex task. **Stop and hand that to Codex** — Claude writes SEO content and runs the build; Codex gathers the connected-browser DataDive + POE inputs to the contract paths. Never substitute the `30%` file for a missing `1%` Expanded MKL.

4. **Build + QA.** Once inputs are present, run the builder without `--preflight` and require every QA gate in the skill to pass (Core/Expanded row counts match CSVs, distinct source paths, DataDive metadata not placeholder, Never-Ever one-word rows, POE tabs current-source, stale-data guard clean, style preserved). Fix any FAIL before delivery.

5. **Deliver + handoff.** Review the `.xlsx`, copy to the client Drive folder, and surface the auto-generated manifest, Obsidian handoff note, and copy-ready Claude/Codex prompt.

Follow the connected-browser checkpoint, evidence, and stop-before-risk rules from `agent.md` throughout.

---
description: Run an Amazon SEO keyword research workbook (DataDive + POE → styled XLSX)
argument-hint: "[brand-product-market] (new run each time, e.g. acme-fiberpowder-it)"
---

# Keyword Research

Drive the end-to-end Amazon SEO keyword workbook workflow. Do not duplicate logic here. Route into the existing skill and builder.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm the brief. Your FIRST action is to ask for it.** Before reading files, scaffolding, or running anything, collect the brief from the user with a single AskUserQuestion (one question per required field, presented as fields they fill in). Only skip a field that `$ARGUMENTS` or the conversation already supplies. Never guess, and never pre-fill examples from a previous client (e.g. don't carry a prior client's brand over as the placeholder for a new product).

   **Required (only the user can give these):**
   - **Brand / client**
   - **Marketplace** (e.g. amazon.it / Italy)
   - **DataDive niche** (URL or ID)
   - **Anchor ASIN**: must be a DataDive-tracked column in the niche, or available via the `datadive` MCP (`get_niche_keywords`) so its rank column can be injected

   **Do NOT ask for the Product. Derive it, then confirm.** Once the niche + anchor ASIN are known the product is derivable, so it is not a question. After the required fields are in, resolve the product from the DataDive niche label (`list_niches` → `nicheLabel` / `heroKeyword`) plus the anchor ASIN's PDP (via the listing capture), then **show the derived product name back to the user for a one-line yes/no** before scaffolding. Keep the safety check: a terse niche label ("manuka cream") is not a full product name, and one niche can contain several of the client's own ASINs (or multiple forms / size-variants under the given anchors). So confirm form and variant grouping rather than assuming. If the derivation is ambiguous, ask a single targeted follow-up.

   **Optional (sensible defaults if unspecified; state the default you used):**
   - Seller Central account (default: same as the client's other runs)
   - PPC / Campaign Structure tab (default: skip, SEO only)
   - Pack size / listing status (else captured from the listing reference)

   Everything else (DataDive CSVs, POE exports, competitor + anchor listing copy) is gathered by Codex via the connected browser, not something the user hand-provides.

2. **Load the workflow.** Use the `amazon-seo-keyword-workflow` skill as the source of truth for load order, data inputs, workbook rules, and QA gates. Pull in `amazon-seo` (writing/compliance), `amazon-opportunity-explorer` (POE/OEI), and `amazon-listing-capture` (live title/bullets/link for anchor + competitors) as that skill directs.

3. **Resolve the config. Always scaffold a new product/client.** Every run is a new product/client, so don't offer or auto-pick an existing `config.*.json`. Using the brief from step 1, follow `tools/amazon-seo-keyword-workbook/NEW-CLIENT.md` to scaffold a fresh `config.<brand>-<product>-<market>.json` (from `config.TEMPLATE.json`) plus a matching `seo_content.<brand>-<market>.json` (copied from an existing `seo_content.*.json`). The only exception: if `$ARGUMENTS` explicitly names an existing config to **continue an in-progress run**, reuse `tools/amazon-seo-keyword-workbook/config.<that>.json` instead of scaffolding.

4. **Preflight.** Run the builder with `--preflight`:
   ```bash
   .venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
     --config tools/amazon-seo-keyword-workbook/config.<client>.json --preflight
   ```
   If browser/UI inputs are missing, it prints a copy-ready Codex task. **Stop and hand that to Codex.** Claude writes SEO content and runs the build; Codex gathers the connected-browser inputs to the contract paths. Input substitution rules and anchor rank injection live in the skill.

5. **Build + QA.** Once inputs are present, run the builder without `--preflight` and require every QA gate listed in the skill to pass. Fix any FAIL before delivery.

6. **Deliver + handoff.** Review the `.xlsx`, then deliver **only the final Excel** to the client's Google Drive keyword folder per the delivery rules in the skill (Google Drive only, never pCloud; verify a byte-identical MD5). Surface the auto-generated manifest, Obsidian handoff note, and copy-ready Claude/Codex prompt.

Follow the connected-browser checkpoint, evidence, and stop-before-risk rules from `AGENTS.md` throughout.

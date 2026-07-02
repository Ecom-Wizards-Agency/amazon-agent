# New Client — Ad/Sales Audit Onboarding

Checklist to run a fresh audit. No code changes — only a new config.

## 1. Scaffold the config

```bash
cp tools/amazon-ad-audit/config.TEMPLATE.json \
   tools/amazon-ad-audit/config.<client>-<market>.json
```

Fill every `<...>` placeholder:

- **`client`, `date`, `marketplaces`, `amazon_account`, `currency`** — basics. `currency` drives $ vs € formatting.
- **`breakeven_acos`** — the ASSUMPTION (ask for real margin; default a sensible guess and flag it). Drives all red/amber verdicts.
- **`brand_tokens`** — the brand and its real misspellings/transpositions that carry brand intent (e.g. a brand plus its transposed spelling). Do NOT include dictionary words that merely resemble the brand.
- **`competitor_tokens`** — competitor brand names (from the DataDive niche competitors + known rivals). Used for the conquesting bucket.
- **`asin_groups`** — map each product line to its ASINs (matches the SQP file split and Business-Report ASINs). Use `null`/`{}` for an ungrouped single line.
- **`windows`** — ads / business-report / SQP-weeks / DataDive dates for the subtitle + method notes.
- **`datadive_niche`** — the DataDive `nicheId` (from `list_niches`). Leave empty to skip the organic overlay.

## 2. Gather the inputs (preflight-driven)

```bash
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json --preflight
```

- If it prints **WAITING ON CODEX**, paste the emitted block to Codex. Codex downloads the ads bulk `.xlsx`, Business Report `.csv`, and multi-ASIN SQP `.csv`(s) to the exact paths in `inputs{}` (connected browser; file downloads use the @Chrome extension per the Codex download rule), captures evidence + caveats, and stops. Codex does **not** run the builder or write the narrative.
- **Claude** pulls the DataDive niche via MCP (`get_niche_keywords`, `get_niche_competitors`) and saves them to the `datadive_niche_json` / `datadive_competitors_json` paths.
- Re-run `--preflight` until it prints **READY**.

## 3. Build

```bash
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json
```

Produces the master + audit + SQP workbooks and the narrative scaffold under `output/<client-slug>/reporting/`.

## 4. QA

```bash
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json --validate
```

All gates must PASS (spend reconciliation, no >100% ACOS colored green, master tab count). The build also prints a **DATA COMPLETENESS** panel and `--validate` prints soft **WARNINGS** (intent coverage <90%, SQP-revenue gap >20% with the uncovered groups, missing channels, multi-parent ad groups). These don't fail the build — resolve each (download the missing report) or disclose it in the deliverable's Method Notes before shipping.

## 5. Write the narrative

Open the `.md` scaffold — KPIs and tables are pre-filled. Write the prose, Problems, and Growth Levers per `docs/amazon-ad-audit-playbook.md` (operator voice, second person, keep it lean — no 30-day plan / "what can be reached" / "bottom line" unless the config flags them on). Regenerate the `.docx`.

## 6. Deliver

Copy the master `.xlsx` + narrative `.docx` to `delivery.drive_folder` (Google Drive). Optionally convert the master to a native Google Sheet for a shareable link. Verify with the operator before anything goes to a prospect.

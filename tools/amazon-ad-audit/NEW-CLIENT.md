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
- **`comparison_windows`** — when the product is offline or suppressed, keep the required incident
  window separate from the latest four complete weeks it was continuously online. Never blend them.
- **`datadive_niche`** — the DataDive `nicheId` (from `list_niches`). Leave empty to skip the organic overlay.

## 2. Gather the inputs (preflight-driven)

```bash
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json --preflight
```

- Gather every **MISSING BROWSER INPUT** into the exact `inputs{}` paths using the connected browser. Business Report and SQP can also come from `tools/report-fetcher/`; the ads bulk `.xlsx` still comes from the Ads console.
- Gather every **MISSING DATADIVE MCP INPUT** with `get_niche_keywords` and `get_niche_competitors`, saving the raw responses to the printed paths.
- Re-run `--preflight` until it prints **READY**, then continue through build, narrative, QA, and authorized internal delivery. If one capability is unavailable, hand off only its checklist to any capable agent.

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

Open the `.md` scaffold. KPIs and tables are pre-filled. Write the prose, Problems, and Growth Levers per `skills/amazon-audit/references/audit-workflow.md` and `writing-and-delivery.md` (operator voice, second person, keep it lean; no 30-day plan, "what can be reached", or "bottom line" unless the config flags them on). Set `narrative.mode` to `evidence_hybrid` when the operator asks for `same style as UltimaPeak`, `UltimaPeak style`, or `evidence-hybrid`. Capture candidates with `capture_audit_evidence.mjs`, select them with `audit_evidence.py`, and reference selected screenshots inline with `![caption](file.png)` (paths relative to the `.md`). SQP and workbook screenshots are forbidden. Re-run the build to regenerate the branded `.docx`.

### Copy-ready request for the next prospect

```text
/amazon-audit deep. Run a first-time audit for [Brand] in [Market] using the same evidence-hybrid
style as UltimaPeak. The main product is [Product] ([ASIN]). Use [break-even ACOS or "assume X%"]
and verify the claims from [call/date]. Add directional market sizing for [optional products]. If
the listing is offline or suppressed, preserve the latest-four-week incident window and compare it
separately with the latest four complete weeks it was continuously online. Build the branded native
Google Doc and MASTER Google Sheet, but ask before placing or sharing them where the prospect can
see them.
```

## 5b. Branding (agency identity from `_local/branding/` — see BRANDING.md)

The build renders a branded **A4 / Inter** `.docx` (`render_branded.py`) from the narrative `.md`.
- Set `branding.first_time: true` for a **first-time audit** → dark cover page. For a **regular update**, set `false` (no cover) or pass `--no-cover`. `--cover` forces it on.
- `branding.prepared_by` (default: `prepared_by_default` from _local/branding/branding.json) and `cover_subtitle` feed the cover.
- One-time per machine: `python3 tools/amazon-ad-audit/prepare_brand_assets.py` populates the gitignored `brand/` assets (logo + Inter). If they're missing, the build degrades to a plain `.docx` with a WARN.

## 6. Deliver

Deliver both the master `.xlsx` and the branded audit `.docx` to `delivery.drive_folder` with `python3 tools/gdrive-deliver/deliver.py <file> "<drive folder>" --name "<YYYY-MM-DD_Client_Market_Artifact_vN>" --artifact-run <run-id>`, which converts them to a **native Google Sheet** and a **native Google Doc**, verifies both, and retains the local Office files for artifactctl. The prospect gets the Doc link, and can download a PDF from it if they want one. Verify with the operator before anything goes to a prospect.

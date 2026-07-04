---
description: Prepare a narrow FlatFilePro upload CSV from an export + evidence (SKU-keyed, partial update; file-only, upload stays manual)
argument-hint: "[client-market, e.g. acme-de — plus attach/point to the FlatFilePro export]"
---

# FlatFilePro Prepare (upload CSV)

Build a narrow, upload-ready FlatFilePro CSV from a FlatFilePro export + source-of-truth evidence. Do not duplicate logic here — route into the `amazon-flatfilepro-compliance` skill and its `scripts/prepare_flatfilepro_compliance_csv.py`.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm inputs — ask first.** Collect with a single AskUserQuestion, skipping what `$ARGUMENTS`/the conversation already supplies: client/brand · marketplace(s) + account · the **FlatFilePro export** path (per market) · affected ASINs/SKUs · which fields change · the source of truth for the new values (label/PDF for compliance, or the SEO copy for a listing refresh). Never carry a prior client's values.

2. **Load the skill** `amazon-flatfilepro-compliance` as source of truth (field-mapping rules, SKU keying, audit-note format).

3. **Read the export headers FIRST.** The `--changes` `attribute` values must match export headers **verbatim** or the script hard-exits (code 2). Pull exact spellings from the export — e.g. title = `item_name.0.value` or `itemName` (template-dependent); Item Highlights = `title_differentiation.0.value` (single ~125-char field, **not** bullets); bullets = `bullet_point.0.value`…`.4.value`; description = the export's exact header.

4. **Scope note (SEO):** the skill's DEFAULT refuses to touch title/bullets/images/etc. — for an SEO refresh you must **explicitly** put those copy fields in scope. Key on **`sku`**, never ASIN. Update **all** SKU contributions for the same ASIN, including `-1` frontend-controlling variants (same values on both rows). Size/variation tokens are matched per SKU by hand — author each SKU's own title/value in the changes CSV.

5. **Build** — author the `sku,attribute,value` changes CSV, then:
   ```bash
   python3 skills/amazon-flatfilepro-compliance/scripts/prepare_flatfilepro_compliance_csv.py \
     --source <FFP export> --changes <changes.csv> --output <upload.csv>
   ```
   Build **separate CSVs per marketplace** from each market's own export (enum spellings diverge, e.g. DE `Gramm` vs IT `Grammi`/`grammo`).

6. **Deliver** — the `upload.csv` + a per-SKU audit note (included/excluded SKUs, changed fields, manual-review flags). Use **`PartialUpdate`** semantics for SEO-only changes so price/images/parentage are untouched.

7. **Stop.** Uploading is a separate step — hand off to `/flatfilepro-upload` (or the operator/Codex). Never upload, save Seller Central changes, or submit cases as part of this command.

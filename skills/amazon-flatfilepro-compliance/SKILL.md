---
name: amazon-flatfilepro-compliance
description: Use to prepare narrow FlatFilePro upload CSVs, audit files, or validation notes from a FlatFilePro export plus label/package evidence (Account Health, food-safety, and label-vs-detail-page mismatch cases). Trigger on FlatFilePro, Flatfire Pro, flat file, backend export, or category listing report work. The upload itself routes to `amazon-flatfilepro-upload-mapper`.
---

# Amazon FlatFilePro Compliance

Browser: None (local CSV build from export + label evidence).

## Core Rule

Use the physical product label or approved packaging PDF as the source of truth. Use the FlatFilePro export, category listing report, or Amazon template as the source for available headers, current backend values, SKUs, product types, and upload structure.

If required inputs are missing, answer briefly with only what is needed. Typical minimum inputs are:

- FlatFilePro export or Amazon template
- product label, packaging PDF, or clear label images
- affected marketplace(s)
- affected ASINs/SKUs
- Amazon case message when the work is for Account Health or Seller Support

## Workflow

1. Identify the marketplace, ASINs, SKUs, product type, and case issue.
2. Read the export/template headers before deciding which fields can be updated.
3. Compare current backend values against the physical label.
4. Review consistency at ASIN level, but write updates at SKU level, including duplicate contribution SKUs such as `-1` variants when they may control the frontend.
5. Create narrow upload files with only `sku` plus relevant existing FlatFilePro headers. **Default to full-grid output** (`--fill-unchanged` on the script): every included column is filled for every included SKU: the new value where changed, the SKU's current source value otherwise. A mapped-but-empty cell risks clearing a live value at upload time; a cell may only stay empty when the field is also empty in the source. Sparse output (changed cells only) is acceptable only when the operator explicitly wants it.
6. **Complete every touched attribute group** (Amazon error 99022 otherwise, per SKU): when the file touches any member of a grouped attribute, include the whole group's required members in the same file: nutrition macros (`energy`/`protein`/`carbohydrate`/`fat`: value **and** unit), vitamins rows (`nutrient` + `value` + `unit`), any `nutritional_info` touch also requires `serving_quantity` + `serving_unit` (+ `serving_description`), `unit_count.0.value` ↔ `unit_count.0.type.value`, and every weight value with its unit. Source companion values current-export-first, reviewed-baseline-second. See `references/flatfilepro-compliance-rules.md` § Attribute-group completeness.
6. Produce an audit note or workbook showing included SKUs, excluded SKUs, changed fields, unchanged matching values, and manual-review fields.
7. Stop before uploading files, saving Seller Central changes, or submitting cases.

Do not touch title, bullets, images, price, offer, variation, claims, browse node, or unrelated fields unless the user explicitly asks.

## Listing Field Terminology

When the user explicitly asks for listing copy fields, keep these fields separate:

- `title` / `itemName`: the product title only.
- `Item Highlights`: Amazon's short, single-line highlight field. It is not a bullet list. When a FlatFilePro export exposes `title_differentiation.0.value`, treat that as the likely upload header for Item Highlights and keep the value within the requested/Amazon limit, commonly 125 characters.
- `bullet points`: the normal Amazon feature bullets. Use only `bullet_point.*.value` headers for bullets.

Never map Item Highlights into `bullet_point.*.value`, and never split one Item Highlight into multiple bullets. If the export/header mapping is ambiguous, stop and confirm the intended FlatFilePro column before creating the upload CSV.

## Field Policy

Prioritize fields named by Amazon and fields needed for label compliance:

- ingredients
- nutritional information
- safety warnings
- daily dose or serving recommendation
- serving size and servings per container
- shelf life and durability indication
- manufacturer and manufacturer contact information
- item/package/unit weights
- unit count and unit count type
- set name for bundles

Preserve existing values when they already match the label and are not in scope. Overwrite missing, wrong-language, stale, or label-conflicting values only for the targeted fields.

Do not invent a field that is not present in the export/template. If the label has information but no safe target column exists, flag it for manual review instead.

## Nutrition String Policy

Do not fill nutrition string fields by default. Use normal numeric and structured nutrition fields first.

Use string nutrition fields only when:

- Amazon explicitly asks for values in both per-serving and per-100 g/ml form and the template exposes only one structured nutrition block
- the available numeric fields cannot represent required label text safely
- an active compliance case has repeated mismatches and a defensive display field is needed

One past collagen case was an exception because repeated compliance checks required defensive dual-basis nutrition text. Do not generalize that to all supplements.

See `references/nutrition-field-policy.md` before using string fields.

## Outputs

Prefer these outputs:

- audit workbook or CSV with old value vs proposed value
- upload-ready CSV split by product type/template when needed
- validation note with assumptions, source files, excluded rows, and manual-review items

For CSV creation from reviewed changes, use `scripts/prepare_flatfilepro_compliance_csv.py`. Read `references/flatfilepro-compliance-rules.md` before building complex upload files. When reading physical labels or packaging, map label sections to backend fields with `references/label-to-backend-mapping.md`.

After the CSV is created, use `amazon-flatfilepro-upload-mapper` when the operator asks Codex to upload the file in Chrome, match by SKU, map columns in FlatFilePro, or leave the flow ready for the operator's final click. Keep this skill focused on preparing the CSV and audit.

## Communication

When preparing Seller Support or Account Health replies, state what was updated and that it was done via FlatFilePro/flat file only if true. Attach or reference label evidence when Amazon asks for compliant label proof. Do not argue with Amazon in the reply; keep it factual and case-specific.

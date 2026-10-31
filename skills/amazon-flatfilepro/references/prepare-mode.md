# Prepare Mode

Mode browser: None (connector reads and a local build from the export grid and label evidence).

**Scope.** The workbook route is for what the direct update cannot do: relationships and variations, clearing a value, price, offer and stock fields, brand and identifiers, new listings, an attended session without the FlatFilePro connector, and Grimoire or scheduled runs.
Copy, backend terms, structured attributes and MAIN or PT images on an existing
listing go through `references/direct-update-mode.md` instead.

## Upload format: .xlsx, not CSV

**FlatFilePro expects `.xlsx` upload files** (operator, 2026-07-26). Give
`prepare_flatfilepro_upload.py` an `--output` path ending in `.xlsx` and it
writes a workbook; the writer switches on the extension. A `.csv` path still works and
is useful for diffing or eyeballing a change set, but it is **not** the artifact that
gets uploaded, and handing the upload step a CSV just forces an unnecessary conversion first.

Two things to check on any `.xlsx` you hand over, because a spreadsheet round-trip is
where they break: that the **separator glyphs survive** (the title's en-dash ` – ` and
the Item Highlights' middot ` · `), and that no numeric-looking value was reinterpreted
(a leading-zero UPC, a SKU that looks like a number, a date-like string). The script
writes every cell as text to prevent the second one.

## Current values: connector export grid first

In an attended session with the FlatFilePro connector, take current values from its
export, not from a manual download (`references/mcp-reads.md`):

1. `ffp-mcp.mjs binding` resolves the seller and marketplace IDs.
2. Export through the connector, then `ffp-mcp.mjs fetch-export` verifies and saves it
   under `downloads/{client}/catalog/`.
3. `ffp-mcp.mjs resolve --export FILE --asin A ...` lists every non-archived SKU of each
   ASIN, including `-1` contribution SKUs. Report `excluded_archived` and any missing SKU
   by name.
4. `ffp-mcp.mjs gaps --export FILE --sku S ... --touch <attributes>` before the build;
   exit 3 means a touched group has saved members the change does not supply.
5. `ffp-mcp.mjs grid --export FILE --sku S ... --out output/{client}/catalog/<name>.csv`
   writes the source grid in FlatFilePro's export spelling (`item_name__1__value`).

The grid is the `--source` for the build. When the connector is unavailable, or the
operator hands over a file, use a FlatFilePro XLSX export or the target account's
Amazon template as before. A saved `get_listings` result never becomes the source.

## Column names: exports lie, uploads want the canonical form

**Not every FlatFilePro export names its columns the way an upload expects.** Two
conventions are in circulation for repeat-group attributes:

| Convention | Example | Where it shows up |
|---|---|---|
| Canonical (dot, **0-based**) | `item_name.0.value`, `bullet_point.4.value` | what FlatFilePro expects **on upload** |
| Mangled (double underscore, **1-based**) | `item_name__1__value`, `bullet_point__5__value` | some exports, e.g. the `<Client>-<MKT>-all-<timestamp>.xlsx` flavour, and every connector grid |

Copying export headers straight into the upload file is therefore **not** always right,
even though the prepare script requires `--changes` attributes to match the export
verbatim. Author the changes file against the **source's** headers verbatim (the
connector grid always uses `__N__`, so `item_name__1__value`, not `item_name.0.value`);
the script now rewrites headers to the canonical form on write and prints what it
renamed. Verified 2026-07-26: a mangled export had **zero** headers matching the
canonical vocabulary, so an un-normalised upload means renaming every column by hand at
mapping time.

Sanity check before handover: every non-`sku` header in the upload file should contain a
`.N.` segment, never `__N__`.

## Core Rule

Use the physical product label or approved packaging PDF as the source of truth. Use the FlatFilePro export, category listing report, or Amazon template as the source for available headers, current backend values, SKUs, product types, and upload structure.

If required inputs are missing, answer briefly with only what is needed. Typical minimum inputs are:

- FlatFilePro export (connector grid or XLSX) or Amazon template
- product label, packaging PDF, or clear label images
- affected marketplace(s)
- affected ASINs/SKUs
- Amazon case message when the work is for Account Health or Seller Support

## Workflow

1. Identify the marketplace, ASINs, SKUs, product type, and case issue.
2. Read the grid, export or template headers before deciding which fields can be updated.
3. Compare current backend values against the physical label.
4. Review consistency at ASIN level, but write updates at SKU level, including duplicate contribution SKUs such as `-1` variants when they may control the frontend.
5. Create narrow upload files with only `sku` plus relevant existing FlatFilePro headers. **Default to full-grid output** (`--fill-unchanged` on the script): every included column is filled for every included SKU: the new value where changed, the SKU's current source value otherwise. A mapped-but-empty cell risks clearing a live value at upload time; a cell may only stay empty when the field is also empty in the source. Sparse output (changed cells only) is acceptable only when the operator explicitly wants it.
6. **Complete every touched attribute group** (Amazon error 99022 otherwise, per SKU): when the file touches any member of a grouped attribute, include the whole group's required members in the same file: nutrition macros (`energy`/`protein`/`carbohydrate`/`fat`: value **and** unit), vitamins rows (`nutrient` + `value` + `unit`), any `nutritional_info` touch also requires `serving_quantity` + `serving_unit` (+ `serving_description`), `unit_count.0.value` ↔ `unit_count.0.type.value`, and every weight value with its unit. Source companion values current-export-first, reviewed-baseline-second. Run `ffp-mcp.mjs gaps` on the touched attributes when the source is a connector export. See `references/flatfilepro-prep-rules.md` § Attribute-group completeness.
7. Produce an audit note or workbook showing included SKUs, excluded SKUs, changed fields, unchanged matching values, and manual-review fields.
8. Stop before uploading files, saving Seller Central changes, or submitting cases.

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

- audit workbook or note with old value vs proposed value
- **upload-ready `.xlsx`** split by product type/template when needed
- validation note with assumptions, source files, excluded rows, and manual-review items

For upload-file creation from reviewed changes, use `scripts/prepare_flatfilepro_upload.py` with an `.xlsx` `--output` (it writes either format; the extension decides). It exits 2 and names the SKUs when a changed SKU has no source row or the source repeats a SKU. Read `references/flatfilepro-prep-rules.md` before building complex upload files. When reading physical labels or packaging, map label sections to backend fields with `references/label-to-backend-mapping.md`.

After the `.xlsx` is created, use the `upload-map` mode in `amazon-flatfilepro` when the operator asks to upload the file in Chrome, match by SKU, map columns in FlatFilePro, or leave the flow ready for the operator's final click.

## Communication

When preparing Seller Support or Account Health replies, state what was updated and that it was done via FlatFilePro/flat file only if true. Attach or reference label evidence when Amazon asks for compliant label proof. Do not argue with Amazon in the reply; keep it factual and case-specific.

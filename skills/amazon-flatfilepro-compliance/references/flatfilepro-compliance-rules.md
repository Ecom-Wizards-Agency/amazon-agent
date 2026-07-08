# FlatFilePro Compliance Rules

## Source Priority

1. Physical product label, approved packaging PDF, or compliant label artwork
2. Amazon case message naming the non-compliant attributes
3. Current FlatFilePro export or Amazon template headers and current values
4. Certificates, test reports, or declarations only when they directly support the named issue

Do not use certificates as the nutrition source unless they actually contain the nutrition panel Amazon is comparing.

## Input Handling

When a user asks for a FlatFilePro compliance file and documents are missing, ask briefly for only the missing inputs:

```text
I need:
- FlatFilePro export or Amazon template
- product label/packaging PDF or clear label images
- marketplace
- affected ASINs/SKUs
- Amazon message, if this is for a case
```

Avoid long explanations at this stage.

## Review Pattern

- Inspect headers first; only output columns that exist in the export/template.
- Treat parent rows as audit-only unless the user explicitly asks to update parent-level data.
- Group rows by ASIN for diagnosis, but prepare upload rows by SKU.
- Update all known SKU contributions for the same ASIN when the same physical product and marketplace are affected.
- Keep unchanged values in the audit if they already match the label.
- In the upload CSV, include only fields needed for the update plus required identifying fields.

## Common Field Families

- `ingredients.*.value`
- `safety_warning.*.value`
- `serving_recommendation.*.value`
- `nutritional_info.*`
- `manufacturer.*.value`
- `rtip_manufacturer_contact_information.*.value`
- `fc_shelf_life.*`
- `product_shelf_life.*`
- `item_weight.*`, `package_weight.*`, `unit_count.*`
- `set_name.*.value`

Use exact headers from the source file. Do not rename columns unless the user specifically asks for a human-readable review sheet.

## Listing Copy Field Mapping

Only prepare title, Item Highlights, or bullet fields when the user explicitly asks for those listing-copy fields. Treat them as distinct fields:

- Title / item name: use the export/template's title header, commonly `itemName` or `item_name.*.value`.
- Item Highlights: use the export/template's Item Highlights-equivalent header. In FlatFilePro exports this may appear as `title_differentiation.0.value`. This is one short highlight field, not bullet points; keep it within the requested/Amazon character limit, commonly 125 characters.
- Bullet points: use only `bullet_point.*.value` headers.

Do not map Item Highlights to `bullet_point.*.value`, do not create bullet columns when the request is only for Item Highlights, and do not invent a human-readable `Item Highlights` column for an upload file unless the template/export already uses that exact header.

## Marketplace Enum Policy

Do not copy localized enum values between marketplaces. Use the current target-marketplace FlatFilePro export as the source for enum spelling.

Known example:

- DE may accept `unit_count.0.type.value = gramm`.
- IT rejects `gramm` for `unit_count.0.type.value`; use the Italy export style such as `grams`.

Apply the same rule to unit fields such as serving unit, unit count type, item weight unit, package weight unit, and nutrition units. If the label value is clear but the enum spelling is uncertain, prefer the enum already used in the target marketplace export over a translated display label.

## Upload File Rules

- Create separate CSVs when product types/templates differ.
- Keep `sku` or the template's required SKU/contribution SKU column as the first column.
- Do not include price, offer, title, bullets, images, claims, variation, or unrelated catalog attributes unless requested.
- Use the marketplace language for label text fields.
- Record manual-review items when a required label value has no safe upload field.

## Stop Points

Stop before:

- uploading a flat file
- saving Seller Central edits
- submitting an Account Health appeal
- sending a Seller Support reply

## Full-grid output rule (2026-07-05)

Upload CSVs are **full-grid by default**: run `prepare_flatfilepro_compliance_csv.py` with `--fill-unchanged` so every included column carries a value for every included SKU: the reviewed change where one exists, the SKU's current source-export value otherwise. Rationale: a column that is mapped in FlatFilePro but empty for some SKUs can clear the live value for those SKUs on apply. A cell may only remain empty when the field is also empty in the source export (nothing to preserve). This also makes the file self-documenting: the operator sees the complete final state per SKU, not a sparse diff. Keep the audit note as the place where changed-vs-carried values are distinguished.

## Attribute-group completeness (Amazon code 99022, 2026-07-05)

Amazon validates grouped attributes as a whole per feed row. Submitting one member of a group without its required companions fails per SKU with code 99022 ("Il campo X per l'attributo Y non ha valori sufficienti. Il minimo necessario è di 1"). Confirmed live on a client amazon.it collagen upload: sending `nutritional_info.0.energy.0.content` without `…energy.0.unit` (and similar) failed every SKU even though the unit was already populated on Amazon.

Companion map: when ANY member on the left is in the file, include ALL fields on the right for that SKU:

- `nutritional_info.0.energy.0.*` → `content` + `unit`
- `nutritional_info.0.protein.0.*` → `value` + `unit`
- `nutritional_info.0.carbohydrate.0.*` → `total` + `unit`
- `nutritional_info.0.fat.0.*` → `total` + `unit`
- `nutritional_info.0.vitamins_and_minerals.N.*` → `nutrient` + `value` + `unit` (per index N)
- any `nutritional_info.*` member at all → `nutritional_info.0.serving_quantity` + `nutritional_info.0.serving_unit` (+ `serving_description.0.value`)
- `unit_count.0.value` ↔ `unit_count.0.type.value` (always both)
- `item_weight` / `item_package_weight` / `item_display_weight` `.0.value` ↔ `.0.unit` (always both)

Fill companions current-export-value-first, reviewed-baseline-second, generic default last (`kilocalories` for energy unit, `grams` for other units). Combined with the full-grid rule, the end state is: every SKU row in the upload carries complete, self-consistent attribute groups.

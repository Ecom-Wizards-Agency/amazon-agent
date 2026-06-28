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

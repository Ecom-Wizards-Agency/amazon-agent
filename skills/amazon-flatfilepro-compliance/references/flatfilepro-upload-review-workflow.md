# FlatFilePro Upload Review Workflow

Use this when the user asks to upload, validate, map, or check a prepared CSV in FlatFilePro. The workflow was captured from an operator demonstration and has been generalized for public use.

## Preconditions

- Use Chrome for FlatFilePro.
- Confirm the selected Seller & Marketplace before opening Upload.
- If FlatFilePro starts on the wrong account, use the `Seller & Marketplace` selector and choose the exact target account/country named by the user or saved in local ignored notes.
- Stop if the user is not logged in.

## Upload And Matching

1. Open FlatFilePro Listings or Upload.
2. Verify the URL/account changed to the intended marketplace after selecting Seller & Marketplace.
3. Open `Upload`.
4. Click `UPLOAD FILE`.
5. Select the prepared CSV. If the picker defaults to Downloads, copy the CSV there first or navigate to the output folder.
6. In the matching step, prefer `SKU`.
7. Choose the CSV's SKU column for the `Column` selector.

## Attribute Mapping

FlatFilePro may not automatically map all technical headers. Map each relevant CSV column manually:

1. Use `Search file columns` to select the CSV header, for example `safety_warning.0.value`.
2. Copy or type the technical header into `Search attributes`.
3. Select the matching Amazon attribute. The display label may be localized, for example `Sicherheitswarnung (safety_warning.0.value)`.
4. Click `MAP ATTRIBUTES`.
5. Repeat for each relevant field.

Common columns from the demonstration:

- `ingredients.0.value`
- `safety_warning.0.value`
- `safety_warning.1.value`
- `safety_warning.2.value`
- `safety_warning.3.value`
- `serving_recommendation.0.value`
- `manufacturer.0.value`
- `rtip_manufacturer_contact_information.0.value`
- `set_name.0.value`
- `item_package_weight.0.value`
- `item_package_weight.0.unit`
- `item_weight.0.value`
- `item_weight.0.unit`

For nutrition columns, follow `nutrition-field-policy.md`; do not add string fields only because they are available.

## Local Memory

Confidential account names, marketplace selectors, recurring upload paths, and learned column quirks belong in `_local/flatfilepro-compliance/local-notes.md` or `_local/flatfilepro-upload-mapper/local-notes.md`. These files are ignored by Git. Do not commit real seller names, client brands, SKUs, ASINs, upload files, screenshots, or support-case details.

## Preview And Issues

- Use the preview rows to confirm the expected SKUs, ASINs, product titles, and product types.
- Confirm values appear under the intended attribute columns before proceeding.
- If FlatFilePro shows validation issues, capture the exact SKU, field, message, and code.
- If the issue is only pre-submission validation and the user mentions forcing, still stop before using any force/update switch unless explicitly approved for that file.

## Stop Point

Stop before final update/submission. Tell the user:

- selected Seller & Marketplace
- file selected
- match basis used, normally SKU
- mapped fields
- preview or validation issues found
- whether the file appears ready for the user to submit

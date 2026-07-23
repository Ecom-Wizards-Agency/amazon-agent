# Team Catalog Change Workflow

Use this workflow for variation and parentage changes. Routine listing-content updates belong in FlatFilePro.

## Entry Points

### Start catalog variation change

1. Confirm the Seller Central account and marketplace.
2. Classify the operation: create parent, add child, create new GTIN-exempt child, delete parent, rebuild, detach, or reparent.
3. Obtain a fresh Category Listings Report and a fresh blank single-marketplace template for the correct product type.
4. Read the CLR as evidence only. Never use it as the upload base.
5. Prepare a manifest from `tools/amazon-catalog-change-pack/config.TEMPLATE.json`.
6. Build the change pack and review `02-change-manifest.md` with the assigned senior.
7. Hand off the validated upload files. The assigned senior performs the final submission.

### Validate catalog upload file

Run the utility's `validate` command against the prepared file and its manifest. Do not approve the upload when validation reports:

- missing or unexpected SKUs
- extra fields on existing child rows
- duplicate variation values
- mixed themes
- an invalid action label
- offer or child-variation data on a parent
- a product ID on a GTIN-exempt child
- modified template metadata or lost VBA content

### Review processing summary

Run `review-summary` and read the Feed Processing Summary per SKU. Upload success alone is not a verdict. Separate pre-existing listing warnings from errors caused by the submitted relationship change.

## Decision Rules

| Situation | Route |
| --- | --- |
| New parent | Full update in a fresh blank template |
| Existing child joins parent | Minimal partial update |
| New GTIN-exempt child | Full update with blank product ID |
| Parent delete | Parent-only delete file |
| Detach, reparent, or rebuild | Ordered delete file, verification gate, then rebuild file |
| Title, bullets, description, images, normal attributes | FlatFilePro |

## Required Verification

After each upload:

1. Read the Feed Processing Summary per SKU.
2. Confirm the hierarchy in Manage All Inventory.
3. Check Variation Wizard when available.
4. Download a fresh Category Listings Report.
5. Check a child detail page for the customer-facing selector.

The parent ASIN does not need a normal customer-facing detail page. Backend, report, and frontend state can update at different times.

## Known Error Recovery

| Code | Meaning | Recovery |
| --- | --- | --- |
| `8032` | Child still belongs to another parent | Finish and verify old-parent deletion before the next file. |
| `8066` | Invalid relationship setup | Check levels, parent SKU, product type, theme, and child value. |
| `8801` | Duplicate variation attributes | Use one unique value per child and verify retained catalog attributes. |
| `90041` | Missing required data | Resolve companion errors first, then check Data Definitions. |
| `90057` | Invalid action label | Use Amazon's exact Full Update, Partial Update, or Delete label. |
| `100521` | Review pending | Wait up to 48 hours before another corrective upload. |

## Evidence Package

Keep the source report, blank template, manifest, upload file, processing summary, backend hierarchy screenshot, and frontend selector screenshot in the generated change pack. Never store client artifacts in the tracked skill or tool folders.

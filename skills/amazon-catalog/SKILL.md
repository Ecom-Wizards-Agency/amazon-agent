---
name: amazon-catalog
description: Use for Amazon catalog management: variations, parentage, flat files, listing edits, A+ content, images, browse nodes, brand attributes, feed processing, delete-relist workflows, Vendor Central catalog feeds, and Brand Registry catalog conflicts. Trigger on "Start catalog variation change", "Validate catalog upload file", and "Review processing summary". Diagnosing an unknown error or suppression → amazon-troubleshooting; routine content updates through FlatFilePro → amazon-flatfilepro-upload-mapper; FlatFilePro compliance CSVs → amazon-flatfilepro-compliance; listing copy/SEO → amazon-seo.
---

# Amazon Catalog

Browser: Mixed (file builds are local; template downloads/uploads are Codex interactive; stop before upload).

## Workflow

1. Identify account, marketplace, ASIN, SKU, parent/child relationship, brand, and contribution source.
2. Search Amazon Seller Help first for current listing rules, error definitions, catalog requirements, and Brand Registry behavior.
3. Search internal notes if the client/workflow has known context.
4. Use MAG catalog SOPs for step-by-step UI or flat-file execution.
5. Decide manual UI vs flat-file vs support case.
6. Preserve current state before edits.
7. Stop before saving listing changes, deleting/relisting, uploading feeds, or submitting support cases.

## Team Entry Points

For variation and parentage work, load `references/team-catalog-change-workflow.md` and the technical `references/parentage-flatfile-playbook.md`.

- **Start catalog variation change**: gather or discover the account, marketplace, operation, fresh Category Listings Report, fresh single-marketplace blank template, product type, parent/children, theme, customer-facing values, and GTIN/offer details for new children. Create a manifest, then run the change-pack builder.
- **Validate catalog upload file**: run the change-pack validator against the manifest and prepared `.xlsm`. Report every blocking issue before upload.
- **Review processing summary**: run the summary reviewer, explain the verdict per SKU, and state the exact next step and verification gate.

Tool location: `tools/amazon-catalog-change-pack/`.

Every build must produce a scoped change pack under `output/{client}/catalog/{date}-{operation}/`. Review `02-change-manifest.md` before upload. The assigned senior performs the final submission manually.

Routine titles, bullets, descriptions, images, backend attributes, and normal listing-content edits remain in FlatFilePro. Do not route those through the variation builder.

## Parentage / Variation Flat Files

For creating or editing variation families (parentage) or any targeted flat-file edit, load `references/parentage-flatfile-playbook.md` BEFORE building or reviewing the file. Non-negotiables from live-verified runs:

- Upload base = a fresh **blank template** (single-country, correct browse node). The Category Listings Report is a **data source only**; re-uploading its echoed values fails current-schema validation.
- Parent rows: Full Update, generic title, ALL required attributes filled (Data Definitions sheet), no variation/offer/condition data.
- Child rows: minimal Partial Update (parentage fields + the variation attribute value, nothing else echoed).
- Map template columns by attribute name, never by index; read `dataRow` from the settings cell (it varies by template flavor).
- Read the Feed Processing Summary per SKU; "successful with other errors" = change applied, pre-existing listing issues flagged separately.
- When merging existing ASINs, capture the pre-merge KPI baseline first (see playbook).
- For delete, detach, reparent, and rebuild operations, generate ordered files and enforce a processing/verification gate between file 01 and file 02. Never combine the destructive step with the rebuild.

# Amazon Catalog Change Pack

Builds and validates tightly scoped Amazon variation and parentage upload files from a fresh blank template. It also reviews Amazon Feed Processing Summary workbooks. The utility never uploads files or changes a catalog.

## Route Work Correctly

Use this tool for:

- creating a variation parent
- adding a child to a parent
- creating a new GTIN-exempt child
- deleting or rebuilding a parent
- detaching or reparenting children through an ordered delete/rebuild sequence
- validating a prepared variation file
- interpreting a processing summary

Use FlatFilePro for routine titles, bullets, descriptions, images, backend attributes, and other normal listing-content updates.

## Required Source Files

1. A fresh Category Listings Report for current-state evidence.
2. A fresh blank template downloaded for one marketplace and the correct product type.

Never use the Category Listings Report as the upload base. It echoes stale catalog values and causes unrelated validation failures.

## Commands

```bash
python3 tools/amazon-catalog-change-pack/catalog_change_pack.py build \
  --manifest /absolute/path/to/change.json

python3 tools/amazon-catalog-change-pack/catalog_change_pack.py validate \
  --manifest /absolute/path/to/change.json \
  --file /absolute/path/to/upload.xlsm

python3 tools/amazon-catalog-change-pack/catalog_change_pack.py review-summary \
  --manifest /absolute/path/to/change.json \
  --summary /absolute/path/to/processing-summary.xlsm
```

Copy `config.TEMPLATE.json` for the manifest contract. Client manifests and files belong under the ignored `output/{client}/catalog/` and `downloads/{client}/` folders, not in this tool folder.

## Manifest Contract

Top-level fields:

| Field | Purpose |
| --- | --- |
| `schema_version` | Must be `1`. |
| `client` | Client name used for output routing. |
| `seller_account` | Visible Seller Central account label. |
| `marketplace` | Target marketplace, such as `US`. |
| `date` | Change date used in the pack folder. |
| `operation` | One supported operation listed below. |
| `source` | Absolute paths to the CLR and blank template. |
| `family` | Parent, children, variation theme, and variation attribute. |

Supported operations:

- `create_parent`
- `add_existing_child`
- `create_gtin_exempt_child`
- `delete_parent`
- `rebuild_family`
- `detach_children`
- `reparent_children`

`source.allow_missing_skus` is an explicit exception for SKUs known to be omitted from the report, such as blocked listings. Every exception appears in the build notes.

`family.parent.status` is `new` or `existing`. It is required for reparenting so the utility knows whether to build the target parent or attach children to a parent that already exists.

`family.parent.fields` and a new child's `fields` use exact technical attribute headers from row 5 of the blank template. The utility supplies protected relationship fields itself. Existing children must not contain a `fields` object because they are intentionally minimal partial updates.

## Update Rules

- New parent: `Create or Replace (Full Update)`.
- New child: `Create or Replace (Full Update)`.
- Existing child relationship: `Edit (Partial Update)` with relationship fields only.
- Parent deletion: `Delete`.
- GTIN-exempt child: `GTIN Exempt` type with a blank product ID.
- Parent: no variation value, price, quantity, condition, or fulfillment data.
- Every child: same theme and one distinct customer-facing variation value.

Multi-stage changes create two files. Process and verify file `01` before submitting file `02`.

## Change Pack

```text
output/{client}/catalog/{date}-{operation}/
├── 01-source-record.md
├── 02-change-manifest.md
├── 03-upload-ready/
├── 04-processing-summary/
└── 05-evidence/
```

The assigned senior reviews the manifest and validation result, then performs the final upload manually.

## Self-Test

```bash
python3 tools/amazon-catalog-change-pack/selftest.py
```

The test uses synthetic workbooks and covers scoped rows, partial/full updates, GTIN exemption, duplicate values, mixed themes, contaminated rows, ordered rebuilds, VBA preservation, and processing-summary errors.

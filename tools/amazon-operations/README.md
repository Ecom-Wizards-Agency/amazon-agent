# Amazon operations for Merlin

Version 1 is a reusable local operation boundary. Wizards owns Slack, identity,
authorization and scheduling; Amazon Agent owns preparation, browser execution,
recovery evidence and domain verification. It never imports Wizards code.

All browser adapters are **implemented but require a scoped live canary**. No
Amazon account was modified during development. Capabilities report
`production_ready: false` as the library baseline; preparing an artifact does not
enable production. Wizards owns the verified-canary release ledger and may grant
`allow_validated_adapter: true` after that adapter is explicitly released.
The CLI trusts the authenticated local caller to supply grants and fresh evidence.
Do not expose it directly to untrusted HTTP, Slack text, or model-generated shell.

Use the Amazon Agent Python environment with `openpyxl` and Pillow installed.
Node must support the repository's existing CDP modules. Browser execution uses
managed task tabs and an exclusive account context on port 9222; there is no
fallback to the read-only port, another browser, raw credentials or arbitrary
commands supplied in a request.

```sh
python3 tools/amazon-operations/operations.py capabilities
python3 tools/amazon-operations/operations.py prepare --request request.json --state-dir /absolute/run-state
python3 tools/amazon-operations/operations.py execute --request execute.json --state-dir /absolute/run-state
python3 tools/amazon-operations/operations.py reconcile --request evidence.json --state-dir /absolute/run-state
```

`advance` aliases `execute`. `status` needs a request containing `operation_id`.
Every command emits one JSON result. Input errors emit `status: blocked` and a
specific `reason` with exit code 2. An exit code of zero is not completion.

## Requests and immutable plans

Preparation accepts `schema_version: 1`, a unique `operation_id`, `operation`,
`account`, `targets` and `inputs`. Targets are unique SKU strings or objects with
`sku` and optional `asin`; objects normalize to SKU strings. ASINs populate
`inputs.sku_asins` for later live verification.

Account identity includes `client_slug`, `profile_key` and `marketplace` and is
preserved exactly across the plan, grant and evidence. Both Seller Central and
FlatFilePro require `seller_id` (template merchant ID) and `marketplace_id` as
nonempty strings. Seller Central also needs `seller_central_name` and
`marketplace_label`. FlatFilePro needs `flatfilepro_display_name` and
`marketplace_label` as displayed
in the visible Seller & Marketplace selector. Missing or ambiguous visible
context stops execution. Seller Central's existing live identity reader checks
stable Seller/marketplace IDs when available. A label fallback requires
`context_binding: {seller_id, marketplace_id, unique_label_mapping: true}` inserted
by the authenticated caller from its unique verified registry mapping. Any
observed live seller or marketplace ID mismatch overrides the trusted label
mapping and stops execution. Exact
selector labels are required; account-name substring matches never pass. Account
alias selection belongs to the caller.

Preparation returns `plan_hash`, `plan_path`, `operation`, `account`, normalized
`targets`, `status`, `verified`, `required_inputs` and adapter capability.
The plan contains copied source artifacts and checksums, the intended changes,
exact upload files, and execution stages. Each later call checks plan and
artifact hashes. Reusing an operation ID with different inputs is rejected;
corrections create a new operation revision ID. A worker lease protects each
journal. The state directory is a caller-selected local artifact root, not a
remote delivery destination; callers register generated artifacts for retention.

Execution request:

```json
{
  "schema_version": 1,
  "operation_id": "seo-example-r1",
  "plan_hash": "SHA256_FROM_PREPARE",
  "grant": {
    "execute": true,
    "account": {"client_slug":"example","profile_key":"example-us","marketplace":"US"},
    "operation": "seo.apply",
    "targets": ["EXAMPLE-SKU"],
    "plan_hash": "SHA256_FROM_PREPARE",
    "allow_live_canary": true
  }
}
```

The grant account must include every identity field supplied at preparation.
Only the authenticated caller may set `allow_live_canary` from an explicit scoped
canary authorization, or `allow_validated_adapter` from the proven release ledger.
Neither flag is accepted directly from user text. Browser adapters only return `processing`, `blocked`,
`failed`, or `uncertain`. Journaling occurs before submission; an unknown result
cannot be executed again without reconciliation. `verified: true` means final
state was verified, or supplied current evidence already matched every requested
field and no write was necessary.

## Operation inputs

- **`seo.apply` / `seo.update`:** `live` has exact account, timezone-aware
  `observed_at` and `rows: {sku: {technical_header: value}}`. `approved_seo` has
  account, `source_id`, `approved: true`, `approved_by`, `approved_at`, and scoped
  desired `rows`. `superseded: true` is rejected. Missing approved copy returns
  the existing `amazon-seo` workflow as the preparation handoff. The caller
  resolves the latest suitable approved revision; no age threshold is invented.
- **`flatfile.apply` / `flatfilepro.update`:** same live evidence, `desired_rows`,
  `scope_fields`, and `source_export: {path, sha256}`. SEO uses these same upload
  inputs. Exact source headers are required. The existing FlatFilePro builder
  writes `.xlsx` with full-grid preservation; every carried field is compared
  against live evidence. Unit count and weight companion fields must be scoped.
  Other grouped attributes must be explicitly supplied as complete groups.
- **`listing.images.replace` / `listing.images`:** `images` contains
  `{sku, slot, artifact: {path, sha256}, url}`. Slots are MAIN, PT01–PT09, or SWCH.
  Images must be JPEG/PNG, at least 500px on both dimensions. `image_fields` maps
  slots to exact source-export image headers. Live/export inputs above prepare
  the real FFP replacement upload. Hosted URLs are fetched using public-IP-pinned
  HTTPS and must match approved bytes or identical decoded pixels, checked again
  before execution. An unchanged URL alone cannot verify live image content.
- **`catalog.family.update` / `catalog.change`:** `manifest` uses the existing
  Catalog Change Pack contract. `source_artifacts` holds checksum-bound
  `category_listings_report` and `blank_template`. The fresh template's merchant
  ID must match the account. Parent deletion/rebuild also requires
  `existing_family: {account, observed_at, relationships: {child_sku: parent_sku}}`.
  Every affected child must be declared and explicitly scoped; child offers are
  protected. File 2 cannot execute until file 1 is verified.
- **`catalog.products.create`:** same sources; manifest may use an existing
  supported child-creation operation or `operation: create_products` with
  `products: [{sku, product_type, title, fields, product_id, product_id_type}]`.
  `gtin_exempt: true` with a blank product ID is the alternative. Existing SKUs,
  mixed product types, and relationship overrides are rejected. Creates full
  updates using the existing template writer; every written field is reopened
  and checked. Product facts and exemption evidence remain preparation duties.
- **`shipment.create`:** `shipment_reference`, complete `ship_from`,
  `lines: [{sku, quantity}]`, `cartons: [{id, weight, weight_unit, dimensions,
  dimension_unit, contents: {sku: quantity}}]`, `carrier`, `currency`,
  `estimated_cost`, `ship_date`, `ship_mode`, `carrier_mode`, `packing_templates`,
  and `label_format`. `client_limits` binds account, `max_units`, `max_cost`,
  currency and carriers. `existing_shipments` binds account, observed time and
  shipment references/statuses. Quantities must exactly reconcile to cartons;
  active duplicate references stop before creation. The browser driver narrows
  this to observed supported shipment modes and reports missing inputs.

`account_health.fields.restore` and `account_health.images.restore` require
`finding_id`, `required_missing: {sku: [technical_header]}`, and
`approved_product_data: {account, source_id, approved_by, approved: true,
verified: true, verified_at, rows}`. Image restores also bind approved
`images: [{sku, slot, url, sha256}]`. Conflicting nonempty values and protected
offer/relationship fields are rejected. Fresh CLR evidence immediately before
execution must prove that planned changes remain missing. For these
`restore_missing_only` operations, every unchanged cell carried in the upload
must also match the fresh report; missing or changed carried values stop the
restoration before submission. While the report
generates, execution returns `processing`, `phase: preflight`,
`effects_started: false`, `next_action: execute`. Reconciliation returns `partial`
with a bound fresh-report receipt when ready; a separate execution claim consumes
it within five minutes. Already restored values produce a bound JSON no-op
receipt. Wizards still limits automatic remedies to its configured rule allowlist.
Performance optimization is outside these operations.

## Reconciliation and evidence

Pass schema version, operation ID and plan hash, plus `evidence` containing exact
account, plan hash, `source_id`, timezone-aware `observed_at`, `submission_id` and
`processing_status` (`processing`, `complete`, `failed`, or `live_observed`).
Evidence older than execution or belonging to another submission is rejected.

Copy verification needs final `rows` covering every transmitted SKU-field cell.
With no evidence supplied, the collector can capture public title, bullets and
description using the established read-only listing-capture runner and bound
SKU–ASIN mapping. Redirected ASINs are rejected. It never labels an upload preview
as live data, nor infers feed completion from a public listing. Hidden fields use the new fresh Category Listings Report collector. It requests
the documented report, persists generation intent before clicking, downloads
through the established report status API, and checks identity, freshness, bytes,
and exact header/SKU coverage. Unavailable or still-generating reports stay pending.

Image evidence needs SKU, slot, approved `source_sha256`, `live_url`, and
`visually_verified: true` from verified content. The automated image collector
reads exact ImageBlock variant slots, validates delivery location and resolved
ASIN, then compares downloaded live bytes or identical decoded pixels to the
approved image. Lossy transformations needing visual judgment remain pending. Catalog evidence needs
`stage`, exact `relationships`, `child_offers: {sku: "preserved"}`, and
`deleted_parents` for deletion stages. Every full-update row additionally needs
`catalog_rows` covering the exact `full_update_values` recorded in its stage. Standalone product evidence instead has
`products: {sku: {asin, product_type, title, parent_sku}}`.

Shipment evidence needs confirmed reference, quantities, carrier, currency,
actual cost and one PDF label record per carton (`carton_id`, local path,
checksum and shipment ID). `submission_ids` supports split shipments. The
collector must establish each label's carton/shipment association; file existence
alone is insufficient. Core reconciliation independently reruns the shipment
driver's PDF page, thermal-size, carton ID and SKU/quantity validator. Pending
proof stays pending and never permits blind retry.

```sh
python3 -m unittest discover -s tools/amazon-operations/tests -v
node --test tools/amazon-operations/tests/browser-contracts.test.mjs
```

Tests use synthetic accounts, workbooks, processing evidence and UI snapshots.
They do not connect to Chrome, submit feeds or create shipments.

## Supported-route limits

Live rollout remains canary-gated. Unknown UI labels, ambiguous account selectors,
unavailable Category Listings Reports, unmatched technical headers, and incomplete
preview coverage stop with evidence. The report collector currently uses the
observed English report controls. Catalog child-offer preservation requires
comparable source and fresh report fields. Images with transformed pixels need
additional visual evidence rather than an approximate similarity claim. Shipment
execution is limited to the driver's documented saved-template, case-pack,
non-partnered SPD route; other modes stay blocked.

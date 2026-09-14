# Amazon operations for Merlin

Version 1 is a reusable local operation boundary. Wizards owns Slack, identity,
authorization and scheduling; Amazon Agent owns preparation, browser execution,
recovery evidence and domain verification. It never imports Wizards code.

All browser adapters are **implemented but require a scoped live canary**. No
Amazon account was modified during development. Capabilities report
`production_ready: false` as the library baseline; preparing an artifact does not
enable production. Wizards owns the release ledger for existing SKU adapters. Case adapters use the
shared account-specific `case-policy.json` readiness record and canonical verified
canary journal; a caller-supplied release flag alone cannot enable them.
The CLI trusts the authenticated local caller to supply grants and fresh evidence.
Do not expose it directly to untrusted HTTP, Slack text, or model-generated shell.

Use the Amazon Agent Python environment with `openpyxl` and Pillow installed.
Node must support the repository's existing CDP modules. Browser execution uses
managed task tabs and an exclusive account context in the shared `grimoire`
session on port 9223. Resolve it before imports with `browserctl run --session
grimoire -- …`. There is no fallback to another profile or arbitrary commands
supplied in a request. Registered executors also require verified access on 9223.

The FlatFilePro import screen observed on 2026-09-13 uses `/import`, the `SKU`
identifier radio, `UPLOAD EXCEL FILE`, and `IMPORT` to parse the uploaded workbook.
The mapping inputs are labeled `Search attribute headings` and `Search attributes`.
The adapter stages a workbook named by its plan hash and journals the exact
seller/marketplace-prefixed server upload key before mapping. A restart selects
that same uploaded file; an unknown upload response never triggers another
attachment automatically.

The current v2 metadata response uses `other_product_image_locator_1__1__media_location`
through slot 8. Its autocomplete hides those identifiers in option rows, but
searches them and includes them in the selected input label. Live read-only
inspection confirmed an exact raw search returns one option; canonical dotted
search returns none. The adapter searches the raw identifier, requires a unique
candidate, and checks the selected technical label before mapping. Ambiguous or
changed labels return `ffp_image_slot_unverifiable`.

The `/import` URL exposes no submission ID. Public app code shows submission
returns a separate `runId` linked at `/activity/import/<runId>`. The observed
read-only `/listing-update-runs` response was empty for the selected account, so
upload-to-run correlation could not be established from a real run. The recorded
server upload key proves which workbook was staged, but does not prove that it was
submitted. Secondary image execution can use an attended canary grant or a
validated image adapter grant supplied by the operation service. That route
durably reserves the uploaded config identity before `Update Listings`, observes
only the exact config's update response body, and persists its returned `runId`.
Missing, malformed or ambiguous responses remain uncertain and cannot replay.
Without those scoped grants, `ffp_submission_recovery_unverified` prevents the
final click on `/import`.

`flatfilepro-activity.mjs` reads a known run's summary and all item pages through
the observed Activity routes. It checks the exact seller, marketplace, SKUs,
attributes and submitted values before returning processing evidence. Secondary
image verification requires that evidence alongside current Amazon images and
preserved MAIN/swatches. Rejected slots are reported separately from verified
slots. The image-only workbook preserves the current export's exact headers;
other workbook routes keep their existing normalization.

A durably captured runId is recoverable after loss of the adapter response.
If the submission response itself was lost before its runId could be recorded,
upload-to-run history correlation remains unavailable and the attempt stays
blocked without another update. Activity item shapes, pagination, mapping
readback and the full preview still require the attended live canary. No Amazon
image update was submitted during development.

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
`account`, `targets` and `inputs`. SKU-operation targets are unique SKU strings or objects with
`sku` and optional `asin`; objects normalize to SKU strings. Case operations use
`{issue_key}` for creation and `{case_id}` for replies. ASINs populate
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
journal. For SKU operations the state directory is a caller-selected local artifact root,
not a remote delivery destination. Case operations require the shared canonical
`~/.amazon-agent/cases/operations` root to prevent alternate-journal replay; callers register generated artifacts for retention.

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

## Team-owned cases

See [the case workflow](../../docs/team-owned-cases.md) for ownership, scope,
daily review and rollout. The shared case service prepares a signed request and
returns its canonical operations state directory. Use that exact request with
`prepare`, then `execute` and `reconcile`; do not construct a separate case plan.

```sh
python3 tools/amazon-operations/case_service.py start --request team-request.json
python3 tools/amazon-operations/case_service.py prepare-send --request reviewed-message.json
python3 tools/amazon-operations/case_service.py list
python3 tools/amazon-operations/case_service.py daily-due
```

`adopt` imports an observed existing case without inventing an owner or mandate.
`reassign`, `revoke` and `resolve` require explicit verified team instructions.
`record-receipt` consumes the canonical independently verified delivery journal.

Every outgoing message includes an evidence-backed routine scope assessment,
with category `factual_evidence`, `clarification` or `status_check`, rationale,
source references and the SHA-256 of the unsigned body. Preparation adds the
saved owner's signature. Changed owner, mandate, content, attachments or account
invalidates the pending action. This structured review does not replace checking
that the underlying facts are supported.

The read-only `observe` command returns complete case correspondence or a scoped
case search. Creation searches by shipment ID, ASIN or exact subject and freezes
the query for the pre-submit duplicate check. Incomplete or truncated history
blocks a send. The current transcript reader supports up to 50 contacts and
reports incompleteness when Amazon exposes more; such cases need an expanded
reader before automatic sending.

Case readiness is recorded per exact seller/marketplace and separately for
`case.create` and `case.reply`. A canary must refer to a real verified canonical
journal and independent saved-correspondence evidence. A visible button alone
is insufficient. The create/reply form selectors still need live validation in
an account with confirmed access before production release.

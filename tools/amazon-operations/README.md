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
Read-only case `observe` may also run in the attended operator session. Case
`execute` refuses every session except `grimoire` with `case_adapter_grimoire_only`,
before the journal records an attempt; attended Seller Support sends use
`seller-assistant.mjs` instead (see Attended case sends).

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

The image route uses current exact FlatFilePro listing reads for identity and
protected baselines. `flatfilepro-discovery.mjs` first verifies the complete
paginated nonarchived inventory, then enriches only explicitly selected targets.
Read time, Amazon update time and unavailable synchronization timestamps remain
separate. A Category Listings Report is not required by this route.

`record-image-review` appends a checksum-bound attended visual receipt for exact
approved source and observed Amazon image bytes, account, plan, SKU, ASIN and
slot. It does not mark an operation verified. Reconciliation must collect fresh
matching PDP evidence, complete processing values and unchanged protected slots.
The returned `image_completion` separates publication, preservation and
processing. `image-release-proof` revalidates the stored evidence. Pending
processing remains visible; mixed pending and rejected contributions keep the
operation partial so the caller cannot treat unresolved writes as retryable.

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

### Attended case sends

Attended sends never pass `prepare-send` or `validate-binding`, so the readiness
switch, canary, 09:00 rule, daily observation and routine-scope gates stay on
Grimoire's path unchanged. Four commands serve attended sends. Each refuses with
`attended_context_required` when `WIZARDS_AI_MODE` is set or `/proc/self/cgroup`
names a `wizards-ai-*` unit. All except `sign` require an attended
authorization: `kind: attended`, the policy's `attended_operator_id`, and
`source.session_id` plus `source.instruction`. A Slack authorization returns
`attended_required`. Grimoire's re-validation of a persisted attended mandate is
unchanged. `observe` now counts `last_sent_at` as the latest seller message when
it is newer than the case log's last seller contact, so a chat reply missing from
the case log still answers older Amazon messages.

`sign` is read-only and returns the exact final text and its SHA-256. It keeps a
body that already ends in the owner's exact policy signature. It refuses
`signature_conflict` when one of the last three lines is a sign-off: a whole line
equal to an approved member's name or signature line, or a closing that ends in a
member's name after a comma or dash (`Best regards, Danica`). A name inside a word
or a sentence (`Davenport`) is body text. Otherwise it appends the owner's
signature, exactly as before. `prepare-send` uses the same rule. A case without an
owner, or a request without `registry_id`, signs as the attended operator
(`owner_source: attended_operator`). Write `signed_body` to the text file without
a trailing newline. `baseline.last_sent_at` is the draft baseline for
`claim-attended`, and `signature_name` is the only name the chat form's "Your
name" field may carry.

```json
{"registry_id":"b8b3…","body":"Dear Amazon Support,\n\nThe invoice is attached."}
{"status":"signed","registry_id":"b8b3…","owner_member_id":"U01…","owner_source":"case_owner","signature_name":"Victor Uhl","signed_body":"Dear Amazon Support,\n\nThe invoice is attached.\n\nVictor Uhl\nEcom Wizards","sha256":"75b8…","baseline":{"last_sent_at":"2026-09-30T14:02:11+00:00"}}
```

`claim-attended` is the driver's check before each outbound click of one reply
run. It refuses `account_mismatch`, `case_not_created` (only a reply in a created
case is claimed), `case_mismatch` (`case_id` is not the registered Amazon case),
`signature_name_mismatch` (a `signature_name` other than the one `sign` returns
for the case), `run_recorded` (this run already has a receipt), `claim_released`,
`reconciliation_required` (an unapplied action that is not invalidated, or an
uncertain one), `daily_sent` (a non-attended operation sent on this case today)
and `baseline_changed` (`last_sent_at` is newer than the draft baseline). Each
success bumps `authorization_revision`, so any binding Grimoire computed earlier
is stale, and adds a new `authorization` to the claim's list. Repeated calls for
the same `run_id` are safe.

A claim stays open until its run is recorded with `record-receipt` or released.
While it is open, `prepare-send` refuses `reconciliation_required` and `observe`
sets `next_action` to `human`, so Grimoire cannot answer over an attended send
that may be out but is not recorded yet.

```json
{"registry_id":"b8b3…","run_id":"acme-12345678901-r1","account":{"seller_id":"A2RB…","marketplace_id":"ATVPDKIKX0DER"},"case_id":"12345678901","signature_name":"Victor Uhl","baseline":{"last_sent_at":"2026-09-30T14:02:11+00:00"},"authorization":{"kind":"attended","requester_id":"U01…","source":{"session_id":"…","request_id":"acme-12345678901-send","instruction":"this is perfect, send it"}}}
{"status":"claimed","operation_id":"attended-3f1c…","authorization_revision":7}
```

`record-receipt` with `attended_receipt` records a reply or chaser that the driver
or a person sent. New cases still register through `start` and `adopt`.
`authorization.source.instruction` is the operator's approval sentence, verbatim.
`label` is one of `routine`, `appeal`, `dispute`, `refund_request`, `commitment`
or `admission`. Kind `driver_run` reads `<run_dir>/run.json` and
`approvals.jsonl`:

- the run's `seller_id` and `marketplace_id` must equal the case's, and run.json
  must name this case's `registry_id` (`registry_binding_required`);
- the run must have claimed the case before its first click (`claim_missing`,
  `claim_after_click`);
- `messages` must list exactly the hashes the run submitted, ignoring attempts
  whose result is `blocked`;
- every attempt's approval must carry the run ID, the case seller, an approval
  sentence that is the receipt's or one the run claimed with, and the message's
  `label` (a message may name its own; it defaults to the receipt's);
- `readback_path` is required and is the case log read after the run
  (`missing_readback`, `readback_not_case_log`); `transcript_path` may name a
  driver transcript record;
- each hash needs a `sent` result, or a readback or transcript that shows the
  exact text. An `uncertain` result or an attempt without a result never passes on
  its own.

A case-log readback is `observe` output or a `case-readback-*.json`. A transcript
needs the message's `text_path` (the file the driver typed) or a transcript
message with the same hash. Each recorded message says what showed it:
`case_log` (an exact seller contact, whose ID is merged into `contact_ids`),
`chat_transcript`, or `driver_result` when only the driver's own read of the chat
after the click did. The record's `verified_by` is the weakest of its messages.

```json
{"registry_id":"b8b3…","attended_receipt":{"schema_version":1,"kind":"driver_run","run_dir":"<run-dir>","purpose":"reply","label":"routine","channel":"case_chat","messages":[{"plan_item":"P3","sha256":"…","text_path":"<run-dir>/P3.txt"},{"plan_item":"followup","sha256":"…","text_path":"<run-dir>/followup-1.txt","label":"admission"}],"readback_path":"<run-dir>/observe-after.json","transcript_path":"<run-dir>/transcripts/09-transcript.json","authorization":{"kind":"attended","requester_id":"U01…","source":{"session_id":"…","request_id":"acme-12345678901-send","instruction":"this is perfect, send it"}}}}
{"status":"recorded","operation_id":"attended-3f1c…","verified_by":"chat_transcript","case":{"…":"…"}}
```

Kind `manual_receipt` records a send made by hand, or a backfill. It takes
`sent_at`, `signed_body_sha256`, an optional `text_path` and `evidence_path`.
The evidence must show the exact message. It can be a case-log readback (pass one
whenever Amazon shows the message there), or a verified send receipt with
`seller_id`, `marketplace_id`, `case_id`, `message_sha256` and `status: verified`.
A bare transcript names no account and is refused. The evidence file's SHA-256 is
stored.

```json
{"registry_id":"b8b3…","attended_receipt":{"schema_version":1,"kind":"manual_receipt","purpose":"reply","label":"routine","channel":"case_chat","sent_at":"2026-10-01T14:40:22Z","signed_body_sha256":"…","evidence_path":"<case-dir>/send-chat-receipt.json","authorization":{"kind":"attended","requester_id":"U01…","source":{"session_id":"…","instruction":"Record the reply I sent in chat"}}}}
{"status":"recorded","operation_id":"attended-9a07…","verified_by":"chat_transcript","case":{"…":"…"}}
```

Both kinds add an applied `attended-*` action with the keys every reader indexes
(`binding`, `signed_body_hash: null`, `scope_hash: null`, `purpose`, `daily_key`,
`request_hash`). They move `last_sent_at` and `next_due_at` forward, set
`awaiting_amazon` unless the case is resolved, set the sent marker of the send's
Asia/Bangkok day if unset (so a backfill never blocks today's reply),
invalidate unapplied actions that are not uncertain and bump
`authorization_revision`. A `driver_run` receipt closes its run's claim. The same
receipt again returns `already_recorded`; a different receipt for the same run
returns `receipt_conflict`.

`release` is the only way to free an action whose operations journal is already
`stalled`. The readback must post-date the attempt, match the account with
complete history and not show the signed message (`message_observed` means
reconcile and record it instead). A released action no longer blocks `adopt`,
`prepare-send` or `claim-attended`. It blocks again if its journal leaves
`stalled`.

```json
{"registry_id":"4b93…","operation_id":"case-9187…","authorization":{"kind":"attended","requester_id":"U01…","source":{"session_id":"…","instruction":"Nothing was created; release it"}},"evidence":{"readback_path":"<operations-dir>/case-9187…/case-readback-fde7….json","summary":"Seller Assistant refused; no case was created"}}
{"status":"released","operation_id":"case-9187…","case":{"…":"…"}}
```

With `run_id` instead of `operation_id`, `release` closes an open claim whose run
sent nothing, for example a chat that ended before Send. It also needs `run_dir`
(`missing_run_dir`). Its `run.json` must name the same run, account and
`registry_id` (`run_mismatch`, `account_mismatch`, `registry_binding_required`).
A `submit` attempt in its `approvals.jsonl` with a `sent` result, or without a
result line, returns `run_sent`: record that run with `record-receipt` instead,
because a chat reply can be missing from the case log. Attempts with a `blocked`
result are ignored; `uncertain` ones need the evidence below. A missing
`approvals.jsonl` means no outbound attempt.
The case-log readback must post-date the run's last claim, hold this case's
complete history and show no seller contact since the first claim; a seller
contact without a time counts unless an earlier observation already knew its ID
(`message_observed` means record it instead). A released run cannot claim again.

```json
{"registry_id":"b8b3…","run_id":"acme-12345678901-r1","run_dir":"<run-dir>","authorization":{"kind":"attended","requester_id":"U01…","source":{"session_id":"…","instruction":"The chat closed before Send; release it"}},"evidence":{"readback_path":"<run-dir>/observe-after.json","summary":"Case log shows no seller message since 10:02"}}
{"status":"released","run_id":"acme-12345678901-r1","case":{"…":"…"}}
```

A run whose submits, apart from `blocked` ones, are all `uncertain` is released
only with three more pieces, and only by an attended operator as above:

- `operator_statement`: the operator's verbatim sentence from chat that the
  message was not sent (`missing_operator_statement`);
- `evidence.page_evidence_path`: the run's latest `transcripts/NN-transcript.json`,
  captured after the last uncertain submit (`missing_page_evidence`,
  `stale_page_evidence`; a later transcript gives `page_evidence_mismatch`). Its
  `url` must equal the `url` in each uncertain submit's `steps/NN-submit.json`,
  and its `-deep.txt` must lie next to it (`page_evidence_mismatch`,
  `evidence_unavailable`). The driver marks a record whose text or deep text hit
  one of its limits (`truncated`) or whose frame it could not read
  (`deep_failed`); such a record, or one without the marks, is refused
  (`page_evidence_truncated`);
- `evidence.text_paths`: the approved text file of every uncertain submit,
  matched by SHA-256 (`missing_approved_text`).

The transcript must show the conversation as the driver saw it right before each
click, which the driver writes into the submit's attempt line as `conversation`:
the same frame, messages found structurally, the same message count and the same
last message. An empty transcript, another frame, a `-deep.txt` without that
frame, or an attempt line without the snapshot gives `page_evidence_mismatch`; a
different count or last message gives `conversation_changed`, because a sent
message the text check cannot recognise still adds a message.

Every capture the run took after a click must not show that click's text: each
transcript with its `.txt`, `-page.txt` and `-deep.txt`, and each `viewcase/`
body, counted as after the click unless its step file says it ran before. A
capture shows the text when it contains the text normalized as the driver
normalizes it before hashing, its first 120 characters after whitespace
collapsing (the driver's own sent check), or any 40-character run of the text
folded to letters and digits after NFKC and case folding, which sees through
Markdown, smart quotes, bullets, link text and invisible characters
(`message_in_page_evidence`: record the send instead). The fold may also match a
sentence the conversation already held, such as a repeated closing line; that
refuses too. The case-log readback must also post-date the last uncertain submit
(`stale_readback`). A transcript taken after the click while a contenteditable
composer still held the text counts as showing it and keeps the run open: when
the submit result says `composer_cleared: false`, the operator clears the
composer by hand before the first transcript. The release record keeps the
statement, each evidence path with its SHA-256, the uncertain submits and the
time.

```json
{"registry_id":"b8b3…","run_id":"acme-12345678901-r1","run_dir":"<run-dir>","authorization":{"kind":"attended","requester_id":"U01…","source":{"session_id":"…","instruction":"It did not go out, release the run"}},"operator_statement":"The invoice message did not go out, the chat shows nothing after Hello.","evidence":{"readback_path":"<run-dir>/observe-after.json","summary":"Case log and transcript show no seller message since 10:02","page_evidence_path":"<run-dir>/transcripts/09-transcript.json","text_paths":["<run-dir>/P3.txt"]}}
{"status":"released","run_id":"acme-12345678901-r1","case":{"…":"…"}}
```

## Seller Assistant step driver

Amazon routes new Seller Support requests through Seller Assistant, a chat that
hands over to a human associate. `seller-assistant.mjs` drives that chat one
approved step at a time. It is for attended sessions only; Grimoire never runs
it, and a case mandate does not replace the operator's approval of the exact texts.
It also sends attended replies in an existing case, through the case page's reply
form or its `Chat now` window. The
route, the approval model and case registration are described in
[the Seller Assistant route](../../skills/amazon-communications/references/seller-assistant-route.md).

One controller process holds the browser for the whole chat. Client calls queue
one command each and wait for its result; they never touch the browser.

```sh
node tools/browserctl/browserctl.mjs run --session operator -- node tools/amazon-operations/seller-assistant.mjs serve --run <dir> [--max-minutes 90] [--idle-minutes 20]
node tools/amazon-operations/seller-assistant.mjs send --run <dir> <command> [args]
```

| Command | Effect |
|---|---|
| `open [--via-lobby \| --conversation <path>]` | Record the `/cu/case-lobby` controls, then open `/assistant?client=sellerSupport-meldFullPage`, click `Get help with a new issue` with `--via-lobby`, or reopen an existing conversation path (`/assistant/amzn1.cyrano.conversation.cid.v2.<digits>?client=sellerSupport-meldFullPage`) after a restart |
| `open --case <digits>` | Open `/cu/case-dashboard/view-case?caseID=<digits>` and report whether `Reply` is present; refused once a case chat window is open |
| `state` | Read URL, frames, composer label, value and counter, visible controls, status texts, tour, access denial, and the handoff terms with their SHA-256 |
| `navigate --label <label>` | Click `Get help with a new issue`, `Show more` or `Show less`; tour labels (`Skip`, `Skip tour`, `Got it`, `Done`, `Next`, `Finish`, `Close`, `Dismiss`) only on a control inside the tour container; `Request changes` while one or more email-case Issue summaries show `Approve`: the click goes to the last summary's `Request changes`, only after the page re-reads the exact terms text that `state` reported, and only when every `Approve` has its own `Request changes`; `Reply` only on the case page opened with `open --case` |
| `type --text-file <f> --sha256 <h>` | Insert the text into the empty composer and read it back; never submits. Multi-line text only into a `TEXTAREA` composer |
| `submit --expect-sha256 <h> --approval-file <f> [--expect-attachment <name>]... [--label Submit\|Send\|"Chat now"]` | Click the composer's `Submit` (default), `Send` or `Chat now` when the composer, the expected hash and the approval agree |
| `approve --expect-terms-sha256 <h> --approval-file <f>` | Click the handoff `Approve` when the terms hash matches |
| `attach --file <path> --sha256 <h> --approval-file <f>` | Set one file on the chat's file input and wait for its chip; never submits |
| `transcript [--wait-new <n>] [--timeout <s>]` | Save and print the conversation text and a structural outline, plus `page_text` (`transcripts/NN-transcript-page.txt`) and a shadow-piercing `deep_text` of every frame (`transcripts/NN-transcript-deep.txt`); denial detection reads all three |
| `screenshot [--name <label>]` | Identity-verified screenshot with its receipt |
| `viewcase-raw --case-id <digits>` | Save the raw ViewCase JSON; print a summary without emails or senders |
| `stop` | Release the task tab and exit |

`send` exits 0 for `ok`, `sent`, `approved` and `attached`, 1 for any other
result status (`refused`, `blocked`, `uncertain`, `timeout`, `expired`, `error`,
`sent_identity_unverified`, `approved_identity_unverified`,
`attached_identity_unverified`), and 2 when no result arrived. The three
`*_identity_unverified` statuses mean the action happened but the identity check
after it failed, so the controller halted. Every queued command carries
`expires_at` and the `send` client's `client_pid`; one without either is refused
as `command_malformed`. `send` itself refuses with `attended_context_required`
under `WIZARDS_AI_MODE` or inside a `wizards-ai-*` unit, before it queues
anything. `serve` reads the client's `/proc/<pid>/cgroup` (never its environment)
and refuses a command from a `wizards-ai-*` unit (`attended_context_required`) or
from a client that has exited (`client_gone`).

Before it runs a command, `serve` writes `results/NNN.running`, and every
`approvals.jsonl` line carries the command's `queue_id`. When `send` gives up
(`serve_exited` or `client_timeout`) it checks both. If `serve` had started the
command, the answer is `uncertain` and nothing is cancelled; with `serve` gone
it also writes that `uncertain` result. Only a command that never started gets
a `cancelled` result, which a later `serve` skips. On startup, `serve` marks
every command with a leftover marker, or with an attempt line and no result
line, as `uncertain` (`interrupted`) and never runs it again. SIGTERM, SIGINT,
an uncaught exception or an unhandled rejection marks the command in flight the
same way before the tab is released as `error`. The handler first sets an
aborting flag, before any wait, so no click, insert or upload starts after the
interrupt, and no new command starts. The client then reads `uncertain`
(`interrupted`) or `blocked` (`aborting`) for the stopped action. Nothing was
clicked in either case.

Safety model:

- Only `Submit`, `Send`, `Chat now`, `Approve`, `Reply` and the navigation labels
  above can be clicked. The driver never presses Enter, never opens `Open the tool`
  and never drives a new tab, except the one case chat window `Chat now` opens.
- `submit --label "Chat now"` takes the approval of the message the chat will
  deliver and no attachment. It needs `open --case` first and `signature_name` in
  `run.json` (the one `sign` returned; claim-attended refuses another). It fills "Your name" with that name and the composer with the
  constant opening line `Hello.`, clicks once, and adopts exactly one new
  same-origin `/hill/website/chat` window with `formType=reply`, this case ID and
  the task tab as opener, bound as the `case-chat` slot of the same task. Later
  commands drive that window; any other new tab halts the run. It is logged as
  `command: chat_now`, so a receipt does not count it as a message, and runs once
  per run. A click that opens a new page target halts `serve`. For `submit` and
  `approve` the status still reports the delivery (`sent`, `approved` or
  `uncertain`) with reason `new_target`, so a sent message never reads as unsent.
- A tour label is clicked only when a dialog, tooltip or popover holding the
  `Step N/M` text is found outside the conversation and the composer, and the
  label matches exactly one control inside that container. `Step N/M` text in a
  chat message is not a tour.
- `type` refuses text containing a line break unless the composer is a
  `TEXTAREA`: `Input.insertText` commits each line break as an edit that a
  rich-text chat editor may treat as Enter. The first live run records how the
  composer handles it.
- `submit` clicks only when the SHA-256 of the composer text equals
  `--expect-sha256` and the approval file's `sha256`. The composer must be
  enabled, and its `Submit` (or the `--label` control) must be the only visible
  one in the frame (enabled or disabled), enabled, and inside the composer's region, the nearest
  ancestor that also holds `Submit` or `Upload file`. A region that spans the
  conversation does not count. The page repeats this check when it looks up the
  control for the click. Attachments are bound to this run: every file shown as
  a chip or held by the file input, and every `--expect-attachment` name, must
  be a file this run's `attach` logged as `attached`, and the expected names must
  equal the files present (none when omitted). A file in the input with no
  detected chip is refused. A `submit` that carried a file uses it up once it is
  sent or uncertain; a chip with the same name then needs a new approved
  `attach`. It
  waits up to 30 seconds for a busy assistant (`Working on it` or a progress
  indicator) to finish, and checks the composer, chips, upload state and
  `Submit` again after the identity read, right before the click. The page
  lookup that returns `Submit`, `Send` or `Chat now` compares the composer text
  with the approved text (for `Chat now`, the opening line `Hello.`) once more
  and fails with `composer_changed` when they differ. It then waits up to 60 seconds for the composer to clear and the text to appear
  once more in the conversation, and reports `sent` or `uncertain`. An uncertain
  send is never retried. Each approved hash is sent once per run. A P2 approval
  may be sent twice, and only when its text is exactly "Please connect me with a
  Seller Support associate."; a P2 approval of any other text is sent once.
- `approve` waits for a busy assistant like `submit`, and reports `approved`
  only when, after the click, the `Approve` control is gone or disabled or the
  composer label changed, on two consecutive scans with a valid frame selection
  and the `Approve` frame still reachable. A new message alone, or one empty
  scan during a re-render, gives `uncertain`.
- After a Submit or Approve click or a file upload, any failure, including a
  replaced frame or a failed log write, is reported as `uncertain` with
  `clicked: true` or `attached: true` and a result line in `approvals.jsonl`,
  never as a plain `error`.
- `approve` hashes the text of the container around the unique `Approve`
  control: the nearest dialog, card or message ancestor with text outside any
  button (basis `card`), else the smallest ancestor with such text (basis
  `smallest_text`), never one holding the composer or the whole conversation.
  `state` shows that text, hash and basis; screenshot the terms before asking
  for approval. The hash normalizes line endings, collapses spaces within a line and
  drops blank lines.
- `attach` first copies the file to `uploads/NN/<name>` in the run directory,
  hashes the copy, and uploads the copy, so a later change to the source file
  cannot reach Amazon. The approval hash, `--sha256` and the copy's hash must
  match, with an enabled `Upload file` control and exactly one file input.
- Seller and marketplace are verified before and after every command and again
  right before each outbound click. The check reads the live header and the
  GetUserContext IDs. A live seller or marketplace ID that differs from
  `run.json` stops at once. When a page lacks one or both live IDs, the IDs read
  on `/home` at startup fill only the missing ones, together with the exact
  header, as the case adapter does. Read errors during a re-render are retried
  for 15 seconds. A mismatch halts `serve`, which releases the tab as `error`.
- The driver works in the one same-origin frame, main frame included, that
  holds exactly one visible composer. It evaluates each frame in an isolated
  world, reused until the frame loads a new document. Zero or several
  composers, or a cross-origin frame whose URL looks like the chat, block with
  details. Other cross-origin frames (ads, metrics) are ignored rather than
  stopping the run, because Seller Central pages carry them routinely.
- It never reads cookies, storage or tokens.

Text for `type` and approved texts must already be normalized: UTF-8 without a
byte order mark, LF line endings, no leading or trailing newline, at most 2,500
characters (JavaScript string length). Then `sha256sum <file>` equals the hash
that `type`, `submit` and the approval use.

Approval files are JSON:
`{"schema_version":1,"plan_item":"P1|P2|P3|approve|attachment|followup","sha256":"<hex>","run_id":"<run.json run_id>","seller_id":"<run.json account.seller_id>","approved_at":"<ISO time with timezone>","approval_text":"<operator's verbatim approval>","label":"routine"}`.
Text items (P1, P2, P3, followup) need `label`: `routine`, `appeal`, `dispute`,
`refund_request`, `commitment` or `admission` (`approval_label_missing`,
`approval_label_invalid`). It is written to `approvals.jsonl`. On a run with
`registry_id`, their `approval_text` must equal `authorization.source.instruction`
(`approval_instruction_mismatch`), unless the approval carries its own attended
`authorization` whose `source.instruction` is its `approval_text` and which has a
`source.session_id`: a text the operator approved later in the same chat. A
malformed one returns `approval_authorization_invalid`. The claim before the click
passes the approval's own authorization, and the receipt accepts it.
`run_id` and `seller_id` must equal `run.json`, so an approval never carries
over to another run or account. `approved_at` must be a real calendar time with
a timezone and not later than the controller clock plus five minutes.
`submit` accepts P1, P2, P3 and followup, `approve` accepts approve, and
`attach` accepts attachment.

The run directory holds `run.json`:
`{"schema_version":1,"run_id":"<slug>","account":{"profile_key","client_slug","marketplace","seller_id","marketplace_id","seller_central_name","marketplace_label","parent_account_name","context_binding"}}`
with every account value a non-empty string. `context_binding` is optional and
copied from the case policy when the profile has one:
`{"seller_id","marketplace_id","unique_label_mapping":true}` with the account's
own IDs; anything else is refused. A reply run adds `registry_id`, `baseline`
(`{"last_sent_at": <sign result>}`) and an attended `authorization` with
`source.instruction`, all three together; the driver then writes
`claim-attended.json` and runs `case_service.py claim-attended` before every
`submit`, `Chat now`, `approve` and `attach`, with the opened `case_id` and, when
set, `signature_name`; any refusal returns `refused` (`claim_refused`, with
`claim_reason`) before the attempt line. Without `registry_id`, `open --case`,
`Chat now` and any `submit` on a case page or its chat window refuse
`registry_binding_required`. `signature_name` is the one-line name for the chat
form, at most 100 characters. The driver writes `queue/NNN.json`,
`results/NNN.json`, `results/NNN.running` while a command runs,
`steps/NN-<command>.json` (URL, frames, controls, composer state and result for
every command), `approvals.jsonl` (the approval and outcome of every outbound
attempt, with its `queue_id`), `uploads/`, `transcripts/`, `screenshots/`,
`viewcase/`, `serve.pid` and `serve.json`.

`serve` runs in the operator session on 9222 or in the Grimoire session on
9223, and only attended: under `WIZARDS_AI_MODE` or inside a `wizards-ai-*` unit
it refuses with `attended_context_required` on either session, before it reads
the run directory. It acquires one task tab (`amazon-communications`, exclusive Seller Central
context) and switches to the account. On 9223 it keeps the 9223 lock until it
exits, so scheduled Grimoire browser jobs defer for that time; on 9222 there is no
port lock, only the task tab's region claim. `stop` releases the tab as `success`. An exception or
SIGTERM releases it as `error`; so do a halt, `--max-minutes` and
`--idle-minutes`, which keeps the chat tab in a two-hour inspection lease. A
`transcript` wait never runs past the `--max-minutes` budget. The conversation-area
and attachment-chip detection is a heuristic until the first live run records
the real page structure.

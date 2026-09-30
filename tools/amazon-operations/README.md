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

## Seller Assistant step driver

Amazon routes new Seller Support requests through Seller Assistant, a chat that
hands over to a human associate. `seller-assistant.mjs` drives that chat one
approved step at a time. It is for attended sessions only; Grimoire never runs
it, and a case mandate does not replace the operator's send-plan approval. The
route, the approval model and case registration are described in
[the Seller Assistant route](../../skills/amazon-communications/references/seller-assistant-route.md).

One controller process holds the browser for the whole chat. Client calls queue
one command each and wait for its result; they never touch the browser.

```sh
node tools/browserctl/browserctl.mjs run --session grimoire -- node tools/amazon-operations/seller-assistant.mjs serve --run <dir> [--max-minutes 90] [--idle-minutes 20]
node tools/amazon-operations/seller-assistant.mjs send --run <dir> <command> [args]
```

| Command | Effect |
|---|---|
| `open [--via-lobby]` | Record the `/cu/case-lobby` controls, then open `/assistant?client=sellerSupport-meldFullPage`, or click `Get help with a new issue` with `--via-lobby` |
| `state` | Read URL, frames, composer label, value and counter, visible controls, status texts, tour, access denial, and the handoff terms with their SHA-256 |
| `navigate --label <label>` | Click `Get help with a new issue`, `Show more` or `Show less`; tour labels (`Skip`, `Skip tour`, `Got it`, `Done`, `Next`, `Finish`, `Close`, `Dismiss`) only on a control inside the tour container; `Request changes` only while exactly one `Approve` control is visible (an email-case Issue summary) |
| `type --text-file <f> --sha256 <h>` | Insert the text into the empty composer and read it back; never submits. Multi-line text only into a `TEXTAREA` composer |
| `submit --expect-sha256 <h> --approval-file <f> [--expect-attachment <name>]...` | Click `Submit` when the composer, the expected hash and the approval agree |
| `approve --expect-terms-sha256 <h> --approval-file <f>` | Click the handoff `Approve` when the terms hash matches |
| `attach --file <path> --sha256 <h> --approval-file <f>` | Set one file on the chat's file input and wait for its chip; never submits |
| `transcript [--wait-new <n>] [--timeout <s>]` | Save and print the conversation text and a structural outline |
| `screenshot [--name <label>]` | Identity-verified screenshot with its receipt |
| `viewcase-raw --case-id <digits>` | Save the raw ViewCase JSON; print a summary without emails or senders |
| `stop` | Release the task tab and exit |

`send` exits 0 for `ok`, `sent`, `approved` and `attached`, 1 for any other
result status (`refused`, `blocked`, `uncertain`, `timeout`, `expired`, `error`,
`sent_identity_unverified`, `approved_identity_unverified`,
`attached_identity_unverified`), and 2 when no result arrived. The three
`*_identity_unverified` statuses mean the action happened but the identity check
after it failed, so the controller halted. Every queued command carries
`expires_at`; one without it is refused as `command_malformed`.

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

- Only `Submit`, `Approve` and the navigation labels above can be clicked. The
  driver never presses Enter, never opens `Open the tool` and never drives a new
  tab. A click that opens a new page target halts `serve`. For `submit` and
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
  enabled, and its `Submit` must be the only visible `Submit` in the frame
  (enabled or disabled), enabled, and inside the composer's region, the nearest
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
  `Submit` again after the identity read, right before the click. It then waits up to 60 seconds for the composer to clear and the text to appear
  once more in the conversation, and reports `sent` or `uncertain`. An uncertain
  send is never retried. Each approved hash is sent once per run; P2 twice.
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
`{"schema_version":1,"plan_item":"P1|P2|P3|approve|attachment|followup","sha256":"<hex>","run_id":"<run.json run_id>","seller_id":"<run.json account.seller_id>","approved_at":"<ISO time with timezone>","approval_text":"<operator's verbatim approval>"}`.
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
own IDs; anything else is refused. The driver writes `queue/NNN.json`,
`results/NNN.json`, `results/NNN.running` while a command runs,
`steps/NN-<command>.json` (URL, frames, controls, composer state and result for
every command), `approvals.jsonl` (the approval and outcome of every outbound
attempt, with its `queue_id`), `uploads/`, `transcripts/`, `screenshots/`,
`viewcase/`, `serve.pid` and `serve.json`.

`serve` runs only in the Grimoire session on 9223. It acquires one task tab
(`amazon-communications`, exclusive Seller Central context), switches to the
account and keeps the 9223 lock until it exits, so scheduled Grimoire browser
jobs defer for that time. `stop` releases the tab as `success`. An exception or
SIGTERM releases it as `error`; so do a halt, `--max-minutes` and
`--idle-minutes`, which keeps the chat tab in a two-hour inspection lease. A
`transcript` wait never runs past the `--max-minutes` budget. The conversation-area
and attachment-chip detection is a heuristic until the first live run records
the real page structure.

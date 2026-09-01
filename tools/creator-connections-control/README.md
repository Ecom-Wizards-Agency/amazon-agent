# Creator Connections Control Runner

Local, deterministic control layer for Creator Connections. It is deliberately separate from Amazon and Google credentials: it resolves creator identity, computes the strict qualification gate, creates the daily action queue, and validates a proposed MCF order before any paid action.

It never sends a message, writes a tracker row, or creates an MCF order by itself. The operating skill or future API worker may perform those actions only after this runner returns `PASS` for the same Creator Record ID.

The shared tracker is the durable system of record. The JSON registry passed to this tool is a private, synchronized run cache of the tracker's `Creator Registry` tab. Refresh it from the tracker at the start of every run, write successful results back to the tracker and action log, and do not treat a leftover local file as authoritative.

## Setup

Set a local HMAC secret once. Do not commit it or put it in a tracker.

```powershell
$env:CREATOR_CONTROL_HMAC_KEY = "use-a-long-random-local-secret"
```

The registry contains opaque HMAC fingerprints for storefront, thread, email, phone, address, and full name. It does not keep raw contact details or raw identity links. Raw contact data and visible links remain only in the approved private tracker.

## Commands

```powershell
# Resolve or issue an immutable Creator Record ID.
python tools/creator-connections-control/creator_control.py register `
  --registry _local/creator-connections/registry.json `
  --record _local/creator-connections/inbox-record.json

# Recompute the 10-point qualification gate from visible evidence.
python tools/creator-connections-control/creator_control.py score `
  --record _local/creator-connections/inbox-record.json

# Produce today's machine-readable action queue. This does not send anything.
python tools/creator-connections-control/creator_control.py queue `
  --input _local/creator-connections/daily-sweep.json `
  --output _local-output/creator-connections/daily-queue.json

# Migrate historic tracker rows only after the sweep has captured their stable
# Creator Connections thread key and campaign ID. Held rows are not changed.
python tools/creator-connections-control/creator_control.py migrate-legacy `
  --registry _local/creator-connections/registry.json `
  --input _local/creator-connections/legacy-candidates.json `
  --output _local-output/creator-connections/legacy-migration.json

# Validate a proposed one-unit MCF order before it is placed.
python tools/creator-connections-control/creator_control.py preflight `
  --registry _local/creator-connections/registry.json `
  --input _local/creator-connections/mcf-proposal.json

# Validate an MCF-blocked product switch before offering it, then validate the
# creator's explicit alternate-ASIN confirmation before changing the tracker.
python tools/creator-connections-control/creator_control.py preflight-switch `
  --registry _local/creator-connections/registry.json `
  --input _local/creator-connections/product-switch.json

# Lock the exact record/ASIN after a passing pre-flight, then confirm it only
# after the authorized worker has a real Amazon order ID and evidence reference.
python tools/creator-connections-control/creator_control.py reserve-mcf --registry <registry> --input <proposal>
python tools/creator-connections-control/creator_control.py confirm-mcf --registry <registry> --creator-record-id <id> --asin <asin> --order-id <order-id> --evidence-reference <private-evidence-path>
```

Exit code `0` means the control result passed. Exit code `2` means it is safely held. The JSON output is the audit artifact to reference from the tracker and action log.

## Identity rules

The runner resolves a creator only by this priority order:

1. Canonical storefront URL or storefront slug.
2. Stable Creator Connections thread key plus campaign context.
3. At least two verified contact fingerprints.

A display name, first name, or address alone can never resolve a record. A conflicting identifier or a match to more than one active record produces `CONFLICT`, locks the record, and prevents messaging, movement, or fulfillment.

## Legacy migration

Historic tracker rows are intentionally not assigned IDs from their row position or visible name. During the next full sweep, capture the stable Amazon thread key and campaign ID for each legacy row, then run `migrate-legacy`. It returns `READY_TO_SYNC` for a provable record and `HELD` for every ambiguity. Write IDs back to the private tracker only for `READY_TO_SYNC` rows. This is how the system avoids falsely deciding that two similarly named creators are the same person.

## Strict 10/10 gate

The score is computed, not typed manually. Each item is worth one point: complete fulfillment details, requested ASIN, exact product match, storefront, recent visible post, strong content quality, strong category fit, performance/revenue evidence, specific ASIN mention, and low spam risk. Only exactly `10/10` is eligible for `Approved for Sample`.

`preflight` also requires one resolved record, the matching ASIN/SKU in the approved product catalog, verified FBA/MCF eligibility, enough currently fulfillable units, a dated private evidence reference for the inventory check, no prior sample for that creator and ASIN, one unit, Standard shipping, fee within the approved cap, complete address/contact data, and no UI validation or truncation warnings. An active FBM listing never satisfies the MCF gate.

The selected catalog item uses these fulfillment fields:

```json
{
  "asin": "B0EXAMPLE1",
  "sku": "SKU-1",
  "fulfillment_channel": "FBA",
  "mcf_fulfillable": true,
  "fulfillable_quantity": 10,
  "inventory_checked_at": "2026-08-05T10:00:00Z",
  "fulfillment_evidence_reference": "private-evidence/mcf-search.json"
}
```

`preflight-switch` has two phases. `offer` proves the original ASIN has a documented MCF blocker and that the proposed alternative is in the same campaign, has an exact SKU mapping, and is FBA/MCF-fulfillable before the creator is contacted. `confirm` additionally requires the creator's explicit reply naming that alternate ASIN and a private thread evidence reference. Until `confirm` passes, keep `Product Switch Pending`, keep Sample Decision `Hold`, and do not change the active ASIN or create an order.

After a passing pre-flight, `reserve-mcf` writes a record lock for that exact Creator Record ID and ASIN. The executor cannot use another creator's data while the lock exists. `confirm-mcf` releases the lock only when it receives the resulting Amazon order ID and private evidence reference. A failed order stays locked and is escalated. This protects against double-sends and concurrent operators.

Registry mutations are serialized through a per-registry lock file. Each command rereads the registry after it owns the lock and replaces the JSON atomically only after the mutation succeeds. Concurrent reservations for the same creator/ASIN therefore produce one lock and one held result. A leftover `.lock` file indicates an interrupted process and must be reviewed rather than bypassed automatically.

## Daily action queue

The `queue` command creates a dated action for every actionable record. It schedules verification and missing-detail follow-ups every two days, and content follow-ups three days after expected delivery then every two days. Message actions use `PENDING_APPROVAL`; a queue item never grants send authority. At the configured limit it emits a PII-free escalation instead of another message action. It can queue `MCF_PREFLIGHT`, but cannot place an order. Until SP-API is authorized, confirmed paid MCF placement remains a controlled operator/API worker step.

Input fixtures use generic data only. Keep real run files under `_local/creator-connections/` and outputs under `_local-output/creator-connections/`, both ignored by Git.

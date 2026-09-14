# Browser lifecycle controller

## Problem

The two Amazon CDP browsers share process and tab state across attended and unattended work. The old launcher restarted Chrome whenever a caller requested a different mode, and the Wizards AI health pass treated every non-standby page as disposable. At the same time, removing cleanup entirely previously allowed tabs to accumulate. The controller therefore needs ownership-aware cleanup without making every runner understand cleanup policy.

## Usage

```bash
node tools/browserctl/browserctl.mjs ensure --port 9223
node tools/browserctl/browserctl.mjs status --port 9223
node tools/browserctl/browserctl.mjs lease release --port 9223 --target TARGET --outcome success
node tools/browserctl/browserctl.mjs cleanup --audit-only
node tools/browserctl/browserctl.mjs cleanup
node tools/browserctl/browserctl.mjs auth --port 9223 --target TARGET
node tools/browserctl/browserctl.mjs restart --port 9223 --mode headed --reason "operator maintenance"
```

Normal JavaScript workflows acquire pages through
`tools/browserctl/task-tabs.mjs`. Each workflow provides a stable task ID and
usually uses its `primary` slot. Repeated steps and retries reacquire that exact
target. The target is registered as `background-active`, receives one atomic
lease/controller/claim renewal while its CDP session is open, and is released with an
explicit outcome. Callers never coordinate registry files, timeouts, activity
probes, or raw target closure themselves.

Retention and ownership are separate. The two-hour inspection window preserves
evidence; heartbeat recovery or tracker installation does not establish observed
interaction. Retrying a retained page first reads its versioned input tracker
without navigating it, then atomically validates the binding and lease generation.
Pointer, keyboard and wheel events count as observed interaction, not proof of a
human actor. Lifecycle events remain part of cleanup retention only.

`TASK_TAB_BUSY: observed-interaction` means input occurred after the latest release
or expired controller deadline. `TASK_TAB_INTERACTION_UNKNOWN` means the retained
page lacks continuous, compatible evidence for that unattended interval. Neither
error promises that waiting until the retention deadline will permit reuse;
safe cleanup or an explicit reviewed `allowOperatorActivity` recovery is required.
Connection failure preserves the target and never authorizes a replacement.

Seller Central readers and account switchers declare their intended context:

```js
const page = await acquireTaskPage({
  taskId, workflow: "amazon-reporting", exclusiveContext: true,
  sellerCentral: { marketplace: "us", origin: "https://sellercentral.amazon.com" },
});
```

The controller derives one region claim per port: `sc:na` (US/CA/MX), `sc:eu`
(supported EU marketplaces and UK/GB), or `sc:au` (AU). Different groups run
concurrently; accounts within the same group serialize. Marketplace/origin
contradictions fail before browser work. Same-group routing is valid, including
French POE data through the German site. Brazil and Turkey stay unmapped.

Keep the claim from selection and identity verification through the dependent
operation, using the acquired session throughout. The report fetcher retains one
claim across its entire batch. Nonexclusive tasks and different ports remain
independent. Omitting the descriptor keeps global exclusion, as do unmapped or
mixed-region workflows. FlatFilePro and mixed-region diagnostics retain this
conservative default. A descriptor requires `exclusiveContext: true`.

A session cannot change its region. The shared account switcher checks the target
origin and canonical `marketplace` code before selection; regional callers must
supply that code alongside the exact picker label. Explicit navigation to another
Seller Central group is rejected, and observed top-level redirects to another
group invalidate the handle. Authentication transitions retain the claim; dependent
work resumes only after account, marketplace and region verification.

`TASK_TAB_BUSY: browser-context-busy` includes the blocking scope and port.
`TASK_TAB_CONTEXT_MISMATCH` identifies contradictory routing facts;
`TASK_TAB_SCOPE_CONFLICT` protects a retained target from a different region.
Neither an activity override nor a different client bypasses an active claim.

Schema-v1 regional claims are additive. The existing per-port claim slot holds
an atomically derived compatibility guard while regional owners exist, so old
acquisition code still sees a busy port. Each renewal checks both the exact
regional claim and that guard; losing either permanently invalidates ownership.
Releasing one region preserves the others. Shipment label downloads additionally
hold a short per-port download claim while setting Chrome's shared download
folder and collecting PDFs. Other regional work continues; competing label
download phases receive `TASK_TAB_DOWNLOAD_BUSY` before changing that folder.
Download ownership renews and expires with its task controller. Live legacy global claims finish
unchanged. An inactive unscoped task can narrow only after its normal interaction
probe and binding checks show a compatible target; ambiguous retained pages keep
global exclusion. IDs, retained targets and retention deadlines are preserved.

Deploy after old managed runners finish naturally. Subsequent runner and cleanup
invocations must load the updated code. Do not reset the registry, close retained
tabs or restart Chrome for this upgrade. Compatibility protects old acquisition
code; already-running old operations do not gain the new fencing guarantees.

Managed sessions check their controller and context claim before each command and
before delivering its result. Renewal updates the controller, context claim and
lease in one transaction. Ownership expiry, registry failure or transport loss
invalidates the handle with `TASK_TAB_CONTROL_LOST` and disconnects it without
closing the tab. Do not automatically resume an interrupted write: a command
already running in Chrome may still finish after the local connection closes.
This is cooperative coordination; raw CDP clients and human account changes can
bypass it, so workflows still verify identity before using data or taking action.

The three Seller Central home pages on each port are permanent anchors. They are
not a pool of working tabs and automation never navigates them. A new target is
created only when a task slot has no target, a named additional slot is required
for genuinely separate work, a site opens its own popup, or the operator asks
for one. `cdp.mjs` rejects unkeyed target creation and unknown option names. This
prevents old `createPage({purpose: ...})` callers from silently opening a new tab
on every retry.

## Shape

- `policy.mjs` validates the machine-local browser policy and provides conservative defaults when no policy is installed.
- `context-scopes.mjs` owns the exact Seller Central marketplace/origin groups and coverage rules.
- `lease-registry.mjs` owns the atomic registry and its lock. It exposes domain operations instead of storage primitives.
- `browserctl.mjs` is the process, anchor, cleanup, authentication, and explicit-restart shell.
- `task-tabs.mjs` owns stable `(port, taskId, slot)` bindings, task control
  tokens, browser-context claims, and reuse or recovery of the bound CDP target.
- `cdp.mjs` remains the direct CDP data plane. Fresh-target access is restricted
  to anchor maintenance and `task-tabs.mjs`.

The public surface is intentionally small: ensure a browser, acquire/touch/release a lease, run safe cleanup, authenticate an allowlisted target, or perform an explicit restart. Storage representation, activity instrumentation, cooldowns, and closure claims remain private.

Cleanup follows the machine policy. Evo X1 runs active cleanup every five
minutes; standard presets remain audit-only. Even in active mode, only an
expired registered lease can be closed after an activity probe and atomic
claim. Evo X1 atomically adopts a newly observed unregistered page as an
inspection lease, installs activity measurement, and waits the full two-hour
window before it can become a close candidate. Standard presets continue to
leave unknown tabs outside cleanup.

Cleanup returns `complete` and a `status` of `complete`, `deferred`, or
`incomplete`. Session contention defers cleanup until a later timer pass without
changing the tab's activity history. Failed activity measurements preserve the
tab and report the failing probe stage and sanitized error; incomplete passes
exit nonzero. A renderer timeout is not treated as a missing tracker.

The same five-minute pass maintains anchors additively on each reachable
managed browser. It creates a missing US, DE, or AUS anchor and replaces a
navigated anchor only after reclassifying the original page as interactive.

Machine routing uses the shared `grimoire` session on port 9223 for Amazon work
from direct chat and Slack. Port 9222 is explicit operator work. T3 Code's in-app browser is explicit-only and is not
a silent fallback from a failed managed CDP session.

## Synthesis decision

The selected design keeps CDP as the data plane and puts target creation behind
a shared keyed-task module. A Python-owned controller was rejected because it
would duplicate the mature WebSocket, page-evaluation, and authentication
behavior already used by Node runners. An always-on daemon was rejected because
it would add process supervision and a new failure point without improving the
required invariants. A documentation-only timeout change was rejected because
repository history shows both destructive cleanup and unbounded accumulation.

## Tradeoffs accepted

- We accept short-lived filesystem lock contention in exchange for a dependency-free registry shared by many Node processes.
- We accept a two-hour delay for newly discovered Evo X1 tabs so cleanup can measure activity before deciding they are disposable.
- We accept delayed cleanup when no controller pass runs in exchange for guaranteeing tabs never close before their lease permits it.
- We accept exact per-site authentication adapters in exchange for refusing unsafe generic password filling.

## Open risks

- A missing page activity tracker receives one conservative two-hour inspection
  window. Repeated tracker installation without measured activity does not slide
  that expiry forever. If installation or the follow-up read fails, the tab is
  preserved.
- Authentication item discovery fails when more than one accessible Login item declares the same exact origin. The route must then be pinned to one item reference.

## Rollout state

The interaction fields are additive within registry schema v1. Existing records
without compatible evidence remain unknown and protected. Installing a new
tracker cannot reconstruct historical input. Preserve live claims and tabs; never
reset the registry as an upgrade step. Let old managed runners finish before
deploying, and ensure subsequent runner and cleanup invocations load the updated
modules. Already-running Node processes retain their loaded code, so mixed
versions do not have the new ownership guarantees. Chrome need not restart.

Temporary-target callers release outcome-based leases. Evo X1 active cleanup
was enabled after its candidate log was reviewed. Standard machine presets
remain audit-only.

## Shared Amazon session

Direct chat and Slack both use `grimoire` (9223). `operator` (9222) is explicit separate work. Run a browser command with:

```sh
node tools/browserctl/browserctl.mjs run --session grimoire -- node tools/opportunity-explorer/run-poe.mjs doctor --origin https://sellercentral.amazon.com
```

`browserctl session --session grimoire` returns only the resolved non-secret environment. Python workers use `browser_session.py` as an adapter to that same resolver. The session is immutable within a process; conflicting ports or profiles fail before connection. Child workers inherit the route and a scoped lock chain. Sibling workers contend for the next link instead of bypassing serialization. Browser-independent MCP/API work needs no browser lock.

The existing task controller still owns workflow IDs, regional claims, stable targets, heartbeat and cleanup. Screenshots call `captureTaskEvidence(handle, {expected})` in the owning worker. Standalone audit captures require the retained `taskId`, `workflow`, `targetId`, and expected identity; they cannot search for a matching tab or replace a missing target. Supported identities are Seller Central seller/marketplace, DataDive niche/hero keyword, and Amazon retail marketplace plus ASIN or search query. Capture receipts retain actual verified identity separately from report association.

A browser login grants no additional action rights. DataDive login recovery occurs in 9223. Extension-only capabilities must be demonstrated in that profile; missing support never redirects work to 9222.

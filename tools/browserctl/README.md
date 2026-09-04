# Browser lifecycle controller

## Problem

The two Amazon CDP browsers share process and tab state across attended and unattended work. The old launcher restarted Chrome whenever a caller requested a different mode, and the Wizards AI health pass treated every non-standby page as disposable. At the same time, removing cleanup entirely previously allowed tabs to accumulate. The controller therefore needs ownership-aware cleanup without making every runner understand cleanup policy.

## Usage

```bash
node tools/browserctl/browserctl.mjs ensure --port 9222
node tools/browserctl/browserctl.mjs status --port 9223
node tools/browserctl/browserctl.mjs lease release --port 9222 --target TARGET --outcome success
node tools/browserctl/browserctl.mjs cleanup --audit-only
node tools/browserctl/browserctl.mjs cleanup
node tools/browserctl/browserctl.mjs auth --port 9222 --target TARGET
node tools/browserctl/browserctl.mjs restart --port 9223 --mode headed --reason "operator maintenance"
```

Normal JavaScript workflows acquire pages through
`tools/browserctl/task-tabs.mjs`. Each workflow provides a stable task ID and
usually uses its `primary` slot. Repeated steps and retries reacquire that exact
target. The target is registered as `background-active`, receives both lease and
task-control heartbeats while its CDP session is open, and is released with an
explicit outcome. Callers never coordinate registry files, timeouts, activity
probes, or raw target closure themselves.

The three Seller Central home pages on each port are permanent anchors. They are
not a pool of working tabs and automation never navigates them. A new target is
created only when a task slot has no target, a named additional slot is required
for genuinely separate work, a site opens its own popup, or the operator asks
for one. `cdp.mjs` rejects unkeyed target creation and unknown option names. This
prevents old `createPage({purpose: ...})` callers from silently opening a new tab
on every retry.

## Shape

- `policy.mjs` validates the machine-local browser policy and provides conservative defaults when no policy is installed.
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

The same five-minute pass maintains anchors additively on each reachable
managed browser. It creates a missing US, DE, or AUS anchor and replaces a
navigated anchor only after reclassifying the original page as interactive.

Machine routing makes port 9222 the normal browser default and reserves port
9223 for Wizards AI reads. T3 Code's in-app browser is explicit-only and is not
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

Temporary-target callers release outcome-based leases. Evo X1 active cleanup
was enabled after its candidate log was reviewed. Standard machine presets
remain audit-only.

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

Normal JavaScript callers continue to use `tools/report-fetcher/cdp.mjs`. A newly created target is registered as `background-active`, receives a heartbeat while its CDP session is open, and is released with an explicit outcome. Callers never coordinate registry files, timeouts, activity probes, or raw target closure themselves.

## Shape

- `policy.mjs` validates the machine-local browser policy and provides conservative defaults when no policy is installed.
- `lease-registry.mjs` owns the atomic registry and its lock. It exposes domain operations instead of storage primitives.
- `browserctl.mjs` is the process, anchor, cleanup, authentication, and explicit-restart shell.
- `cdp.mjs` remains the direct CDP data plane and registers every created target through the lease API.

The public surface is intentionally small: ensure a browser, acquire/touch/release a lease, run safe cleanup, authenticate an allowlisted target, or perform an explicit restart. Storage representation, activity instrumentation, cooldowns, and closure claims remain private.

Cleanup follows the machine policy. Evo X1 runs active cleanup every five
minutes; standard presets remain audit-only. Even in active mode, only an
expired registered lease can be closed after an activity probe and atomic
claim. Unknown tabs are absent from cleanup entirely.

The same five-minute pass maintains anchors additively on each reachable
managed browser. It creates a missing US, DE, or AUS anchor and replaces a
navigated anchor only after reclassifying the original page as interactive.

Machine routing makes port 9222 the normal browser default and reserves port
9223 for Wizards AI reads. T3 Code's in-app browser is explicit-only and is not
a silent fallback from a failed managed CDP session.

## Synthesis decision

The selected design keeps direct CDP calls and adds a shared lifecycle module. A Python-owned controller was rejected because it would duplicate the mature WebSocket, page-evaluation, and authentication behavior already used by Node runners. An always-on daemon was rejected because it would add process supervision and a new failure point without improving the required invariants. A documentation-only timeout change was rejected because repository history shows both destructive cleanup and unbounded accumulation.

## Tradeoffs accepted

- We accept short-lived filesystem lock contention in exchange for a dependency-free registry shared by many Node processes.
- We accept that unregistered tabs can accumulate in exchange for never guessing that a user-owned tab is disposable.
- We accept delayed cleanup when no controller pass runs in exchange for guaranteeing tabs never close before their lease permits it.
- We accept exact per-site authentication adapters in exchange for refusing unsafe generic password filling.

## Open risks

- A missing page activity tracker is reinstalled and starts a fresh two-hour inspection window. If installation or the follow-up read fails, the tab is preserved.
- Authentication item discovery fails when more than one accessible Login item declares the same exact origin. The route must then be pinned to one item reference.

## Rollout state

Temporary-target callers release outcome-based leases. Evo X1 active cleanup
was enabled after its candidate log was reviewed. Standard machine presets
remain audit-only.

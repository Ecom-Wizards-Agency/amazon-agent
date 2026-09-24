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

`task complete --port <port> --task-id <id>` and
`task detach --port <port> --task-id <id> --slot <slot> --control-token <token>`
expect the hashed ID returned by `taskIdFor(workflow, stableKey)`, in
`label:20hexdigest` form. Both commands operate on the registry. Detach requires
the slot and current control token; it does not stop the worker heartbeat or
close a CDP session or browser target. Completion is permanent for that task ID.
Shared `seller-central-region` tasks are released after each operation, never
completed.

`region state --port <port>` reports each region's stored `url` alongside
`liveUrl` and `title` from a read-only request to that port's `/json/list`.
Live fields are matched by target ID and are null when the target is missing
or the endpoint is unavailable; the request times out after two seconds.

Normal JavaScript workflows acquire pages through
`tools/browserctl/task-tabs.mjs`. Each workflow provides a stable task ID and
usually uses its `primary` slot. Repeated steps and retries reacquire that exact
target. Ordinary task targets use `background-active`; regional primaries keep
their permanent `anchor` class. Each receives one atomic
lease/controller/claim renewal while its CDP session is open, and is released with an
explicit outcome. Callers never coordinate registry files, timeouts, activity
probes, or raw target closure themselves. `releaseTaskPage(handle, { outcome:
"success", closeTarget: true })` and `detachTaskPage(handle, { outcome:
"inspection", closeTarget: true })` apply the outcome, close the exact target,
and remove its lease and task binding before unlocking. Region primaries ignore
`closeTarget`; omitted flags keep normal retention. Close failures are logged
without changing the release result; the binding is removed and the lease remains
tracked for cleanup. `acquireTaskPage({ ..., closeOnFailure: true })` also closes
non-region task targets when acquisition setup fails. Collectors forward the
top-level boolean `close_tab_after` to both options. Temporary handoffs use
`closeReleasedTaskPage(handle)` on failure or SIGTERM; it checks the retained
binding under the port lock before closing the exact released target.

Retention and ownership are separate. The two-hour inspection window preserves
evidence; heartbeat recovery or tracker installation does not establish observed
interaction. Retrying a retained page first reads its versioned input tracker
without navigating it, then atomically validates the binding and lease generation.
Pointer, keyboard and wheel events count as observed interaction, not proof of a
human actor. Focus and page lifecycle events do not extend inspection retention.
The low-level `touchLease(kind: "activity")` still extends existing inspection
and interactive leases; callers must use `interaction` for retention updates.
Cleanup already follows that rule; the remaining low-level guard is pending.

`TASK_TAB_BUSY: observed-interaction` means input occurred after the latest release
or expired controller deadline. `TASK_TAB_INTERACTION_UNKNOWN` means the retained
page lacks continuous, compatible evidence for that unattended interval. Neither
error promises that waiting until the retention deadline will permit reuse;
safe cleanup or an explicit reviewed `allowOperatorActivity` recovery is required.
Connection failure preserves the target and never authorizes a replacement.

Seller Central readers acquire the regional primary; account-switcher workflows
add `claimScope: "global"` to retain the regional anchor while holding a global claim:

```js
const page = await acquireTaskPage(sellerCentralRegionTask({ marketplace: "us", origin: "https://sellercentral.amazon.com" }));
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

A regional claim cannot cross region groups. An explicit global claim permits
the account-switcher host transition without changing the region tab's identity.
The shared account switcher checks the target
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

Each port keeps three permanent Seller Central region anchors: US for NA, DE
for EU, and AUS for AU. These are the working tabs for the
`seller-central-region` workflow. Fresh controllers protect them at any URL;
success parks them at home, explicit handoff keeps them without parking, and
every other release outcome detaches them as inspection tabs.
Surplus anchors become inspection leases with two hours of retention before
cleanup can reclaim them. Named additional slots and other surfaces keep their
own task tabs. `cdp.mjs` rejects unkeyed creation and unknown option names.

## Tab model and lifecycle

This is the operating summary agents need; the sections below give the full contract.

CDP runners start or reuse this dedicated profile lazily through the shared
`ensureChrome()` helper. `assertChrome()` is the read-only probe for setup and
diagnostics. Set `CDP_AUTOSTART=0` only when a caller explicitly needs probe-only
behavior. Mode, profile, window class, anchors, and cleanup timings come from
`~/.amazon-agent/browser-runtime/policy.json`. `ensureChrome()` never restarts a
reachable browser to change mode. A mismatch fails with
`MODE_CHANGE_REQUIRES_RESTART`; only `browserctl restart` may intentionally stop
and relaunch a managed browser, and it requires an explicit reason.
`browserctl ensure` and cleanup reject a reachable port with `PROFILE_MISMATCH`
when its listening process does not use the policy profile. Profile comparison
resolves symlinks. Status exposes `profile_verified` and `devtools_active_port`.
Seller Central sign-in and authentication redirects keep their anchor lease with
`authRequired: true`; maintenance reports `auth-required` and suppresses replacement
creation during the origin cooldown. Recent inspection leases also delay creation.
Install managed GNOME autostart entries with `tools/browserctl/autostart/install.sh`
from the deployed repo. It archives competing raw Chrome entries and wrappers;
review the reconciliation notes under GNOME autostart installation below before deployment.

The standard machine preset remains headless. Evo X1 runs ports 9222 and 9223
headed with distinct window classes. Every programmatic tab has a machine-local
lease. Active controllers heartbeat every 30 seconds. Three kinds of tab share
the controller in `tools/browserctl/task-tabs.mjs`:

- Region tab: exactly one permanent `anchor` per region per port, NA at the US
  home, EU at the DE home, and AU at the AUS home. Seller Central primary work
  uses the fixed `seller-central-region` workflow and its regional task ID.
  `success` parks the page at its region home and keeps the anchor role;
  explicit `handoff` keeps the anchor without parking. Every other release
  outcome detaches the target into a two-hour inspection lease, removing its
  anchor role and task binding. The next acquisition or cleanup creates the
  missing region tab. Acquisition failure on a live regional target abandons
  the reservation rather than detaching it. A concurrent anchor binding raises
  retryable `REGION_ANCHOR_CONFLICT`. Maintenance never demotes or replaces a
  live region tab with a fresh controller heartbeat, whatever its URL.
- Task tab: FlatFilePro, public PDPs, Brand Store builder and named additional
  slots use one stable task ID per rollout or job, never per revision or
  sub-step. Steps and retries reacquire that target. `success` gives ten minutes
  of grace before cleanup; `handoff` means explicit operator handover only.
  The terminal step completes the task. Regional tasks are released, never
  permanently completed. Bulk-image keys use `bulk-images:<rollout_id or job_id>`;
  terminal reconciliation requests `complete_task: true`. Operations keeps
  collector flags false, finishes preservation reads, then calls `task complete`
  only for `verified`, `failed` or `blocked`. Processing and partial results
  retain the task. Earlier steps never request completion.
  A workflow may close its own task tab at release, as scheduled image checks do; region tabs are never closed.
- Inspection tab: an error, lost heartbeat, detach or adoption preserves the
  target for two hours of idle time. Only pointer, key or wheel input, kind
  `interaction`, extends retention. Focus, pageshow and visibilitychange, kind
  `activity`, do not. Evo X1 adopts unknown tabs with a full two-hour window on
  first observation; standard presets preserve unknown tabs. Cleanup preserves
  targets when interaction cannot be measured.

Seller Central tasks declare `sellerCentral: { marketplace, origin }` and
`exclusiveContext: true`. Regional claims serialize US/CA/MX, EU/UK and AU work
per port. Account-switcher workflows, including profile identity and FBA
shipments, add `claimScope: "global"` (bridge flag `--claim global`) because the
switcher uses the US host. Regional reads keep their regional claim. Unspecified,
mixed or unmapped contexts retain global exclusion. Hold the claim through
selection and dependent work; verify account, marketplace and region before
using data. Non-region workflows cannot bind anchors. Direct `createPage()` is
restricted to anchor maintenance and the keyed controller.

The five-minute cleanup takes the port lock once per pass, waits up to 120
seconds by default (`--lock-wait-ms`), and reports `deferred` with exit 0 when
busy. `--audit-only` previews anchor changes and destructive actions, while
tracker repair, observations and background heartbeat transitions still persist.
Surplus anchors become inspection leases owned by `browserctl:anchor-duplicate`;
permanent region anchors never
expire. `task complete`, `task detach` and `region state` expose the registry
through browserctl; task commands take the hashed task ID. Collector timeouts
send SIGTERM, allow 15 seconds for cleanup, then send SIGKILL.

Known implementation gap: cleanup follows interaction-only retention, but the
low-level `touchLease(kind: "activity")` still extends an existing inspection or
interactive lease. Callers must use `interaction` for retention updates; the
low-level guard needs a separate browserctl change.

The Linux operator profile remains merged with `~/.config/google-chrome-amazon-operator`
through the `chrome-debug` symlink. It is independent of Grimoire's profile.

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
`incomplete`. It holds the session lock for the whole port pass, retrying every
five seconds for up to `--lock-wait-ms` (default 120000). If the lock stays busy,
that port is deferred with reason `session-busy`; deferred passes exit 0.
Failed activity measurements preserve the tab and report the failing probe
stage and sanitized error; incomplete passes exit nonzero. A renderer timeout
is not treated as a missing tracker. Only pointer, key, or wheel interaction
extends retention; focus and visibility events do not.

The same five-minute pass maintains the three region anchors on each reachable
managed browser and reclassifies surplus anchors for later cleanup. It creates
a missing region anchor after detachment and preserves every anchor with a
fresh controller, including one navigated away from home.
Missing targets are replaced even when their controller heartbeat is fresh.
Anchor-maintenance errors appear under `anchorMaintenance.error`; lease expiry
continues and determines whether that port's cleanup is complete.
Audit-only passes preview anchor creation, reclassification, removal and
detachment, plus lease adoption, removal and tab closure, using `would-*`
actions. Unregistered tabs are still probed and report `would-adopt` with probe
health. Tracker restoration, observed interaction, probe-failure records and
background heartbeat transitions still run and persist their evidence.

Machine routing uses the shared `grimoire` session on port 9223 for Grimoire's
Slack and scheduled work. Attended direct chat uses `routing.attended_cdp_port`
from the machine policy: 9223 unless set to 9222, as on Evo X1. The older
`routing.default_cdp_port` key is ignored, so a policy rendered with it as 9222
still keeps attended work on 9223. Port 9222 is
otherwise explicit operator work. T3 Code's in-app browser is explicit-only and is not
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

Slack and scheduled Grimoire work use `grimoire` (9223) and keep `--session grimoire`. Attended direct chat uses the machine's attended default, which is machine-local: `routing.attended_cdp_port` in the setup-owned policy, 9223 when absent. Evo X1 sets 9222, so attended work there runs on `operator` with the operator's own login. Run an attended browser command with:

```sh
node tools/browserctl/browserctl.mjs run -- node tools/opportunity-explorer/run-poe.mjs doctor --origin https://sellercentral.amazon.com
```

The session resolves in this order: `--session`, `AMAZON_BROWSER_SESSION`, `CDP_PORT` (9222 or 9223), then the policy default. A disagreeing pair fails with `BROWSER_SESSION_CONFLICT`. With `WIZARDS_AI_MODE=1`, which every Grimoire unit sets, the default is `grimoire` and any selection of `operator` or port 9222 fails with `BROWSER_SESSION_REFUSED`. The refusal also covers every `--port 9222` command, the CDP and launcher paths behind them and `auth-broker.mjs`; `cleanup` without `--port` then covers only 9223. Only 9223 has a session lock. Seller Central work on 9222 relies on its regional or global task claim, and `tools/sc-sqp-competitor`, which switches accounts without one, refuses 9222.

`run --lock-wait-ms <milliseconds>` waits up to 120000 milliseconds by default
for the shared session lock, retrying every two seconds within that deadline.
Use `0` to fail immediately when busy. If the deadline expires, the command
returns `BROWSER_SESSION_BUSY` with the elapsed wait in milliseconds and does
not launch the child.

The launcher releases its lock when its direct child finishes its last task
page, while the child can continue downloading, formatting, or running PDF
tools. The control message is `SIGUSR1` to `process.ppid`. The launcher sets
`AMAZON_BROWSER_LAUNCHER_CONTROL=sigusr1-v1` and
`AMAZON_BROWSER_LAUNCHER_PID`; the child checks both, validates the inherited
lock chain, and verifies that its parent owns the final link before signaling.
The launcher ignores a signal while its lock has a child delegation. It clears
its release callback after releasing, so child exit cannot release a later
owner's lock. Children that never release task pages retain the exit fallback.

`releaseLauncherSessionLock(port = 9223)` waits up to ten seconds for removal
of the launcher's exact lock token as acknowledgement, then clears the child's
inherited token, chain, and launcher-control environment. A timeout fails with
`BROWSER_SESSION_LOCK_LOST`. Release, detach, acquisition failure and target-close
paths call it after releasing their local lock references; other active pages
or CDP sessions keep those references and prevent early release.

Later `acquireTaskPage({...spec, lockWaitMs?})` calls acquire the session lock
directly, without a parent token. They wait for a pending release acknowledgement
and use the existing BUSY/retry behavior. The wait defaults to the launcher's
`--lock-wait-ms`, propagated as `AMAZON_BROWSER_LOCK_WAIT_MS`, or 0 outside
a launcher. `0` fails immediately. `sessionLockHasChildren(port = 9223)` exposes
the launcher's delegation guard. In-process scheduled workers without the
launcher-control environment keep their existing lock ownership.

On 9222 there is no session lock to wait for, so attended tools take turns on the
Seller Central claim instead. `acquireTaskPageWithRegionWait(spec, { waitMs,
maxWaitMs, workBy, pollMs, onWaiting }, dependencies)` retries `acquireTaskPage` while it
answers `TASK_TAB_BUSY` with a `blockingScope`, meaning another controller holds
the regional or global claim. It polls every two seconds on a ref'd timer for at
most `waitMs`: `AMAZON_BROWSER_REGION_WAIT_MS` when set (whole milliseconds from
`0`, which fails at the first busy answer, to 300000, half the default success
grace, so a tab reacquired by `expectedTargetId` returns before cleanup may close
it), else 120000, capped by `maxWaitMs`. `onWaiting`
runs once with the holder's facts from the registry (`blocking_scope`, `owner`,
`workflow`, `task_id`, `heartbeat_age_s`, never the control token); the default
writes one stderr line. When the bound passes it throws `TASK_TAB_BUSY` with
`holder`, `waitedMs` and a message naming the holder. A busy answer holds no
claim or task record between attempts. Other errors, and busy answers without a
blocking scope (the same task in another process, input on the task's own tab),
fail at once. On 9223, which has the session lock, and under `WIZARDS_AI_MODE`
it makes the single `acquireTaskPage` attempt. The report fetcher, endpoint
capture, POE runner and endpoint discovery, catalog upload and export, shipments,
audit evidence and attended case observation use it. `workBy` (epoch milliseconds) serves callers
with their own hard timeout: it also bounds the wait, and an acquisition that
lands after it, having waited, is released with success and throws
`TASK_TAB_BUSY` (`late: true`) instead of starting work that cannot finish. An
acquisition that never saw a busy answer is not refused for lateness.
`operations.py` stops collectors after 180 seconds, so case observation and every
catalog-export acquisition use a `workBy` 60 seconds after start, which keeps 120
seconds for their work. `seller-assistant.mjs serve`
keeps its own `--region-wait-minutes` wait; both use the holder facts in
`tools/browserctl/region-holder.mjs`.

Before initial local preparation, a direct child can also await
`releaseLauncherSessionLock(port)` while it holds no task page or other local
session-lock reference. FlatFilePro does this before staging the workbook;
shipments do it before probing PDF tools. Their first page acquisition then
uses the same independent lock and wait path as later reacquisitions.

`browserctl session [--session grimoire|operator]` returns only the resolved non-secret environment. Python workers use `browser_session.py` as an adapter to that same resolver. The session is immutable within a process; conflicting ports or profiles fail before connection. Child workers inherit the route and a scoped lock chain. Sibling workers contend for the next link instead of bypassing serialization. Browser-independent MCP/API work needs no browser lock.

The existing task controller still owns workflow IDs, regional claims, stable targets, heartbeat and cleanup. Screenshots call `captureTaskEvidence(handle, {expected})` in the owning worker. Standalone audit captures require the retained `taskId`, `workflow`, `targetId`, and expected identity; they cannot search for a matching tab or replace a missing target. Supported identities are Seller Central seller/marketplace, DataDive niche/hero keyword, and Amazon retail marketplace plus ASIN or search query. Capture receipts retain actual verified identity separately from report association.

A browser login grants no additional action rights. DataDive login recovery occurs in 9223. Extension-only capabilities must be demonstrated in that profile; missing support never redirects work to 9222.


## Authentication and profile identity

An anchor redirected to a same-origin sign-in, MFA, CAPTCHA or recovery page,
or to authentication on a configured `auth_origins` host, stays an anchor.
Maintenance marks `authRequired: true` and returns `reason: "auth-required"` in
`kept`. Returning to an accepted URL clears the flag. No login is attempted by
anchor maintenance. Existing live anchors block replacement, and missing anchors
respect `auth_retry_cooldown_ms` for their port and origin. Recent navigation or
inspection leases for the key or origin also suppress creation. The result's
`skipped` entries carry `key`, `reason` and `retryAt`; cleanup includes them in
`anchorMaintenance`. Audit mode previews this without changing auth state.

Before anchor or lease changes, `browserctl ensure` and cleanup check the actual
listening process's `--user-data-dir` against the policy profile using real paths.
A reachable port with a failed check returns `PROFILE_MISMATCH: port N is served
by a browser whose profile is not <policy profile>`. Cleanup returns an empty
action list and null `anchorMaintenance`. The operator profile symlink remains
valid. `status --port N` includes `profile_verified` and `devtools_active_port`
(the first line of the profile's DevToolsActivePort file, or null). A stale launcher
state file or DevToolsActivePort file cannot establish profile identity. Linux
uses socket ownership from `/proc`; other Unix hosts use `lsof`. Unavailable
process evidence fails verification; Windows verification is not implemented.

One refusal applies to every `authenticateTarget()` caller. It never types an
empty one-time code: when the page asks for a code and none was supplied, it
returns `totp_unavailable` with nothing submitted.

The code options, `otpFetchedAt` (the code's fetch time in epoch milliseconds)
and `onOtpSubmitted`, change four more things, and only for the caller that
passes them. The credential transport passes both for `require_totp` routes.
One call types at most one code: if the code form returns after a submitted
code, the result is `totp_rejected` and nothing is typed again.
With `otpFetchedAt`, if the code's 30-second period has ended when the code
field appears, the result is `totp_expired` and nothing is typed. The result carries
`otp_submitted`, and `onOtpSubmitted()` runs once, just before the click on the
code form's submit control is dispatched, so a retry after a thrown error can
refuse to submit a second code.
The code form is submitted by exactly one trusted click and nothing else: no
Enter, no `requestSubmit`, no second click. Amazon's Two-Step Verification form
does not submit on Enter. A control belongs to the form of the visible code input
when it sits inside that form or names it with `form="..."`. For the amazon
adapter the control is that form's `#auth-signin-button` and nothing else. Other
adapters use the form's submit control, skipping any whose text, value, name or
`aria-label` reads as resend, send a new code, didn't receive, different account,
another way or cancel. If that rule does not leave exactly one visible control,
nothing is clicked, `otp_submitted` stays false and the call throws
`AUTH_CODE_SUBMIT_AMBIGUOUS`. A navigation error from the click's own dispatch
does not end the call. After the click the broker waits up to 30 seconds
for the URL, the visible fields or the visible alert text to change. A new alert
ends through the usual classification as `totp_rejected` or
`authentication_failed`. A page that does not change throws
`AUTH_CODE_FORM_STALLED`: the code was submitted once and is not submitted again.
Email and password forms keep the full sequence below with or without the code
options.

A caller that passes neither option, as Grimoire's 9223 login does, keeps the
existing result fields and the existing submit sequence: Enter, then a click on
the submit button, then `requestSubmit`, each followed by up to 10 seconds of
waiting for the form to advance. When the code form returns after a code, it
loads and submits the code again.
`test/auth-broker-parity.test.mjs` runs the same scripted pages through the
broker at commit `26c5d90` and the current one and compares every call.

## GNOME autostart installation

Run this only from the deployed repository after review:

```sh
tools/browserctl/autostart/install.sh
```

`AMAZON_AGENT_REPO` can select the deployed repo. The installer copies
`operator-9222` and `grimoire-9223` to `~/.local/bin` and writes
`amazon-operator-9222.desktop` and `wizards-ai-9223.desktop` in
`~/.config/autostart`, with delays of 8 and 12 seconds and `Terminal=false`.
Their Exec lines set `AMAZON_AGENT_REPO` and invoke the copied wrappers, which
exec `node <repo>/tools/browserctl/browserctl.mjs ensure --port N`. Source-tree
wrappers also resolve the repo relative to their own location. The policy supplies
profiles, browser executable, mode and window classes.

The installer retires the raw `chrome-amazon-operator.desktop` and
`chrome-wizards-readonly.desktop` entries and their same-named bin wrappers,
plus duplicate autostart entries referencing these ports. It moves them to
`~/.amazon-agent/retired-autostart-<date>/`, preserves relative paths, and prints
every retirement, installation or unchanged result. Re-running it leaves one
managed autostart entry per port and preserves earlier backups.

Read-only inspection on 2026-09-19 also found application-menu entries at
`~/.local/share/applications/amazon-operator-9222.desktop` and
`~/.local/share/applications/wizards-ai-9223.desktop`. Their Exec lines run
`tools/report-fetcher/launch-chrome-debug.py --mode headed` with the correct
`~/.amazon-agent/chrome-debug` and `~/.amazon-agent/wizards-ai-chrome` profiles,
respectively. They select `chrome-amazon-operator-classed` and `chrome-wizards-ai`
through `CHROME_BIN`. The new entries preserve their names and StartupWMClass
values but route execution through browserctl and policy. The old raw 9223
wrapper selected `~/.config/google-chrome-wizards-readonly`, causing the conflict.
The installer does not edit application-menu entries, systemd units or Wizards AI
code. The deployer must reconcile any separate login invocation of those launchers
and verify equivalent headed mode and window-class values in policy.

On an already reachable, verified managed port, ensure reuses Chrome without a
restart. On a cold start, the Python launcher uses `start_new_session=True` and
redirects browser output to DEVNULL, so Chrome survives the autostart process.
Ensure waits for startup and anchor maintenance, then returns; it is not a daemon.
A wrong profile is preserved and reported, never killed or silently adopted.

Validation:

```sh
node --test tools/browserctl/test
```

```sh
python3 tools/lint_agent_docs.py
```

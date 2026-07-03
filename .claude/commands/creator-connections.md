---
description: Run a Creator Connections workflow — inbox audit, tracker update, reply drafts, campaign prep, gap check, or reconcile (status-filtered; stop before any send/publish)
argument-hint: "[client + marketplace + mode: audit|campaign|tracker|gaps|reconcile (default audit) + scope/details]"
---

# Creator Connections

Operate Amazon Creator Connections for a client. Do not duplicate logic here — route into the `amazon-creator-connections` skill as source of truth.

The user's target is: **$ARGUMENTS**

## Steps

1. **Load the `amazon-creator-connections` skill** and check `_local/creator-connections/<client>-config.json` + `local-notes.md` before asking for inputs. Pick the mode from the arguments (default `audit`).

2. **Confirm inputs — ask briefly** only for what's missing: client/brand, marketplace, Ads account label, tracker sheet URL, and message scope.

3. **Connected-browser checkpoint, then navigate** via the AGENTS.md route: Campaign Manager → account selector → `Brand content` → `Creator connections`. Verify account, brand, and marketplace before reading anything.

4. **Apply the status filter.** If the client's skip rule isn't confirmed yet, run the first-run discovery: screenshot every distinct message status, propose the skip/process mapping, get operator confirmation, save it to the client config. Skipped threads are always reported, never silently dropped.

5. **Run the mode** — match messages to products (ASIN/URL → campaign reference → product name; ambiguous → manager-review queue), update the tracker tabs per the schema, and draft replies for threads that need answers.

6. **STOP before any send or publish.** Present drafted replies (and any prepared campaign) as a batch; sending a creator message or publishing a campaign each requires the operator's explicit approval of that exact action in the current chat or a matching `_local/local-permissions.md` entry. Finish with the handoff report (processed/skipped/flagged counts, tracker changes, drafts vs sent, evidence paths).

# SOP Update: Drop the 13 MAG SOPs the coverage check found fully covered

Date: 2026-10-10
Status: applied locally
Source SOP: 13 MAG SOP pages listed under Files Changed
Source link: `_local/knowledge-sop-triage/drops-2026-10-10-coverage.csv` and `_local-output/knowledge-sweep/sop-coverage-check-2026-10-10.md` (this machine)

## Problem

After the 08.10.2026 reduction, 89 pages stayed `needs-update`. Each was compared with the owning skill, its references, the knowledge units and the first-party captures by one read-only reviewer per skill area on 10.10.2026.

## Verification

The check returned 32 pages worth a knowledge unit, 44 pages with a specific step or rule to fold into a skill, and 13 pages whose procedure or rule the repo already states, each with the covering paths named. The operator reviewed the counts and decided on 10.10.2026 to drop the 13 covered pages. The 32 and 44 stay `needs-update` and form the troubleshooting lead's worklist.

## Change Made

`sop_triage.py merge-verdicts` set the 13 rows to `drop`; `sop_apply_triage.py --apply --approved-by "Victor" --date 2026-10-10 --csv _local/knowledge-sop-triage/drops-2026-10-10-coverage.csv` removed the files with `git rm`, appended `13 SOPs triaged as unusable` with date `2026-10-10` to the index `dropped` list, slimmed the index, regenerated the README and stripped any path of the removed files from units and sweep cards.

## Files Changed

Removed: 13 files under `MAG SOPs/` (the rows of the CSV above). Updated: `MAG SOPs/_index/sop-index.json` (119 entries, was 132; needs-update 76, superseded 26, active 11, merged 6), `MAG SOPs/README.md`.

## Checks Run

`sop_apply_triage.py --check` (0 problems), `--dry-run` (exactly 13 `git rm` lines), `lint_knowledge.py --strict` (67 units clean), `/usr/bin/python3 tools/lint_agent_docs.py`.

## Evidence

The per-page verdicts with reasons and covering paths are in the coverage report named above.

## Follow-Up

The 76 remaining `needs-update` pages are the troubleshooting lead's list: 32 units to write and 44 deltas to fold, in the team vault handoff of 10.10.2026.

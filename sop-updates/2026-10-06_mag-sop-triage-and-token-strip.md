# SOP Update: MAG SOP triage, drops, archive and image-URL token strip

Date: 2026-10-06
Status: applied locally / needs review
Source SOP: the whole `MAG SOPs/` runtime tree (475 entries captured 12.05.2026)
Source link: My Amazon Guy SOP Library (login), see `docs/mag-sops-assets.md`

## Problem

No SOP carried a revision date, 110 described platforms or tools the agency does not use (Vendor Central, Helium 10 tool chains, HubSpot, Google Meet, YouTube, macro tools), three sets were exact duplicates across categories, several were already replaced by live-verified repo procedures, and a handful of image links still carried signed query-string tokens from the original capture.

## Verification

Every SOP got a signal pass (`tools/knowledge/sop_triage.py signals`) and a read verdict by a reviewer agent; every supersede, merge and drop verdict was tested by a second reader, and the automatic drop list was checked entry by entry (one SOP pulled back out). The operator approved the drop classes on 06.10.2026; the per-file list is in the PR. Verdicts and the claims each kept SOP still needs checked live are kept in the gitignored `_local/knowledge-sop-triage/` (triage.csv, verdicts-detail.json).

## Change Made

- 110 SOPs removed from the runtime tree with `git rm` (the pCloud archive keeps the full capture): 89 Vendor Central, 9 Vendor Central titles under other categories, 12 tool-specific SOPs.
- 13 duplicate SOPs moved under `MAG SOPs/_archive/` with `merge_into` set to the kept copy.
- 27 SOPs marked `status: superseded` in the index with `superseded_by` pointing at the repo file that owns the procedure now.
- 314 marked `needs-update` (relevant, needs a live check before an agent quotes limits, fees or labels), 11 `active`.
- 16 further drops proposed by the readers were parked as `needs-update` with the `proposed_drop` flag for the operator to decide.
- Signed query strings stripped from `files.document360.io` image URLs in the active SOPs (list in the gitignored triage folder). No SOP text was changed.

## Files Changed

`MAG SOPs/**` (deletions, archive moves, image URL query strings), `MAG SOPs/_index/sop-index.json` (status, superseded_by, merge_into, triaged_on, flags, knowledge_value, dropped), `MAG SOPs/README.md` (regenerated), `tools/slim_sop_index.py` (new index fields, dropped list), `docs/amazon-library-map.md` (counts).

## Checks Run

`python3 tools/knowledge/sop_apply_triage.py --check` (0 problems), `--apply` counts, `python3 tools/slim_sop_index.py --readme` idempotent, `python3 tools/lint_agent_docs.py`, active file count equals index active count.

## Evidence

`_local/knowledge-sop-triage/triage.csv`, `verdicts-detail.json`, `verdicts-raw-2026-10-06.json`, `token-strip-2026-10-06.json` (gitignored, this machine).

## Follow-Up

Operator decision on the 16 proposed drops; the supersede wave for the high-value `needs-update` SOPs (knowledge units or skill references verified live); the BookStack revision check once the library login is available.

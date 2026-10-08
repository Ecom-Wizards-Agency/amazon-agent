# SOP Update: Reduce the needs-update MAG SOPs to the ones worth rewriting

Date: 2026-10-08
Status: applied locally
Source SOP: 216 MAG SOP pages (210 active pages plus 6 archived duplicates)
Source link: `_local/knowledge-sop-triage/triage.csv` and `drops-2026-10-08-reduction.csv` (gitignored, this machine)

## Problem

After the 06.10.2026 triage, 299 SOPs stayed in the runtime library as `needs-update`, and a rewrite wave for all of them was handed to the troubleshooting lead. The operator questioned whether that work is needed, since the repo's own skills cover most of the procedures. The triage data agreed: of the 299, only 48 carry high knowledge value, and 204 had been revised on the MAG site after our 12.05.2026 capture, so most captured texts were stale as well as redundant.

## Verification

Buckets from the triage columns (knowledge value, overlap with repo files, flags) and the 08.10.2026 site revision check, reviewed with the operator on 08.10.2026:

- High value, no repo overlap (5) and high value with repo overlap (43): kept for a per-SOP coverage check against the owning skill.
- Medium value, no repo overlap (41): kept for the same check, default drop afterwards.
- Medium value with repo overlap (140) and low or unknown value (70): dropped on the operator's decision.
- Six archived duplicates whose merge target was among the dropped pages: dropped with them.

The overlap signal is loose (word matches against docs), which is why the high and medium no-overlap pages wait for a real check rather than a rewrite.

## Change Made

`sop_triage.py merge-verdicts` set the 216 rows to `drop`; `sop_apply_triage.py --apply --approved-by "Victor" --date 2026-10-08 --csv _local/knowledge-sop-triage/drops-2026-10-08-reduction.csv` removed the 210 active files with `git rm` and appended `210 SOPs triaged as unusable` with date `2026-10-08` to the index `dropped` list. The six archived duplicates under `MAG SOPs/_archive/` were removed by hand with `git rm`, then `tools/slim_sop_index.py --readme` slimmed the index and regenerated the README. Knowledge unit KC-0005 lost its `related_sops` link to one of the dropped pages.

## Files Changed

Removed: 210 files under `MAG SOPs/` (164 catalog, 23 advertising, 12 general, 7 SEO, 4 design) and 6 files under `MAG SOPs/_archive/`. Updated: `MAG SOPs/_index/sop-index.json` (132 entries, was 348; status counts needs-update 89, superseded 26, active 11, merged 6), `MAG SOPs/README.md`, `knowledge/brand-registry/KC-0005_*.md`, `knowledge/_index/knowledge-index.json`, `knowledge/README.md`.

## Checks Run

`sop_apply_triage.py --check` (475 rows, 0 problems after the six duplicate rows were added), `--dry-run` (exactly 210 `git rm` lines, equal to the files on disk), `tools/slim_sop_index.py --readme`, `lint_knowledge.py --strict`, `/usr/bin/python3 tools/lint_agent_docs.py`.

## Evidence

`_local-output/knowledge-sweep/needs-update-sop-overview-2026-10-08.md` (the bucket overview with every row and reason), `_local/knowledge-sop-triage/drops-2026-10-08-reduction.csv`.

## Follow-Up

A coverage check over the remaining 89 `needs-update` pages: one reader per skill area compares each page with the current skill and returns covered, fold this delta, or unit worth writing. The troubleshooting lead's worklist is paused until that list exists.

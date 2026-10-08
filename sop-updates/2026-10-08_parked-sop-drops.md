# SOP Update: Drop the 16 parked MAG SOPs

Date: 2026-10-08
Status: applied locally
Source SOP: 16 MAG SOP pages listed under Files Changed
Source link: `_local/knowledge-sop-triage/triage.csv` (gitignored, this machine)

## Problem

The 06.10.2026 triage parked 16 drops proposed by the readers as `needs-update` with the `proposed_drop` flag, pending the operator's decision. They stayed in the runtime library and in the search index although none of them describes current Amazon seller work the agent can run.

## Verification

The operator reviewed the 16 titles with their reasons on 08.10.2026 and decided to drop all of them. Groups:

- Vendor Central procedures (3): purchase quantity variance shortage claims, update attributes using the item maintenance form, VC image and video upload.
- Helium 10 procedures (3): competitor research, phase 2 incremental indexing, phase 3 high-level keyword strategy.
- Third-party platforms outside Amazon (2): Flowspace 3PL inbound and outbound orders, uploading COGs in MerchantSpring.
- Deprecated feature (1): creating Amazon Social Posts (the SOP's own banner records the deprecation on 03.06.2025).
- Empty placeholder (1): "New Page".
- Not Amazon work (4): identifying font styles on websites, design tier Q&A, how to make HTML tags, client communication etiquette.
- Image rules the listing-images skill already covers (2): Amazon image best practices, Amazon photo rules and guide.

## Change Made

`sop_triage.py merge-verdicts` set the 16 rows to `drop`, then `sop_apply_triage.py --apply --approved-by "Victor" --date 2026-10-08 --csv _local/knowledge-sop-triage/drops-2026-10-08.csv` removed the files with `git rm`, appended `16 SOPs triaged as unusable` with date `2026-10-08` to the index `dropped` list and regenerated the README through `tools/slim_sop_index.py`. Passing the 16-row CSV kept `triaged_on: 2026-10-06` on every other row.

## Files Changed

Removed from `MAG SOPs/`: `catalog/catalog-sop-creating-amazon-social-posts.md`, `catalog/catalog-sop-purchase-quantity-variance-shortage-claims.md`, `catalog/catalog-sop-update-attributes-using-item-maintenance-form.md`, `catalog/catalog-sop-vc-image-video-upload.md`, `catalog/logistics-sop-create-inbound-or-outbound-order-in-flowspace-3pl-shipment.md`, `catalog/new-page.md`, `seo/seo-sop-competitor-research.md`, `seo/seo-sop-phase-2-seo-incremental-indexing.md`, `seo/seo-sop-phase-3-seo-high-level-keyword-strategy-for-advanced-keyword-striking-distance-rankings.md`, `design/creative-sop-amazon-image-best-practices.md`, `design/design-sop-amazon-photo-rules-and-guide.md`, `design/design-sop-identifying-font-styles-on-websites.md`, `design/design-tier-q-and-a.md`, `general/general-sop-how-to-make-html-tags.md`, `general/general-sop-uploading-cogs.md`, `general/supplemental-article-ensuring-consistent-communication-through-multi-threading.md`.

Updated: `MAG SOPs/_index/sop-index.json` (348 entries, was 364; index status counts now needs-update 299, superseded 26, merged 12, active 11), `MAG SOPs/README.md`.

## Checks Run

`sop_apply_triage.py --check` (475 rows, 0 problems), `--dry-run` (exactly 16 `git rm` lines), `/usr/bin/python3 tools/lint_agent_docs.py`.

## Evidence

`_local/knowledge-sop-triage/drops-2026-10-08.csv` and `triage.csv` (gitignored, this machine). Observation: before this change the triage CSV held 111 earlier `drop` rows against the 110 files the 06.10.2026 note reports; the 111th file, an archived advertising SOP, was removed in commit ac83a97 on 07.10.2026 without an entry in the index `dropped` list. Left as recorded.

## Follow-Up

None for these pages. The supersede wave for the high-value `needs-update` SOPs runs through the troubleshooting lead's handoff; the BookStack revision check runs once the library login is available.

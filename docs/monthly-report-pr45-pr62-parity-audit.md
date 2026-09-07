# Monthly Report PR 45 to PR 62 Parity Audit

Audit date: 2026-09-04

## Decision

PR 62 preserves the reusable monthly-report controls that were essential in the superseded PR 45 reference build. The removed `reference_builds.py` file must not be restored to this repository because it embedded client-specific names, figures, commentary, and source paths. Those approved client artifacts belong in the private client workspace and archive.

## Preserved on main

- source contract and source precedence
- operator-input handoff that asks only for missing, stale, or changed inputs
- exact report and audit-workbook pairing
- mandatory page structure and ordering
- break-even ACOS and traffic-segmentation controls
- optional-section brand isolation
- multi-marketplace source and currency boundaries
- DataDive unsupported-marketplace handling
- source, numerical, formula, and visual QA gates
- reusable brand configuration schema
- composition engine and regression tests

## Intentional replacements

- Client-locked reference builders were removed and replaced by generic composition tests and private-workspace fixtures.
- Direct PDF rendering and Desktop delivery were replaced by the repository's current native Google Doc and Google Sheet delivery policy.
- A hard-coded client exception was replaced by a generic persisted three-segment brand configuration.
- A hard-coded root-cause module was replaced by an allowlisted brand-restricted optional-module mechanism.

## Verification standard

The parity conclusion is about reusable behavior, controls, and report structure. It does not assert that private reference outputs can be reproduced without their private client fixtures and owning branded renderer. Before a live monthly delivery, the operator must still run a full client-workspace build, numerical QA, formula QA, and rendered-page visual inspection.

Validated with `tools/client-monthly-report-template/test_template_engine.py` on current main plus this branch. No client names, creator details, figures, or private tracker links are included in this audit.

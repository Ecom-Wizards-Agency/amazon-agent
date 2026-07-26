# AdLabs Help

Downloaded/updated: 2026-07-26

Offline capture of the public AdLabs methodology articles that document the optimizer's math. Purpose: the /ppc-manage caps-are-ceilings rule. The opt-group max-change settings clamp these formulas; they are never the step size.

## Files

- `articles/000-formula-summary.md`: distilled operator sheet (start here)
- `articles/001-four-essential-bid-formulas.md`: the 4 weekly bid-optimization categories and their formulas
- `articles/002-placement-bidding-adjustments.md`: placement adjustment formula (Target ACOS / Current ACOS - 1)
- `articles/003-rpc-bidding-formula-acos-goals.md`: RPC bidding foundation article
- `articles/004-bid-optimization-guide.md`: the long-form bid optimization guide
- `_index/adlabs-help-index.json`: capture index

## Caveats

- These are the public methodology articles; the in-app optimizer applies the same math with additional weighting (AdLabs says outputs "may differ slightly"), and the Campaign Placement Modifier weighting is a trade secret.
- The authoritative per-entity numbers are always the optimizer preview / UI download, not a hand calculation. OPEN: capture the in-app optimizer values via a Codex record-and-replay session to pin the clamp behavior.

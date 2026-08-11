# Ads doctrine upgrade — pointer

**Status: specified, not applied.** Nothing in this repo has been changed yet.
The agent still runs the pre-review ads doctrine.

## What happened

326 transcribed Amazon Ads videos were synthesised into 14 topic files in the
team vault (`Research/amazon-ads/`). Every point where that external material
disagreed with our own tested practice was filed as a challenge rather than an
edit. Victor and João decided all 28 on 11.08.2026.

- Decisions, with evidence and citations: team vault
  `Research/amazon-ads/challenges.md`
- **The implementation spec — where each decision lands, how, and in what
  order:** team vault `Decisions/2026-08-11-amazon-ads-doctrine-upgrade.md`

Resolve the vault path from `_local/team-vault-path.txt` or
`AMAZON_AGENT_TEAM_VAULT`.

## Files this upgrade will change

| Path | Nature of the change |
|---|---|
| `_local/ads-strategy/strategy.json` | Starting bids, per-bucket budgets, PAT split method; removal of the two SP BMM buckets; new `harvest.gates`, `negation.review_triggers`, `management.checks.out_of_budget`, `management.event_mode`, `rank_lifecycle.entry_gate`, `management.sufficiency` |
| `_local/ads-strategy/strategy.md` | Core philosophy, Budget & bids, Launch phases, Rank keyword lifecycle, Optimizer cadence |
| `skills/amazon-ppc-management/SKILL.md` | New out-of-budget step; bid run, harvest run, graduation, standing conventions |
| `skills/amazon-audit/SKILL.md` + `references/writing-and-delivery.md` | CTR/CVR diagnostic split; mandatory branded split; recorded walkthrough |
| `skills/amazon-seo/SKILL.md` | Product Type / browse-node pre-spend gate |
| `skills/amazon-campaign-builder/SKILL.md` | SP BMM removed from the bucket list; opener and budget sizing |
| `skills/amazon-ads-monitor/SKILL.md` | Capped campaigns and branded share in the brief |
| `AGENTS.md` | Sponsored-Products-only scope stated explicitly |
| `tools/amazon-ads-monitor/{flags,pacing}.py`, `tools/amazon-ppc-management/batches.py`, `tools/amazon-campaign-builder/campaign_model.py` | Hard-coded thresholds reconciled with `strategy.json` |

## Before any of that, three structural fixes

The spec sequences these first, because applying 28 decisions onto the current
surface means writing each change in up to five places:

1. **One canonical home per number.** `strategy.json` is the source of truth; the
   prose, the skills and the tool defaults cite it instead of repeating it.
2. **A drift check** in `tools/lint_agent_docs.py` that fails when a hard-coded
   threshold disagrees with the `strategy.json` key it mirrors.
3. **Version history for `_local/ads-strategy/`** — currently gitignored, so the
   two files holding every operating threshold have no history at all. Needs an
   explicit call, since it affects what this public repo exposes.

The spec also records values that were deliberately left open. Do not invent
them; see its "Named TBDs" section.

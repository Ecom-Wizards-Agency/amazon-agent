# Ads doctrine upgrade: pointer

**Status: phase one implemented on 20.08.2026.** The canonical-source map,
drift-lint foundation, team-knowledge recall, obsolete-reference cleanup, and
decision-complete non-numeric rules are active. Numeric strategy migration and
named TBDs remain deliberately deferred.

## What happened

326 transcribed Amazon Ads videos were synthesised into 14 topic files in the
team vault (`Research/amazon-ads/`). Every point where that external material
disagreed with our own tested practice was filed as a challenge rather than an
edit. Victor and João decided all 28 on 11.08.2026.

- Decisions, with evidence and citations: team vault
  `Research/amazon-ads/challenges.md` (all 28 synchronized from the approved review)
- **The implementation spec, covering where each decision lands, how, and in what
  order:** team vault `Decisions/2026-08-11-amazon-ads-doctrine-upgrade.md`

Resolve the vault path from `_local/team-vault-path.txt` or
`AMAZON_AGENT_TEAM_VAULT`.

## Full-program surfaces

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

## Phase-one structural foundation

The spec sequences these first, because applying the decisions onto the former
surface meant writing each change in up to five places:

1. **One canonical home per number.** `_local/ads-strategy/strategy.json` is the
   source of truth. `docs/ads-doctrine-sources.md` records rule ownership and
   `docs/ads-doctrine-source-map.json` registers every tracked numeric mirror.
2. **A drift check** in `tools/lint_agent_docs.py` validates every registered
   consumer now. It starts comparing a mirror automatically when the numeric phase
   adds that canonical strategy key.
3. **Ordered recall** through `tools/ads_recall.py` loads the approved decision,
   matching Playbook, and relevant Research without making the private vault a
   repository dependency.

Versioning `_local/ads-strategy/` remains deferred. It affects what the public repo
exposes and still needs a separate explicit operator decision.

The spec also records values that were deliberately left open. Do not invent
them; see its "Named TBDs" section. Phase one intentionally does not add those
keys or change current numeric defaults.

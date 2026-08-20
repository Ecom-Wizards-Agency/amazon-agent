# Amazon Ads doctrine sources

This map prevents one operating rule from acquiring several competing homes.

## Authority order

1. Current first-party Amazon documentation controls platform rules, eligibility, and live UI behavior.
2. `_local/ads-strategy/strategy.json` owns numeric operating thresholds. Skills and tools consume or cite its keys instead of creating independent values.
3. Tracked `SKILL.md` files own non-numeric operating procedure and safety gates.
4. The team-vault `Research/amazon-ads/challenges.md` holds the synchronized challenge decisions and evidence. `Decisions/2026-08-11-amazon-ads-doctrine-upgrade.md` records the implementation order and named TBDs.
5. Team-vault Playbooks contain tested agency practice. Research is evidence and never overrides doctrine automatically.

The machine-readable threshold-to-consumer registry is
`docs/ads-doctrine-source-map.json`. `tools/lint_agent_docs.py` validates every
registered consumer and compares its literal with the canonical strategy value when
that key exists. A mapping marked `required: false` is a phase-one bridge: the linter
validates the consumer locator now and starts comparing values as soon as the numeric
phase adds the canonical key. Missing optional keys never authorize an agent to guess
the value.

## Rule ownership

| Rule family | Canonical tracked owner | Runtime input |
|---|---|---|
| Bids, placements, harvests, negatives, pacing, and staged applies | `skills/amazon-ppc-management/SKILL.md` | `_local/ads-strategy/strategy.json` |
| Interactive Ads Console work and non-SP routing | `skills/amazon-ads/SKILL.md` | Current Amazon help |
| New Sponsored Products campaign construction | `skills/amazon-campaign-builder/SKILL.md` | Per-run config plus local strategy |
| Read-only performance flags and briefs | `skills/amazon-ads-monitor/SKILL.md` | Local strategy plus client goal/stage |
| Audit diagnosis and client-facing verdicts | `skills/amazon-audit/SKILL.md` | Audit evidence and local strategy |
| Product Type, browse-node, and catalog-attribute readiness | `skills/amazon-seo/SKILL.md` | Backend catalog evidence |

## Recall contract

Before an ads workflow, run `python3 tools/ads_recall.py <surface>`. The helper
resolves the team vault, lists the implementation decision when present, then the
synchronized challenge decisions, matching Playbook, and Research topics. The agent reads the returned files in that
order. If the team vault is unavailable, the helper exits successfully without output
and the tracked skill plus local strategy remain sufficient to continue.

New contradictions go to `Research/amazon-ads/challenges.md`. Decided challenges are
not re-opened from Research. Changing an approved rule requires a new decision record.

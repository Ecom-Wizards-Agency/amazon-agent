# New client setup: SB video briefs

1. Copy `config.TEMPLATE.json` to `config.<client>-<market>.json` (stays local, gitignored). Fill every `<...>`; never carry values from another client's config.
2. Required before the first run: Seller Central account name (POE `--expect-account`), marketplace + language, target ASIN(s), DataDive niche id, break-even ACOS (mark ASSUMED if unconfirmed), and the client's Drive ads/creative folder for the briefing Google Doc.
3. Brand kit and footage locations can start as "none": the first brief then carries a shot list instead of a source-footage column.
4. Run via `/video-brief <client>-<market>`. The skill (`skills/amazon-sb-video-briefs/SKILL.md`) owns the workflow; this folder only holds the config contract.

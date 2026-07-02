---
description: Create Amazon SP campaigns from a text brief (config → bulk-upload .xlsx + review; file-only, upload stays manual)
argument-hint: "[client-market or the brief itself, e.g. acme-us: 5 SKW + 1 auto for GB-001]"
---

# Create Campaigns (SP bulk file)

Build Sponsored Products campaigns from the operator's text brief. Do not duplicate logic here — route into the `amazon-campaign-builder` skill and the `tools/amazon-campaign-builder/` toolkit.

The user's brief is: **$ARGUMENTS**

## Steps

1. **Confirm the brief — ask first.** Collect with a single AskUserQuestion, skipping what `$ARGUMENTS`/the conversation already supplies: client/brand · marketplace + account · SKUs (or ASINs for vendors) · campaign types (SKW/Halo/BMM/Phrase/Auto/PAT) · keywords or target ASINs · daily budget + bid · portfolio · negatives · start date · paused (default) vs enabled. Never carry a prior client's values.

2. **Load the skill** `amazon-campaign-builder` as source of truth.

3. **Scaffold the config** — copy `tools/amazon-campaign-builder/config.TEMPLATE.json` → `config.<client>-<market>.json` and fill `campaigns[]` from the brief.

4. **Preflight** — `build_campaigns.py --config <cfg> --preflight` until READY (fix what it lists).

5. **Preview** — `--preview`; show the operator every planned campaign and the combined daily budget. Adjust the config until it matches intent.

6. **Build + QA** — `--config <cfg>`; gates must PASS. Deliver the `.xlsx` + `_REVIEW.md` paths.

7. **Stop.** Uploading in Campaign Manager → Bulk Operations (or any AdLabs push) is a separate operator-confirmed action — never do it as part of this command.

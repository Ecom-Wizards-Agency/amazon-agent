# /fill-campaigns: fill the workbook's Campaign Structure tab (visual plan only)

Fill the `5. Campaign Structure` tab of a built keyword-research workbook per the local ads
strategy. Output = the filled tab + a Proposed Campaign Names block. **This flow never creates
campaign bulk files, never uploads anything, and never touches Amazon.** Pasting the plan into the
bulk-creator webapp is the operator's manual step afterwards.

Load the `amazon-seo-keyword-workflow` skill (section "Campaign Structure Fill") first.

## Steps

1. **Confirm scope** with the operator if not given: which client config
   (`tools/amazon-seo-keyword-workbook/config.<client>.json`) and which built workbook `.xlsx`.
2. **Check the local strategy files** `_local/ads-strategy/strategy.json` + `strategy.md`:
   - Missing or `<placeholders>` → Claude: offer to create/refresh them from the Notion playbooks
     listed in the strategy.md header (via `tools/amazon-seo-keyword-workbook/ads-strategy.TEMPLATE.*`).
     Codex: stop and ask the operator for the files. Never guess thresholds.
   - Check the client config has `campaign_structure.own_brand_tokens` and
     `product_name_for_naming`; ask once for missing values.
3. **Extract**:
   ```bash
   .venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
     --config <cfg> --workbook <xlsx> --extract output/<client>/ads/<date>_campaign_candidates.json
   ```
4. **Classify** (agent judgment): read the candidates JSON + `_local/ads-strategy/strategy.md`;
   assign keywords/ASINs to scaffold slots per the judgment rules (Wave intent tiers, discovery
   root specificity, halo theming, PAT strength). Write
   `output/<client>/ads/<date>_campaign_classification.json`
   (schema `amazon-agent.campaign-classification.v1`), each judgment call with a short `why`.
5. **Dry-run and show the operator** the slot fill counts + proposed names:
   ```bash
   ... --apply <classification.json> --dry-run
   ```
   Fix validation FAILs by correcting the classification, never by weakening the validator.
6. **Apply** after the operator confirms (writes a timestamped `.bak` next to the workbook):
   ```bash
   ... --apply <classification.json>
   ```
7. **Report and stop**: filled counts per bucket, warnings, backup path, and where the Proposed
   Campaign Names block is (below the scaffold). Do not build bulk files, do not open the webapp,
   do not push anything to AdLabs.

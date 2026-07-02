# Campaign Builder — End-to-End Workflow

Text brief → structured config → SP bulk-upload `.xlsx` → operator review → operator upload. The config is the contract; nothing in the code is client-specific.

## Roles

- **Agent (Claude or Codex)**: parses the operator's brief, asks for missing required fields, scaffolds the config, runs preflight/preview/build, presents the review — then **stops**.
- **Operator**: confirms the preview, uploads the file in Campaign Manager → Bulk Operations, flips paused campaigns live when ready.

## Steps

1. **Brief** — the operator describes the campaigns in plain text ("SKW campaigns for these 5 keywords on GB-001, $15 budget, plus one auto at $10…"). Ask once for anything required but missing: marketplace/account, SKUs/ASINs, keywords or target ASINs, budget, bid, portfolio, negatives, start date, paused vs enabled.

2. **Scaffold** — copy `config.TEMPLATE.json` → `config.<client>-<market>.json` (gitignored), fill `campaigns[]` from the brief. See `NEW-CLIENT.md`.

3. **Preflight** — `build_campaigns.py --config <cfg> --preflight` until READY. It catches invalid enums, sub-minimum bids/budgets, missing SKUs/keywords, past start dates, and name fan-out without a `Counter` token.

4. **Preview** — `--preview` prints every planned campaign (name, type, state, budget, bid, strategy, target counts) and the combined daily budget. Show this to the operator; adjust the config until it matches intent.

5. **Build** — `--config <cfg>` writes `output/<client-slug>/ads/<date>_<Brand>_<Market>_SP_bulk_campaigns.xlsx` + `…_REVIEW.md` and auto-runs the QA gates (must PASS).

6. **Review + handoff** — give the operator the review file and the path. **The workflow ends here.**

## Safety rails

- Campaigns default to **paused**; `enabled` requires the operator to ask for it and triggers a preflight live-on-upload note.
- The tool writes a file; it has no Amazon Ads API or AdLabs write path. Uploading the bulk file, pushing via AdLabs `create_entities`, changing live bids/budgets — each is a stop-before-risk action needing explicit operator instruction in the current chat (or a matching `_local/local-permissions.md` standing permission).
- For AdLabs-managed accounts the operator may instead ask for a gated AdLabs push: that follows the `amazon-adlabs-audit` write policy (explicit per-write lift, batch-by-batch what-will-change summary, tags) — it is not part of this toolkit.

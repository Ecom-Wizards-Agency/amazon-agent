# New Client — Campaign Builder Onboarding

Checklist to build campaigns for a new client/brief. No code changes — only a new config.

## 1. Scaffold the config

```bash
cp tools/amazon-campaign-builder/config.TEMPLATE.json \
   tools/amazon-campaign-builder/config.<client>-<market>.json
```

Never carry another client's values (the config-scaffolding rule: the anchor SKUs/ASINs are exactly what the operator gives, no leftovers).

Fill from the operator's brief:

- **`client`, `brand`, `marketplace`, `amazon_account`** — basics; `brand`+`marketplace` drive the output filename.
- **`vendor_central_mode`** — vendors advertise by ASIN (SKU column left blank); sellers by SKU.
- **`naming`** — the agency default is `Goal | SP | MatchType | ProductName | TargetDescriptor | EW`. Add `Counter` to `variable_order` whenever a spec fans out (SKW without keyword-in-name, or `transpose_keywords`); preflight will insist.
- **`defaults`** — `state` stays `paused` unless the operator explicitly asks for `enabled` (preflight prints a live-on-upload note if so). `start_date` empty = today. Placement percentages are whole numbers; 0 = no Bidding Adjustment row.
- **`campaigns[]`** — one entry per campaign spec from the brief. Minimum per entry: `campaign_type`, `product_name`, `sku` (or `asin` for vendors), and `keywords[]` (or `target_asins[]` for PAT). Everything else falls back to the campaign-type defaults or `defaults{}`.

## 2. Ask before assuming

If the brief doesn't say, ask the operator (one AskUserQuestion round): marketplace/account, SKUs to advertise, budget + bid, campaign types wanted, portfolio, negatives, start date, paused vs enabled.

## 3. Preflight → preview → build

```bash
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --preflight
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --preview   # show the operator
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg>             # build + QA gates
```

Present the `--preview` output (or the built `_REVIEW.md`) to the operator before treating the file as final.

## 4. Hand off — and stop

The deliverable is the `.xlsx` + `_REVIEW.md` under `output/<client-slug>/ads/`. Uploading it (Campaign Manager → Bulk Operations) is the operator's action, or a separately-confirmed agent action per the stop-before-risk rule. Never upload, push via AdLabs, or enable campaigns as part of this workflow.

# Amazon Campaign Builder Toolkit

Client-agnostic builder that turns a plain-text campaign brief into an Amazon **Sponsored Products bulk-upload `.xlsx`** (Bulk Operations format). Python port of the Ecom Wizards "Amazon Ads Bulk Creator" web app's generation core (`Ecom-Wizards-Agency/amazon-ads-bulk-creator`), verified row-for-row against the original (71-row fixture, 0 mismatches).

**One config, preview, build.** Nothing client-specific lives in the code. The agent fills `campaigns[]` from the operator's brief; the operator reviews the `_REVIEW.md` and uploads the file. Local `config.<client>-<market>.json` files are gitignored; only `config.TEMPLATE.json` is committed.

**Output is a file only.** This tool never uploads or touches live campaigns. Uploading via Campaign Manager → Bulk Operations (or any AdLabs push) is a separate, operator-confirmed action — stop-before-risk applies.

## Campaign types (same as the app)

| Type | Match | Goal | Bidding default | Shape |
|---|---|---|---|---|
| SKW | exact | Rank | down only | one campaign per keyword |
| Halo | exact | Profit | down only | one campaign, all keywords |
| BMM | broad (optional `+word` modifier) | Discovery | down only | one campaign, or chunked via `transpose_keywords` |
| Phrase | phrase | Discovery | down only | one campaign |
| Auto | auto | Discovery | up and down | 4 targeting groups with per-group bid/state |
| PAT | `asin=` / `asin-expanded=` | any | down only | one campaign over `target_asins[]` |

Campaign names come from `naming` (`Goal | SP | MatchType | ProductName | TargetDescriptor | EW` by default; add `Counter` whenever a spec fans out into several campaigns — preflight enforces this).

## Format fixes vs the source app

The web app emits vocabulary the bulksheets 2.0 upload parser doesn't document. This port emits what Amazon's docs and real bulk exports use (see `campaign_model.py` header):

| | App | This toolkit |
|---|---|---|
| Sheet name | `SP Campaigns` | `Sponsored Products Campaigns` |
| ID headers | `Campaign Id` … | `Campaign ID` … |
| Match type | `EXACT`/`BROAD`/`PHRASE` | `exact`/`broad`/`phrase` |
| Negative match | `NEGATIVE_EXACT`/`NEGATIVE_PHRASE` | `negativeExact`/`negativePhrase` |
| Bidding strategy | `Down only`/`Up and down`/`Fixed bids` | `Dynamic bids - down only`/`Dynamic bids - up and down`/`Fixed bid` |
| PAT expanded | `similar-product="…"` | `asin-expanded="…"` |
| Placement | `Placement Rest of Search` | `Placement Rest Of Search` |

Config files keep the app's short enums (`EXACT`, `Down only`, `NEGATIVE_EXACT`); the mapping happens at row-build time.

## Commands

```bash
# 1. Preflight — check the config contract, list missing/invalid fields or READY
python3 tools/amazon-campaign-builder/build_campaigns.py --config tools/amazon-campaign-builder/config.<client>-<market>.json --preflight

# 2. Preview — print the planned campaigns (names, budgets, targets), write nothing
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --preview

# 3. Build — write the bulksheet .xlsx + _REVIEW.md, then auto-run the QA gates
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg>

# QA gates only (re-check an already-built file)
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --validate
```

Default output: `output/<client-slug>/ads/<date>_<Brand>_<Market>_SP_bulk_campaigns.xlsx` (+ `…_REVIEW.md`). Override with `--out`.

## QA gates (`--validate`, also run after every build)

Header row exact; every row links to a real Campaign/Ad Group temp ID; enum values are Amazon-valid; bids in `[0.02, 1000]`, budget ≥ 1, placements whole 0–900; start dates `YYYYMMDD` and not past; no duplicate campaign names; no duplicate keyword+match in an ad group (cross-campaign duplicates warn as self-competition); every campaign has a Product Ad and ≥1 target; negatives over Amazon's 10-word/80-char cap warn.

## Files

- `campaign_model.py` — pure model: constants, naming, campaign generator, bulksheet row builder (channel-keyed; `SP` implemented, SB/SD writers can slot in later).
- `build_campaigns.py` — CLI: `--preflight` / `--preview` / build / `--validate`.
- `config.TEMPLATE.json` — the config contract (copy per client; see `NEW-CLIENT.md`).

Extend the toolkit, never hand-edit it per client — everything client-specific belongs in the config.

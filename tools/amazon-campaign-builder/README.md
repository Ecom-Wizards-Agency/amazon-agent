# Amazon Campaign Builder Toolkit (v2: create + update)

Client-agnostic toolkit that turns a plain-text brief (or a keyword-research workbook) into
Amazon **Sponsored Products bulk-upload `.xlsx`** files (Bulk Operations format), both to
**create** brand-new campaigns and to **update/pause/archive** existing ones. Create-mode is
a Python port of the Ecom Wizards "Amazon Ads Bulk Creator" web app's generation core
(`Ecom-Wizards-Agency/amazon-ads-bulk-creator`), verified row-for-row against the original
(71-row fixture, 0 mismatches); update-mode is new in v2 and has no web-app equivalent.
`tools/amazon-campaign-builder/selftest.py` is the regression suite for both. See "Testing"
below.

**One config, preview, build.** Nothing client-specific lives in the code. The agent fills
`campaigns[]` (or a change-set) from the operator's brief; the operator reviews the
`_REVIEW.md` and uploads the file. Local `config.<client>-<market>.json` /
`config.UPDATE.<client>-<market>.json` files are gitignored; only the `.TEMPLATE.json` files
are committed.

**Output is a file only.** This tool never uploads or touches live campaigns. Uploading via
Campaign Manager → Bulk Operations (or any AdLabs push) is a separate, operator-confirmed
action (stop-before-risk applies). **Update mode is the one exception to "nothing is live
yet"**: its rows reference real, currently-serving entities, so uploading an update-mode
file changes a live account the moment Amazon processes it. Its `_REVIEW.md` is mandatory
reading before that upload.

## Create mode

### Campaign types

| Type | Match | Goal | Bidding default (purpose) | Shape |
|---|---|---|---|---|
| SKW | exact | Rank | **Fixed bid** (Rank SKW) | one campaign per keyword |
| Halo | exact | Profit | down only | one campaign, all keywords |
| BMM | broad (optional `+word` modifier) | Discovery | down only | one campaign, or chunked via `transpose_keywords` |
| Phrase | phrase | Discovery | down only | one campaign |
| Auto | auto | Discovery | up and down | 4 targeting groups with per-group bid/state |
| PAT | `asin=` / `asin-expanded=` | any | down only (competitor) / up and down (self, via `campaign_purpose`) | one campaign over `target_asins[]` |

### Per-type bidding defaults (naming-convention.md, QC-enforced)

The bidding-strategy table is keyed by campaign **purpose**, not just `campaign_type`. Some
purposes cut across types (a Shield campaign can be SKW, BMM, or Phrase; PAT can be
competitor-targeting or self-targeting). Set `campaign_purpose` on a spec to opt into one of
these; leave it empty for the plain per-type default:

| Purpose | Bidding strategy | Trigger word |
|---|---|---|
| Rank SKW (default for `SKW`) | Fixed bid | `SKW` |
| Auto (default for `Auto`) | Dynamic bids - up and down | `Auto` |
| Category (`campaign_purpose: CATEGORY`) | Dynamic bids - up and down | `Category` |
| Self-Targeting (`campaign_purpose: SELF_TARGETING`) | Dynamic bids - up and down | `Self-Targeting` |
| Shield / Brand Defence (`campaign_purpose: SHIELD`) | Dynamic bids - down only | `Shield` |
| Discovery: BMM/Phrase/competitor PAT (default for `BMM`/`Phrase`/`PAT`) | Dynamic bids - down only | literal type |
| Halo (default for `Halo`) | Dynamic bids - down only | `Halo` |

Preflight NOTEs (not blocks) whenever a config's explicit `bidding_strategy` overrides this
table, so overrides are visible, never silent. `CATEGORY` has no dedicated generator yet
(no campaign type builds `category="..."` Product Targeting rows). It's a bidding/trigger-
word hook for when that's added; set it manually on a PAT-shaped spec if you build one by
hand today.

### Naming: EW convention (default) vs legacy

Default preset is **EW**, the 8-slot Ecom Wizards convention from `naming-convention.md`:

```
Goal | Ad Type | Match Type | Trigger Words OR Placement | Product Identifier | Keyword | Camp Counter | Suffix
```

- `Camp Counter` is emitted **only** for Halo and Auto campaigns (naming-convention.md); every
  other type has it silently blank (dropped from the joined name).
- `Trigger Words` matches the campaign type exactly, unless `campaign_purpose` sets it to
  `Shield` / `Self-Targeting` / `Category`.
- Ad group name is the shorter form: campaign name minus `Goal`/`Ad Type`/`Camp Counter`/`Suffix`.
  It is guaranteed to differ from the campaign name (preflight NOTEs the rare case where it doesn't).

Set `naming.preset: "LEGACY"` to keep the pre-v2 6-token order
(`Goal | SP | MatchType | ProductName | TargetDescriptor | EW`). Every existing config that
sets its own `naming.variable_order` explicitly continues to produce byte-identical names,
regardless of preset (an explicit `variable_order` always wins over any preset default; see
`build_campaigns.load_config`).

### Keyword-file input

Create mode can source `campaigns[]` from a keyword-research workbook instead of (or in
addition to) hand-written config entries:

```bash
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> \
  --keyword-file <keyword-research-workbook.xlsx> [--keyword-sheet "<sheet name>"]
```

See `keyword_workbook.py` for the two supported shapes:
1. The EW SEO keyword workbook's **"5. Campaign Structure"** tab (see
   `tools/amazon-seo-keyword-workbook/fill_campaign_structure.py`, which scaffolds/fills the
   same tab): bucketed sections (Rank-SKW, Shield-SKW, Long-Tails (Halo), Discovery-Root
   Keywords ×2 [BMM/Phrase], Shield Discovery-Brand Keywords, PAT (Stronger)/(Weaker)), each
   parsed independently of that sibling tool (no import-time coupling).
2. A generic tolerant flat table (any sheet with recognizable campaign-type/keyword/
   product/match-type/bid columns), grouped one campaign per (type, product).

**This parser is built against the documented scaffold shape and a synthetic fixture
(`selftest.py`). It has not been validated against a real client keyword workbook.**
Validate it against one before relying on it in production; the generic flat-table fallback
degrades gracefully if the "5. Campaign Structure" scan finds no sections.

`keyword_file_defaults` in the config supplies `product_name`/`sku`/`asin` (the workbook
itself doesn't carry those).

## Update mode

New in v2: `update_campaigns.py` + `update_model.py`, using a **downloaded bulksheets
export** (real IDs) + a **change-set config** (`config.UPDATE.TEMPLATE.json`) to build
Update/Archive/Create rows against an existing account.

```bash
# 1. Preflight: check the change-set against the loaded export
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg> --preflight

# 2. Preview: print every planned change in plain English, write nothing
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg> --preview

# 3. Build: write the bulksheet .xlsx + _REVIEW.md, then auto-run the QA gates
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg>

# QA gates only (re-check an already-built file against the same export)
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg> --validate
```

**Input:** `export_file`. A bulksheets download of the "Sponsored Products Campaigns" tab
(Bulk Operations → create/download a spreadsheet) is the **only** valid source of real
Campaign/Ad Group/Keyword/Product Targeting/Portfolio IDs. Never the console UI, never a
remembered/hardcoded ID from a prior session. The reference is explicit that this produces
a hard upload error.

**Supported operations:** campaign daily budget / bidding strategy / state / end date;
ad-group default bid / name / state; pause/archive keywords & targets; add new
keywords/negatives/PAT ASINs to existing ad groups; placement % modifiers; archive
campaigns/ad groups.

**Rules enforced (references/bulksheets-2.0-reference.md section 4):**
- Blank field on an Update row = unchanged, **except End Date**: blank clears an existing
  end date. This toolkit carries the export's current End Date forward on every Campaign
  Update row by default; clearing it requires the per-row `clear_end_date: true` **and** the
  change-set's top-level `allow_end_date_clear: true` (double opt-in, never accidental).
- **Portfolio ID is force-re-included** on every Campaign Update row from the export, never
  left to "blank = unchanged", since that silently drops the campaign from its portfolio.
- **Keyword Text / Match Type / Product Targeting Expression are immutable**: "changing" one
  is always Archive-old + Create-new (fresh temp ID for the new entity; real parent
  Campaign/Ad Group ID), never an Update to text.
- **Archive cascades**: archiving a Campaign/Ad Group automatically archives its children.
  The generator drops any explicit child-archive request whose parent is already archived in
  the same change-set (logged to the review trail as a cascade-skip), and the validator FAILs
  if one slips through anyway.
- **Negatives can only be archived**, never paused.
- **No-op rows are dropped** at generation time (nothing to change vs. the export = no row).

### QA gates (`--validate`)

Every Update/Archive row's ID must be real (bulksheets-numeric) **and** present in the loaded
export; Campaign Update rows belonging to a portfolio must carry `Portfolio ID`; no stray
Create rows for a whole new Campaign/Ad Group (those belong in create mode); Create rows for
Keyword/Negative/Target must attach to a real, existing parent; no-op Update rows; no
parent+child double archive.

## Format fixes vs the source app (create mode)

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

Config files keep the app's short enums (`EXACT`, `Down only`, `NEGATIVE_EXACT`); the mapping happens at row-build time. Operation values: this toolkit uses `Create`/`Update`/`Archive` (capitalized, matching the English-locale bulksheets template and the already-verified create-mode output). The reference's generic examples show lowercase `create`/`update`/`archive`; verify against a live upload if this ever becomes ambiguous in practice.

Default output: `output/<client-slug>/ads/<date>_<Brand>_<Market>_SP_bulk_campaigns.xlsx` (create) or `..._SP_bulk_UPDATE.xlsx` (update), each + `..._REVIEW.md`. Override with `--out`.

## Testing

```bash
python3 tools/amazon-campaign-builder/selftest.py
```

Synthetic, no network/Amazon access. Exercises: create mode with the LEGACY naming preset
(backward-compat check: unchanged naming formula and bidding defaults except the deliberate
SKW → Fixed bid change) and the EW preset (8-slot naming, `campaign_purpose` overrides, QC
notes); keyword-file input against a synthetic "5. Campaign Structure" fixture; update mode
against a synthetic export (budget/bidding/state/placement/portfolio/end-date rules,
ad-group updates, keyword pause/replace/add, negative archive/add, target archive/add,
parent+child archive cascade-dropping); and the update-mode QA gates against a deliberately
broken already-built file (temp ID, missing portfolio, parent+child double archive). All
three must FAIL `--validate`. Run this after any change to either toolkit.

## Files

- `campaign_model.py`: pure model. Constants, naming (LEGACY/EW presets), campaign-purpose
  bidding table, campaign generator, create-mode bulksheet row builder (channel-keyed; `SP`
  implemented, SB/SD writers can slot in later).
- `build_campaigns.py`: create-mode CLI. `--preflight` / `--preview` / build / `--validate`
  / `--keyword-file`.
- `keyword_workbook.py`: keyword-research-workbook → `campaigns[]` parser.
- `config.TEMPLATE.json`: create-mode config contract (copy per client; see `NEW-CLIENT.md`).
- `update_model.py`: pure model. Bulksheets-export reader, change-set → Update/Archive/
  Create row builder, cascade/no-op handling.
- `update_campaigns.py`: update-mode CLI. `--preflight` / `--preview` / build / `--validate`.
- `config.UPDATE.TEMPLATE.json`: update-mode change-set contract.
- `selftest.py`: regression suite for both modes (run after any change).
- `references/bulksheets-2.0-reference.md`: Amazon bulksheets 2.0 developer reference (the
  authority for column headers, Operation values, entity IDs, and Update semantics).

Extend the toolkit, never hand-edit it per client. Everything client-specific belongs in the config.

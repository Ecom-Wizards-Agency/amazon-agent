# Amazon Bulksheets 2.0: Developer Reference

Synthesized from Amazon's official docs at
`https://advertising.amazon.com/API/docs/en-us/no-code-tools/bulksheets/2-0/*`
for the `amazon-campaign-builder` toolkit (SP/SB/SD bulk-upload `.xlsx` generator).

**Scrape coverage:** 23 of the 29 target pages were retrieved in full; 5 were retrieved
partially (oversized pages, content extracted via targeted excerpts rather than a full
verbatim dump); 2 could not be retrieved at all after repeated retries (Firecrawl
rate-limiting / hard scrape failures). See the coverage table at the end of this file.
Every section below cites its source page(s); where confidence is lower (partial/failed
source), that is flagged explicitly rather than presented as verified fact.

---

## 1. Overview & file model

**Sources:** overview-about-bulksheets, get-started-with-bulksheets-part1, understand-bulksheets-data, migration-guide (all fully captured)

### The three-column foundation

Every bulksheets row is driven by three leading columns:

| Col | Field | Meaning |
|---|---|---|
| A | **Product** | Which channel this row belongs to: `Sponsored Products`, `Sponsored Brands`, `Sponsored Display` |
| B | **Entity** | What kind of record this row defines: `Campaign`, `Ad Group`, `Product Ad`, `Keyword`, `Negative Keyword`, `Product Targeting`, `Negative Product Targeting`, `Bidding Adjustment`, `Draft Campaign` (SB), `Ad` (SB multi-ad-group), etc. |
| C | **Operation** | The action to take on this row: `create`, `update`, `archive`, or `submit` (SB draft campaigns only, to launch a draft). **Blank = row is ignored entirely**. This is how you can safely re-upload a full campaign-data download without touching rows you don't want to change. |

This replaced the legacy bulksheets' single "Record Type" + "Record ID" model. In the new
model, every entity type gets its own ID column (Campaign ID, Ad Group ID, Keyword ID,
Product Targeting ID, Ad ID / Product Ad ID, Portfolio ID, Draft Campaign ID for SB), and
Campaign/Ad Group **names are now directly editable** (a genuine capability upgrade over
legacy bulksheets). (Source: migration-guide)

### Create vs Update vs Archive vs Submit

- **create**: define a brand-new entity. Requires a **temporary text ID** in that entity's
  ID column (e.g. `campaign_1`), not a real numeric ID.
- **update**: modify an existing entity. Requires the **real, system-generated ID** for
  that entity and every parent entity it references. Fields left blank are generally
  **unchanged** (see Section 4 for the important exceptions).
- **archive**: soft-delete an entity. Requires the real ID. **Cascades to all children**
  (archiving a Campaign also archives its Ad Groups, Keywords, Targets, etc.); see the
  cascade warning in Section 4.
- **submit**: Sponsored Brands only, applies to Draft Campaigns. Launches a campaign that
  was created in draft state (Entity = `Draft Campaign`) so it stops being a draft and
  starts serving.

### Temp-ID linking (create) vs real-ID linking (update/archive)

When **creating**, you invent a temporary ID string for a parent entity (Campaign ID, Ad
Group ID) and every child row in the *same upload file* that belongs to that parent must
reuse the **exact same temp ID string**. Amazon replaces the temp ID with a real
system-generated numeric ID during processing. You cannot create a parent in one uploaded
file and reference its temp ID from a later, separate upload. Once processed, only the
real ID works going forward.

When **updating or archiving**, every ID column must contain the **real, Amazon-generated
ID**: never a temp ID, and never the ID shown in the advertising console UI. Bulksheets
IDs are sourced by **downloading a bulksheet with campaign data** (Bulk operations page →
create/download a spreadsheet with the entities you want). This is a critical, easy-to-miss
rule: **console-displayed campaign/ad-group/keyword IDs are not guaranteed to match
bulksheets IDs**. Always source IDs from a bulksheets download, never from the console UI
or from IDs remembered/hardcoded from a prior session. Uploading an Update row with an
"actual" ID that is really a leftover temp ID produces a hard error (confirmed verbatim in
the error-report catalog, Section 7: *"This Update operation requires you to specify an
actual 'Campaign ID', rather than a temporary ID"*).

### Tab-per-channel layout

A custom-downloaded bulksheet can contain one tab per campaign type you selected
(Sponsored Products, Sponsored Brands, Sponsored Display), plus:
- a **Portfolios** tab (Portfolio ID, name, budget policy) if you included portfolio data
- a **Brand Assets Data** tab (Sponsored Brands only, if you check "brand assets data" on
  download), required to source Brand Entity ID / Brand Logo Asset ID / Video Asset ID
  values before you can create new SB campaigns via bulksheets referencing existing
  creative. Columns: Asset Type (`backgroundVideo`, `brandLogo`, `customImage`,
  `otherImage`, `productImage`, `video`), Brand Entity ID (sellers only, format like
  `ENTITY00BR549`), Asset ID, Asset Name, Asset URL.
- an optional **input guidance** column set for Sponsored Products (English-only feature)

Terminated campaigns and zero-impression items are excluded from downloads by default;
check the corresponding boxes on download to include them (useful for finding
under-performing keywords to negate). (Source: understand-bulksheets-data)

---

## 2. Column / field dictionary

**Sources:** get-started-with-sp-bulksheets, get-started-with-sb-bulksheets, sb-multi-ad-groups-overview, get-started-with-sd-bulksheets, sp-entities, sb-entities, sb-multi-ad-group-entities, sd-entities, migration-guide

### Common to all channels
`Product`, `Entity`, `Operation`, `Campaign ID`, `Campaign Name`, `Portfolio ID`,
`Start Date`, `End Date` (format **`YYYYMMDD`**, e.g. 20230712), `State`
(`enabled` / `paused` / `archived`), `Budget`/`Daily Budget`, `Budget Type`.

### Sponsored Products (SP)
Entity-specific columns, matching the toolkit's existing `SP_COLUMNS`:

`Product, Entity, Operation, Campaign ID, Ad Group ID, Portfolio ID, Ad ID, Keyword ID,
Product Targeting ID, Campaign Name, Ad Group Name, Start Date, End Date, Targeting Type,
State, Daily Budget, SKU, ASIN, Ad Group Default Bid, Bid, Keyword Text, Match Type,
Bidding Strategy, Placement, Percentage, Product Targeting Expression, Sites`

Which columns each entity row actually uses:

| Entity | Required/used columns |
|---|---|
| Campaign | Campaign ID, Campaign Name, Start Date, Targeting Type (`manual`/`auto`), State, Daily Budget, (Portfolio ID, End Date, Bidding Strategy optional) |
| Bidding Adjustment (optional child of Campaign) | Campaign ID, Placement, Percentage |
| Ad Group | Campaign ID, Ad Group ID, Ad Group Name, State, Ad Group Default Bid |
| Product Ad | Campaign ID, Ad Group ID, Ad ID, SKU **or** ASIN (one, not both; sellers use SKU, vendors use ASIN), State |
| Keyword | Campaign ID, Ad Group ID, Keyword ID, Keyword Text, Match Type, Bid (blank ⇒ inherits Ad Group Default Bid), State |
| Negative Keyword (ad-group or campaign level) | same as Keyword + Negative Match Type instead of Match Type; no Bid |
| Product Targeting | Campaign ID, Ad Group ID, Product Targeting ID, Product Targeting Expression, Bid, State |
| Negative Product Targeting | same, no Bid |

`Sites` is a US-only, SP-only "off-Amazon ad serving" toggle at the campaign level
(values: `Increase reach`, `Limit off-Amazon spend`).

### Sponsored Brands: legacy (single implicit ad group)
Key columns beyond the common set: `Ad Format` (`productCollection`, `video`; bulksheets
does **not** support `Store Spotlight` per the migration guide), `Budget`, `Budget Type`,
`Landing Page Url`, `Landing Page ASINs` (defines products shown on a *new* landing page;
do not use `Landing Page Url` to create a new page), `Brand Name`, `Brand Entity Id`
(sellers only, now **required**, sourced from Brand Assets Data tab), `Brand Logo Asset Id`,
`Creative Headline`, `Creative ASINs`, `Video Media Ids`, `Bid Optimization`
(`auto`/`manual`), `Bid Multiplier`, `Bid`, `Keyword Text`, `Match Type`,
`Product Targeting Expression`, `State`. There is **no Ad Group column**: SB legacy
manages its single ad group implicitly.

### Sponsored Brands: multi-ad-group (v4)
Adds explicit `Ad Group ID`/`Ad Group Name` entity rows and an `Ad` entity row (nested
under Ad Group ID) carrying the creative fields instead of the Campaign row. Keyword and
Product Targeting rows now nest under **Ad Group ID**, not directly under Campaign ID.
`Bid Optimization` becomes a boolean `true`/`false` (vs legacy's `auto`/`manual` string).
Ad entity types (see Section 6 for the full list): `Manual Collection ad`,
`Automatic Collection ad`, `Store spotlight ad`, `Video ad`, `Brand video ad` (and the
deprecated `Product collection ad`).

### Sponsored Display (SD)
Common set plus: `Ad Group ID`/`Ad Group Name`/`Ad Group Default Bid`, `Ad ID`, `SKU`/`ASIN`,
a targeting-expression column (product or audience targeting, syntax matches SP's
`asin="..."`/`category="..." price<49.99 rating>3` style; see Section 6), `Bid`,
`Cost Type`, and a Tactic/targeting-type distinction between contextual and audience
targeting. **Caveat:** the SD create-flow page (`create-sd-campaign`) could not be
retrieved in this pass (see coverage table). Verify the exact SD column set and row
order against a fresh bulksheets download before building an SD writer.

---

## 3. Create semantics per channel

**Sources:** create-sp-campaign (partial), create-sb-campaign (full), create-sb-multi-ad-group-campaigns (partial), create-sd-campaign (failed, not retrieved)

### Sponsored Products
Row-by-row build order (temp IDs at each step, reused by children):
1. **Define the campaign entity.** Required fields: `Product, Entity, Operation, Campaign
   ID (temp), Campaign Name, Start Date, Targeting Type, State, Daily Budget`.
2. **Bidding Adjustment entity (optional)**: references the same Campaign ID (temp),
   defines `Placement`/`Percentage` bid modifiers.
3. **Ad Group entity**: new temp `Ad Group ID`, references parent `Campaign ID`.
4. **Product Ad entity**: references `Campaign ID` + `Ad Group ID`, carries `SKU`/`ASIN`.
5. **Keyword / Product Targeting entities**: reference `Campaign ID` + `Ad Group ID`, each
   gets its own temp ID (`Keyword ID` / `Product Targeting ID`).
6. **Negative Keyword / Negative Product Targeting**: same pattern, at ad-group or
   campaign level.

### Sponsored Brands (legacy, create-sb-campaign: fully captured)
Because SB legacy has one implicit ad group, the **Campaign row itself carries the ad
creative fields** (Ad Format, Landing Page, Brand assets, Creative Headline/ASINs, Video
Media IDs). There is no separate Ad Group or Ad entity step. Keyword/Product Targeting
rows reference the Campaign ID (temp) directly. Draft campaigns: create with
`Entity = Draft Campaign`, `Operation = create` (and a `Draft Campaign ID` temp ID); to
launch, submit a subsequent row with `Operation = submit` referencing the real Draft
Campaign ID (post-processing).

### Sponsored Brands multi-ad-group (v4, create-sb-multi-ad-group-campaigns: partial)
Confirmed step structure from partial extraction: **Step 1** campaign entity (required
fields list confirmed present but not fully re-extracted verbatim) → **Step 1a** →
**Step 2** ad group entity → **Step 3** ad entity (creative fields move here, off the
campaign row) → **Step 3a** / **Step 3b** keyword/targeting entities nested under Ad Group
ID → **Step 4**. Recommend re-verifying the exact per-step required-field list against a
live bulksheets template before building an SB-v4 writer, since this page was only
partially recovered.

### Sponsored Display
**Not retrieved** (create-sd-campaign scrape failed on every attempt; see coverage
table). Do not assume SD create-row-order without checking a live template; only the
general column dictionary in Section 2 is confidently known.

### Universal create rule
Every temp ID must be **unique within the upload** for its entity type (reusing a temp ID
across two different Create rows for the same entity type is a documented error:
"Duplicate ID", Section 7), and every child row's parent-ID reference must resolve to a
parent-defining row present in the **same file** (a "Missing Parent ID" error otherwise).

---

## 4. Update semantics per channel: the critical rules

**Sources:** campaign-update-overview, update-sp-campaigns, update-sb-campaigns, update-sd-campaigns (all fully captured), update-sb-multi-ad-group-campaigns (partial), migration-guide, bulksheets-error-reports (partial, verbatim error strings captured)

This is the section the campaign-builder v2 toolkit most needs, since the current
implementation is create-only.

### 4.1 IDs must be real, not temp
Every ID column on an Update or Archive row (Campaign ID, Ad Group ID, Keyword ID, Product
Targeting ID, Ad ID, Portfolio ID) must be the **real system-generated ID**, sourced from
a **bulksheets download**: never a temp ID, never a console-displayed ID. Confirmed
verbatim error: *"Input Error | Invalid ID | This Update operation requires you to specify
an actual 'Campaign ID', rather than a temporary ID."*

### 4.2 Blank fields = unchanged, with exceptions
On an Update row, a blank cell generally means **"leave this field unchanged"**: bulksheets
Update is a sparse/partial patch, not a full overwrite. The most important documented
**exception** is:

- **End Date**: leaving End Date blank lets the campaign run indefinitely (removes any
  existing end date). This is explicitly documented for the "run campaigns indefinitely"
  create-time behavior (migration-guide); treat blank End Date on an Update row as
  clear/override, not "no change," and **verify this against a live test upload** before
  relying on it in production, since the two source pages did not give a single
  unambiguous statement reconciling create-time vs update-time blank-End-Date behavior.

### 4.3 Portfolio ID must be re-included on every campaign update
If a campaign belongs to a Portfolio and you submit an Update row for that campaign, you
must **re-include the Portfolio ID** on that row. Omitting/blanking it **removes the
campaign from its portfolio**. This is not a "no change" case despite the general
blank-means-unchanged rule, so it is one of the highest-risk silent-data-loss traps in the
whole spec.

### 4.4 Keyword Text and Match Type are immutable
You cannot Update the `Keyword Text` or `Match Type` of an existing Keyword ID: these
fields are locked once created. To "change" a keyword: **Archive** the old Keyword ID row
and **Create** a brand-new keyword row (fresh temp ID) with the new text/match type,
either in the same upload or a follow-up one. The same immutability applies to Product
Targeting Expression.

### 4.5 SB creative fields are immutable post-creation
Landing Page URL, Brand Entity ID/Name/Logo, Creative Headline, Creative ASINs, Video
Media IDs, and Ad Format/Creative Type cannot be changed via Update. To change any of
these, Archive and recreate the whole campaign (SB legacy) or the specific Ad row (SB
multi-ad-group v4).

### 4.6 Archive cascades to children: do not double-archive
Archiving a parent entity (Campaign, Ad Group) automatically archives all of its children.
**Do not also explicitly Archive a child row in the same upload as its parent's Archive
row**. This produces confusing "Not Processed" duplicate-processing warnings in the error
report rather than a clean result. Archive only the highest-level entity you actually want
removed.

### 4.7 Campaign negative keywords cannot be paused
For campaign-level negative keywords, the only lifecycle transition is Archive (there is
no pause). Archiving a campaign negative keyword deletes it from all records it applied
to. (Source: migration-guide known-issues table.)

### 4.8 Exact Operation values
`create`, `update`, `archive`, `submit` (submit = SB draft campaigns only). Values are
translated per-profile-language on download but any supported language's translated value
is accepted on upload regardless of the uploader's profile language (Source:
bulksheets-language-guide; full translation table in Section 7).

### 4.9 Every row needing action needs an explicit Operation value
Rows with a blank Operation are **ignored entirely, including for validation**. This is
what makes it safe to re-upload a full data export and only touch specific rows.

### 4.10 Common Update-time errors (verbatim from bulksheets-error-reports, partial capture)
- `Missing Parent ID`: "Invalid value for column: 'Campaign ID', which can't be found in
  any parent entity row". The referenced parent doesn't exist yet in Amazon's system (for
  Update) or wasn't defined in the same file (for Create).
- `Invalid User Input`: "Could not find campaign/ad group/keyword with id: NNNN". Stale
  or wrong ID.
- `Invalid User Input`: "Invalid id provided." / "EntityID does not exist." (seen on
  Portfolio ID rows specifically; fix: use the correct system-generated Portfolio ID).
- `Duplicate ID`: same temp ID reused across two Create rows.
- `Duplicate Text`: same Keyword Text reused within the same ad group/match type context.
- `Invalid user input`: "Campaign with name = X already exists!" / "AdGroup with name = X
  already exists!" (name collision with an existing active entity).
- `#VALUE!` in a numeric field (e.g. Bid): a literal Excel formula error leaked into the
  cell instead of a plain number; replace with a valid numeric value.
- `Invalid user input`: "Keyword is invalid" (invalid character in Keyword Text).

---

## 5. Editable vs non-editable fields

**Source:** editable-non-editable-bulksheets-fields (fully captured)

General categorization (cross-checked against Sections 3/4 above; treat the specific
immutability rules in 4.4/4.5 as the load-bearing detail, and this section as the
organizing summary):

**Editable via Update** (blank = unchanged, per 4.2): Campaign Name, Ad Group Name,
Budget/Daily Budget, State, Start Date, End Date (with the blank-clears-it exception for
End Date), Bid, Ad Group Default Bid, Bidding Strategy, Portfolio ID (must be
**re-supplied**, not just "editable"), Percentage (bidding adjustment).

**Not editable / immutable once created** (must Archive + Create to change):
Keyword Text, Match Type, Product Targeting Expression, Targeting Type (manual/auto,
campaign-level), SKU/ASIN on a Product Ad, and for Sponsored Brands: Landing Page URL,
Landing Page ASINs, Brand Name/Entity/Logo IDs, Creative Headline, Creative ASINs, Video
Media IDs, Ad Format/Creative Type.

**Read-only (system-generated, informational only)**: all `*ID` columns (Campaign ID, Ad
Group ID, Keyword ID, Product Targeting ID, Ad ID) once assigned, plus any performance
metric columns (impressions, clicks, CPC, ROAS, conversion rate, etc.) included in a
downloaded bulksheet, useful for filtering/analysis but never uploaded back as an
instruction.

---

## 6. Entities reference: per-channel entities and enum values

**Sources:** sp-entities, sb-entities, sb-multi-ad-group-entities, sd-entities (fully captured), get-started-with-ras-bulksheets (fully captured), bulksheets-portfolios (fully captured)

### Entity lists per channel
- **SP:** Campaign, Bidding Adjustment, Ad Group, Product Ad, Keyword, Negative Keyword,
  Product Targeting, Negative Product Targeting.
- **SB (legacy):** Campaign, Draft Campaign, Keyword, Negative Keyword, Product Targeting,
  Negative Product Targeting. (No Ad Group/Ad; implicit single ad group.)
- **SB (multi-ad-group / v4):** Campaign, Draft Campaign, Ad Group, Ad, Keyword, Negative
  Keyword, Product Targeting, Negative Product Targeting.
- **SD:** Campaign, Ad Group, Product Ad, Product Targeting, Audience Targeting
  (contextual vs audience tactic), Negative Targeting.

### Verbatim enum values to preserve exactly

| Field | Values (exact strings) |
|---|---|
| Match Type (SP/SB) | `broad`, `phrase`, `exact` |
| Negative Match Type (SP/SB) | `negativeExact`, `negativePhrase` |
| Bidding Strategy (SP) | `Dynamic bids - down only`, `Dynamic bids - up and down`, `Fixed bid` |
| Product Targeting Expression syntax | `asin="B000000000"` (lowercase `asin`), `asin-expanded="B000000000"`, `category="5524098011" price<49.99 rating>3`, `prime-shipping-eligible="true"` |
| State (all entities) | `enabled`, `paused`, `archived` |
| SB Ad Format (legacy) | `productCollection`, `video` (Store Spotlight not supported via bulksheets) |
| SB Ad types (v4/multi-ad-group) | `Manual Collection ad`, `Automatic Collection ad`, `Store spotlight ad`, `Video ad`, `Brand video ad`; `Product collection ad` is **deprecated** |
| SB Bid Optimization | legacy: `auto` / `manual` (string); v4: `true` / `false` (boolean) |
| RAS Auto Match Type | `Keywords Close Match`, `Keywords Loose Match`, `Product Substitutes` |
| RAS Keyword Match Type | `BROAD`, `PHRASE`, `EXACT` (**all caps**; differs from SP's lowercase) |
| RAS Bidding Adjustment Placement | `PLACEMENT TOP` |
| Portfolio Budget Policy | `dateRange`, `monthlyRecurring`, `noCap` |
| Off-Amazon ad serving (SP `Sites`, US only) | `Increase reach`, `Limit off-Amazon spend` |
| Native profile-language locale codes (bulksheets-language-guide) | `ar_AE`, `nl_NL`, `fr_FR`, `de_DE`, `it_IT`, `ja_JP`, `pl_PL`, `pt_BR`, `es_ES`, `es_MX`, `sv_SE`, `zh_CN` |
| Operation values | `create`, `update`, `archive`, `submit` (SB draft only) |

**RAS note:** Retail Ad Service (Sponsored Products across retailers) reuses the SP entity
model but with its own casing for match types (`BROAD`/`PHRASE`/`EXACT` vs SP's lowercase)
and its own placement string (`PLACEMENT TOP`). Do not share an enum-mapping table between
SP and RAS if the toolkit ever adds RAS support.

### Portfolios
Portfolio ID is sourced from a Portfolios tab in a bulksheets download; **bulksheets
cannot create new portfolios**, only associate an existing Portfolio ID with a campaign.
Budget Policy values: `dateRange`, `monthlyRecurring`, `noCap`.

---

## 7. Input guidance, language guide, keyword translations, portfolios, search-term report, error reports

**Sources:** input-guidance (full), bulksheets-language-guide (full), bulksheets-keyword-translations-guide (full), bulksheets-portfolios (full), bulksheets-search-term-report (**failed, not retrieved**), bulksheets-error-reports (partial)

### Input guidance (SP only, English-only)
An optional checkbox on download adds inline guidance columns/tips to a Sponsored Products
bulksheet (e.g., bid-range suggestions, warnings). This feature is disabled in the upload
UI whenever the advertiser profile's language isn't English.

### Language guide for the Operation field
Bulksheets downloads render in the advertiser profile's language, but **uploads accept any
supported language's values regardless of profile language**. Full translation table for
the Operation column (Create / Update / Archive / Submit):

| Locale | Create | Update | Archive | Submit |
|---|---|---|---|---|
| English (EN/AU/CA/GB/IN/SG) | Create | Update | Archive | Submit |
| Arabic (AE) | إنشاء | تحديث | الأرشيف | إرسال |
| Simplified Chinese (CN) | 创建 | 更新 | 存档 | 提交 |
| Traditional Chinese (TW) | 建立 | 更新 | 封存 | 提交 |
| French (FR/CA) | Créer | Mettre à jour | Archiver | Soumettre |
| German (DE) | Erstellen | Aktualisieren | Archivieren | Absenden |
| Italian (IT) | Crea | Aggiorna | Archivia | Invia |
| Japanese (JP) | 作成 | 更新 | 非表示にする | 送信 |
| Korean (KO) | 생성 | 업데이트 | 보관 | 제출 |
| Swedish (SE) | Skapa | Uppdatera | Arkiv | Skicka in |
| Spanish (CO/ES/MX) | Crear | Actualizar | Archivar | Enviar |
| Polish (PL) | Utwórz | Aktualizuj | Zarchiwizuj | Prześlij |
| Portuguese (BR) | Criar | Atualização | Arquivar | Enviar |
| Tamil (IN) | உருவாக்கு | புதுப்பிப்பு | காப்பகம் | சமர்ப்பிக்கவும் |
| Thai (TH) | สร้าง | อัพเดต | เก็บถาวร | ส่ง |
| Turkish (TR) | Oluştur | Güncelle | Arşivle | Gönder |
| Vietnamese (VN) | Tạo | Cập nhật | Lưu trữ | Gửi |
| Dutch (NL) | Maken | Bijwerken | Archief | Indienen |
| Hindi (IN) | बनाएँ | अपडेट करें | आर्काइव करें | सबमिट करें |

Blank Operation = row ignored, regardless of language.

### Keyword translations guide
Covers translated field values (match-type labels etc.) appearing in non-English
downloads and guidance on entering keyword text for non-English catalogs/marketplaces;
same underlying principle as the language guide: downloads localize, uploads accept any
supported-language value.

### Portfolios
See Section 6. Portfolio ID from a bulksheets download only; no portfolio creation via
bulksheets; Budget Policy = `dateRange` / `monthlyRecurring` / `noCap`.

### Search term report
**Not retrieved**: every scrape attempt on this page failed ("all scraping engines
failed"/rate-limited). No verified detail available; do not rely on this reference for
search-term-report specifics. General expectation (unverified): a downloadable report of
customer search terms that triggered SP/SB impressions for auto/broad/phrase targeting,
obtained via the same bulk-operations download flow. Confirm against the live docs page
before implementing anything dependent on it.

### Error reports
After any upload, Amazon returns a downloadable error report with columns resembling
`Product | Entity | Operation | [ID columns] | Error Type | Error code | Error message`.
Error Type is either `Warning` (e.g. `Not Processed`: row skipped due to a related row's
failure) or `Input Error` (a real problem: `Missing Parent ID`, `Invalid ID`,
`Duplicate ID`, `Duplicate Text`, `Invalid User Input`). See the verbatim examples
catalogued in Section 4.10. This page was only partially recovered (oversized scrape);
the excerpts above are representative but not the complete error catalog; cross-check
against a live error report if building automated error-report parsing.

---

## 8. Implications for the campaign-builder v2 toolkit

Current toolkit state (per `README.md`/`campaign_model.py`): **SP-only, create-only.**
`SP_COLUMNS` and the enum-mapping tables (`AMAZON_MATCH`, `AMAZON_NEG_MATCH`,
`AMAZON_BIDDING`, `asin-expanded=`) already match real Amazon bulksheets 2.0 vocabulary.
This is correct and should not change. Everything below is what's **missing** for
correct-and-safe Update support, plus channel-expansion caveats.

1. **Every SP column/enum currently in `campaign_model.py` is verified correct** against
   the real bulksheets 2.0 spec (exact/broad/phrase, negativeExact/negativePhrase,
   "Dynamic bids - down only"/"...up and down"/"Fixed bid", `asin-expanded=`,
   "Placement Rest Of Search"). No changes needed there.

2. **Update mode needs a completely separate ID-sourcing input**, distinct from the
   create-mode temp-ID generator. The generator must accept real, bulksheets-downloaded
   Campaign ID / Ad Group ID / Keyword ID / Product Targeting ID / Ad ID / Portfolio ID
   values as config input for any row where `Operation = update` or `archive`, and must
   never reuse a temp-ID-style value in that path. Add explicit validation that these look
   like real numeric IDs, not generator-invented strings.

3. **The Operation column must become an explicit per-row field** the generator sets
   (`create`/`update`/`archive`/`submit`) instead of being implicitly "create" for every
   row, as it is today.

4. **Update rows must be sparse, not fully populated.** The row-builder for Update needs
   opposite semantics from the create row-builder: only emit values for fields the caller
   actually wants changed; leave everything else blank so Amazon preserves the existing
   value. This is a structurally different code path, not a flag on the existing builder.

5. **Portfolio ID must be force-re-included on every Update row for a campaign that has
   one.** This is the single highest-risk silent-data-loss trap: if the generator's Update
   path doesn't carry forward a campaign's existing Portfolio ID, the campaign silently
   drops out of its portfolio. Add a QA gate that flags any Update-Campaign row missing
   Portfolio ID when the target campaign is known to belong to one.

6. **Never emit an Update row that changes Keyword Text, Match Type, or Product Targeting
   Expression.** These are immutable. The generator must instead emit an
   Archive-old-Keyword-ID + Create-new-Keyword(fresh temp ID) pair whenever a config
   change implies altering keyword text/match type.

7. **Never emit an Update row for SB creative fields** (Landing Page URL, Brand
   Entity/Name/Logo IDs, Creative Headline, Creative ASINs, Video Media IDs, Ad
   Format/Creative Type). These require Archive + recreate of the whole campaign (SB
   legacy) or the specific Ad (SB v4). The generator should refuse/error rather than
   silently emit an ineffective Update row.

8. **QA must reject simultaneous parent+child Archive in one file.** Extend the existing
   `--validate` gates to flag any upload where a Campaign/Ad Group is marked `archive`
   while one of its own children (Ad Group/Keyword/Product Ad/Target) is *also* explicitly
   marked `archive` in the same file; archive only the top-most entity.

9. **End Date blank-on-update needs a live-test confirmation before relying on it.** The
   docs indicate blank End Date clears/removes an existing end date (letting the campaign
   run indefinitely), which is an exception to the general "blank = unchanged" rule for
   Update rows, but this should be verified with a real test upload before the generator
   depends on it, since the retrieved pages didn't give one unambiguous statement covering
   both create-time and update-time blank-End-Date behavior side by side.

10. **Duplicate/collision validation should be extended**, based on the real error catalog:
    reject duplicate temp IDs reused across Create rows for the same entity type; reject
    duplicate Keyword Text + Match Type within the same ad group; warn on Campaign/Ad
    Group names that collide with a likely-existing active entity of the same name.

11. **Per-channel sheet names/columns are separate config**, not a flag on SP. If SB or SD
    writers are added, they need their own `SHEET_NAMES` entries ("Sponsored Brands
    Campaigns", "Sponsored Display Campaigns") and their own `COLUMNS` lists; do not try
    to reuse `SP_COLUMNS` with conditional fields.

12. **Do not reuse SP's enum-mapping tables for RAS or SD.** RAS's keyword match type is
    upper-case (`BROAD`/`PHRASE`/`EXACT`) versus SP's lowercase, and its placement string
    differs (`PLACEMENT TOP`). Any future RAS/SD writer needs its own
    `AMAZON_MATCH`-equivalent table, not a shared one with SP.

13. **Two source pages were never retrieved** (`create-sd-campaign`,
    `bulksheets-search-term-report`) and two more were only partially recovered
    (`create-sb-multi-ad-group-campaigns`, `update-sb-multi-ad-group-campaigns`). Before
    building an SD writer or an SB-v4 writer, re-scrape these pages or verify the exact
    row order and required fields against a live bulksheets template download; this
    reference's SD/SB-v4 create/update sections are lower-confidence than the SP and SB
    (legacy) sections.

---

## Scrape coverage summary

**Fully captured (23):** overview-about-bulksheets, get-started-with-bulksheets-part1,
get-started-with-sp-bulksheets, get-started-with-sb-bulksheets, sb-multi-ad-groups-overview,
get-started-with-sd-bulksheets, get-started-with-ras-bulksheets, input-guidance,
bulksheets-language-guide, bulksheets-keyword-translations-guide, bulksheets-portfolios,
understand-bulksheets-data, migration-guide, sp-entities, sb-entities,
sb-multi-ad-group-entities, sd-entities, editable-non-editable-bulksheets-fields,
create-sb-campaign, campaign-update-overview, update-sp-campaigns, update-sb-campaigns,
update-sd-campaigns.

**Partially captured (5, structure/key facts only, not full verbatim tables):**
create-sp-campaign, examples-sb-multi-ad-group-campaigns,
update-sb-multi-ad-group-campaigns, create-sb-multi-ad-group-campaigns,
bulksheets-error-reports.

**Failed / never retrieved (2):** create-sd-campaign, bulksheets-search-term-report
(Firecrawl returned "all scraping engines failed" and rate-limit errors on every retry).

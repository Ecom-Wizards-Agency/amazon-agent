# SoldScope adapters

SoldScope is the keyword, competitor and rank source for the keyword workbook, the audit, SUPA, the ads monitor and the monthly report. The agent calls the `soldscope` MCP, saves every raw response in the run folder, and runs one of the two adapters here. The adapters read saved files only; they never call SoldScope.

- `tools/soldscope/keywords.py` turns saved keyword research pages into the builder CSVs and `research.json`.
- `tools/soldscope/ranks.py` turns saved rank-tracker responses into the rank series and the weekly rows for the ads monitor.

Both write the shapes the tools already read from DataDive, so a consumer only changes the input path. Relevancy is always 0-1 in what they write. Old DataDive files stay readable in the consumers.

## Credit and approval rule

Before any SoldScope call that spends credits or starts server-side work, state the ASINs, the marketplace and the expected credits, and get one approval for the run. That covers `keyword_research_search_multi_asin` (one credit per ASIN), `kr_asin_search`, `keyword_research_search_by_keyword`, `product_research_search_products`, `product_live_info_start`, `title_check_data`, `common_search_volume_batch`, `index_checker_start`, `review_analyzer_get`, `buy_box_map_start_search`, `influencer_radar_search_influencers`, `rank_tracker_get_suggested_keywords` and `rank_tracker_init_export`.

Rank-tracker writes (`rank_tracker_create_group`, `rank_tracker_attach_products`, `rank_tracker_apply_suggested_phrases`, `rank_tracker_toggle_phrases_boost`) and `index_checker_delete` need approval of that exact action.

Poll `keyword_research_get_search_progress` at most every 5 seconds (the route allows 30 requests per minute). Save raw result pages and log credits in `credits-log.tsv` in the run folder, one row per paid call:

```
timestamp	tool	marketplace	asins	search_id	credits	approved_by	note
```

Free reads (no credits): `auth_check`, `kr_get_results`, `keyword_research_get_search_progress`, `keyword_research_get_multi_results`, `keyword_research_get_multi_word_frequency`, `keyword_research_get_asin_word_frequency`, all `rank_tracker_*` list, get and heatmap reads, `index_checker_history`, `sales_and_traffic_status`, `product_research_get_categories_tree`, `buy_box_map_list_searches`, `buy_box_map_get_search`, `product_live_info_get`.

No tool returns the credit balance. Check it in the SoldScope web app when it matters.

## Keyword research procedure

A run is identified by marketplace, ASIN list (anchor first when there is one) and `search_id`. SoldScope keeps no persistent niche, so the run folder is the record.

1. Pick the ASIN set: the anchor first when the product is live, plus up to 9 competitors (from POE top clicked products, the top 10 of `keyword_research_search_by_keyword` for the hero keyword, or the operator's list). A prelaunch run has no anchor; set `ranking_context.mode: unavailable` in the workbook config.
2. Marketplace US, CA, MX, UK, DE, ES, FR or IT: one `keyword_research_search_multi_asin` with 2 to 10 ASINs. Other marketplaces: one `kr_asin_search` per ASIN, merged by the adapter with `--asin-pages`. Those results have no native relevancy, so the adapter computes it.
3. State the credits and get the run approval (rule above).
4. Poll progress (`searchStatus` 2 = done, 13 = failed), then page `keyword_research_get_multi_results` with `per_page` 1000 until every `meta.total` row is read. Save each page unchanged as `multi-<search_id>-page-NNN.json`. For `kr_get_results` pages use `kr-<asin>-<search_id>-page-NNN.json`.
5. Optional: `product_live_info_get` responses for competitors the pages do not summarize.
6. Run `keywords.py` and check `keywords-receipt.json` before building.

```
python3 tools/soldscope/keywords.py --pages PAGE.json [PAGE.json ...] --out-dir DIR
  [--anchor ASIN] [--asins ASIN,ASIN,...] [--marketplace US] [--search-id ID]
  [--date-from YYYY-MM-DD --date-to YYYY-MM-DD] [--live-info LIVE.json ...]
  [--asin-pages ASIN=PAGE.json[,PAGE.json] ...]   # single-ASIN kr_get_results merge mode
  [--relevancy auto|native|computed] [--core-min 0.30] [--pool-min 0.01]
  [--top-n 50] [--pool-min-top-asins 1] [--allow-one-word kw,kw] [--ngram-max 3] [--ngram-min-freq 3]
```

Examples:

```
# multi-ASIN run, live product
python3 tools/soldscope/keywords.py --pages run/soldscope/multi-70001-page-*.json \
  --anchor B0TEST0001 --marketplace US --search-id 70001 --out-dir run/soldscope/csv

# prelaunch run with live info for gaps
python3 tools/soldscope/keywords.py --pages run/soldscope/multi-70001-page-*.json \
  --live-info run/soldscope/live-info-*.json --marketplace US --search-id 70001 --out-dir run/soldscope/csv

# a marketplace outside the 8: one kr_asin_search per ASIN
python3 tools/soldscope/keywords.py --marketplace NL --search-id 70001,70002 \
  --asin-pages B0TEST0001=run/kr-B0TEST0001-70001-page-001.json B0TEST0002=run/kr-B0TEST0002-70002-page-001.json \
  --anchor B0TEST0001 --out-dir run/soldscope/csv
```

`--pages` and `--asin-pages` are exclusive. The ASIN order is `--asins`, else the pages' `productDetails` order, else the order of first appearance; `--anchor` always moves first.

### What keywords.py does

- Cleans each keyword: HTML entities, U+FFFC and zero-width characters, edge quotes, URL-style `+` joins (`giant+widget+seeds`, `brand +widget +spray`), case and spaces. A free-standing `+` (`cleaner + polish`) stays. Rows with `|` are product-title fragments and are dropped. Duplicates after cleaning merge into the higher-SV row.
- Relevancy, 0-1:
  - `native`: SoldScope's multi-ASIN `relevancy` (0-100, rank-weighted) divided by 100.
  - `computed`: share of the compared ASINs ranking organically in the top `--top-n` (50). This matched DataDive's Relev. on most rows.
  - `auto` (default): native while it tracks computed (Core-membership Jaccard >= 0.9 and Pearson r >= 0.9 on non-zero rows), else computed. Merge mode has no native score and always computes.
- Pool (`expanded.csv`): relevancy >= `--pool-min` and at least `--pool-min-top-asins` compared ASIN at organic rank <= `--top-n`. SoldScope also scores ranks down to about 300, which let unrelated traffic into the pool.
- Core (`core.csv`): pool rows with relevancy >= `--core-min` and more than one word, unless listed in `--allow-one-word`. Rows without search volume stay out of both.
- Roots (`roots.csv`): 1 to `--ngram-max` word n-grams over the Core, plurals folded only when the singular also occurs, stop words trimmed at the edges, multi-word roots kept at `--ngram-min-freq` Core keywords or more. Broad SV is the summed SV of the Core keywords containing the root; the 5th column is Broad SV over the top root's.
- Ranks: 1-100 as given, above 100 written as 101, not ranked left blank (CSV) or null (JSON).
- Competitors: `productsSummary` and `productDetails` from the pages first; `--live-info` fills only fields the summary lacks (an ASIN missing from the summary takes its row from live info). `category` is the summary category name. `sellerCountry` is blank. `fulfillmentType` 1 is written `AMZ` (seen as an Amazon.com buy box), 2 `FBA`, 3 `FBM`; live info alone writes `AMZ` or `FBA/FBM`.
- `advertisedKws`: Core keywords where the ASIN has a sponsored rank. `kwRankedOnP1Percent`: share (0-1) of Core keywords where the ASIN ranks organically at 48 or better. On saved DataDive niches, `kwRankedOnP1` matched the count at rank <= 48, so these mean what the audit's "Adv. kws" and "% kw on P1" columns showed before.
- Reconciliation: rows read must equal `meta.total` (per ASIN in merge mode) and unique + dropped + merged must equal rows read. A raw keyword that appears twice in one search means the pages overlapped and exits 2. An `--anchor` that is not one of the searched ASINs exits 2. A repeated page, a missing page or a lost row exits 2 and writes only `keywords-receipt.json` with `ok: false`. A `--marketplace` that differs from the pages also exits 2.

### Outputs

- `roots.csv`: `"","Normalized Root","Frequency","Broad Search Volume",""`
- `core.csv`, `expanded.csv`: `"","Search Terms","SV","Relev.","Sugg. bid & range",<ASIN columns, anchor first>`. The bid column is `cpc (min-max)` when SoldScope has one.
- `competitors.csv`: `asin,brand,seller country,variations,rating,review count,price,30d sales,30d revenue,fulfillment,category`
- `research.json`:

```
{"provider":"soldscope","source":"keyword_research_search_multi_asin"|"kr_asin_search",
 "search_id":ID|[IDs],"marketplace":"US","asins":[...],"anchor":ASIN|null,
 "date_from":..,"date_to":..,"created_at":ISO8601,
 "statistics":{"numKeywords":<pool rows>,"rawRows":..,"uniqueRows":..,"poolRows":..,"coreRows":..,
               "rankDates":{"organicMin":"YYYY-MM-DD"|null,"organicMax":"YYYY-MM-DD"|null}},
 "thresholds":{"topN":50,"p1RankMax":48,"rankCap":101,"poolMin":0.01,"coreMin":0.3},
 "relevancyChoice":"native"|"computed",
 "keywords":[{"keyword":..,"searchVolume":int|null,"relevancy":0-1,
              "asinRanks":{ASIN:int|null},"sponsoredAsinRanks":{ASIN:int|null},"origin":"core"|"pool",
              "cpc":float|null,"cpcMin":float|null,"cpcMax":float|null}],
 "competitors":[{"asin","brand","title","price","rating","reviewCount","reviews","revenue","sales",
                 "sellerCountry":"","category":"<name string>","variations","fulfillment",
                 "advertisedKws":int,"kwRankedOnP1Percent":float,"isAnchor":bool,
                 "listingAgeDays":int|null,"listingAgeApprox":bool}],
 "benchmark":{"price":median,"reviewCount":median,"rating":median,"basis":"median of N compared ASINs"}}
```

`keywords` holds the pool; Core rows carry `origin: "core"`. The benchmark is the median of the compared ASINs (at most 10), not a category median. `listingAgeDays` is SoldScope's `listingAge.days`; when that is missing it is computed from years, months and days and `listingAgeApprox` is true. `rankDates` spans the `organicScrapeEventDate` values of the rows read.

- `keywords-receipt.json`: `ok`, `raw_rows`, `meta_total`, `unique`, `dropped`, `merged` (merge mode adds `merged_within_asin`, `joined_across_asins`, `per_asin`), Core and pool counts and SV, roots and competitor counts, the relevancy choice with its agreement figures, thresholds, noise-filter removals, warnings, the dropped and merged keyword lists, and every input file with its sha256.

## Keyword matrix

`tools/soldscope/matrix.py` turns a research.json from `keywords.py` into one self-contained, sortable page, `matrix.html`, in DataDive's competitor-by-keyword layout, plus `matrix-receipt.json`. It reads saved files only and never calls SoldScope. The procedure, the publish approval and storage live in the `keyword-matrix` mode of `amazon-seo` (`skills/amazon-seo/references/keyword-matrix.md`).

```
python3 tools/soldscope/matrix.py --research DIR/research.json --out-dir DIR
  [--roots DIR/roots.csv] [--title "Widget Keyword Matrix"] [--views roots,outliers]
  [--min-relev-pct 30] [--outlier-min-sv 2000] [--max-bytes 250000]
```

- It exits 2 on a research.json without `thresholds`. Older runs only need `keywords.py` again on their saved pages, which costs nothing.
- `--views roots,outliers` adds the Roots tab (from `roots.csv` next to research.json unless `--roots` says otherwise) and the Outliers tab. The default is the matrix alone.

### Metrics

Every figure is computed in Python over the full row set before any trimming. The page only sorts, filters and draws. Below, n is the number of compared ASINs and h is how many of them rank organically at `thresholds.topN` (50) or better; comparisons are done in integers.

| Item | Rule |
|---|---|
| Matrix rows | pool rows with `100*h >= 30*n` (the `--min-relev-pct`) and SV above 0, one-word terms included; DataDive's MKL default |
| Relev. | h/n as a whole percentage, recomputed per row, because research.json may hold SoldScope's native rank-weighted score; its filter uses the same scale (`>=60`) |
| Launch Score | `(6*SV*n + 1000*h) // (2000*h)` when `10*h >= 4*n`, else blank; DataDive's round(SV / relevancy x 0.003), half-up |
| Sugg. bid & range | `cpc (cpcMin-cpcMax)`, sorted on cpc |
| Rank cell | organic rank (Sponsored toggle: sponsored rank); blank when not ranked, muted ">100" for 101. Heatmap tint in DataDive's bands: 1-5 red (bold), 6-21 orange, 22-40 yellow, 41+ green |
| KWs on P1 | matrix rows at organic rank 48 or better (`p1RankMax`), count and share |
| SV on P1 | SV of those rows over the SV of all matrix rows: the Share of Voice |
| Strength | Share of Voice 80% or more Very Strong, 60% Strong, 40% Weak, 20% Very Weak, below that no label |
| Advertised KWs | matrix rows with any sponsored rank for the ASIN, count and share |
| Outliers | pool rows with SV of at least `--outlier-min-sv` (2,000) and `100*h <= 30*n`. 30d Outlier SV per ASIN sums those where it ranks in the top 50. Rows also in the matrix carry an "in matrix" tag |
| Listing Age | `listingAgeDays`, marked "approx." when computed |
| Niche Median | median of the compared ASINs with a value; unique counts for brand and ASIN, the fulfillment types, category counts, Strength chips. 30d sales and revenue show a range between the median and the average of the 2nd to 4th highest |
| Totals line | count and SV of the rows a filter leaves visible; the only figure that follows filters |

The anchor sits first with a "Your product" tag; the others follow by 30d sales, highest first. A listing that SoldScope reports with rating 0 and no reviews shows a blank rating.

### Page and size

- **What the page uses:** plain HTML, CSS and JavaScript. The only external request is the IBM Plex font stylesheet from Google Fonts, which both page hosts allow; offline the page falls back to system fonts. The data is embedded as gzip+base64 JSON and unpacked with `DecompressionStream` (Chrome 80+, Safari 16.4+, Firefox 113+). Browsers without it show a message.
- **Size cap:** `--max-bytes` (default 250,000) keeps the file under the 256 KiB Codex Pages limit. If the file would be larger, the lowest-SV rows are dropped, the page shows a banner, and the receipt names every dropped keyword. `--max-bytes 0` removes the cap.
- **Sizes on real runs:** a 10-ASIN run (2,392 terms, 518 outliers, 1,745 roots) came to about 148 KB, and a 5-ASIN run (553 terms) to about 39 KB.
- **Receipt contents:** every input with its sha256, thresholds, `eligible`, `rendered` and `dropped` counts per view, `outliers_in_matrix`, and `payload_sha256`. That hash is taken over the uncompressed payload and is identical on every run of the same input.

### Not shown, and how to read it

- **Not shown:** Seller's Country (it would take a paid `product_research_search_products` call), KWs and SV with TOS ads (SoldScope has no placement field), and product images (both page hosts block Amazon's image host).
- **Advertised KWs** counts any sponsored rank SoldScope recorded for the run. On a 5-ASIN supplement run checked against a DataDive screenshot of the same ASINs, it ran well above DataDive (62% vs 30% and 54% vs 12% for two competitors). Read it as advertising presence, not as a DataDive-equivalent figure.
- **Data source differences:** organic ranks, listing ages and prices matched DataDive closely on that check. SV did not, because SoldScope estimates its own search volume (212,610 vs 256,445 for the head term), and Launch Score follows SV.
- **Sibling ranks:** many ranks come from a sibling variation (`asinsPositions[ASIN].organicAsin` differs from the ASIN), 38% on the 10-ASIN run.

## Rank procedure

The rank tracker holds tracking groups (`group_id`) with products (`product_id`) and tracked phrases.

1. `rank_tracker_list_groups` (filter by marketplace and ASIN) gives `group_id`. Check the group marketplace.
2. `rank_tracker_list_products(group_id)` gives the own `product_id`: the primary product, or the one whose ASIN matches.
3. `rank_tracker_list_phrases(group_id, product_id, heatmap=true, heatmap_date_from, heatmap_date_to, results_type=organic, per_page=100)`, every page, at most 92 days. Repeat with `results_type=sponsored` when sponsored rank is needed. Save the pages; the file name must say organic or sponsored because the response does not.
4. For one keyword's snapshots, `rank_tracker_get_ranks_history(group_id, group_phrase_id, type, product_ids, from, to)`; `group_phrase_id` is the row `id` from step 3, and `type` 1 is organic, 2 sponsored.
5. Run `ranks.py`.

```
python3 tools/soldscope/ranks.py (--organic PAGE.json ... | --sponsored PAGE.json ... | --history KEYWORD=RESP.json ...) --out OUT.json
  [--asin ASIN | --product-id N] [--marketplace US] [--date-from --date-to]
  [--weekly-rows] [--graduate-rank-max 3]
  [--history-sponsored KEYWORD=RESP.json ...] [--export EXPORT.json ...] [--export-sponsored EXPORT.json ...]
  [--include-partial-week] [--keep-before-group] [--allow-partial]
```

The inputs combine: organic and sponsored pages, or heatmap pages plus history, merge by keyword.

Examples:

```
# series for SUPA (inputs.rank_jsons) or the audit (inputs.rank_series_json)
python3 tools/soldscope/ranks.py --organic run/rank/organic-page-*.json --sponsored run/rank/sponsored-page-*.json \
  --marketplace US --out run/rank/rank-series.json

# weekly rows for the ads monitor (run_weekly.py --rank-json)
python3 tools/soldscope/ranks.py --organic run/rank/organic-page-*.json --marketplace US \
  --weekly-rows --graduate-rank-max 3 --date-to 2026-11-07 --out run/rank/rank-weekly.json

# one keyword's snapshot history
python3 tools/soldscope/ranks.py --history "widget cleaner=run/rank/history-widget-cleaner.json" \
  --product-id 501 --out run/rank/history-series.json
```

### Rank rules

- Heatmap pages: each row has one `r_YYYY-MM-DD` key per day, `{"date","rank","amazon_choice"}`; rank 0 means not ranked. The day value is SoldScope's daily value for the requested results type. Days before the group's `createdAt` are dropped (they read as not ranked only because tracking had not started); `--keep-before-group` keeps them.
- History: `data.history[product_id]` snapshots with a unix `created_at`. The day value is the upper median of that UTC day's snapshots. Without `--product-id`, `--asin` picks the product whose snapshots carry that ASIN, and a single product is used as is.
- Export (provisional): `rank_tracker_get_export` JSON rows. The JSON field names were not captured yet; the reader accepts `phrase`/`keyword`, `date`/`created_at`, `position`/`rank`, an optional `asin` and `product_id`, and takes the upper median per day. Check the output against a heatmap read before relying on it. Grimoire cannot start exports, so the heatmap and history paths are the main ones.
- Rank 0, null, missing snapshots and anything above 100 become 101, as in DataDive Rank Radar data.
- Fails (exit 2) when `--marketplace` differs from `group.marketplace`, when pages come from different groups, or when the phrases read differ from `meta.total` (pass `--allow-partial` to accept a known partial read).

### Rank outputs

Series (default), the shape DataDive Rank Radar data had:

```
[{"keyword":..,"searchVolume":int|null,"ranks":[{"date":"YYYY-MM-DD","organicRank":int,"sponsoredRank":int|null}]}]
```

`sponsoredRank` is null when no sponsored input was given. `organicRank` is null only when no organic input was given.

Weekly rows (`--weekly-rows`), read by `normalize_rank_rows` in `tools/amazon-ads-monitor/recommendations.py`:

```
[{"keyword":..,"rank_now":int,"rank_prev":int|null,"weeks_stable":int,"week_start":"YYYY-MM-DD"}]
```

Weeks run Sunday to Saturday. A week's rank is the upper median of its daily organic ranks, the rule `load_rank` in `tools/sqp-supa/build_supa_workbook.py` applies to the series, so the two agree. `rank_now` is the latest complete week (its Saturday on or before `--date-to`, default the last data day; `--include-partial-week` allows a running week). `rank_prev` is the week before, null when it has no data. `weeks_stable` counts consecutive weeks, ending at the latest, at or under `--graduate-rank-max`; the ads monitor graduates a keyword at `graduate_weeks_stable` (2). A keyword with no data in the latest week gets no row.

## Marketplace coverage

- Multi-ASIN research (`keyword_research_search_multi_asin`): 8 marketplaces, US, CA, MX, UK, DE, ES, FR, IT.
- Single-ASIN research (`kr_asin_search`): 17, US, CA, MX, BR, DE, ES, FR, IT, UK, NL, SE, IN, AE, TR, SA, AU, JP.
- Rank tracker: 16, the same list without JP.

## Known gaps

- No persistent niche. The run folder (pages, receipt, `credits-log.tsv`) is the record; re-running a search costs credits again.
- No seller country. `sellerCountry` and the `seller country` column stay blank.
- No Ranking Juice. Use the keyword ranking score from `tools/amazon-seo-keyword-workbook/ranking_score.py`; client-visible text never says "Ranking Juice".
- No credit balance through the MCP.
- The 30d sales and revenue figures are SoldScope's `productsSummary` estimates; SoldScope does not document their window.
- Rank history for the 43 former DataDive Rank Radars starts on 21.10.2026, when they were copied to SoldScope rank-tracker groups (mapping in the team vault run note for that copy). Earlier weeks need the old DataDive data.
- The single-ASIN `kr_get_results` row shape was not captured yet. Merge mode reads `asinsPositions[ASIN]`, else top-level `organicRank`/`sponsoredRank`, else `mainOrganicRank`/`mainSponsoredRank`. Check the first real merge run's receipt.
- The SoldScope account has no connected Amazon seller account yet, which blocks SQP export, sales and traffic, and the review analyzer.

## Tests

```
python3 -m unittest discover -s tools/soldscope/test -v
```

Fixtures under `tools/soldscope/test/fixtures/` are synthetic (`B0TEST000N` ASINs). The SUPA and ads-monitor agreement tests skip when the interpreter lacks `openpyxl`; run them with the repo venv.

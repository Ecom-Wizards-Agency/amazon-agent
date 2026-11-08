# Keyword matrix

One sortable competitor-by-keyword HTML page from a SoldScope keyword research run, in the layout the team knew from DataDive: competitor facts on top, one color-coded organic rank column per competitor below, plus KWs and SV on page 1, Strength, outliers and Launch Score. The page is built locally and published as a private page in the operator's own account.

## Inputs

- A saved run folder with `multi-<search_id>-page-NNN.json` pages, or a finished SoldScope `search_id`. Read an existing search with `keyword_research_get_multi_results` (`per_page` 1000, every page until `meta.total` rows are read); that read is free.
- No saved run: one `keyword_research_search_multi_asin` for 2 to 10 ASINs, anchor first. Outside US, CA, MX, UK, DE, ES, FR and IT, the README's single-ASIN route instead runs one `kr_asin_search` per ASIN and merges them with `--asin-pages`; the matrix step is the same.
- Either route spends credits. Before any search, state the ASINs, the marketplace and the expected credits, then stop until the operator approves the run. Log each paid call in `credits-log.tsv` in the run folder (`tools/soldscope/README.md`).
- Client, niche and marketplace, for the folder and the page title.

## Build

Save the pages unchanged into `output/{client}/seo/<YYYY-MM-DD>-soldscope/<niche>/`, then run:

```bash
python3 tools/soldscope/keywords.py --pages <run>/multi-<id>-page-*.json --marketplace <MKT> \
  --search-id <id> [--anchor ASIN] [--date-from YYYY-MM-DD --date-to YYYY-MM-DD] --out-dir <run>/matrix
python3 tools/soldscope/matrix.py --research <run>/matrix/research.json --out-dir <run>/matrix \
  --title "<Niche> Keyword Matrix" [--views roots,outliers]
```

- `--views roots,outliers` adds the Roots and Outliers tabs. Leave it off unless the operator asks for roots or outliers.
- A research.json written before this mode has no `thresholds`, and matrix.py refuses it. Re-run keywords.py on the saved pages; it spends nothing.
- Keep the default `--max-bytes 250000` so one file works on every host.
- An agent that cannot run the repo's scripts stops here and says the page needs a Codex or Claude Code session; it can still answer rank questions in text from the free read.

## Check

Read `<run>/matrix/matrix-receipt.json` before publishing:

- `ok` is true.
- Each view satisfies `rendered + dropped = eligible`.
- `html_bytes` is under `max_bytes`.

If rows were dropped to fit, tell the operator how many. The page shows the top terms by search volume, and the receipt names every dropped keyword.

## Publish

Ask once for each publish: "Publish `<run>/matrix/matrix.html` (N KB, X keywords x Y competitors, client, niche) as a private page in my account? Sharing it stays a separate decision." Stop until the operator approves. Never share the page or make it public unless the operator asks for that separately. If the runtime cannot publish pages, give the local path; the file opens in any current browser.

**Claude Code.** Publish `matrix.html` with the Artifact tool (private by default, icon `table`). Republish the same file path to update the same link.

**Codex.** Create the page with `chatgpt_space_create_page` (title = the matrix title), then send the file's full text as `html` to `chatgpt_space_create_page_visualization`. Update it later with `replace_block`. The default byte cap keeps the file under the 256 KiB Pages limit.

## Store

The page is internal and never goes into `<Client> - Shared/`. Register every new file by exact path with `tools/artifactctl/artifactctl`:

1. `run start --owner amazon-seo --client <client> --workflow seo` gives the run id.
2. `register --run <id> --path <file> --disposition preserve` for each saved `multi-*.json` page, because a new search costs credits.
3. The same with `--disposition reproducible` for everything in `<run>/matrix/`: the keywords.py outputs, `matrix.html` and `matrix-receipt.json`. The saved pages rebuild them.
4. `run complete --run <id> --outcome success`, or the real outcome.

Column definitions, metric rules and what the page leaves out: the Keyword matrix section of `tools/soldscope/README.md`.

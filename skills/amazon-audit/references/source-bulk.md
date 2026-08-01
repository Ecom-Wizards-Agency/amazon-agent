# Data source: downloaded files (prospects)

Loaded at step 2 when the brand has no AdLabs profile. Every Lens A row must still be filled
from here. "Not available on this path" is only an acceptable answer for margin.


Scaffold a config, preflight, hand the browser downloads to Codex, pull DataDive yourself.

1. Copy `tools/amazon-ad-audit/config.TEMPLATE.json` to `config.<client>-<market>.json`
   (gitignored). Fill client, marketplaces, product lines and ASINs, break-even ACOS, brand and
   competitor tokens, `core_tokens`, `asin_groups`, windows. Never reuse another client's values.
2. `python3 tools/amazon-ad-audit/build_audit.py --config <cfg> --preflight` prints per-input
   OK or MISSING, then either READY or a copy-ready Codex download task.
3. Codex gathers the browser downloads to the exact contract paths, notes evidence and caveats,
   and stops. It does not run the builder and does not write the narrative.
4. Pull the DataDive niche and competitors over MCP to the config paths, then re-run
   `--preflight` until READY.

| Input | Config key | Gatherer |
|---|---|---|
| Ads bulk `.xlsx` (SP required; SB, SB-Multi, SD, RAS if running) | `ads_bulk_xlsx` | Codex |
| Business Report `.csv` (Detail Page Sales and Traffic by Child ASIN) | `business_report_csv` | Codex, or `tools/report-fetcher/` |
| Multi-ASIN SQP `.csv`, one per product group, weekly | `sqp_csvs` | Codex, or `tools/report-fetcher/` |
| DataDive niche keywords + competitors JSON | `datadive_niche_json`, `datadive_competitors_json` | This skill, over MCP |
| Rank Radar payload (optional, drives the rank chart) | `rank_radar_json` | This skill, over MCP |

Recommended extras: the SB campaign placement report (the bulk's SB placement rows are
incomplete, only Detail Page populated in practice) and the SP Search-Term Impression-Share
report (top-of-search headroom, and the only real paid share-of-voice number). Not needed:
SB and SD search-term reports.

**Fix the window BEFORE the ads bulk is exported.** The bulk carries no date dimension:
`Start Date` and `End Date` are campaign scheduling fields, and performance is aggregated over
whatever range was requested. A window cannot be sliced afterwards, so a clean-weeks-only cut
needs a second export. Default to 4 complete SQP weeks, Sunday to Saturday, about 28 days, so
ads, BR and SQP line up. `--weeks` takes the period-END date, the Saturday; a Sunday returns
HTTP 400.

Raw exports stage under gitignored `downloads/{client}/` and stay there. Clear the same files
from the browser's `~/Downloads` afterwards. Only deliverables reach the client's Drive folder,
never raw source files.

---

## Mechanics learned the hard way

**Download path.** Reading Amazon bulk `.xlsx` needs streaming: `openpyxl` with `read_only=True` and
bounded `iter_rows`. A real account hit about 288k rows on the SP Campaigns sheet alone, roughly
355 MB decompressed. Amazon writes a bogus `A1:A1` sheet `<dimension>` and openpyxl 3.1.5 clips the
read to it on **both** axes; `reset_dimensions=True` does not override it. The fix is explicit bounds
on both axes: read the header with a generous `max_col`, trim trailing empties to the true width, then
stream from `min_row=2` with a large `max_row` at that width. Never open the bulk with
`read_only=False`: per-cell access over 288k rows ran about 40 minutes at multi-GB RSS. If a build
hangs for minutes on a large account, this is why.

## Data-completeness gate

On the download path, `--validate` must pass three hard gates (spend reconciliation, no ACOS ratio
above 1.0 carrying a green fill, master tab count) and also prints soft WARNINGS plus a DATA
COMPLETENESS panel: low intent coverage, SQP revenue gap, missing channels, multi-parent ad groups.
These are not bugs, they are thin data. **Resolve or disclose every one before delivery.**

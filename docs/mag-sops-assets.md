# MAG SOP Visual Archive

The GitHub/runtime project keeps the MAG SOP markdown searchable and lightweight. The full visual SOP archive is stored outside GitHub because it contains thousands of screenshots and GIFs.

## Canonical Visual Archive

- The operator's current local placeholder path: `<your-pcloud>/Amazon Agent/MAG SOPs`
- Expected contents: 535 Markdown files and 3,621 assets in `assets/`
- Expected missing local image references: 0

The pCloud archive stays complete. The runtime `MAG SOPs/` tree in this repo is curated for Amazon work (2026-07-08): the AI ChatGPT-prompt and Product Development categories and two Business Analysis SOPs were removed, and the Walmart SOPs sit under `MAG SOPs/_archive/` (excluded from the index and the search helper). Regenerate the slim index and README with `python3 tools/slim_sop_index.py --readme`.

This path is user-specific. Each team member should download or sync the shared pCloud visual archive locally and point their setup to their own path.

## Usage Rule

Search local/GitHub markdown SOPs first. When visual confirmation, screenshots, GIFs, or layout references are needed, use the pCloud visual archive path.

## Do Not Commit

Do not commit `.final-build`, image assets, zip files, generated evidence, downloads, review tracking, or client work output to GitHub. Keep those in pCloud or ignored local-only artifact folders.

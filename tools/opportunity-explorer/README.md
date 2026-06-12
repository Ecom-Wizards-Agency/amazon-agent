# Opportunity Explorer Extraction Workflow

This folder replaces the old Chrome-extension-first approach with an AI-friendly extraction workflow.

Default model: script-first. Codex should run the browser-side extractor in the already logged-in connected browser Seller Central page, then save JSON and Markdown. The user should not need to install, open, or click a browser extension.

## Files

- `extract-opportunity-explorer.js`: browser-side scraper for the currently open Product Opportunity Explorer page.
- `format-opportunity-explorer-export.mjs`: local formatter that saves a raw JSON copy and a Markdown copy.

## Workflow

1. Open the target Amazon Seller Central Product Opportunity Explorer page in the connected browser.
2. Verify account, marketplace, and niche/page title.
3. Run `extract-opportunity-explorer.js` in the page context using the available browser automation tool.
4. Save the returned object as a temporary `.json` file.
5. Format it:

```bash
node tools/opportunity-explorer/format-opportunity-explorer-export.mjs /path/to/export.json output/{client-or-brand}/opportunity-data
```

6. Use the Markdown/JSON export with `amazon-opportunity-explorer`, `amazon-image-strategy`, `oei-product-strategy`, `amazon-seo`, and Rufus/Alexa AI strategy workflows.

## Historical Reference

The old pCloud Chrome extension can be used as source reference during transition, but it is not part of the intended workflow once this script is tested. This is The operator's current local placeholder path, not a repo dependency:

`/Users/<your-username>/pCloud Drive/Account shares/Amazon Wizards/2_Company/2.7_Tools/Chrome Extension-Opportunity Explorer Downloader`

## Safety

The extractor only reads visible page DOM text/tables and page URL/title. It must not inspect cookies, local storage, session storage, bearer tokens, credentials, payment details, tax IDs, or private account settings.

Stop before changing listings, uploading images, editing A+ content, changing catalog data, or publishing recommendations externally.

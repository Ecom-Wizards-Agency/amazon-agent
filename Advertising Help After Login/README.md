# Advertising Help After Login

Downloaded/updated: 2026-05-13; 120 articles re-captured verbatim and 114 linked pages added on 2026-10-06 with `tools/knowledge/help_capture.mjs` (15 dead linked URLs recorded in `_index/advertising-help-missing.json`)

Amazon Ads Support Center library for the Amazon SOP master project.

> These are local snapshots of Amazon's own Help content, kept for internal reference and search routing — not for redistribution. Account-specific UI chrome from the original capture has been replaced with a neutral `Example Brand` placeholder.

## Coverage

- Source: https://advertising.amazon.com/help
- Firecrawl discovery: capped crawl found 300 help pages
- Chrome snapshot links indexed: 109
- Content files captured: 123
- Status: 109 Chrome-indexed Support Center pages complete; linked expansion complete on 2026-10-06.
- Linked expansion: 14 linked pages captured in May 2026, 114 more on 2026-10-06; 15 linked URLs no longer resolve to an article (listed in `_index/advertising-help-missing.json`).

## Files

- Articles: `articles/`
- Index: `_index/advertising-help-index.json`
- Chrome homepage/category snapshots: `_index/*.txt`
- Linked expansion checkpoint: `_index/linked-expansion/`

## Operator Navigation Notes

Some captured Chrome snapshots list Creator Connections as ~~`https://advertising.amazon.com/choose-account?destination=/bi`~~ or a `/choose-account?destination=/bi?entityId=...` link. Keep those source captures intact, but do not use that as the operational starting route: it can show only a partial account list.

Correct Creator Connections route: open `https://advertising.amazon.com/campaign-manager`, choose the right account from the top-right account selector, then use the left navigation `Brand content` > `Creator connections`.

## Safety Note

Capture was completed without process inspection, process killing, or Chrome/Node reset commands. Firecrawl was used for page content and local writes were limited to this folder.

Sensitive billing/payment details were summarized. Private payment identifiers, credentials, tokens, and secret values are not stored in this library.

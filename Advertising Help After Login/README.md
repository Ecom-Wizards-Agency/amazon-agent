# Advertising Help After Login

Downloaded/updated: 2026-05-13

Amazon Ads Support Center library for the Amazon SOP master project.

## Coverage

- Source: https://advertising.amazon.com/help
- Firecrawl discovery: capped crawl found 300 help pages
- Chrome snapshot links indexed: 109
- Content files captured: 123
- Status: 109 Chrome-indexed Support Center pages complete; linked expansion in progress.
- Linked expansion: 14 additional linked pages captured, 127 linked pages remaining.

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

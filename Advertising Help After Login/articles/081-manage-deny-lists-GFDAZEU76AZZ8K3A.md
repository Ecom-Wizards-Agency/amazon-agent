---
title: "Manage deny lists"
source_url: "https://advertising.amazon.com/help/GFDAZEU76AZZ8K3A"
library: "Amazon Ads Support Center"
section: "account-management"
downloaded_at: "2026-05-13"
status: "captured"
---

# Manage Deny Lists

Deny lists restrict where ads can appear on Amazon-supported inventory.

## Key Points

- Deny lists can limit ad delivery on specific domains, apps, and creator tags.
- The feature is listed as available to advertisers in the US.
- Deny lists can block entire websites, but not individual web pages.

## File Format

| Value | Type |
| --- | --- |
| `www.example.com` | `WEBSITE` |
| `com.example.app` | `APP` |
| Creator tag ID | `CREATOR` |

Supported upload formats include CSV, XLSX, and TSV.

## Workflow

1. Create a file with the URL, app, or creator tag ID in column one.
2. Add the type in column two: `WEBSITE`, `APP`, or `CREATOR`.
3. In the left menu, go to **Administration**.
4. Open **Account access and settings**.
5. Open **Deny list**.
6. Click **Upload deny list**.
7. Check **Last action** for upload status.
8. Download the result report after completion.
9. To clear the deny list, use the menu next to **Upload deny list** and confirm.

## Visual Reference

![Administration icon](https://d369o5h5zn8mv7.cloudfront.net/images/Icons/Administration.png)

## Checkpoints

- Stop before uploading or clearing a deny list.
- If the deny list exceeds 10,000 entries, split it into multiple files.
- Download the existing deny list before clearing it because clearing is irreversible.

## Routing Use

Use this page when the user asks to block ad placements, exclude websites/apps/creators, or audit brand safety placement restrictions.

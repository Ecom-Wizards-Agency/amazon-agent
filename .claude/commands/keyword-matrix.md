---
description: Build a sortable DataDive-style competitor x keyword matrix page from a SoldScope run (local HTML, private publish after approval)
argument-hint: "[client niche + search_id or ASINs + marketplace] (e.g. 'acme widgets 12345 US')"
---

# Keyword Matrix

Load the `amazon-seo` skill and follow its `keyword-matrix` mode (`skills/amazon-seo/references/keyword-matrix.md`). Do not duplicate logic here.

The user's target is: **$ARGUMENTS**

Ask only for what `$ARGUMENTS` and the conversation do not give: client, niche, marketplace, and a saved run folder, a finished SoldScope `search_id`, or the ASIN set. A new SoldScope search needs the run approval named in the mode, and publishing the page needs its own approval.

---
title: "Understand keyword match types"
source_url: "https://advertising.amazon.com/help/GHTRFDZRJPW6764R"
library: "Amazon Ads Support Center"
downloaded_at: "2026-05-12"
updated_on: "2026-03-09"
status: "captured"
---

# Understand keyword match types

Keyword match types fine-tune which shopping queries ads are eligible to show against.

For each keyword added, choose a match type. In Sponsored Products automatic targeting campaigns, targeting groups are used instead of match types for a similar purpose.

> Note: After campaign creation, initial match types cannot be changed. Keywords with different match types can be added while the campaign is running.

## Manual targeting match types

Manual targeting campaigns have three match-type options. They account for plurals, misspellings, and translations.

If multiple match types with different bids exist for the same keyword, the match type with the highest bid is used for any matching shopping query.

| Match type | Description | Example |
| --- | --- | --- |
| Broad match | Broad exposure. Query can contain keyword terms in any order and may include singulars, plurals, variations, synonyms, and related terms based on keyword meaning and advertised product context. Keyword itself may not appear in the query. | "sneakers" may match "canvas sneakers", "basketball shoes", "athletic shoes", "cleats", "trainers", or "foam runners". |
| Phrase match | Ad is shown when the keyword phrase or sequence of words, or close variations, appear in shopper queries. More restrictive than broad. | "curtain rod" may match "extra long curtain rods" or "curtain rods for bedroom". |
| Exact match | Ad is shown when the keyword or sequence exactly matches shopper queries, plus close variations. Most restrictive. | "outside lights" can still match "outdoor lights". |

Sponsored Brands campaigns use general match and semantic match. Sponsored Products uses only general match.

| Match type | Customer query | General match | Semantic match |
| --- | --- | --- | --- |
| Exact | Outside curtain rod | Outside curtain rod | Outdoor curtain pole |
| Phrase | Outside curtain rod | Outside curtain rods gold | Poles of curtains |
| Broad | Outside curtain rod | Outdoor curtains | Patio curtains |

> Tip: Start with broad match to measure where ads perform best. Review keyword metrics in Campaign manager or the targeting report, then adjust bids or create a more concise keyword group.

## Broad match modifiers for Sponsored Brands

Sponsored Brands can use broad match modifiers to indicate words that must appear in customer shopping queries.

Add a plus symbol `+` before the keyword. Example: `+kids shoes` matches queries containing "kids", such as "kids sneakers" or "running shoes for kids", but not "sneakers" or "running shoes".

## Automatic targeting groups for Sponsored Products

Automatic targeting is available only for Sponsored Products. After creating an automatic campaign, targeting options can be adjusted in Campaign manager.

- **Close match:** search terms closely related to products.
- **Loose match:** search terms loosely related to products.
- **Substitutes:** product detail pages of similar products.
- **Complements:** product detail pages of complementary products.

## Negative keyword match types

- **Negative phrase:** ads do not show on shopping queries containing the complete phrase or close variations. Maximum 4 words and 80 characters.
- **Negative exact:** ads do not show on shopping queries containing the exact phrase or close variation. Maximum 10 words and 80 characters.

## Related topics

- [Understand targeting](https://advertising.amazon.com/help/G3XAU5G7C2JTNQTM)
- [Set up keyword targeting](https://advertising.amazon.com/help/GK3MNACNTXG659J9)
- [Set up product targeting](https://advertising.amazon.com/help/GB2JECV9CJK6R6AL)
- [Add negative keywords or negative products](https://advertising.amazon.com/help/GTEHPEG5BXY9UX5W)
- [Branded keyword guidelines and keyword suspension](https://advertising.amazon.com/help/G2QZJUGUT4RGLJ6N)
- [Keyword translation](https://advertising.amazon.com/help/GHPTCVTGNFZ2KTSP)
- [Reserve keywords in a Sponsored Brands campaign](https://advertising.amazon.com/help/G86SD7HK6NHHRB9B)

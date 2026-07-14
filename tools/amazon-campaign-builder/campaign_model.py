#!/usr/bin/env python3
"""
Amazon Sponsored Products campaign model — pure logic, no I/O.

Python port of the Ecom Wizards "Amazon Ads Bulk Creator" web app core
(src/types/index.ts, src/lib/naming.ts, src/lib/campaignGenerator.ts,
src/lib/bulkExport.ts in Ecom-Wizards-Agency/amazon-ads-bulk-creator),
generalized for config-driven CLI use. Row structure, naming, chunking,
and defaults are 1:1 with the app.

Deliberate vocabulary fixes vs the app — the app emits values the current
bulksheets 2.0 upload parser does not document; this port emits what
Amazon's docs and real bulk exports use (the parity harness maps the app's
vocabulary through the AMAZON_* tables below before diffing):

  sheet name    'SP Campaigns'             -> 'Sponsored Products Campaigns'
  id headers    'Campaign Id' etc.         -> 'Campaign ID' etc.
  match type    'EXACT'/'BROAD'/'PHRASE'   -> 'exact'/'broad'/'phrase'
  neg. match    'NEGATIVE_EXACT'/'_PHRASE' -> 'negativeExact'/'negativePhrase'
  bidding       'Down only'/'Up and down'/'Fixed bids'
                                           -> 'Dynamic bids - down only'/
                                              'Dynamic bids - up and down'/'Fixed bid'
  PAT expanded  'similar-product="..."'    -> 'asin-expanded="..."'
  placement     'Placement Rest of Search' -> 'Placement Rest Of Search'

v2 additions (campaign-builder v2 — create + update, keyword-file input, EW
naming, see tools/amazon-campaign-builder/README.md):
  - `campaign_purpose` + CAMPAIGN_PURPOSE_BIDDING: the naming-convention.md
    bidding-strategy table is keyed by campaign *purpose* (Rank SKW / Auto /
    Category / Self-Targeting / Shield / discovery / Halo), which cuts across
    the existing campaign_type enum (e.g. a Shield SKW campaign is still
    campaign_type=SKW but purpose=SHIELD, and gets "Down only" not "Fixed
    bids"). CAMPAIGN_TYPE_BIDDING still gives the type-level default (used
    when no purpose is specified) and now matches naming-convention.md's
    "Rank SKW = Fixed bid" row (previously all-down-only).
  - EW_NAMING_PRESET: the 8-slot Ecom Wizards campaign-name format
    (Goal | Ad Type | Match Type | Trigger Words OR Placement |
    Product Identifier | Keyword | Camp Counter | Suffix), selectable via
    naming.preset in the config. LEGACY_NAMING_PRESET keeps the original
    6-token order used by every existing config.
  - Update-mode (real-ID Update/Archive/Create rows against an existing
    account) lives in update_model.py / update_campaigns.py, which import
    the shared constants below (SP_COLUMNS, AMAZON_* maps) but never reuse
    this module's temp-ID create-row builder for update output.
"""
from __future__ import annotations

from datetime import date

# ----------------------------------------------------------------- domain constants (1:1 app)
CAMPAIGN_TYPES = ("SKW", "Halo", "BMM", "Phrase", "Auto", "PAT")
GOALS = ("Discovery", "Rank", "Profit")
MATCH_TYPES = ("EXACT", "BROAD", "PHRASE", "ASIN_EXACT", "ASIN_EXPANDED", "AUTO")
NEGATIVE_MATCH_TYPES = ("NEGATIVE_EXACT", "NEGATIVE_PHRASE")
NEGATIVE_LEVELS = ("ad_group", "campaign")
BIDDING_STRATEGIES = ("Down only", "Up and down", "Fixed bids")
STATES = ("enabled", "paused")
SITE_RESTRICTIONS = ("Amazon", "Amazon Business")

CAMPAIGN_TYPE_GOALS = {
    "SKW": ["Rank"],
    "Halo": ["Profit"],
    "BMM": ["Discovery"],
    "Phrase": ["Discovery"],
    "Auto": ["Discovery"],
    "PAT": ["Discovery", "Rank", "Profit"],
}

CAMPAIGN_TYPE_MATCH = {
    "SKW": "EXACT",
    "Halo": "EXACT",
    "BMM": "BROAD",
    "Phrase": "PHRASE",
    "Auto": "AUTO",
    "PAT": "ASIN_EXACT",
}

CAMPAIGN_TYPE_BIDDING = {
    "SKW": "Fixed bids",   # naming-convention.md: Rank SKW = Fixed bid
    "Halo": "Down only",
    "BMM": "Down only",
    "Phrase": "Down only",
    "Auto": "Up and down",
    "PAT": "Down only",
}

# ----------------------------------------------------------------- campaign purpose (naming-convention.md)
# The QC-enforced bidding-strategy table is keyed by *purpose*, which is more
# granular than campaign_type: a Shield or Self-Targeting campaign can be
# built on top of SKW/BMM/Phrase/PAT but takes a different bidding default
# than that type's usual one. Config specs may set `campaign_purpose`
# explicitly (SHIELD / SELF_TARGETING / CATEGORY); otherwise it's inferred
# from campaign_type below.
CAMPAIGN_PURPOSES = ("RANK_SKW", "HALO", "DISCOVERY", "AUTO", "CATEGORY", "SELF_TARGETING", "SHIELD")

CAMPAIGN_TYPE_DEFAULT_PURPOSE = {
    "SKW": "RANK_SKW",
    "Halo": "HALO",
    "BMM": "DISCOVERY",
    "Phrase": "DISCOVERY",
    "Auto": "AUTO",
    "PAT": "DISCOVERY",  # competitor-ASIN targeting ("BMM & Phrase & PAT ASIN" row); self
                         # PAT sets campaign_purpose="SELF_TARGETING" explicitly to get up/down.
}

# naming-convention.md: "Bidding strategy by campaign type (QC-enforced, must match Figma)".
# NOTE this replaces the old blanket down-only assumption in CAMPAIGN_TYPE_BIDDING above.
CAMPAIGN_PURPOSE_BIDDING = {
    "RANK_SKW": "Fixed bids",
    "AUTO": "Up and down",
    "CATEGORY": "Up and down",
    "SELF_TARGETING": "Up and down",
    "SHIELD": "Down only",
    "DISCOVERY": "Down only",  # Broad Match Modifier & Phrase & PAT ASIN
    "HALO": "Down only",
}

# Trigger word shown in the EW campaign name's "Trigger Words OR Placement" slot.
# "The trigger word must exactly match the campaign type" (naming-convention.md) —
# for the three purposes that aren't literal campaign_type values (Shield,
# Self-Targeting, Category) we use their own label; everything else falls back
# to the literal campaign_type (SKW/Halo/BMM/Phrase/Auto/PAT).
TRIGGER_WORD_LABELS = {
    "SHIELD": "Shield",
    "SELF_TARGETING": "Self-Targeting",
    "CATEGORY": "Category",
}

NAMING_VARIABLES = ["Goal", "SP", "AdType", "MatchType", "TriggerWord", "ProductName", "Keyword",
                    "TargetDescriptor", "EW", "Counter", "CampCounter", "CampaignType", "Date",
                    "Custom1", "Custom2"]

MATCH_TYPE_LABELS = {
    "EXACT": "Exact",
    "BROAD": "Broad",
    "PHRASE": "Phrase",
    "ASIN_EXACT": "ASINExact",
    "ASIN_EXPANDED": "ASINExpanded",
    "AUTO": "Auto",
}

CAMPAIGN_TYPE_LABELS = {t: t for t in CAMPAIGN_TYPES}

MIN_BID = 0.02
DEFAULT_BID = 0.50
DEFAULT_BUDGET = 10.00

# ----------------------------------------------------------------- Amazon bulksheet vocabulary
# Keyed by channel so SB/SD writers can slot in later without restructuring.
SHEET_NAMES = {"SP": "Sponsored Products Campaigns"}

SP_COLUMNS = [
    "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID",
    "Ad ID", "Keyword ID", "Product Targeting ID", "Campaign Name", "Ad Group Name",
    "Start Date", "End Date", "Targeting Type", "State", "Daily Budget", "SKU", "ASIN",
    "Ad Group Default Bid", "Bid", "Keyword Text", "Match Type", "Bidding Strategy",
    "Placement", "Percentage", "Product Targeting Expression", "Sites",
]
COLUMNS = {"SP": SP_COLUMNS}

AMAZON_MATCH = {"EXACT": "exact", "BROAD": "broad", "PHRASE": "phrase"}
AMAZON_NEG_MATCH = {"NEGATIVE_EXACT": "negativeExact", "NEGATIVE_PHRASE": "negativePhrase"}
AMAZON_BIDDING = {
    "Down only": "Dynamic bids - down only",
    "Up and down": "Dynamic bids - up and down",
    "Fixed bids": "Fixed bid",
}
PLACEMENT_LABELS = {
    "top_of_search_placement": "Placement Top",
    "rest_of_search_placement": "Placement Rest Of Search",
    "product_pages_placement": "Placement Product Page",
}
AUTO_EXPRESSIONS = ("close-match", "loose-match", "substitutes", "complements")


# ----------------------------------------------------------------- naming (port of naming.ts)
def _variable_value(variable, ctx, settings, today):
    if variable == "Goal":
        return ctx["goal"]
    if variable in ("SP", "AdType"):
        return "SP"
    if variable == "MatchType":
        return MATCH_TYPE_LABELS.get(ctx["match_type"], ctx["match_type"])
    if variable == "CampaignType":
        return CAMPAIGN_TYPE_LABELS.get(ctx["campaign_type"], ctx["campaign_type"])
    if variable == "TriggerWord":
        return ctx.get("trigger_word") or CAMPAIGN_TYPE_LABELS.get(ctx["campaign_type"], ctx["campaign_type"])
    if variable == "ProductName":
        return ctx.get("product_name") or "ProductName"
    if variable == "Keyword":
        return ctx.get("keyword_text") or ""
    if variable == "TargetDescriptor":
        return ctx.get("target_descriptor") or "Target"
    if variable == "EW":
        return settings.get("suffix") or "EW"
    if variable == "Counter":
        return f"{ctx['counter']:02d}" if ctx.get("counter") is not None else ""
    if variable == "CampCounter":
        # naming-convention.md: "Camp Counter ONLY used for Halo and Auto campaigns;
        # leave it off for everything else" — blank parts are dropped when the name
        # is joined, so returning "" here is how "off otherwise" is enforced.
        if ctx.get("campaign_type") in ("Halo", "Auto") and ctx.get("counter") is not None:
            return f"{ctx['counter']:02d}"
        return ""
    if variable == "Date":
        return (today or date.today()).isoformat().replace("-", "")
    if variable == "Custom1":
        return settings.get("custom1_value") or ""
    if variable == "Custom2":
        return settings.get("custom2_value") or ""
    return variable


def generate_campaign_name(settings, ctx, today=None):
    parts = [_variable_value(v, ctx, settings, today) for v in settings["variable_order"]]
    return settings["delimiter"].join(p for p in parts if p)


def generate_ad_group_name(settings, ctx, today=None):
    # "Ad group name is the shorter form — drop prefix & suffix" (naming-convention.md).
    # NOTE: "SP" is deliberately NOT dropped here — the original (legacy-preset) app
    # behavior keeps it in the ad group name and that's what the 71-row parity fixture
    # verifies. The EW preset uses "AdType" (not "SP") for the same slot, so adding
    # AdType/CampCounter to the drop set only affects the new preset, never the legacy one.
    drop = ("Goal", "EW", "Counter", "Date", "AdType", "CampCounter")
    keep = [v for v in settings["variable_order"] if v not in drop]
    parts = [_variable_value(v, ctx, settings, today) for v in keep]
    return settings["delimiter"].join(p for p in parts if p)


def swap_name_order(settings):
    order = list(settings["variable_order"])
    if "ProductName" in order and "TargetDescriptor" in order:
        p, t = order.index("ProductName"), order.index("TargetDescriptor")
        order[p], order[t] = order[t], order[p]
    return {**settings, "variable_order": order}


# ----------------------------------------------------------------- naming presets
# LEGACY is the original app order (unchanged — every existing config that sets its
# own naming.variable_order continues to work exactly as before, see build_campaigns
# .load_config). EW is the Ecom Wizards 8-slot convention from naming-convention.md:
#   Goal | Ad Type | Match Type | Trigger Words OR Placement | Product Identifier |
#   Keyword | Camp Counter | Suffix
LEGACY_NAMING_PRESET = {
    "variable_order": ["Goal", "SP", "MatchType", "ProductName", "TargetDescriptor", "EW"],
    "delimiter": " | ",
    "suffix": "EW",
    "custom1_value": "",
    "custom2_value": "",
}

EW_NAMING_PRESET = {
    "variable_order": ["Goal", "AdType", "MatchType", "TriggerWord", "ProductName", "Keyword",
                        "CampCounter", "EW"],
    "delimiter": " | ",
    "suffix": "EW",
    "custom1_value": "",
    "custom2_value": "",
}

NAMING_PRESETS = {"LEGACY": LEGACY_NAMING_PRESET, "EW": EW_NAMING_PRESET}


def resolve_campaign_purpose(form):
    """campaign_purpose override, else the campaign_type's default purpose."""
    return form.get("campaign_purpose") or CAMPAIGN_TYPE_DEFAULT_PURPOSE.get(form["campaign_type"], "DISCOVERY")


def resolve_trigger_word(form):
    purpose = resolve_campaign_purpose(form)
    return TRIGGER_WORD_LABELS.get(purpose) or CAMPAIGN_TYPE_LABELS.get(form["campaign_type"], form["campaign_type"])


def resolve_bidding_strategy(form):
    """Explicit override wins; otherwise the naming-convention.md purpose default,
    falling back to the plain campaign_type default for a purpose with no table row."""
    if form.get("bidding_strategy"):
        return form["bidding_strategy"]
    purpose = resolve_campaign_purpose(form)
    return CAMPAIGN_PURPOSE_BIDDING.get(purpose) or CAMPAIGN_TYPE_BIDDING[form["campaign_type"]]


# ----------------------------------------------------------------- generator (port of campaignGenerator.ts)
def _chunk(arr, size):
    return [arr[i:i + size] for i in range(0, len(arr), size)]


def apply_bmm_modifier(keyword):
    return " ".join(f"+{w}" for w in keyword.split())


def _format_start_date(iso_date):
    if not iso_date:
        return ""
    parts = iso_date.split("-")
    if len(parts) != 3 or not all(parts):
        return ""
    yyyy, mm, dd = parts
    return f"{mm}/{dd}/{yyyy}"


def _build_campaign(overrides, form, bidding_strategy):
    c = {
        "sku": form.get("sku", ""),
        "asin": form.get("asin", ""),
        "daily_budget": form["daily_budget"],
        "keyword_bid": form["keyword_bid"],
        "bidding_strategy": bidding_strategy,
        "negative_keywords": form.get("negative_keywords", []),
        "negative_match_type": form.get("negative_match_type", "NEGATIVE_EXACT"),
        "negative_level": form.get("negative_level", "ad_group"),
        "portfolio_id": form.get("portfolio_id", ""),
        "state": form["state"],
        "start_date": _format_start_date(form.get("start_date", "")),
        "site_restriction": form.get("site_restriction", "Amazon"),
    }
    for grp in ("close_match", "loose_match", "substitutes", "complements"):
        c[f"auto_{grp}_bid"] = form.get(f"auto_{grp}_bid")
        c[f"auto_{grp}_state"] = form.get(f"auto_{grp}_state")
    c.update(overrides)
    return c


def generate_campaigns(form, naming_settings, today=None):
    """Port of generateCampaigns(): one form entry -> list of campaign dicts."""
    campaigns = []
    naming = swap_name_order(naming_settings) if form.get("swap_name_order") else naming_settings

    match_type = form.get("match_type") or CAMPAIGN_TYPE_MATCH[form["campaign_type"]]
    purpose = resolve_campaign_purpose(form)
    bidding = resolve_bidding_strategy(form)
    trigger_word = resolve_trigger_word(form)
    targeting_type = "AUTO" if form["campaign_type"] == "Auto" else "MANUAL"

    raw_keywords = [k.strip() for k in form.get("keywords_raw", "").split("\n") if k.strip()]
    keywords = ([apply_bmm_modifier(k) for k in raw_keywords]
                if form.get("bmm_modifier") and form["campaign_type"] == "BMM" else raw_keywords)

    def ctx(target_descriptor, counter):
        return {
            "goal": form["goal"],
            "campaign_type": form["campaign_type"],
            "match_type": match_type,
            "product_name": form.get("product_name", ""),
            "target_descriptor": target_descriptor,
            "counter": counter,
        }

    def push(c, kws, asins):
        c = {**c, "trigger_word": trigger_word,
             "keyword_text": kws[0] if len(kws) == 1 else (c.get("target_descriptor") or "")}
        name = generate_campaign_name(naming, c, today)
        campaigns.append(_build_campaign({
            "campaign_name": name,
            "ad_group_name": generate_ad_group_name(naming, c, today),
            "targeting_type": targeting_type,
            "campaign_type": form["campaign_type"],
            "campaign_purpose": purpose,
            "goal": form["goal"],
            "keywords": kws,
            "match_type": match_type,
            "asins": asins,
            "target_descriptor": c["target_descriptor"],
        }, form, bidding))

    if form["campaign_type"] == "PAT":
        push(ctx(form.get("target_descriptor", ""), 1), [], raw_keywords)
        return campaigns

    if form["campaign_type"] == "Auto":
        push(ctx(form.get("target_descriptor", ""), 1), [], [])
        return campaigns

    if form["campaign_type"] == "SKW":
        for i, kw in enumerate(raw_keywords):
            desc = kw if form.get("skw_include_keyword_in_name") else form.get("target_descriptor", "")
            push(ctx(desc, i + 1), [kw], [])
        return campaigns

    if form.get("transpose_keywords") and keywords:
        per = max(1, int(form.get("keywords_per_campaign") or 1))
        for i, chunk in enumerate(_chunk(keywords, per)):
            push(ctx(form.get("target_descriptor", ""), i + 1), chunk, [])
    else:
        push(ctx(form.get("target_descriptor", ""), 1), keywords, [])
    return campaigns


# ----------------------------------------------------------------- bulk rows (port of bulkExport.ts)
def _empty_row():
    row = {c: "" for c in SP_COLUMNS}
    row["Product"] = "Sponsored Products"
    row["Operation"] = "Create"
    return row


def _parse_date_to_export(date_str, today=None):
    today = today or date.today()
    if not date_str:
        return today.isoformat().replace("-", "")
    parts = date_str.replace("/", "-").split("-")
    if len(parts) != 3:
        return today.isoformat().replace("-", "")
    if len(parts[0]) == 4:
        yyyy, mm, dd = parts
    else:
        mm, dd, yyyy = parts
    return f"{yyyy}{mm.zfill(2)}{dd.zfill(2)}"


def parse_product_list(value):
    """SKU/ASIN field -> list; accepts a list or a newline/comma-separated string."""
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    import re
    return [v.strip() for v in re.split(r"[\n,]", value or "") if v.strip()]


def _money(v):
    return round(float(v), 2)


def build_sp_campaign_rows(campaign, defaults, next_id, today=None):
    rows = []
    start_date = _parse_date_to_export(campaign.get("start_date") or "", today)
    portfolio_id = campaign.get("portfolio_id") or defaults.get("portfolio_id", "")
    sites = "Amazon Business" if campaign.get("site_restriction") == "Amazon Business" else ""

    campaign_id = next_id()
    ad_group_id = next_id()

    rows.append({
        **_empty_row(),
        "Entity": "Campaign",
        "Campaign ID": campaign_id,
        "Campaign Name": campaign["campaign_name"],
        "Start Date": start_date,
        "Targeting Type": campaign["targeting_type"],
        "State": campaign["state"],
        "Daily Budget": _money(campaign["daily_budget"]),
        "Bidding Strategy": AMAZON_BIDDING[campaign["bidding_strategy"]],
        "Portfolio ID": portfolio_id,
        "Sites": sites,
    })

    for key, label in PLACEMENT_LABELS.items():
        pct = defaults.get(key, 0) or 0
        if pct > 0:
            rows.append({
                **_empty_row(),
                "Entity": "Bidding Adjustment",
                "Campaign ID": campaign_id,
                "Campaign Name": campaign["campaign_name"],
                "Placement": label,
                "Percentage": int(pct),
            })

    rows.append({
        **_empty_row(),
        "Entity": "Ad Group",
        "Campaign ID": campaign_id,
        "Ad Group ID": ad_group_id,
        "Campaign Name": campaign["campaign_name"],
        "Ad Group Name": campaign["ad_group_name"],
        "State": campaign["state"],
        "Ad Group Default Bid": _money(campaign["keyword_bid"]),
    })

    sku_list = parse_product_list(campaign.get("sku", ""))
    asin_list = parse_product_list(campaign.get("asin", ""))
    for i in range(max(len(sku_list), len(asin_list))):
        sku = sku_list[i] if i < len(sku_list) else ""
        asin = asin_list[i] if i < len(asin_list) else ""
        if not sku and not asin:
            continue
        rows.append({
            **_empty_row(),
            "Entity": "Product Ad",
            "Campaign ID": campaign_id,
            "Ad Group ID": ad_group_id,
            "Campaign Name": campaign["campaign_name"],
            "Ad Group Name": campaign["ad_group_name"],
            "State": campaign["state"],
            "SKU": "" if defaults.get("vendor_central_mode") else sku,
            "ASIN": asin,
        })

    if campaign["targeting_type"] == "AUTO":
        for grp, expression in (("close_match", "close-match"), ("loose_match", "loose-match"),
                                ("substitutes", "substitutes"), ("complements", "complements")):
            bid = campaign.get(f"auto_{grp}_bid")
            state = campaign.get(f"auto_{grp}_state")
            rows.append({
                **_empty_row(),
                "Entity": "Product Targeting",
                "Campaign ID": campaign_id,
                "Ad Group ID": ad_group_id,
                "Campaign Name": campaign["campaign_name"],
                "Ad Group Name": campaign["ad_group_name"],
                "State": state if state is not None else campaign["state"],
                "Bid": _money(bid if bid is not None else campaign["keyword_bid"]),
                "Product Targeting Expression": expression,
            })
    elif campaign["campaign_type"] == "PAT":
        expanded = campaign["match_type"] == "ASIN_EXPANDED"
        for target_asin in campaign["asins"]:
            rows.append({
                **_empty_row(),
                "Entity": "Product Targeting",
                "Campaign ID": campaign_id,
                "Ad Group ID": ad_group_id,
                "Campaign Name": campaign["campaign_name"],
                "Ad Group Name": campaign["ad_group_name"],
                "State": campaign["state"],
                "Bid": _money(campaign["keyword_bid"]),
                "Product Targeting Expression": (
                    f'asin-expanded="{target_asin}"' if expanded else f'asin="{target_asin}"'),
            })
    else:
        for kw in campaign["keywords"]:
            rows.append({
                **_empty_row(),
                "Entity": "Keyword",
                "Campaign ID": campaign_id,
                "Ad Group ID": ad_group_id,
                "Campaign Name": campaign["campaign_name"],
                "Ad Group Name": campaign["ad_group_name"],
                "State": campaign["state"],
                "Bid": _money(campaign["keyword_bid"]),
                "Keyword Text": kw,
                "Match Type": AMAZON_MATCH[campaign["match_type"]],
            })

    neg_match = AMAZON_NEG_MATCH[campaign.get("negative_match_type") or "NEGATIVE_EXACT"]
    neg_level = campaign.get("negative_level") or "ad_group"
    for nkw in campaign.get("negative_keywords", []):
        if neg_level == "campaign":
            rows.append({
                **_empty_row(),
                "Entity": "Campaign Negative Keyword",
                "Campaign ID": campaign_id,
                "Campaign Name": campaign["campaign_name"],
                "State": campaign["state"],
                "Keyword Text": nkw,
                "Match Type": neg_match,
            })
        else:
            rows.append({
                **_empty_row(),
                "Entity": "Negative Keyword",
                "Campaign ID": campaign_id,
                "Ad Group ID": ad_group_id,
                "Campaign Name": campaign["campaign_name"],
                "Ad Group Name": campaign["ad_group_name"],
                "State": campaign["state"],
                "Keyword Text": nkw,
                "Match Type": neg_match,
            })

    return rows


ROW_BUILDERS = {"SP": build_sp_campaign_rows}


def build_bulk_rows(campaigns, defaults, channel="SP", today=None):
    """All campaigns -> flat row list; temp IDs count up from 1 across the file."""
    counter = iter(range(1, 10 ** 9))

    def next_id():
        return str(next(counter))

    rows = []
    for campaign in campaigns:
        rows.extend(ROW_BUILDERS[channel](campaign, defaults, next_id, today))
    return rows

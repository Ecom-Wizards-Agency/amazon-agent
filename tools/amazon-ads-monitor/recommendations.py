"""recommendations.py -- the weekly brief's PROPOSAL engine.

Pure functions over normalized AdLabs campaign/target-level rows for one
account's week (no I/O, no MCP -- same discipline as analyze.py/flags.py).
This is the piece that makes the weekly brief more than a bigger daily
report: it looks at the week's campaign/target detail and proposes THREE
goal-aware, read-only decision lists for the operator:

- **PUSH** -- targets/campaigns worth scaling (converting, rank-driving,
  budget-capped, or with real headroom).
- **PAUSE / OPTIMIZE** -- bleeders and bloat (zero-sale high spend,
  discovery creep past ~20% of spend, high-ACOS non-rank targets,
  self-competition, stalled campaigns).
- **TEST** -- ONLY IF PERTINENT, drawn from the vetted
  `_local/ads-knowledge/conflicts-and-tests.md` backlog and the week's
  external-signal digest, filtered to what actually maps to this brand's
  goal/situation. Never fabricated to fill space.

Every rule respects the rank-first philosophy from `_local/ads-strategy/
strategy.md` (ACOS is an indicator, not a decision factor -- a Rank/SKW
target is never proposed for a cut on ACOS grounds alone). This module
recommends; it never executes. Any resulting change routes to
`amazon-ads`/`amazon-campaign-builder` with explicit operator approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from datasource import (
    CATEGORY_DISCOVERY, CATEGORY_PROFIT, CATEGORY_RANK, CATEGORY_SHIELD,
    CATEGORY_UNKNOWN, classify_campaign_category,
)
from flags import DEFAULT_THRESHOLDS, resolve_goal_lens

# ---------------------------------------------------------------------------
# Thresholds. Layered the same way flags.py does: toolkit defaults, then a
# goal-lens override, then an explicit config override (config always wins).

DEFAULT_REC_THRESHOLDS = {
    "near_zero_impressions_weekly": 100,     # weekly impressions floor for a Rank target to count as "losing visibility"
    "zero_sale_spend_min_weekly": 15.0,      # $ weekly spend with 0 orders -> negative-candidate (non-Rank only)
    "budget_headroom_max_utilization": 0.70, # spend below this fraction of (daily budget * 7) counts as "headroom"
    "non_rank_acos_ceiling": 0.35,           # default non-rank ACOS ceiling (neutral lens)
    "profitable_push_acos_ceiling": 0.20,    # Profit/Halo ACOS at/below this = "clearly profitable, push"
    "discovery_cvr_push_floor": 0.03,        # Discovery CVR at/above this = converting well enough to consider pushing
    "stalled_spend_max": 1.0,                # weekly spend below this = stalled/redundant candidate
    "stalled_impressions_max": 20,           # weekly impressions below this = stalled/redundant candidate
}

# Non-rank ACOS ceiling per goal lens (mirrors flags.py's GOAL_LENSES
# philosophy: profit-maintain/defend watch efficiency closely; rank-launch
# and liquidate accept looser non-rank ACOS since the whole account is
# running hotter than usual for a reason).
_NON_RANK_ACOS_CEILING_BY_GOAL = {
    "rank-launch": 0.45,
    "scale": 0.35,
    "profit-maintain": 0.25,
    "defend": 0.40,
    "liquidate": None,  # margin erosion is expected; skip the ceiling check entirely
    "maintain": 0.35,
    "neutral": 0.35,
}


def _thresholds(config: Optional[dict] = None) -> dict:
    merged = dict(DEFAULT_REC_THRESHOLDS)
    if config and "rec_thresholds" in config:
        merged.update({k: v for k, v in config["rec_thresholds"].items() if k in DEFAULT_REC_THRESHOLDS})
    return merged


def _non_rank_acos_ceiling(goal: Optional[str], thresholds: dict) -> Optional[float]:
    if goal in _NON_RANK_ACOS_CEILING_BY_GOAL:
        return _NON_RANK_ACOS_CEILING_BY_GOAL[goal]
    return thresholds["non_rank_acos_ceiling"]


def _discovery_share_max(goal: Optional[str]) -> float:
    lens = resolve_goal_lens(goal)
    return lens.get("threshold_overrides", {}).get("discovery_share_max", DEFAULT_THRESHOLDS["discovery_share_max"])


# ---------------------------------------------------------------------------
# Entity normalization. The skill layer supplies a list of dicts (from the
# AdLabs MCP, already filtered post-fetch by profile_id -- see SKILL.md's
# note on AdLabs returning all team profiles regardless of the filter
# passed to it). Missing/optional fields degrade gracefully.

@dataclass
class Entity:
    entity_type: str
    name: str
    campaign_name: str
    campaign_id: Optional[str]
    category: str
    match_type: Optional[str]
    impressions: int
    clicks: int
    spend: float
    sales: float
    orders: int
    daily_budget: Optional[float]
    budget_capped_days: int
    raw: dict = field(default_factory=dict)

    @property
    def acos(self) -> Optional[float]:
        return (self.spend / self.sales) if self.sales else (None if self.spend == 0 else float("inf"))

    @property
    def cvr(self) -> Optional[float]:
        return (self.orders / self.clicks) if self.clicks else None

    @property
    def week_budget(self) -> Optional[float]:
        return (self.daily_budget * 7) if self.daily_budget else None

    @property
    def has_headroom(self) -> bool:
        wb = self.week_budget
        if not wb:
            return False
        return self.spend < DEFAULT_REC_THRESHOLDS["budget_headroom_max_utilization"] * wb

    @property
    def dedupe_key(self):
        return ((self.name or "").strip().lower(), (self.match_type or "").strip().lower())


def normalize_entities(raw_entities: list) -> list:
    """`raw_entities`: list of dicts, each roughly:
    `{entity_type, name, campaign_name, campaign_id, category (optional),
    match_type (optional), impressions, clicks, spend, sales, orders,
    daily_budget (optional), budget_capped_days (optional)}`. `category`
    falls back to `classify_campaign_category(campaign_name)` when absent
    or "Unknown", same convention as the daily toolkit."""
    out = []
    for r in raw_entities:
        campaign_name = r.get("campaign_name") or r.get("name") or ""
        category = r.get("category") or CATEGORY_UNKNOWN
        if category == CATEGORY_UNKNOWN:
            category = classify_campaign_category(campaign_name)
        out.append(Entity(
            entity_type=r.get("entity_type", "target"),
            name=r.get("name") or campaign_name,
            campaign_name=campaign_name,
            campaign_id=r.get("campaign_id"),
            category=category,
            match_type=r.get("match_type"),
            impressions=int(r.get("impressions") or 0),
            clicks=int(r.get("clicks") or 0),
            spend=float(r.get("spend") or 0.0),
            sales=float(r.get("sales") or 0.0),
            orders=int(r.get("orders") or 0),
            daily_budget=r.get("daily_budget"),
            budget_capped_days=int(r.get("budget_capped_days") or 0),
            raw=r,
        ))
    return out


# ---------------------------------------------------------------------------
# Output shapes.

@dataclass
class PushItem:
    entity: str
    scope: str
    category: str
    why: str
    action: str
    expected_impact: str


@dataclass
class PauseOptimizeItem:
    entity: str
    scope: str
    category: str
    why: str
    action: str


@dataclass
class TestIdea:
    hypothesis: str
    method: str
    success_metric: str
    source: str
    status: str  # "vetted_backlog" | "external_signal_hypothesis"
    priority: str = "medium"


@dataclass
class RecommendationsResult:
    push: list
    pause_optimize: list
    tests: list
    notes: list  # data-quality / no-fabrication notes, e.g. "no new tests warranted this week"


# ---------------------------------------------------------------------------
# PUSH.

def _push_for_entity(e: Entity, goal: Optional[str], thresholds: dict) -> Optional[PushItem]:
    if e.category == CATEGORY_RANK:
        if e.impressions <= thresholds["near_zero_impressions_weekly"]:
            return PushItem(
                entity=e.name, scope=e.campaign_name, category=e.category,
                why=(
                    f"Rank/SKW target collapsed to {e.impressions:,} impressions this week -- losing "
                    "visibility on the exact keyword we're trying to rank is the single worst outcome "
                    "under the rank-first philosophy."
                ),
                action="Raise the bid (and lift the ToS/placement modifier if capped) to regain impression share; verify the listing isn't suppressed/out of stock first.",
                expected_impact="Restore impression share and resume rank progress on this keyword.",
            )
        if e.budget_capped_days >= 1:
            return PushItem(
                entity=e.name, scope=e.campaign_name, category=e.category,
                why=f"Budget-capped {e.budget_capped_days} of 7 days this week on a Rank/SKW target -- capping loses impression share on the keyword we're trying to rank.",
                action=f"Raise the daily budget (currently ${e.daily_budget:,.2f}/day)." if e.daily_budget else "Raise the daily budget.",
                expected_impact="More consistent impression share across the full day; faster rank progress.",
            )
        if e.orders > 0:
            # Converting Rank keyword with room to keep pushing: ACOS is
            # not a decision factor here even if high -- that's the plan.
            if e.has_headroom or not e.week_budget:
                return PushItem(
                    entity=e.name, scope=e.campaign_name, category=e.category,
                    why=(
                        f"Rank/SKW target converting ({e.orders} order(s) this week, ACOS "
                        f"{_fmt_pct(e.acos)}) with budget headroom -- ACOS is an indicator, not a "
                        "decision factor, for a keyword we're deliberately running at/above break-even to drive rank."
                    ),
                    action="Raise the bid modestly and/or lift the top-of-search placement modifier to accelerate rank.",
                    expected_impact="Faster organic rank movement on this keyword.",
                )
        return None

    if e.category == CATEGORY_SHIELD:
        if e.budget_capped_days >= 1 or e.impressions <= thresholds["near_zero_impressions_weekly"]:
            return PushItem(
                entity=e.name, scope=e.campaign_name, category=e.category,
                why="Brand-defense target is budget-capped or impressions collapsed -- ceding branded search real estate to a competitor/hijacker is the real risk here.",
                action="Raise bid/budget to protect the brand term; confirm no listing/inventory issue is the real cause first.",
                expected_impact="Hold Amazon's Choice / top-of-search on the brand term.",
            )
        return None

    if e.category == CATEGORY_PROFIT:
        if e.orders > 0 and e.acos is not None and e.acos <= thresholds["profitable_push_acos_ceiling"]:
            return PushItem(
                entity=e.name, scope=e.campaign_name, category=e.category,
                why=f"Profit/Halo target converting at a clearly profitable ACOS ({_fmt_pct(e.acos)}, {e.orders} order(s) this week).",
                action="Raise bid and/or budget to capture more of this low-ACOS demand." + (" Currently budget-capped -- raise the daily budget first." if e.budget_capped_days >= 1 else ""),
                expected_impact="Incremental profit at low risk.",
            )
        return None

    if e.category == CATEGORY_DISCOVERY:
        if e.orders > 0 and e.cvr is not None and e.cvr >= thresholds["discovery_cvr_push_floor"] and not e.budget_capped_days:
            return PushItem(
                entity=e.name, scope=e.campaign_name, category=e.category,
                why=f"Discovery target converting well (CVR {_fmt_pct(e.cvr)}, {e.orders} order(s) this week) -- a candidate to graduate into an exact/Rank campaign, or a modest bid raise in place.",
                action="Raise the bid slightly and/or harvest the converting search term into its own exact/Profit campaign; watch the account's overall discovery share stays near the ~20% cap.",
                expected_impact="Captures more of a proven-converting term without growing discovery bloat.",
            )
        return None

    return None


def _generate_push(entities: list, goal: Optional[str], thresholds: dict) -> list:
    items = []
    for e in entities:
        item = _push_for_entity(e, goal, thresholds)
        if item is not None:
            items.append(item)
    return items


# ---------------------------------------------------------------------------
# PAUSE / OPTIMIZE.

def _discovery_share_of_spend(entities: list) -> Optional[float]:
    total = sum(e.spend for e in entities)
    if total <= 0:
        return None
    discovery = sum(e.spend for e in entities if e.category == CATEGORY_DISCOVERY)
    return discovery / total


def _self_competition_groups(entities: list) -> dict:
    """Group targets by (name, match_type) across DISTINCT campaigns.
    Returns {dedupe_key: [entities]} for keys that appear in 2+ distinct
    campaign_ids -- same keyword/target running in more than one campaign,
    bidding against itself in the auction."""
    by_key: dict = {}
    for e in entities:
        if not e.name or e.entity_type == "campaign":
            continue
        by_key.setdefault(e.dedupe_key, []).append(e)
    return {k: v for k, v in by_key.items() if len({e.campaign_id for e in v if e.campaign_id}) > 1}


def _campaign_totals(entities: list) -> dict:
    """Roll target/keyword-level rows up to campaign totals (spend,
    impressions) for the stalled-campaign check. Rows already at
    entity_type == 'campaign' are used directly."""
    totals: dict = {}
    for e in entities:
        key = e.campaign_id or e.campaign_name
        agg = totals.setdefault(key, {"name": e.campaign_name, "spend": 0.0, "impressions": 0, "category": e.category})
        if e.entity_type == "campaign":
            agg["spend"] = e.spend
            agg["impressions"] = e.impressions
        else:
            agg["spend"] += e.spend
            agg["impressions"] += e.impressions
    return totals


def _generate_pause_optimize(entities: list, goal: Optional[str], thresholds: dict) -> tuple:
    """Returns (items, notes, tags) -- `notes` carries the Rank exception
    call-outs (e.g. a zero-sale Rank target that is deliberately NOT
    proposed for a cut) so the operator still sees it, just not
    mis-classified as a pause/optimize action. `tags` is the set of
    situational signals this pass actually found (feeds TEST selection)."""
    items = []
    notes = []
    tags = set()
    ceiling = _non_rank_acos_ceiling(goal, thresholds)

    for e in entities:
        if e.entity_type == "campaign":
            continue  # campaign-level rollups handled by the stalled-campaign check below

        # 1. Zero-sale high spend (negative-keyword/target candidate).
        if e.spend >= thresholds["zero_sale_spend_min_weekly"] and e.orders == 0:
            if e.category == CATEGORY_RANK:
                notes.append(
                    f"'{e.name}' (Rank/SKW, {e.campaign_name}): ${e.spend:,.2f} spend with 0 orders this "
                    "week -- NOT proposed for a cut. Rank/SKW targets may intentionally run at break-even "
                    "or a loss to drive rank (strategy.md); verify this is the plan before touching it."
                )
            else:
                items.append(PauseOptimizeItem(
                    entity=e.name, scope=e.campaign_name, category=e.category,
                    why=f"${e.spend:,.2f} spend with 0 orders this week, non-rank target -- negative-keyword/target candidate.",
                    action="Add as a negative exact (or pause the target) unless there's a known reason to keep testing it.",
                ))
                continue  # already actioned; don't also run the ACOS-ceiling check on it

        # 2. High-ACOS non-rank target (converting but inefficient).
        if (
            e.category != CATEGORY_RANK and ceiling is not None
            and e.orders > 0 and e.acos is not None and e.acos > ceiling
        ):
            items.append(PauseOptimizeItem(
                entity=e.name, scope=e.campaign_name, category=e.category,
                why=f"ACOS {_fmt_pct(e.acos)} vs the ~{_fmt_pct(ceiling)} ceiling for a {e.category} target under this goal, despite converting.",
                action="Lower the bid, tighten match type, or reallocate budget toward the account's Rank/Profit campaigns.",
            ))
            tags.add("high_acos_non_rank")

    # 3. Discovery share of spend creeping past the goal-aware cap.
    share = _discovery_share_of_spend(entities)
    cap = _discovery_share_max(goal)
    if share is not None and share > cap:
        items.append(PauseOptimizeItem(
            entity="Discovery campaigns (account-wide)", scope="account", category=CATEGORY_DISCOVERY,
            why=f"Discovery is {_fmt_pct(share)} of this week's spend (target ~{_fmt_pct(cap)} or less per the ~80/20 exact/discovery split).",
            action="Tighten Discovery bids and search-term hygiene; reallocate the freed budget toward Rank/exact campaigns.",
        ))
        tags.add("discovery_bloat")

    # 4. Self-competition: same keyword/target + match type across
    # distinct campaigns, bidding against itself.
    for key, group in _self_competition_groups(entities).items():
        name, match_type = key
        # Keep the strongest performer (most orders, then lowest ACOS)
        # unflagged; flag the rest as the consolidation candidates.
        ranked = sorted(group, key=lambda e: (-e.orders, e.acos if e.acos is not None else float("inf")))
        keep, rest = ranked[0], ranked[1:]
        campaigns = ", ".join(sorted({e.campaign_name for e in group}))
        items.append(PauseOptimizeItem(
            entity=f"{name} ({match_type or 'match type n/a'})", scope=campaigns, category=keep.category,
            why=f"Same target running in {len({e.campaign_id for e in group})} campaigns ({campaigns}) -- self-competition, bidding against itself in the auction.",
            action=f"Consolidate into '{keep.campaign_name}' (best performer: {keep.orders} order(s), ACOS {_fmt_pct(keep.acos)}); pause/remove the duplicate(s) in {', '.join(sorted({e.campaign_name for e in rest}))}.",
        ))
        tags.add("self_competition")

    # 5. Redundant / stalled campaigns (near-zero spend and impressions).
    for key, agg in _campaign_totals(entities).items():
        if agg["spend"] <= thresholds["stalled_spend_max"] and agg["impressions"] <= thresholds["stalled_impressions_max"]:
            items.append(PauseOptimizeItem(
                entity=agg["name"], scope=agg["name"], category=agg["category"],
                why=f"Near-zero activity this week (${agg['spend']:,.2f} spend, {agg['impressions']:,} impressions) -- stalled/redundant.",
                action="Investigate (suppressed listing, exhausted keyword, mis-targeted) and archive if there's no path back to relevance.",
            ))
            tags.add("stalled_campaign")

    return items, notes, tags


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "n/a"
    if v == float("inf"):
        return "inf"
    return f"{v * 100:.0f}%"


# ---------------------------------------------------------------------------
# TEST. Draws from a curated, tagged subset of the vetted backlog in
# `_local/ads-knowledge/conflicts-and-tests.md` (Part B) plus any
# additional structured candidates the caller passes in (e.g. a fuller
# JSON export of that file), filtered against this week's actual signals
# -- never fabricated to fill space.

# Each candidate's `requires` is a list of tag-sets; the candidate is
# pertinent if ANY tag-set is fully satisfied by this week's brand tags
# (OR across alternatives, AND within one alternative).
DEFAULT_TEST_BACKLOG = (
    {
        "id": "T1", "source": "conflicts-and-tests.md#T1",
        "hypothesis": "Single-keyword exact-match Rank campaigns produce faster/more durable organic rank gains per dollar than equivalent broad/auto/category campaigns, despite showing worse headline ACOS.",
        "method": "Run a matched broad-match and exact-match campaign for the same target keyword in parallel (same product, budget, period) for 4-8 weeks.",
        "success_metric": "Organic rank position delta + ACOS/CVR, both campaign types, same window.",
        "priority": "high",
        "requires": [{"rank_present", "goal:rank-launch"}, {"rank_present", "goal:scale"}],
    },
    {
        "id": "T3", "source": "conflicts-and-tests.md#T3",
        "hypothesis": "A permanent, very-low-bid scavenger/catch-all campaign captures incremental, low-ACOS orders without cannibalizing structured Rank/Discovery/Profit spend.",
        "method": "Run alongside (never instead of) the existing structure; track for 60 days.",
        "success_metric": "Incremental profit contribution net of any overlap with existing broad/auto discovery campaigns.",
        "priority": "high",
        "requires": [{"discovery_present", "goal:scale"}],
    },
    {
        "id": "T4", "source": "conflicts-and-tests.md#T4",
        "hypothesis": "Self-targeted product placement (STPP) on your own ASIN produces low-cost, incremental retargeting-like sales.",
        "method": "Set up an STPP campaign on 1-2 SKUs; compare resulting ACOS and order volume to account baseline.",
        "success_metric": "ACOS and incremental order volume vs. a matched control period/account.",
        "priority": "high",
        "requires": [{"profit_present"}, {"shield_present"}],
    },
    {
        "id": "T6", "source": "conflicts-and-tests.md#T6",
        "hypothesis": "Comparing your own CTR/CVR per keyword to the SQP market/aggregate average reliably distinguishes a listing/creative problem from a genuinely winnable keyword that deserves more spend.",
        "method": "Pull SQP for the flagged high-ACOS non-rank keywords; flag >2x CTR/CVR gaps vs. market average; act on the flagged set.",
        "success_metric": "CTR/CVR/rank change 4-8 weeks after acting on flagged keywords, vs. an unflagged control set.",
        "priority": "high",
        "requires": [{"high_acos_non_rank"}],
    },
    {
        "id": "T18", "source": "conflicts-and-tests.md#T18",
        "hypothesis": "A formalized statistical negative-keyword threshold (e.g. 3x the clicks needed for one expected sale) produces fewer false-negative pauses than ad-hoc negation timing.",
        "method": "Apply the threshold consistently to Discovery-category auto/broad campaigns for 60 days; audit the false-negative rate.",
        "success_metric": "ACOS improvement and negative-keyword harvest speed vs. ad-hoc review.",
        "priority": "medium",
        "requires": [{"discovery_bloat"}],
    },
    {
        "id": "T13", "source": "conflicts-and-tests.md#T13",
        "hypothesis": "Day-parting bid rules, applied only to Profit/Halo/Shield campaigns (never Rank) and only once volume/CTR/CVR fundamentals are solid, improve blended ACOS without suppressing Rank-campaign bids.",
        "method": "Export hourly reports, build a red/white/green conditional pivot, apply bid rules only to the eligible campaign categories.",
        "success_metric": "Blended ACOS variance and conversion rate before/after; Rank-category keyword bids unchanged.",
        "priority": "medium",
        "requires": [{"goal:profit-maintain"}],
    },
    {
        "id": "T5", "source": "conflicts-and-tests.md#T5",
        "hypothesis": "Pausing own-brand Shield campaigns opens the door to competitor capture of branded search real estate within weeks.",
        "method": "Confirmatory only -- do not actually pause Shield spend to test this. Monitor competitor impression/click share on branded terms via SQP as a standing watch.",
        "success_metric": "Competitor share-of-search on the brand term over time.",
        "priority": "high",
        "requires": [{"goal:defend", "shield_present"}, {"hijacker_mentioned", "shield_present"}],
    },
)


def _tag_frozensets(candidate: dict) -> list:
    return [frozenset(s) for s in candidate.get("requires", [])]


def _candidate_pertinent(candidate: dict, brand_tags: set) -> bool:
    alts = _tag_frozensets(candidate)
    if not alts:
        return False  # a candidate with no requirements is never auto-included -- avoid fabricating relevance
    return any(alt <= brand_tags for alt in alts)


def select_tests(brand_tags: set, candidates: Optional[list] = None, signal_items: Optional[list] = None) -> list:
    """Filter the vetted backlog (`candidates`, default `DEFAULT_TEST_BACKLOG`)
    plus any pre-vetted external `signal_items` (already-parsed digest
    entries, see `parse_signal_digest_markdown`) down to what's pertinent
    to this week's `brand_tags` (goal + situational signals). Returns []
    -- not a fabricated filler test -- when nothing matches."""
    out = []
    for c in (candidates if candidates is not None else DEFAULT_TEST_BACKLOG):
        if _candidate_pertinent(c, brand_tags):
            out.append(TestIdea(
                hypothesis=c["hypothesis"], method=c["method"], success_metric=c["success_metric"],
                source=c.get("source", "conflicts-and-tests.md"), status="vetted_backlog",
                priority=c.get("priority", "medium"),
            ))
    for s in (signal_items or []):
        if _candidate_pertinent(s, brand_tags):
            out.append(TestIdea(
                hypothesis=s["hypothesis"], method=s.get("method", "Design a small controlled test in this account before generalizing."),
                success_metric=s.get("success_metric", "Define a success metric before running."),
                source=s.get("source", "external signal digest"), status="external_signal_hypothesis",
                priority=s.get("priority", "low"),
            ))
    return out


# ---------------------------------------------------------------------------
# Signal digest parsing (pure text parsing; the CLI/skill layer reads the
# file, this function only parses the string). Convention (documented in
# `_local/ads-signals/README.md`):
#
#     - **Claim text.** Tags: tag1, tag2. Source: <name/url>. Confidence: unverified.
#
# Any bullet that doesn't match this convention is skipped (not an error)
# -- a malformed/freeform digest just yields zero parsed items rather than
# crashing the weekly run.

_DIGEST_BULLET_RE = re.compile(
    r"^\s*-\s*\*\*(?P<claim>.+?)\*\*\.?\s*Tags:\s*(?P<tags>[^.]*)\.\s*Source:\s*(?P<source>[^.]*)\.\s*Confidence:\s*(?P<confidence>[\w-]+)\.?\s*$"
)


def parse_signal_digest_markdown(text: str) -> list:
    """Parse a `_local/ads-signals/<ISO-year>-W<week>/digest.md`-style file
    into structured candidate dicts consumable by `select_tests`. Returns
    [] for missing/empty/unparseable content -- not an error."""
    if not text:
        return []
    items = []
    for line in text.splitlines():
        m = _DIGEST_BULLET_RE.match(line)
        if not m:
            continue
        tags = {t.strip() for t in m.group("tags").split(",") if t.strip()}
        items.append({
            "hypothesis": m.group("claim").strip().rstrip(".").strip(),
            "success_metric": "Define a success metric mapped to this brand's goal before running.",
            "source": m.group("source").strip(),
            "confidence": m.group("confidence").strip().lower(),
            "requires": [tags] if tags else [],
        })
    return items


# ---------------------------------------------------------------------------
# Brand-tag computation (drives TEST selection) + top-level entry point.

# Free-text -> tag keyword map for the brand's `situation` string (from
# `_local/ads-monitor/brand-goals.json`). Deliberately small and literal --
# this is a light nudge for TEST selection, not an NLP layer.
_SITUATION_KEYWORD_TAGS = {
    "hijack": "hijacker_mentioned",
    "crisis": "crisis_mentioned",
    "acos spike": "acos_spike_mentioned",
    "recurring acos": "acos_spike_mentioned",
}


def _situation_tags(situation: Optional[str]) -> set:
    if not situation:
        return set()
    low = situation.lower()
    return {tag for kw, tag in _SITUATION_KEYWORD_TAGS.items() if kw in low}


def _compute_brand_tags(entities: list, goal: Optional[str], situation: Optional[str], pause_tags: set) -> set:
    """`pause_tags`: the situational tags `_generate_pause_optimize` already
    derived while building that list (discovery_bloat, high_acos_non_rank,
    self_competition, stalled_campaign) -- combined here with the
    goal/category-presence tags and a light keyword read of `situation` so
    TEST selection sees the full picture."""
    tags = set(pause_tags) | _situation_tags(situation)
    if goal:
        tags.add(f"goal:{goal}")
    if any(e.category == CATEGORY_RANK for e in entities):
        tags.add("rank_present")
    if any(e.category == CATEGORY_DISCOVERY for e in entities):
        tags.add("discovery_present")
    if any(e.category == CATEGORY_PROFIT for e in entities):
        tags.add("profit_present")
    if any(e.category == CATEGORY_SHIELD for e in entities):
        tags.add("shield_present")
    return tags


def build_recommendations(
    raw_entities: list,
    goal: Optional[str] = None,
    situation: Optional[str] = None,
    test_candidates: Optional[list] = None,
    signal_items: Optional[list] = None,
    config: Optional[dict] = None,
) -> RecommendationsResult:
    """Top-level entry point. `raw_entities`: normalized AdLabs weekly
    campaign/target rows (see `normalize_entities`). `signal_items`: parsed
    external-signal digest entries (see `parse_signal_digest_markdown`),
    already tagged/pre-filtered by the critical-review protocol upstream
    -- this function still requires them to map to a `brand_tags` entry
    before surfacing them, so an unrelated signal never leaks in just
    because it survived critical review generically.
    """
    thresholds = _thresholds(config)
    entities = normalize_entities(raw_entities)

    push = _generate_push(entities, goal, thresholds)
    pause_optimize, pause_notes, pause_tags = _generate_pause_optimize(entities, goal, thresholds)
    brand_tags = _compute_brand_tags(entities, goal, situation, pause_tags)
    tests = select_tests(brand_tags, candidates=test_candidates, signal_items=signal_items)

    notes = list(pause_notes)
    if not entities:
        notes.append("No AdLabs campaign/target-level rows supplied this week -- Push/Pause-Optimize lists are empty by construction, not a clean bill of health.")
    if not tests:
        notes.append("No new tests warranted this week.")

    return RecommendationsResult(push=push, pause_optimize=pause_optimize, tests=tests, notes=notes)

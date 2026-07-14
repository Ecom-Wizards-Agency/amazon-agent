"""flags.py -- severity-tagged, philosophy-aware, GOAL-AWARE performance flags.

Every flag carries metric, threshold crossed, likely cause, and severity
(info/warn/alert/critical). Grounded in _local/ads-strategy/strategy.md
(the rank-first philosophy) and the corroborated heuristics in
_local/ads-knowledge/knowledge-digest.md.

CRITICAL: some things that look like anomalies are expected by the
strategy and must be suppressed, not alerted on -- most importantly, high
top-of-search ACOS (and wide day-to-day ACOS swings) on a Rank/SKW
campaign, which is a known last-click-attribution artifact, not a real
problem (strategy.md: "ACOS is an indicator, not a decision factor...
last-click attribution makes ToF/MoF ACOS unreliable"; digest.md bidding
theme: "ACOS is a lagging, distorted indicator ... the single most
corroborated principle in the entire corpus"). `evaluate()` returns both
the active flags and a separate suppressed list so a report can show
"noted, not flagged" instead of silently dropping the signal.

## Goal-based lenses

A brand's stage/goal changes what "anomalous" even means (per
`_local/ads-monitor/sellerboard-feeds.json` `_context_rules`: "Apply
GOAL-BASED lenses ... thresholds, which flags matter, and recommendations
must adapt per the brand's profile, not one-size-fits-all"). `evaluate()`
takes an optional `goal` string (from the brand's Notion "Amazon Agent
Ops Profiles" row); unknown/missing goals default to the neutral lens
(today's plain thresholds, unchanged behavior). See `GOAL_LENSES` below
for the presets and exactly what each one changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from analyze import AnalysisResult, SeriesAnalysis
from datasource import CATEGORY_DISCOVERY, CATEGORY_RANK, CATEGORY_UNKNOWN

SEVERITY_CRITICAL = "critical"
SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_ALERT = "alert"
_SEVERITY_ORDER = {SEVERITY_CRITICAL: 0, SEVERITY_ALERT: 1, SEVERITY_WARN: 2, SEVERITY_INFO: 3}

DEFAULT_THRESHOLDS = {
    "spend_spike_pct": 0.60,             # vs trailing-7 avg
    "spend_collapse_pct": -0.50,         # vs trailing-7 avg
    "cvr_drop_pct": -0.25,               # vs trailing-7 avg
    "clicks_stable_band_pct": 0.15,      # clicks must stay within this band to call CVR drop "not a bid issue"
    "near_zero_impressions_abs": 50,
    "near_zero_impressions_ratio": 0.15, # vs trailing-7 avg
    "discovery_share_max": 0.20,         # per strategy.md ~80/20 exact/discovery split
    "acos_swing_pct": 0.50,              # vs trailing-7 avg
    "zero_sales_spend_min": 20.0,        # $ spend with 0 orders -> negative-candidate alert
    "budget_capped_min_days": 1,
    "tacos_rise_alert_pct": 0.20,        # account-level TACOS rise vs trailing-7 avg (goal-lens-gated, see below)
    "margin_drop_alert_pct": -0.15,      # account-level margin drop vs trailing-7 avg (goal-lens-gated, see below)
}

# ---------------------------------------------------------------------------
# Goal-based lens presets.
#
# Each lens is a small dict of knobs `evaluate()` reads:
# - "label" / "description": for wording in flag messages and the report.
# - "threshold_overrides": DEFAULT_THRESHOLDS keys this lens nudges before
#   any explicit per-account `config["thresholds"]` override is applied
#   (config always wins -- a lens is a sane per-goal default, not a hard
#   rule).
# - "tacos_margin_behavior": how the account-level TACOS-rise/margin-drop
#   check (`_check_goal_aware_tacos_margin`) treats a breach:
#     "expected_high" -> breach is the plan, not a problem (INFO, wording
#       says so) -- rank-launch, liquidate.
#     "alert_on_rise" -> breach is exactly the thing this goal watches for
#       (ALERT) -- profit-maintain, defend.
#     "ignore"        -> no goal-aware TACOS/margin check at all (scale,
#       neutral) -- the plain `_check_acos_swing` still applies as usual.
# - "impression_rank_critical": escalate a near-zero-impressions flag on a
#   Rank/SKW campaign from ALERT to CRITICAL (rank-launch/defend: losing
#   the keyword we're trying to rank/hold is the single worst outcome).
# - "escalate_spend_spike": escalate a spend-spike flag to ALERT
#   (profit-maintain: aggressive spend growth needs a reason, not a shrug).
# - "downgrade_zero_sales": downgrade a zero-sales-with-spend flag one
#   level (liquidate: some loss-driving spend to sell through fast is the
#   plan).
GOAL_RANK_LAUNCH = "rank-launch"
GOAL_SCALE = "scale"
GOAL_PROFIT_MAINTAIN = "profit-maintain"
GOAL_DEFEND = "defend"
GOAL_LIQUIDATE = "liquidate"
GOAL_NEUTRAL = "neutral"
DEFAULT_GOAL = GOAL_NEUTRAL

GOAL_LENSES = {
    GOAL_RANK_LAUNCH: {
        "label": "Rank / Launch",
        "description": (
            "Building organic rank on a new/young ASIN. High or rising TACOS/ACOS is the plan, "
            "not a problem -- the real emergency is losing impression share on the Rank keyword "
            "we're trying to rank."
        ),
        "threshold_overrides": {"tacos_rise_alert_pct": 0.35, "acos_swing_pct": 0.75},
        "tacos_margin_behavior": "expected_high",
        "impression_rank_critical": True,
    },
    GOAL_SCALE: {
        "label": "Scale",
        "description": (
            "Proven winner, pushing volume. Efficiency matters more than at launch but growth "
            "still leads -- watch discovery bloat and CVR more closely than raw ACOS/TACOS."
        ),
        "threshold_overrides": {"discovery_share_max": 0.15},
        "tacos_margin_behavior": "ignore",
        "impression_rank_critical": False,
    },
    GOAL_PROFIT_MAINTAIN: {
        "label": "Profit / Maintain",
        "description": (
            "Mature ASIN, defending margin. Rising TACOS or falling margin IS the alert; "
            "aggressive spend growth is the flag, not expected upside."
        ),
        "threshold_overrides": {"tacos_rise_alert_pct": 0.15, "margin_drop_alert_pct": -0.10, "spend_spike_pct": 0.35},
        "tacos_margin_behavior": "alert_on_rise",
        "impression_rank_critical": False,
        "escalate_spend_spike": True,
    },
    GOAL_DEFEND: {
        "label": "Defend",
        "description": (
            "Protecting rank/share against a competitor or hijacker push. Near-zero impressions "
            "and Shield-category anomalies are urgent; some extra spend to hold position is expected."
        ),
        "threshold_overrides": {"tacos_rise_alert_pct": 0.25, "near_zero_impressions_ratio": 0.25},
        "tacos_margin_behavior": "alert_on_rise",
        "impression_rank_critical": True,
    },
    GOAL_LIQUIDATE: {
        "label": "Liquidate",
        "description": (
            "Clearing inventory fast (excess stock, sunsetting SKU). Margin erosion, and even a "
            "real loss on ads, is expected -- the real risk is NOT selling through fast enough."
        ),
        "threshold_overrides": {"near_zero_impressions_ratio": 0.25, "zero_sales_spend_min": 40.0},
        "tacos_margin_behavior": "expected_high",
        "impression_rank_critical": False,
        "downgrade_zero_sales": True,
    },
    GOAL_NEUTRAL: {
        "label": "Neutral",
        "description": "No goal profile on file yet -- plain thresholds, no goal-based severity changes.",
        "threshold_overrides": {},
        "tacos_margin_behavior": "ignore",
        "impression_rank_critical": False,
    },
}


def resolve_goal_lens(goal: Optional[str]) -> dict:
    """Unknown/None goal -> the neutral lens (documented default)."""
    return GOAL_LENSES.get(goal, GOAL_LENSES[DEFAULT_GOAL])


@dataclass
class Flag:
    severity: str
    metric: str
    threshold: str
    message: str
    likely_cause: str
    scope: str  # "account" or a campaign label
    category: str = CATEGORY_UNKNOWN
    suppressed: bool = False
    suppressed_reason: Optional[str] = None

    def sort_key(self):
        return (_SEVERITY_ORDER.get(self.severity, 9), self.scope, self.metric)


def _thresholds(config: Optional[dict], lens: Optional[dict] = None) -> dict:
    """Layering, lowest to highest priority: toolkit defaults -> goal-lens
    overrides -> explicit per-account config overrides (config always
    wins -- a lens is a sane per-goal default, not a hard rule)."""
    merged = dict(DEFAULT_THRESHOLDS)
    if lens and lens.get("threshold_overrides"):
        merged.update({k: v for k, v in lens["threshold_overrides"].items() if k in DEFAULT_THRESHOLDS})
    if config and "thresholds" in config:
        merged.update({k: v for k, v in config["thresholds"].items() if k in DEFAULT_THRESHOLDS})
    return merged


def _pct(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v * 100:.0f}%"


_SEVERITY_ORDER_LIST = [SEVERITY_CRITICAL, SEVERITY_ALERT, SEVERITY_WARN, SEVERITY_INFO]


def _escalate_severity(severity: str) -> str:
    """One step towards CRITICAL (used by goal lenses that treat a signal
    as more urgent than the plain default, e.g. rank-launch/defend on a
    near-zero-impressions Rank/SKW campaign)."""
    idx = _SEVERITY_ORDER_LIST.index(severity) if severity in _SEVERITY_ORDER_LIST else len(_SEVERITY_ORDER_LIST) - 1
    return _SEVERITY_ORDER_LIST[max(idx - 1, 0)]


def _downgrade_severity(severity: str) -> str:
    """One step towards INFO (used by goal lenses that expect the signal,
    e.g. liquidate on a zero-sales-with-spend candidate)."""
    idx = _SEVERITY_ORDER_LIST.index(severity) if severity in _SEVERITY_ORDER_LIST else len(_SEVERITY_ORDER_LIST) - 1
    return _SEVERITY_ORDER_LIST[min(idx + 1, len(_SEVERITY_ORDER_LIST) - 1)]


# ---------------------------------------------------------------------------
# Individual rules. Each takes a SeriesAnalysis (+ context) and returns
# zero or one Flag (some checks are account-only or need cross-series data
# and are handled separately below). Every rule accepts an optional
# resolved goal `lens` dict (see GOAL_LENSES/resolve_goal_lens above) so
# `evaluate()` can call every check the same way whether or not a goal was
# supplied; only the checks a lens actually adjusts read from it.

def _check_spend_spike_or_collapse(series: SeriesAnalysis, thresholds: dict, lens: Optional[dict] = None) -> Optional[Flag]:
    d = series.deltas.get("spend")
    if not d or d.trailing7_pct_change is None:
        return None
    if d.trailing7_pct_change >= thresholds["spend_spike_pct"]:
        severity = SEVERITY_WARN
        cause = "Spend spike: bid/budget change, new campaign, or a competitor pullback opening cheaper auctions. Check for an intentional change first."
        if lens and lens.get("escalate_spend_spike"):
            severity = _escalate_severity(severity)
            cause += f" Escalated under the '{lens.get('label')}' goal: aggressive spend growth needs a reason, not a shrug."
        return Flag(
            severity=severity,
            metric="spend",
            threshold=f">= +{_pct(thresholds['spend_spike_pct'])} vs trailing-7 avg",
            message=f"Spend {_pct(d.trailing7_pct_change)} vs trailing-7 avg (${d.value:,.2f} vs ${d.trailing7_avg:,.2f} avg).",
            likely_cause=cause,
            scope=series.label,
            category=series.category,
        )
    if d.trailing7_pct_change <= thresholds["spend_collapse_pct"]:
        return Flag(
            severity=SEVERITY_WARN,
            metric="spend",
            threshold=f"<= {_pct(thresholds['spend_collapse_pct'])} vs trailing-7 avg",
            message=f"Spend {_pct(d.trailing7_pct_change)} vs trailing-7 avg (${d.value:,.2f} vs ${d.trailing7_avg:,.2f} avg).",
            likely_cause="Spend collapse: budget exhaustion earlier in the day, a paused campaign/ad group, out-of-stock advertised SKU, or a suppressed listing.",
            scope=series.label,
            category=series.category,
        )
    return None


def _check_budget_capped(series: SeriesAnalysis, thresholds: dict, lens: Optional[dict] = None) -> Optional[Flag]:
    row = series.report_row
    if not row or not row.budget_capped:
        return None
    severity = SEVERITY_WARN
    cause = "Campaign hit its daily budget cap; it stopped serving before demand ran out."
    if series.category == CATEGORY_RANK:
        cause += " On a Rank/SKW campaign this means lost impression share on the exact keyword we're trying to rank -- raise the budget rather than let it cap."
    return Flag(
        severity=severity,
        metric="spend",
        threshold=f"budget-capped >= {thresholds['budget_capped_min_days']} day(s)",
        message=f"Budget-capped on the report date (spend ${row.spend:,.2f} of ${row.budget:,.2f} budget)." if row.budget else "Budget-capped on the report date.",
        likely_cause=cause,
        scope=series.label,
        category=series.category,
    )


def _check_cvr_drop_stable_clicks(series: SeriesAnalysis, thresholds: dict, lens: Optional[dict] = None) -> Optional[Flag]:
    cvr_d = series.deltas.get("cvr")
    clicks_d = series.deltas.get("clicks")
    if not cvr_d or not clicks_d:
        return None
    if cvr_d.trailing7_pct_change is None or clicks_d.trailing7_pct_change is None:
        return None
    if cvr_d.trailing7_pct_change > thresholds["cvr_drop_pct"]:
        return None
    if abs(clicks_d.trailing7_pct_change) > thresholds["clicks_stable_band_pct"]:
        return None  # clicks also moved a lot; this isn't the "stable clicks" pattern
    return Flag(
        severity=SEVERITY_WARN,
        metric="cvr",
        threshold=f"<= {_pct(thresholds['cvr_drop_pct'])} vs trailing-7 avg with clicks within +/-{_pct(thresholds['clicks_stable_band_pct'])}",
        message=f"CVR {_pct(cvr_d.trailing7_pct_change)} vs trailing-7 avg while clicks held ({_pct(clicks_d.trailing7_pct_change)}).",
        likely_cause="Clicks are stable so this isn't a bid/visibility issue -- check the listing (price, stock, reviews, image, buy box) rather than the campaign.",
        scope=series.label,
        category=series.category,
    )


def _check_near_zero_impressions_rank(series: SeriesAnalysis, thresholds: dict, lens: Optional[dict] = None) -> Optional[Flag]:
    if series.category != CATEGORY_RANK:
        return None
    d = series.deltas.get("impressions")
    if not d or d.value is None:
        return None
    ratio_ok = d.trailing7_avg and d.value <= thresholds["near_zero_impressions_ratio"] * d.trailing7_avg
    abs_ok = d.value <= thresholds["near_zero_impressions_abs"]
    if not (ratio_ok or abs_ok):
        return None
    severity = SEVERITY_ALERT
    cause = "Likely suppressed listing, out-bid, budget/end-date issue, or paused by mistake. This is the keyword we're trying to rank -- treat as urgent."
    if lens and lens.get("impression_rank_critical"):
        severity = _escalate_severity(severity)
        cause += f" Escalated to CRITICAL under the '{lens.get('label')}' goal: losing impression share on the keyword we're trying to rank/hold is the single worst outcome."
    return Flag(
        severity=severity,
        metric="impressions",
        threshold=f"<= {thresholds['near_zero_impressions_abs']} impressions or <= {_pct(thresholds['near_zero_impressions_ratio'])} of trailing-7 avg",
        message=f"Rank/SKW campaign impressions collapsed to {d.value:,.0f} (trailing-7 avg {d.trailing7_avg:,.0f}).",
        likely_cause=cause,
        scope=series.label,
        category=series.category,
    )


def _check_zero_sales_spend(series: SeriesAnalysis, thresholds: dict, lens: Optional[dict] = None) -> Optional[Flag]:
    row = series.report_row
    spend_d = series.deltas.get("spend")
    orders_d = series.deltas.get("orders")
    if not row or spend_d is None or orders_d is None:
        return None
    # Look at the trailing week, not just the single report day, so one
    # lucky click doesn't hide a genuine negative-keyword candidate.
    trailing_spend = spend_d.trailing7_avg or 0.0
    trailing_orders = orders_d.trailing7_avg or 0.0
    if trailing_spend < thresholds["zero_sales_spend_min"] or trailing_orders > 0 or (row.orders or 0) > 0:
        return None
    severity = SEVERITY_ALERT
    cause = "Zero orders despite real spend over the trailing week -- negative-keyword/target candidate."
    if series.category == CATEGORY_RANK:
        severity = SEVERITY_WARN
        cause += " Rank/SKW campaigns may intentionally run at break-even or a loss to drive rank (strategy.md) -- verify this is the plan, not simply wasted spend, before cutting it."
    if lens and lens.get("downgrade_zero_sales"):
        severity = _downgrade_severity(severity)
        cause += f" Downgraded under the '{lens.get('label')}' goal: some loss-driving spend to sell through fast is the plan."
    return Flag(
        severity=severity,
        metric="orders",
        threshold=f">= ${thresholds['zero_sales_spend_min']:.0f} trailing-7 avg spend with 0 orders",
        message=f"~${trailing_spend:,.2f}/day trailing-7 avg spend with 0 orders (report day spend ${row.spend:,.2f}).",
        likely_cause=cause,
        scope=series.label,
        category=series.category,
    )


def _check_acos_swing(series: SeriesAnalysis, thresholds: dict, lens: Optional[dict] = None) -> Optional[Flag]:
    """Returns a Flag for a real ACOS swing outside Rank/SKW campaigns.
    Rank/SKW handling (suppression) happens in `evaluate()`, not here, so
    the suppressed-vs-active split stays in one place."""
    if series.category == CATEGORY_RANK:
        return None
    d = series.deltas.get("acos")
    if not d or d.trailing7_pct_change is None:
        return None
    if abs(d.trailing7_pct_change) < thresholds["acos_swing_pct"]:
        return None
    direction = "up" if d.trailing7_pct_change > 0 else "down"
    return Flag(
        severity=SEVERITY_INFO,
        metric="acos",
        threshold=f">= +/-{_pct(thresholds['acos_swing_pct'])} vs trailing-7 avg",
        message=f"ACOS swung {direction} {_pct(d.trailing7_pct_change)} vs trailing-7 avg ({_pct(d.value)} vs {_pct(d.trailing7_avg)} avg).",
        likely_cause="Wait for a full attribution window before reacting; exclude event days from the read. Check bid/placement changes and competitor activity before touching bids.",
        scope=series.label,
        category=series.category,
    )


def _acos_swing_would_fire(series: SeriesAnalysis, thresholds: dict) -> bool:
    d = series.deltas.get("acos")
    if not d or d.trailing7_pct_change is None:
        return False
    return abs(d.trailing7_pct_change) >= thresholds["acos_swing_pct"]


def _check_discovery_share(analysis: AnalysisResult, thresholds: dict) -> Optional[Flag]:
    discovery_spend = 0.0
    total_spend = 0.0
    any_data = False
    for series in analysis.campaign_series:
        d = series.deltas.get("spend")
        if not d or d.value is None:
            continue
        any_data = True
        total_spend += d.value
        if series.category == CATEGORY_DISCOVERY:
            discovery_spend += d.value
    if not any_data or total_spend <= 0:
        return None
    share = discovery_spend / total_spend
    if share <= thresholds["discovery_share_max"]:
        return None
    return Flag(
        severity=SEVERITY_WARN,
        metric="discovery_share_of_spend",
        threshold=f"> {_pct(thresholds['discovery_share_max'])} of total spend",
        message=f"Discovery campaigns are {_pct(share)} of today's spend (target ~{_pct(thresholds['discovery_share_max'])} or less).",
        likely_cause="Discovery bloat: broad/auto/phrase campaigns are absorbing budget that should be funding Rank/exact. Review Discovery bids and search-term hygiene.",
        scope="account",
        category=CATEGORY_DISCOVERY,
    )


CAMPAIGN_CHECKS = (
    _check_spend_spike_or_collapse,
    _check_budget_capped,
    _check_cvr_drop_stable_clicks,
    _check_near_zero_impressions_rank,
    _check_zero_sales_spend,
    _check_acos_swing,
)


def _check_goal_aware_tacos_margin(analysis: AnalysisResult, thresholds: dict, lens: dict):
    """Account-level TACOS-rise / margin-drop read, gated entirely by the
    lens's `tacos_margin_behavior` (see GOAL_LENSES docstring above).
    Only meaningful for a Sellerboard-style account series carrying
    `tacos`/`margin` in its metric set (`datasource.SELLERBOARD_METRICS`);
    a mock/SP-Ads account series without those metrics simply never
    trips this (the deltas come back None). Returns
    `(active_flag_or_None, suppressed_flag_or_None)`."""
    behavior = lens.get("tacos_margin_behavior", "ignore")
    if behavior == "ignore":
        return None, None

    series = analysis.account_series
    tacos_d = series.deltas.get("tacos")
    margin_d = series.deltas.get("margin")
    tacos_rise = bool(
        tacos_d and tacos_d.trailing7_pct_change is not None
        and tacos_d.trailing7_pct_change >= thresholds["tacos_rise_alert_pct"]
    )
    margin_drop = bool(
        margin_d and margin_d.trailing7_pct_change is not None
        and margin_d.trailing7_pct_change <= thresholds["margin_drop_alert_pct"]
    )
    if not tacos_rise and not margin_drop:
        return None, None

    bits = []
    if tacos_rise:
        bits.append(
            f"TACOS {_pct(tacos_d.trailing7_pct_change)} vs trailing-7 avg "
            f"({_pct(tacos_d.value)} vs {_pct(tacos_d.trailing7_avg)} avg)"
        )
    if margin_drop:
        bits.append(
            f"margin {_pct(margin_d.trailing7_pct_change)} vs trailing-7 avg "
            f"({_pct(margin_d.value)} vs {_pct(margin_d.trailing7_avg)} avg)"
        )
    message = "; ".join(bits) + "."
    threshold = (
        f">= +{_pct(thresholds['tacos_rise_alert_pct'])} TACOS or "
        f"<= {_pct(thresholds['margin_drop_alert_pct'])} margin vs trailing-7 avg"
    )

    if behavior == "expected_high":
        return None, Flag(
            severity=SEVERITY_INFO,
            metric="tacos_margin",
            threshold=threshold,
            message=message,
            likely_cause=f"Expected under the '{lens.get('label')}' goal: {lens.get('description')}",
            scope="account",
            category=CATEGORY_UNKNOWN,
            suppressed=True,
            suppressed_reason=(
                f"'{lens.get('label')}' goal treats rising TACOS / falling margin as the plan, not a problem."
            ),
        )

    # alert_on_rise: this IS the thing the goal watches for.
    return Flag(
        severity=SEVERITY_ALERT,
        metric="tacos_margin",
        threshold=threshold,
        message=message,
        likely_cause=(
            f"Under the '{lens.get('label')}' goal this is exactly the signal to act on: {lens.get('description')}"
        ),
        scope="account",
        category=CATEGORY_UNKNOWN,
    ), None


def evaluate(analysis: AnalysisResult, config: Optional[dict] = None, goal: Optional[str] = None):
    """Returns (active_flags, suppressed_flags), both lists of Flag,
    sorted alert > warn > info.

    `goal`: the brand's goal/stage string (rank-launch, scale,
    profit-maintain, defend, liquidate) from its Notion "Amazon Agent Ops
    Profiles" row. Unknown/missing goals resolve to the neutral lens
    (`resolve_goal_lens`), which leaves every threshold and severity
    exactly as before -- passing no `goal` is fully backward compatible.
    """
    lens = resolve_goal_lens(goal)
    thresholds = _thresholds(config, lens)
    active = []
    suppressed = []

    all_series = [analysis.account_series] + list(analysis.campaign_series)
    for series in all_series:
        if series.report_row is None:
            continue
        for check in CAMPAIGN_CHECKS:
            flag = check(series, thresholds, lens)
            if flag is not None:
                active.append(flag)
        # Suppression: a Rank/SKW campaign's ACOS swing is expected
        # (last-click ToS attribution) -- surface it as suppressed, never
        # as an active flag, even though the raw threshold would trigger.
        if series.category == CATEGORY_RANK and _acos_swing_would_fire(series, thresholds):
            d = series.deltas["acos"]
            suppressed.append(Flag(
                severity=SEVERITY_INFO,
                metric="acos",
                threshold=f">= +/-{_pct(thresholds['acos_swing_pct'])} vs trailing-7 avg",
                message=f"ACOS swung {_pct(d.trailing7_pct_change)} vs trailing-7 avg ({_pct(d.value)} vs {_pct(d.trailing7_avg)} avg).",
                likely_cause="Expected on a Rank/SKW campaign: last-click attribution makes top-of-search ACOS unreliable as a decision signal (strategy.md). Not flagged.",
                scope=series.label,
                category=series.category,
                suppressed=True,
                suppressed_reason="High/volatile ACOS on a Rank/SKW campaign is a known attribution artifact, not a real anomaly, per the rank-first philosophy.",
            ))

    discovery_flag = _check_discovery_share(analysis, thresholds)
    if discovery_flag is not None:
        active.append(discovery_flag)

    tacos_margin_active, tacos_margin_suppressed = _check_goal_aware_tacos_margin(analysis, thresholds, lens)
    if tacos_margin_active is not None:
        active.append(tacos_margin_active)
    if tacos_margin_suppressed is not None:
        suppressed.append(tacos_margin_suppressed)

    active.sort(key=lambda f: f.sort_key())
    suppressed.sort(key=lambda f: f.sort_key())
    return active, suppressed

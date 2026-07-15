"""crosscheck.py -- Sellerboard vs AdLabs data-quality cross-check.

Sellerboard's "Dashboard Totals" feed is whole-account truth (it's built
from Amazon's own payout/order ledger); AdLabs is ad-platform-reported and
ad-granular. On any given report day the two SHOULD roughly agree on the
figures they both cover -- ad spend, ad sales, and total sales (the input
to TACOS). When they don't, that's a data-quality signal (AdLabs' known
same-day lag/correction, a missing marketplace/profile, a mis-scoped
AdLabs filter) to flag alongside the performance read, not a silent
discrepancy the report just picks one number for.

Pure functions, no I/O, no MCP -- the skill/runtime layer fetches both
sides (Sellerboard via `datasource.SellerboardDataSource`, AdLabs via the
AdLabs MCP) and calls `cross_check()` with same-day figures from each.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DEFAULT_TOLERANCE = 0.07  # +/-7%

VERIFIED = "verified"
MISMATCH = "mismatch"
NO_DATA = "no_data"  # one or both sides missing this figure -- can't compare

_FIGURE_LABELS = {"ad_spend": "ad spend", "ad_sales": "ad sales", "total_sales": "total sales"}


@dataclass
class FigureCheck:
    figure: str  # "ad_spend" | "ad_sales" | "total_sales"
    sellerboard_value: Optional[float]
    adlabs_value: Optional[float]
    delta_abs: Optional[float]
    delta_pct: Optional[float]  # (adlabs - sellerboard) / abs(sellerboard)
    verdict: str


@dataclass
class CrossCheckResult:
    tolerance: float
    figures: list  # list[FigureCheck], one per figure checked
    headline_verdict: str  # verified | mismatch | no_data

    def mismatches(self) -> list:
        return [f for f in self.figures if f.verdict == MISMATCH]


def _pct_delta(sb_value: float, al_value: float) -> Optional[float]:
    if sb_value == 0:
        return None if al_value == 0 else 1.0  # undefined base; treat any nonzero AdLabs figure as a full mismatch
    return (al_value - sb_value) / abs(sb_value)


def _check_figure(name: str, sb_value: Optional[float], al_value: Optional[float], tolerance: float) -> FigureCheck:
    if sb_value is None or al_value is None:
        return FigureCheck(name, sb_value, al_value, None, None, NO_DATA)
    delta_abs = al_value - sb_value
    delta_pct = _pct_delta(sb_value, al_value)
    if delta_pct is None:
        verdict = NO_DATA
    elif abs(delta_pct) <= tolerance:
        verdict = VERIFIED
    else:
        verdict = MISMATCH
    return FigureCheck(name, sb_value, al_value, delta_abs, delta_pct, verdict)


def cross_check(sellerboard: dict, adlabs: dict, tolerance: float = DEFAULT_TOLERANCE) -> CrossCheckResult:
    """`sellerboard` / `adlabs`: dicts with optional keys `ad_spend`,
    `ad_sales`, `total_sales` (float or None) for the SAME report day and
    the SAME account/marketplace scope. A figure missing on either side
    is `no_data` for that figure (excluded from the headline verdict
    unless every figure is `no_data`, in which case the headline is
    `no_data` too -- "not cross-checked", not a false "verified").
    """
    figures = [
        _check_figure("ad_spend", sellerboard.get("ad_spend"), adlabs.get("ad_spend"), tolerance),
        _check_figure("ad_sales", sellerboard.get("ad_sales"), adlabs.get("ad_sales"), tolerance),
        _check_figure("total_sales", sellerboard.get("total_sales"), adlabs.get("total_sales"), tolerance),
    ]
    comparable = [f for f in figures if f.verdict != NO_DATA]
    if not comparable:
        headline = NO_DATA
    elif any(f.verdict == MISMATCH for f in comparable):
        headline = MISMATCH
    else:
        headline = VERIFIED
    return CrossCheckResult(tolerance=tolerance, figures=figures, headline_verdict=headline)


def render_verdict_line(result: CrossCheckResult) -> str:
    """One scannable, no-emoji line (markdown-safe)."""
    if result.headline_verdict == VERIFIED:
        return f"Data verified: Sellerboard and AdLabs agree within tolerance (+/-{result.tolerance * 100:.0f}%)."
    if result.headline_verdict == NO_DATA:
        return "Data verified: not cross-checked (AdLabs or Sellerboard figure missing for this day)."
    parts = []
    for f in result.mismatches():
        sb_s = f"${f.sellerboard_value:,.2f}" if f.sellerboard_value is not None else "n/a"
        al_s = f"${f.adlabs_value:,.2f}" if f.adlabs_value is not None else "n/a"
        pct_s = f"{f.delta_pct * 100:+.0f}%" if f.delta_pct is not None else "n/a"
        label = _FIGURE_LABELS.get(f.figure, f.figure)
        parts.append(f"{label} SB {sb_s} vs AdLabs {al_s} ({pct_s})")
    return "Data mismatch: " + "; ".join(parts) + "."


def render_verdict_emoji_line(result: CrossCheckResult) -> str:
    """Same line, prefixed with the scannable emoji the report should
    lead the cross-check section with (renders fine in both markdown and
    Slack mrkdwn -- Slack accepts literal unicode emoji in message text)."""
    body = render_verdict_line(result)
    if result.headline_verdict == VERIFIED:
        return f"✅ {body}"  # ✅
    if result.headline_verdict == NO_DATA:
        return f"ℹ️ {body}"  # ℹ️
    return f"⚠️ {body}"  # ⚠️

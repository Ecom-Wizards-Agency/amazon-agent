"""crosscheck.py -- Sellerboard vs ads-source data-quality cross-check.

Sellerboard's "Dashboard Totals" feed is whole-account truth (it's built
from Amazon's own payout/order ledger); the ads source (SYNQ by default;
AdLabs for the AdLabs carve-out account only) is ad-platform-reported and ad-granular. On any
given report day the two SHOULD roughly agree on the figures they both
cover -- ad spend, ad sales, and total sales (the input to TACOS). When
they don't, that's a data-quality signal (same-day lag or correction, the
2-3 day Sales and Traffic lag, a missing marketplace or client, a
mis-scoped filter, a row-capped pull) to flag alongside the performance
read, not a silent discrepancy the report just picks one number for.

Pure functions, no I/O, no MCP -- the skill/runtime layer fetches both
sides (Sellerboard via `datasource.SellerboardDataSource`, the ads source
via its MCP, converted by `tools/synq/convert.py totals` for SYNQ) and
calls `cross_check()` with same-day figures from each. `source_label`
names the ads source in every rendered line.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DEFAULT_TOLERANCE = 0.07  # +/-7%
DEFAULT_SOURCE_LABEL = "SYNQ"

VERIFIED = "verified"
MISMATCH = "mismatch"
NO_DATA = "no_data"  # one or both sides missing this figure -- can't compare

_FIGURE_LABELS = {"ad_spend": "ad spend", "ad_sales": "ad sales", "total_sales": "total sales"}


@dataclass
class FigureCheck:
    figure: str  # "ad_spend" | "ad_sales" | "total_sales"
    sellerboard_value: Optional[float]
    ads_value: Optional[float]
    delta_abs: Optional[float]
    delta_pct: Optional[float]  # (ads - sellerboard) / abs(sellerboard)
    verdict: str

    @property
    def adlabs_value(self) -> Optional[float]:
        """Legacy alias for `ads_value` (pre-SYNQ callers)."""
        return self.ads_value


@dataclass
class CrossCheckResult:
    tolerance: float
    figures: list  # list[FigureCheck], one per figure checked
    headline_verdict: str  # verified | mismatch | no_data
    source_label: str = DEFAULT_SOURCE_LABEL  # ads source named in rendered lines

    def mismatches(self) -> list:
        return [f for f in self.figures if f.verdict == MISMATCH]


def _pct_delta(sb_value: float, al_value: float) -> Optional[float]:
    if sb_value == 0:
        return None if al_value == 0 else 1.0  # undefined base; treat any nonzero ads-source figure as a full mismatch
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


def cross_check(
    sellerboard: dict,
    ads: dict,
    tolerance: float = DEFAULT_TOLERANCE,
    source_label: str = DEFAULT_SOURCE_LABEL,
) -> CrossCheckResult:
    """`sellerboard` / `ads`: dicts with optional keys `ad_spend`,
    `ad_sales`, `total_sales` (float or None) for the SAME report day and
    the SAME account/marketplace scope. A figure missing on either side
    is `no_data` for that figure (excluded from the headline verdict
    unless every figure is `no_data`, in which case the headline is
    `no_data` too -- "not cross-checked", not a false "verified").
    `source_label` names the ads source ("SYNQ", or "AdLabs" for
    the AdLabs carve-out account) in the rendered verdict line.
    """
    figures = [
        _check_figure("ad_spend", sellerboard.get("ad_spend"), ads.get("ad_spend"), tolerance),
        _check_figure("ad_sales", sellerboard.get("ad_sales"), ads.get("ad_sales"), tolerance),
        _check_figure("total_sales", sellerboard.get("total_sales"), ads.get("total_sales"), tolerance),
    ]
    comparable = [f for f in figures if f.verdict != NO_DATA]
    if not comparable:
        headline = NO_DATA
    elif any(f.verdict == MISMATCH for f in comparable):
        headline = MISMATCH
    else:
        headline = VERIFIED
    return CrossCheckResult(
        tolerance=tolerance, figures=figures, headline_verdict=headline, source_label=source_label
    )


def render_verdict_line(result: CrossCheckResult) -> str:
    """One scannable, no-emoji line (markdown-safe)."""
    src = result.source_label or DEFAULT_SOURCE_LABEL
    if result.headline_verdict == VERIFIED:
        return f"Data verified: Sellerboard and {src} agree within tolerance (+/-{result.tolerance * 100:.0f}%)."
    if result.headline_verdict == NO_DATA:
        return f"Data verified: not cross-checked ({src} or Sellerboard figure missing for this day)."
    parts = []
    for f in result.mismatches():
        sb_s = f"${f.sellerboard_value:,.2f}" if f.sellerboard_value is not None else "n/a"
        al_s = f"${f.ads_value:,.2f}" if f.ads_value is not None else "n/a"
        pct_s = f"{f.delta_pct * 100:+.0f}%" if f.delta_pct is not None else "n/a"
        label = _FIGURE_LABELS.get(f.figure, f.figure)
        parts.append(f"{label} SB {sb_s} vs {src} {al_s} ({pct_s})")
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

"""datasource.py -- pluggable data-source layer for amazon-ads-monitor.

Returns per-account, per-day rows (account-level and campaign-level) with
the raw metrics (impressions, clicks, spend, sales, orders) plus a shared
helper to compute derived metrics (CTR, CVR, CPC, ACOS, ROAS, TACOS).

No MCP calls live here. This module is pure Python (stdlib + requests) so
it can be unit-tested without any live Amazon account, Slack, or Notion
access. The runtime/skill layer decides which adapter to instantiate and
does any MCP-backed enrichment (Notion, Slack, firecrawl, AdLabs)
separately.

Adapters:
- MockDataSource        -- fully implemented, deterministic synthetic data.
- SellerboardDataSource -- PRIMARY real adapter (as of 2026-07-14). Parses
                           the Sellerboard "Dashboard Totals" CSV feed
                           (whole-account truth: total sales, ad spend, ad
                           sales, real ACOS, margin, etc). See its
                           docstring and `_local/ads-monitor/
                           SELLERBOARD-FORMAT.md`. AdLabs is the
                           ad-granular cross-check source (see
                           `crosscheck.py`), wired at the skill layer via
                           the AdLabs MCP -- not implemented as a
                           `DataSource` adapter here because it needs a
                           live chat-session/entity-data call shape that
                           doesn't fit a simple "one CSV in, rows out"
                           parse (see `AdLabsDataSource` below).
- SPAdsApiDataSource    -- SECONDARY real adapter (Amazon Ads API v3
                           reporting), demoted from primary 2026-07-14 in
                           favor of SellerboardDataSource. Built from
                           Amazon's published docs, not live-tested. Still
                           useful for campaign-level detail if Sellerboard
                           /AdLabs access isn't available for an account.
                           See its docstring.
- AdLabsDataSource, MarketplaceAdProsDataSource -- documented stubs only.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Strategy categories (see _local/ads-strategy/strategy.md "four categories").
# Plain strings, not an enum, so an adapter can pass through an "Unknown"
# value without import-time coupling to a closed set.

CATEGORY_RANK = "Rank"
CATEGORY_DISCOVERY = "Discovery"
CATEGORY_PROFIT = "Profit"
CATEGORY_SHIELD = "Shield"
CATEGORY_UNKNOWN = "Unknown"
STRATEGY_CATEGORIES = (CATEGORY_RANK, CATEGORY_DISCOVERY, CATEGORY_PROFIT, CATEGORY_SHIELD)


def classify_campaign_category(campaign_name: str) -> str:
    """Best-effort category classification from campaign name tokens.

    Matches the EW naming convention trigger words used by
    tools/amazon-campaign-builder (Rank/SKW, Discovery Auto-BMM-Phrase,
    Halo=Profit, Shield). Falls back to "Unknown" so downstream flags never
    silently assume a category they have no evidence for. Real accounts
    that don't follow this convention should carry an explicit override in
    config (see config.TEMPLATE.json `campaign_category_overrides`).
    """
    if not campaign_name:
        return CATEGORY_UNKNOWN
    name = campaign_name.lower()
    if "shield" in name:
        return CATEGORY_SHIELD
    if "skw" in name or "rank" in name:
        return CATEGORY_RANK
    if "halo" in name or "profit" in name:
        return CATEGORY_PROFIT
    if any(tok in name for tok in ("auto", "bmm", "phrase", "discovery", "broad")):
        return CATEGORY_DISCOVERY
    return CATEGORY_UNKNOWN


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if not numerator and numerator != 0:
        return None
    if not denominator:
        return None
    return numerator / denominator


@dataclass
class DailyRow:
    """One account-level or campaign-level daily performance row."""

    account: str
    date: dt.date
    level: str  # "account" | "campaign"
    impressions: int
    clicks: int
    spend: float
    sales: float
    orders: int
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    category: str = CATEGORY_UNKNOWN
    budget: Optional[float] = None
    budget_capped: bool = False
    total_sales: Optional[float] = None  # brand total (organic+ad) sales that day, for TACOS

    # -- Sellerboard-only fields (None for SP-Ads/mock rows) --------------
    # `spend` = ad_spend (SponsoredProducts+Display+Brands+BrandsVideo, abs'd)
    # and `sales` = ad_sales (SalesPPC) for a Sellerboard row, same as the
    # SP-Ads mapping, so `acos`/`roas`/`tacos` above work unchanged. These
    # extra fields carry the account-total figures Sellerboard reports
    # that SP Ads reporting doesn't (see SELLERBOARD-FORMAT.md).
    ad_sales_sp: Optional[float] = None
    ad_sales_sd: Optional[float] = None
    real_acos: Optional[float] = None  # Sellerboard's own "Real ACOS" column, as a fraction (0-1)
    units_organic: Optional[int] = None
    units_ppc: Optional[int] = None
    refunds: Optional[int] = None
    gross_profit: Optional[float] = None
    net_profit: Optional[float] = None
    margin: Optional[float] = None  # fraction (0-1)
    sessions: Optional[int] = None
    unit_session_pct: Optional[float] = None  # fraction (0-1)

    # -- derived metrics: computed on demand, never stored/stale ----------
    @property
    def ctr(self) -> Optional[float]:
        return _safe_div(self.clicks, self.impressions)

    @property
    def cvr(self) -> Optional[float]:
        return _safe_div(self.orders, self.clicks)

    @property
    def cpc(self) -> Optional[float]:
        return _safe_div(self.spend, self.clicks)

    @property
    def acos(self) -> Optional[float]:
        return _safe_div(self.spend, self.sales)

    @property
    def roas(self) -> Optional[float]:
        return _safe_div(self.sales, self.spend)

    @property
    def tacos(self) -> Optional[float]:
        if not self.total_sales:
            return None
        return _safe_div(self.spend, self.total_sales)


# Order matters only for display; keep raw metrics before derived ones.
METRICS = ("impressions", "clicks", "spend", "sales", "orders", "ctr", "cvr", "cpc", "acos", "roas", "tacos")

# Metrics analyzed for a Sellerboard account-level series: no impressions/
# clicks/CTR/CVR/CPC (Sellerboard's "Dashboard Totals" feed is account
# totals, not click-level), plus the Sellerboard-only fields above. Passed
# to `analyze.analyze_account(..., metrics=SELLERBOARD_METRICS)` so the
# day-over-day / trailing-7-avg delta math runs over the right metric set.
SELLERBOARD_METRICS = (
    "total_sales", "sales", "spend", "acos", "tacos", "real_acos", "orders",
    "units_organic", "units_ppc", "refunds", "gross_profit", "net_profit",
    "margin", "sessions", "unit_session_pct", "ad_sales_sp", "ad_sales_sd",
)


def metric_value(row: Optional[DailyRow], metric: str) -> Optional[float]:
    if row is None:
        return None
    return getattr(row, metric)


class DataSource(ABC):
    """Interface every adapter implements."""

    @abstractmethod
    def list_accounts(self) -> list:
        ...

    @abstractmethod
    def get_account_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        """One row per date (inclusive of start and end) at the account
        (all-campaigns) level."""

    @abstractmethod
    def get_campaign_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        """One row per (date, campaign) for the same window."""


# ---------------------------------------------------------------------------
# Errors shared by real adapters.

class SPAdsApiError(RuntimeError):
    """Non-timeout failure returned by the Amazon Ads API."""


class SPAdsApiTimeout(RuntimeError):
    """The report did not reach COMPLETED within the polling budget."""


class SPAdsApiConfigError(RuntimeError):
    """Config is missing a value SPAdsApiDataSource needs."""


# ---------------------------------------------------------------------------
# MockDataSource -- fully implemented, deterministic synthetic data.

import hashlib
import random as _random


def _seeded_random(*parts: str) -> _random.Random:
    key = "|".join(parts).encode("utf-8")
    seed = int(hashlib.sha256(key).hexdigest(), 16) % (2**32)
    return _random.Random(seed)


@dataclass
class _MockCampaignSpec:
    campaign_id: str
    campaign_name: str
    category: str
    base_impressions: float
    base_ctr: float
    base_cvr: float
    base_cpc: float
    base_budget: Optional[float] = None
    # Scenario knobs, all keyed off "days before report_date" (0 = report date).
    impression_collapse_days: tuple = ()  # near-zero impressions on these day-indices
    spend_spike_days: tuple = ()  # multiply spend by spike_multiplier
    spike_multiplier: float = 3.0
    cvr_drop_days: tuple = ()  # cvr collapses, clicks held stable
    cvr_drop_to: float = 0.02
    zero_orders_always: bool = False
    budget_capped_days: tuple = ()
    acos_swing_days: tuple = ()  # deterministic ACOS spike on these day-indices
    acos_swing_cvr_factor: float = 0.35  # multiply cvr by this on those days (spikes ACOS up)


_MOCK_ACCOUNTS = {
    "acme-us": [
        _MockCampaignSpec(
            campaign_id="10001",
            campaign_name="Rank | SP | Exact | bamboo cutting board | ACME-BCB | EW",
            category=CATEGORY_RANK,
            base_impressions=1200,
            base_ctr=0.045,
            base_cvr=0.10,
            base_cpc=1.10,
            base_budget=60.0,
            budget_capped_days=(0, 1, 2),
            acos_swing_days=(0,),
            acos_swing_cvr_factor=0.3,
        ),
        _MockCampaignSpec(
            campaign_id="10002",
            campaign_name="Rank | SP | Exact | bamboo salad bowl | ACME-BSB | EW",
            category=CATEGORY_RANK,
            base_impressions=800,
            base_ctr=0.04,
            base_cvr=0.09,
            base_cpc=0.95,
            base_budget=40.0,
            impression_collapse_days=(0,),
        ),
        _MockCampaignSpec(
            campaign_id="10003",
            campaign_name="Discovery Auto | SP | Auto | close-loose-subs-comp | ACME | EW",
            category=CATEGORY_DISCOVERY,
            base_impressions=3000,
            base_ctr=0.02,
            base_cvr=0.05,
            base_cpc=0.55,
            spend_spike_days=(0,),
            spike_multiplier=2.6,
        ),
        _MockCampaignSpec(
            campaign_id="10004",
            campaign_name="Discovery BMM | SP | Broad | cutting board | ACME | EW",
            category=CATEGORY_DISCOVERY,
            base_impressions=1800,
            base_ctr=0.018,
            base_cvr=0.045,
            base_cpc=0.60,
            spend_spike_days=(0,),
            spike_multiplier=2.2,
        ),
        _MockCampaignSpec(
            campaign_id="10005",
            campaign_name="Discovery Phrase | SP | Phrase | wood utensils | ACME | EW",
            category=CATEGORY_DISCOVERY,
            base_impressions=900,
            base_ctr=0.02,
            base_cvr=0.05,
            base_cpc=0.58,
        ),
        _MockCampaignSpec(
            campaign_id="10006",
            campaign_name="Halo | SP | Exact | organic bamboo kitchenware long tail | ACME | EW",
            category=CATEGORY_PROFIT,
            base_impressions=600,
            base_ctr=0.05,
            base_cvr=0.12,
            base_cpc=0.70,
        ),
        _MockCampaignSpec(
            campaign_id="10007",
            campaign_name="Halo | SP | Exact | bamboo cheese board long tail | ACME | EW",
            category=CATEGORY_PROFIT,
            base_impressions=700,
            base_ctr=0.05,
            base_cvr=0.08,
            base_cpc=0.65,
            cvr_drop_days=(0,),
            cvr_drop_to=0.015,
        ),
        _MockCampaignSpec(
            campaign_id="10008",
            campaign_name="Shield | SP | Exact | acme brand defense | ACME | EW",
            category=CATEGORY_SHIELD,
            base_impressions=500,
            base_ctr=0.10,
            base_cvr=0.20,
            base_cpc=0.35,
        ),
        _MockCampaignSpec(
            campaign_id="10009",
            campaign_name="Discovery Auto | SP | Auto | new arrivals scavenger | ACME | EW",
            category=CATEGORY_DISCOVERY,
            base_impressions=1800,
            base_ctr=0.016,
            base_cvr=0.0,
            base_cpc=2.20,
            zero_orders_always=True,
        ),
    ],
    "globex-us": [
        _MockCampaignSpec(
            campaign_id="20001",
            campaign_name="Rank | SP | Exact | ceramic knife set | GLOBEX-CKS | EW",
            category=CATEGORY_RANK,
            base_impressions=950,
            base_ctr=0.05,
            base_cvr=0.11,
            base_cpc=1.20,
            base_budget=55.0,
        ),
        _MockCampaignSpec(
            campaign_id="20002",
            campaign_name="Discovery Auto | SP | Auto | close-loose-subs-comp | GLOBEX | EW",
            category=CATEGORY_DISCOVERY,
            base_impressions=1600,
            base_ctr=0.02,
            base_cvr=0.06,
            base_cpc=0.50,
        ),
        _MockCampaignSpec(
            campaign_id="20003",
            campaign_name="Halo | SP | Exact | kitchen knife long tail | GLOBEX | EW",
            category=CATEGORY_PROFIT,
            base_impressions=500,
            base_ctr=0.05,
            base_cvr=0.13,
            base_cpc=0.60,
        ),
        _MockCampaignSpec(
            campaign_id="20004",
            campaign_name="Shield | SP | Exact | globex brand defense | GLOBEX | EW",
            category=CATEGORY_SHIELD,
            base_impressions=350,
            base_ctr=0.11,
            base_cvr=0.22,
            base_cpc=0.30,
        ),
    ],
}


class MockDataSource(DataSource):
    """Fully implemented synthetic adapter for testing without credentials.

    Generates plausible daily data for the sample accounts in
    `_MOCK_ACCOUNTS` over any requested [start, end] window, deterministic
    per (account, campaign, date) via a seeded RNG (same inputs -> same
    output, useful for repeatable demo runs and CI).

    A handful of campaigns carry deliberate, scripted anomalies anchored to
    "days before end date" (0 = the last requested day, i.e. the report
    date whatever it is): a near-zero-impression Rank campaign, a Discovery
    spend spike (crosses the ~20% discovery-share threshold), a CVR
    collapse with stable clicks, a persistently zero-order Discovery
    campaign, and a budget-capped Rank campaign -- so `--source mock`
    produces a report with real flags to look at, not just flat lines.
    One Rank/SKW campaign (10001) also runs a wide day-to-day ACOS swing
    on purpose, to prove the philosophy-aware ACOS-swing suppression in
    flags.py actually suppresses it instead of raising a false alarm.
    """

    def list_accounts(self) -> list:
        return list(_MOCK_ACCOUNTS.keys())

    def _specs(self, account: str) -> list:
        if account not in _MOCK_ACCOUNTS:
            raise KeyError(f"unknown mock account '{account}'; available: {list(_MOCK_ACCOUNTS)}")
        return _MOCK_ACCOUNTS[account]

    def _dates(self, start: dt.date, end: dt.date) -> list:
        n = (end - start).days
        return [start + dt.timedelta(days=i) for i in range(n + 1)]

    def _gen_row(self, account: str, spec: _MockCampaignSpec, date: dt.date, day_index: int) -> DailyRow:
        rng = _seeded_random(account, spec.campaign_id, date.isoformat())
        impressions = max(0, spec.base_impressions * rng.uniform(0.85, 1.15))
        ctr = max(0.0005, spec.base_ctr * rng.uniform(0.8, 1.2))
        cvr = max(0.0, spec.base_cvr * rng.uniform(0.7, 1.3))
        cpc = max(0.05, spec.base_cpc * rng.uniform(0.85, 1.15))

        if day_index in spec.acos_swing_days:
            # Deliberate, deterministic ACOS spike on the report date:
            # expected per strategy.md on a Rank/SKW campaign (last-click
            # ToS attribution), must be suppressed downstream, never
            # alerted on. Kept deterministic (not per-day random) so it
            # reliably crosses the swing threshold regardless of which
            # report date is requested.
            cvr = max(0.005, cvr * spec.acos_swing_cvr_factor)

        if day_index in spec.impression_collapse_days:
            impressions *= 0.02  # near-zero: suppressed/outbid/paused-by-mistake

        clicks = impressions * ctr
        if day_index in spec.cvr_drop_days:
            cvr = spec.cvr_drop_to

        orders = 0 if spec.zero_orders_always else clicks * cvr
        spend = clicks * cpc
        if day_index in spec.spend_spike_days:
            spend *= spec.spike_multiplier

        aov = 28.0 * rng.uniform(0.9, 1.1)
        sales = 0.0 if spec.zero_orders_always else orders * aov

        budget_capped = day_index in spec.budget_capped_days
        budget = spec.base_budget
        if budget_capped and budget:
            spend = min(spend, budget) if spend < budget else budget * rng.uniform(0.97, 1.0)

        return DailyRow(
            account=account,
            date=date,
            level="campaign",
            impressions=int(round(impressions)),
            clicks=int(round(clicks)),
            spend=round(spend, 2),
            sales=round(sales, 2),
            orders=int(round(orders)),
            campaign_id=spec.campaign_id,
            campaign_name=spec.campaign_name,
            category=spec.category,
            budget=budget,
            budget_capped=budget_capped,
        )

    def get_campaign_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        specs = self._specs(account)
        rows = []
        dates = self._dates(start, end)
        for date in dates:
            day_index = (end - date).days
            for spec in specs:
                rows.append(self._gen_row(account, spec, date, day_index))
        return rows

    def get_account_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        campaign_rows = self.get_campaign_daily(account, start, end)
        by_date = {}
        for r in campaign_rows:
            agg = by_date.setdefault(r.date, {"impressions": 0, "clicks": 0, "spend": 0.0, "sales": 0.0, "orders": 0})
            agg["impressions"] += r.impressions
            agg["clicks"] += r.clicks
            agg["spend"] += r.spend
            agg["sales"] += r.sales
            agg["orders"] += r.orders
        rows = []
        for date in sorted(by_date):
            agg = by_date[date]
            rng = _seeded_random(account, "total-sales", date.isoformat())
            # PPC sales ~25-32% of total revenue, per strategy.md's 20-40% band.
            ppc_share = rng.uniform(0.25, 0.32)
            total_sales = agg["sales"] / ppc_share if ppc_share else None
            rows.append(DailyRow(
                account=account,
                date=date,
                level="account",
                impressions=agg["impressions"],
                clicks=agg["clicks"],
                spend=round(agg["spend"], 2),
                sales=round(agg["sales"], 2),
                orders=agg["orders"],
                total_sales=round(total_sales, 2) if total_sales else None,
            ))
        return rows


# ---------------------------------------------------------------------------
# SellerboardDataSource -- PRIMARY real adapter (Sellerboard "Dashboard
# Totals" CSV feed).

class SellerboardCSVError(RuntimeError):
    """Raised when a non-blank Sellerboard CSV can't be parsed at all
    (e.g. no recognizable header). A genuinely blank/empty feed is NOT an
    error -- `parse_sellerboard_csv` returns `[]` for that, which signals
    the caller to fall back to AdLabs for the account, per
    SELLERBOARD-FORMAT.md."""


_SB_DATE_FMT = "%d/%m/%Y"

# Column names exactly as Sellerboard emits them (quoted in the CSV; the
# csv module strips the quotes). Never reference these by position --
# column SETS differ between accounts (some carry extra fee columns
# that others don't).
_SB_AD_SPEND_COLUMNS = ("SponsoredProducts", "SponsoredDisplay", "SponsoredBrands", "SponsoredBrandsVideo")


def _sb_detect_dialect(header_line: str):
    """Sniff comma vs semicolon from the header line. Falls back to a
    simple character-count heuristic if the stdlib Sniffer can't decide
    (e.g. a header with no delimiter at all -- a single-column CSV)."""
    try:
        return csv.Sniffer().sniff(header_line, delimiters=",;")
    except csv.Error:
        pass

    class _Fallback(csv.excel):
        delimiter = ";" if header_line.count(";") > header_line.count(",") else ","

    return _Fallback


def _sb_opt_float(raw: dict, key: str) -> Optional[float]:
    v = raw.get(key)
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sb_float(raw: dict, key: str, default: float = 0.0) -> float:
    v = _sb_opt_float(raw, key)
    return default if v is None else v


def _sb_opt_int(raw: dict, key: str) -> Optional[int]:
    v = _sb_opt_float(raw, key)
    return None if v is None else int(round(v))


def _sb_int(raw: dict, key: str, default: int = 0) -> int:
    v = _sb_opt_int(raw, key)
    return default if v is None else v


def _sb_opt_fraction(raw: dict, key: str) -> Optional[float]:
    """Sellerboard reports percentages as plain numbers (e.g. "19.96"
    means 19.96%); convert to the toolkit's 0-1 fraction convention so
    report.py's `_PERCENT` formatting (`value * 100`) matches every other
    percent metric (ACOS, TACOS, CTR, CVR)."""
    v = _sb_opt_float(raw, key)
    return None if v is None else v / 100.0


def parse_sellerboard_csv(text: Optional[str], account: str) -> list:
    """Parse one Sellerboard "Dashboard Totals" CSV (comma OR
    semicolon-delimited, sniffed from the header; column SET varies by
    account, always mapped by name) into account-level `DailyRow`s.

    Returns `[]` for a blank/empty/header-only feed -- NOT an error. Per
    SELLERBOARD-FORMAT.md, a just-requested Sellerboard report can come
    back blank; the caller (this toolkit's `SellerboardDataSource`, or
    the skill layer) should treat an empty result as "fall back to
    AdLabs for this brand/day", not crash.

    Dates are DD/MM/YYYY. Ad-spend columns (`SponsoredProducts`,
    `SponsoredDisplay`, `SponsoredBrands`, `SponsoredBrandsVideo`) are
    NEGATIVE in the source CSV; this function takes `abs()` before
    summing them into `ad_spend`.
    """
    if not text or not text.strip():
        return []
    stripped = text.strip()
    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []  # header-only or otherwise no data rows: blank feed

    dialect = _sb_detect_dialect(lines[0])
    reader = csv.DictReader(io.StringIO(stripped), dialect=dialect)
    if not reader.fieldnames or "Date" not in [f.strip() for f in reader.fieldnames]:
        raise SellerboardCSVError(
            f"Sellerboard CSV for '{account}' has no 'Date' column in its header "
            f"(found: {reader.fieldnames}); can't map by column name."
        )

    rows = []
    for raw_row in reader:
        raw = {(k or "").strip(): v for k, v in raw_row.items() if k is not None}
        date_raw = (raw.get("Date") or "").strip()
        if not date_raw:
            continue
        try:
            date = dt.datetime.strptime(date_raw, _SB_DATE_FMT).date()
        except ValueError:
            continue  # unparseable date row -- skip rather than crash the whole feed

        sales_organic = _sb_float(raw, "SalesOrganic")
        sales_ppc = _sb_float(raw, "SalesPPC")
        total_sales = sales_organic + sales_ppc
        ad_spend = sum(abs(_sb_float(raw, col)) for col in _SB_AD_SPEND_COLUMNS)

        rows.append(DailyRow(
            account=account,
            date=date,
            level="account",
            impressions=0,
            clicks=0,
            spend=round(ad_spend, 2),
            sales=round(sales_ppc, 2),
            orders=_sb_int(raw, "Orders"),
            total_sales=round(total_sales, 2) if total_sales else None,
            ad_sales_sp=_sb_opt_float(raw, "SalesSponsoredProducts"),
            ad_sales_sd=_sb_opt_float(raw, "SalesSponsoredDisplay"),
            real_acos=_sb_opt_fraction(raw, "Real ACOS"),
            units_organic=_sb_opt_int(raw, "UnitsOrganic"),
            units_ppc=_sb_opt_int(raw, "UnitsPPC"),
            refunds=_sb_opt_int(raw, "Refunds"),
            gross_profit=_sb_opt_float(raw, "GrossProfit"),
            net_profit=_sb_opt_float(raw, "NetProfit"),
            margin=_sb_opt_fraction(raw, "Margin"),
            sessions=_sb_opt_int(raw, "Sessions"),
            unit_session_pct=_sb_opt_fraction(raw, "Unit Session Percentage"),
        ))
    return rows


class SellerboardDataSource(DataSource):
    """PRIMARY real adapter: Sellerboard "Dashboard Totals" CSV feed.

    Unlike `SPAdsApiDataSource`, this adapter takes its raw CSV text (or a
    file path) directly -- it makes NO network calls itself. Per
    SELLERBOARD-FORMAT.md, the runtime/skill layer fetches each brand's
    feed URL(s) via `firecrawl_scrape` (formats: ["markdown"], which
    returns the raw CSV text for this endpoint) and hands the text to
    this adapter with `add_feed`/`from_texts`/`from_paths`. This keeps
    the toolkit MCP-free and unit-testable (see selftest.py).

    Sellerboard gives whole-account totals only (no campaign/keyword
    breakdown) -- `get_campaign_daily` always returns `[]`. Pair with
    AdLabs (via the AdLabs MCP at the skill layer) for campaign-level
    detail and the spend/sales cross-check (`crosscheck.py`).

    A brand can have more than one feed (a ~30-day window and a ~7-day
    window); pass all of them via repeated `add_feed` calls for the same
    account. `get_account_daily` merges them by date, keeping the first
    feed's row when two feeds overlap on the same date (call `add_feed`
    with the feed you want prioritized first -- typically the shorter/
    fresher window).
    """

    def __init__(self, csv_texts_by_account: Optional[dict] = None):
        self._raw: dict = {}
        for account, texts in (csv_texts_by_account or {}).items():
            for text in texts:
                self.add_feed(account, text)

    @classmethod
    def from_paths(cls, paths_by_account: dict) -> "SellerboardDataSource":
        ds = cls()
        for account, paths in paths_by_account.items():
            for path in paths:
                with open(path, encoding="utf-8-sig") as fh:
                    ds.add_feed(account, fh.read())
        return ds

    def add_feed(self, account: str, csv_text: Optional[str]) -> None:
        self._raw.setdefault(account, []).append(csv_text or "")

    def list_accounts(self) -> list:
        return list(self._raw)

    def get_account_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        by_date: dict = {}
        for text in self._raw.get(account, []):
            for row in parse_sellerboard_csv(text, account):
                if row.date in by_date:
                    continue  # earlier feed in the list wins on overlap
                by_date[row.date] = row
        return sorted((r for d, r in by_date.items() if start <= d <= end), key=lambda r: r.date)

    def get_campaign_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        # Sellerboard's Dashboard Totals feed is account-level only. Real
        # campaign detail comes from AdLabs at the skill layer.
        return []


# ---------------------------------------------------------------------------
# SPAdsApiDataSource -- SECONDARY real adapter (Amazon Ads API v3 reporting).

class _RequestsUnavailable:
    def __getattr__(self, item):
        raise SPAdsApiConfigError(
            "The 'requests' package is required for SPAdsApiDataSource "
            "(pip install requests). Not needed for --source mock."
        )


try:
    import requests as _requests
except ImportError:  # pragma: no cover - exercised only when requests is missing
    _requests = _RequestsUnavailable()


class SPAdsApiDataSource(DataSource):
    """PRIMARY real adapter: Amazon Ads API v3 reporting.

    Flow (async report create -> poll status -> download GZIP_JSON ->
    parse), matching Amazon's published v3 reporting docs
    (https://advertising.amazon.com/API/docs/en-us/guides/reporting/v3/
    get-started, .../report-types) as fetched 2026-07-13:

    1. POST {base}/reporting/reports with headers `Amazon-Ads-ClientId`,
       `Authorization: Bearer <access_token>`, `Amazon-Advertising-API-Scope:
       <profile_id>`, `Content-Type: application/vnd.createasyncreportrequest.v3+json`,
       body `{name, startDate, endDate, configuration: {adProduct:
       "SPONSORED_PRODUCTS", groupBy, columns, reportTypeId: "spCampaigns",
       timeUnit: "DAILY", format: "GZIP_JSON"}}` -> returns `reportId`.
    2. GET {base}/reporting/reports/{reportId} repeatedly until
       `status` is `COMPLETED` (or `FAILURE`/`CANCELLED`) -> returns `url`
       (an S3 link) once completed.
    3. GET that `url`, gunzip, `json.loads` -> list of flat dict rows keyed
       by the requested `columns` (e.g. `campaignId`, `impressions`,
       `clicks`, `cost`, `sales7d`, `purchases7d`, `date`).

    Access tokens come from a Login-With-Amazon (LWA) refresh-token
    exchange (`POST https://api.amazon.com/auth/o2/token`), valid ~60
    minutes; cached and refreshed here.

    NOT LIVE-TESTED. No real client_id/client_secret/refresh_token/
    profile_id exists in this workspace yet (see
    _local/ads-monitor/README.md for the credential checklist). Every
    method that talks to Amazon is marked "NEEDS LIVE-CREDENTIAL TEST" in
    its docstring below; the request/response shapes follow Amazon's
    documented contract exactly and are exercised in selftest.py against
    an injected fake `session` (no network), which proves the internal
    logic (auth header assembly, gzip/json parsing, aggregation, category
    classification) but cannot prove Amazon's live behavior (real
    throttling, real column availability, real report latency).

    Known gaps that need a live account to close (documented, not
    silently assumed):
    - Campaign metadata (name) join: v3 reporting only returns dimension
      IDs. Amazon's own docs say to call the Exports API separately and
      join by `campaignId`. `_fetch_campaign_metadata` is a stub that
      returns `{}` until that's wired up; until then `campaign_name`
      falls back to the raw ID and `classify_campaign_category` degrades
      to "Unknown" (harmless, but strategy-aware flags that need a
      category, like the Rank ACOS-swing suppression, won't fire for
      unclassified campaigns -- see flags.py).
    - Budget / budget-capped state: not part of this reporting report;
      needs a separate Budget Usage or Campaigns-list call. Left `None`/
      `False` here; real accounts should backfill via config overrides
      or a follow-up toolkit extension.
    - Report generation latency: Amazon states this can take up to three
      hours. `_poll_report`'s bounded wait loop is fine for a same-run
      poll on typical SP daily volume, but a production cron should
      split "request" and "fetch" into two separate scheduled runs
      instead of blocking for hours.
    """

    LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
    REGION_ENDPOINTS = {
        "NA": "https://advertising-api.amazon.com",
        "EU": "https://advertising-api-eu.amazon.com",
        "FE": "https://advertising-api-fe.amazon.com",
    }
    REPORT_TYPE_ID = "spCampaigns"
    CONTENT_TYPE = "application/vnd.createasyncreportrequest.v3+json"

    def __init__(self, config: dict, session=None, sleep=time.sleep):
        self.config = config
        try:
            self.lwa = config["lwa"]
            self.accounts_cfg = config["accounts"]
        except KeyError as exc:
            raise SPAdsApiConfigError(f"config missing required key: {exc}") from exc
        self.region = config.get("region", "NA")
        self.attribution_window = config.get("attribution_window", "7d")
        self.session = session or _requests.Session()
        self._sleep = sleep
        self._token = None
        self._token_expires_at = 0.0
        self._name_cache = {}

    # -- config lookups -----------------------------------------------
    def list_accounts(self) -> list:
        return [a["account"] for a in self.accounts_cfg]

    def _account_cfg(self, account: str) -> dict:
        for a in self.accounts_cfg:
            if a["account"] == account:
                return a
        raise SPAdsApiConfigError(f"account '{account}' not found in config.accounts[]")

    def _base_url(self) -> str:
        return self.REGION_ENDPOINTS.get(self.region, self.REGION_ENDPOINTS["NA"])

    # -- auth ------------------------------------------------------------
    def _get_access_token(self) -> str:
        """LWA refresh-token -> access-token exchange. NEEDS LIVE-CREDENTIAL TEST."""
        if self._token and time.time() < self._token_expires_at:
            return self._token
        resp = self.session.post(self.LWA_TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": self.lwa["refresh_token"],
            "client_id": self.lwa["client_id"],
            "client_secret": self.lwa["client_secret"],
        })
        if resp.status_code != 200:
            raise SPAdsApiError(f"LWA token refresh failed ({resp.status_code}): {resp.text}")
        body = resp.json()
        self._token = body["access_token"]
        self._token_expires_at = time.time() + body.get("expires_in", 3600) - 60
        return self._token

    def _headers(self, profile_id) -> dict:
        return {
            "Amazon-Ads-ClientId": self.lwa["client_id"],
            "Authorization": f"Bearer {self._get_access_token()}",
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Content-Type": self.CONTENT_TYPE,
        }

    # -- reporting v3 flow -------------------------------------------------
    def _columns_for(self, group_by: str) -> list:
        base = ["impressions", "clicks", "cost", "date"]
        sales_col = f"sales{self.attribution_window}"
        purchases_col = f"purchases{self.attribution_window}"
        if group_by == "campaign":
            return base + ["campaignId", sales_col, purchases_col]
        if group_by == "adGroup":
            return base + ["campaignId", "adGroupId", sales_col, purchases_col]
        raise ValueError(f"unsupported groupBy '{group_by}'")

    def _create_report(self, profile_id, start: dt.date, end: dt.date, group_by: str) -> str:
        """POST /reporting/reports. NEEDS LIVE-CREDENTIAL TEST (real
        acceptance of this body; duplicate-request 425 handling; real
        rate limits -- see Amazon's retry-with-backoff guidance)."""
        body = {
            "name": f"amazon-ads-monitor {group_by} {start.isoformat()}..{end.isoformat()}",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "configuration": {
                "adProduct": "SPONSORED_PRODUCTS",
                "groupBy": [group_by],
                "columns": self._columns_for(group_by),
                "reportTypeId": self.REPORT_TYPE_ID,
                "timeUnit": "DAILY",
                "format": "GZIP_JSON",
            },
        }
        url = f"{self._base_url()}/reporting/reports"
        resp = self.session.post(url, json=body, headers=self._headers(profile_id))
        data = resp.json()
        if resp.status_code not in (200, 202):
            raise SPAdsApiError(f"report create failed ({resp.status_code}): {data}")
        return data["reportId"]

    def _poll_report(self, profile_id, report_id: str, max_wait_seconds: int = 180, poll_interval: int = 10) -> dict:
        """GET /reporting/reports/{id} until COMPLETED/FAILURE.
        NEEDS LIVE-CREDENTIAL TEST. Amazon's docs note report generation
        can take up to three hours; this bounded loop suits small/fresh
        daily windows. For production, split into a separate "request"
        cron and "fetch" cron rather than blocking a single run for hours.
        """
        url = f"{self._base_url()}/reporting/reports/{report_id}"
        waited = 0
        status = None
        while waited <= max_wait_seconds:
            resp = self.session.get(url, headers=self._headers(profile_id))
            data = resp.json()
            status = data.get("status")
            if status == "COMPLETED":
                return data
            if status in ("FAILURE", "CANCELLED"):
                raise SPAdsApiError(f"report {report_id} failed: {data.get('failureReason')}")
            self._sleep(poll_interval)
            waited += poll_interval
        raise SPAdsApiTimeout(f"report {report_id} not ready after {max_wait_seconds}s (status={status})")

    def _download_report(self, url: str) -> list:
        """GET the S3 url, gunzip, json.loads. NEEDS LIVE-CREDENTIAL TEST
        (real payload shape; this follows Amazon's documented sample
        exactly: a flat JSON array of dicts keyed by requested columns)."""
        resp = self.session.get(url)
        raw = resp.content
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass  # tolerate an already-decompressed body
        return json.loads(raw.decode("utf-8"))

    def _fetch_rows(self, account: str, start: dt.date, end: dt.date, group_by: str):
        cfg = self._account_cfg(account)
        profile_id = cfg["profile_id"]
        report_id = self._create_report(profile_id, start, end, group_by)
        meta = self._poll_report(profile_id, report_id)
        raw_rows = self._download_report(meta["url"])
        return raw_rows

    # -- metadata / TACOS extension points (stubs, documented) ------------
    def _fetch_campaign_metadata(self, account: str) -> dict:
        """campaignId -> campaignName join via the Exports API.
        NOT IMPLEMENTED: needs a live account to verify the Exports API
        contract (POST /exports/campaigns, poll, download, join by
        campaignId per Amazon's get-started tip). Returns {} so
        campaign_name falls back to the raw campaignId. NEEDS
        LIVE-CREDENTIAL TEST + implementation."""
        return {}

    def _campaign_names(self, account: str) -> dict:
        if account not in self._name_cache:
            self._name_cache[account] = self._fetch_campaign_metadata(account)
        return self._name_cache[account]

    def _load_total_sales(self, account: str) -> dict:
        """Optional external total-sales source for TACOS (see config
        `total_sales_source`). Only a manual CSV (date,total_sales) is
        supported today; a Business Reports puller is a documented
        extension point, not implemented here."""
        src = self.config.get("total_sales_source", {})
        if src.get("type") != "manual_csv" or not src.get("path"):
            return {}
        import csv as _csv
        out = {}
        with open(src["path"], newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                if row.get("account") not in (None, "", account):
                    continue
                try:
                    out[dt.date.fromisoformat(row["date"])] = float(row["total_sales"])
                except (KeyError, ValueError):
                    continue
        return out

    # -- DataSource interface ---------------------------------------------
    def get_campaign_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        raw_rows = self._fetch_rows(account, start, end, "campaign")
        names = self._campaign_names(account)
        rows = []
        for r in raw_rows:
            cid = str(r.get("campaignId"))
            name = names.get(cid, cid)
            rows.append(DailyRow(
                account=account,
                date=dt.date.fromisoformat(r["date"]),
                level="campaign",
                impressions=int(r.get("impressions", 0)),
                clicks=int(r.get("clicks", 0)),
                spend=float(r.get("cost", 0.0)),
                sales=float(r.get(f"sales{self.attribution_window}", 0.0)),
                orders=int(r.get(f"purchases{self.attribution_window}", 0)),
                campaign_id=cid,
                campaign_name=name,
                category=classify_campaign_category(name),
            ))
        return rows

    def get_account_daily(self, account: str, start: dt.date, end: dt.date) -> list:
        campaign_rows = self.get_campaign_daily(account, start, end)
        by_date = {}
        for r in campaign_rows:
            agg = by_date.setdefault(r.date, {"impressions": 0, "clicks": 0, "spend": 0.0, "sales": 0.0, "orders": 0})
            agg["impressions"] += r.impressions
            agg["clicks"] += r.clicks
            agg["spend"] += r.spend
            agg["sales"] += r.sales
            agg["orders"] += r.orders
        total_sales_by_date = self._load_total_sales(account)
        rows = []
        for d in sorted(by_date):
            agg = by_date[d]
            rows.append(DailyRow(
                account=account,
                date=d,
                level="account",
                total_sales=total_sales_by_date.get(d),
                **agg,
            ))
        return rows


# ---------------------------------------------------------------------------
# Documented stubs: secondary/cross-check sources only.

class AdLabsDataSource(DataSource):
    """Documented stub, not implemented as a `DataSource` adapter.

    AdLabs is the ad-granular cross-check source (confirmed 2026-07-13,
    see _local/skill-build-plans/ads-and-bulk-skills.md) paired with
    SellerboardDataSource's whole-account totals via `crosscheck.py`.
    Historically it lagged the live account by ~4-5 days; as of
    2026-07-14 the operator confirms AdLabs data is current except that
    **today's** figures are slightly off and get corrected the next day
    (caveat this in the report for the report date only, not older days).

    Wire this via the AdLabs MCP at the runtime/skill layer (this toolkit
    makes no MCP calls): `start_chat_session` -> `read_resource
    adlabs://docs/entities` -> `get_entity_data(entity_type='profile'|
    'campaign', team_id, profile_id, filters=[DATE=<report_date>,
    COMPARE_DATE])` for spend/sales/ACOS + campaign-level anomalies. Feed
    the resulting figures into `crosscheck.cross_check()` against the
    same-day Sellerboard totals, and (optionally) build `DailyRow`
    campaign-level rows from the AdLabs response to pass as
    `campaign_rows` into `analyze.analyze_account()` alongside the
    Sellerboard account rows -- `analyze.py`/`report.py` don't care which
    adapter produced a row. See also `amazon-adlabs-audit` for the
    existing AdLabs MCP audit flow this can borrow call patterns from.
    """

    def list_accounts(self) -> list:
        raise NotImplementedError(
            "AdLabsDataSource is a documented stub. Wire it via the AdLabs MCP "
            "at the skill/runtime layer: start_chat_session -> read_resource "
            "adlabs://docs/entities -> get_entity_data(...). Use it as the "
            "ad-granular cross-check against SellerboardDataSource's account "
            "totals (crosscheck.py), and note today's-data-corrects-tomorrow "
            "caveat for the report date."
        )

    def get_account_daily(self, account, start, end):
        raise NotImplementedError(self.list_accounts.__doc__)

    def get_campaign_daily(self, account, start, end):
        raise NotImplementedError(self.list_accounts.__doc__)


class MarketplaceAdProsDataSource(DataSource):
    """Documented stub, not implemented.

    Optional secondary/cross-check source. As of 2026-07-13 the operator's
    MarketplaceAdPros AI Connect plan is expired (metrics null) and several
    profiles show access-revoked, so this adapter is not usable until
    renewed/reauthorized. Wire via the MarketplaceAdPros MCP at the
    runtime/skill layer when available.
    """

    def list_accounts(self) -> list:
        raise NotImplementedError(
            "MarketplaceAdProsDataSource is a documented stub; not usable "
            "until the operator's AI Connect plan is renewed/reauthorized."
        )

    def get_account_daily(self, account, start, end):
        raise NotImplementedError(self.list_accounts.__doc__)

    def get_campaign_daily(self, account, start, end):
        raise NotImplementedError(self.list_accounts.__doc__)


DATASOURCES = {
    "mock": MockDataSource,
    "sellerboard": SellerboardDataSource,
    "spads": SPAdsApiDataSource,
    "adlabs": AdLabsDataSource,
    "marketplaceadpros": MarketplaceAdProsDataSource,
}

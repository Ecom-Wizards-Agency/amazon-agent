"""Composition engine for the approved Ecom Wizards monthly-report template.

The engine deliberately owns page order, optional-module routing, page totals,
and structural validation. Brand modules still own their exact data and page
renderers. This keeps a root-cause package from leaking into an unrelated brand.

The engine composes and validates; it does not render. Document rendering goes
through the owning branded renderer per the client-facing brand precedence in
`AGENTS.md`, and delivery converts the intermediary to a native Google file via
`tools/gdrive-deliver/deliver.py`. Page renderers receive whatever drawing
backend the owning renderer provides; this module never imports one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

# A4 in points (210mm x 297mm); kept local so the engine needs no PDF library.
A4 = (595.2755905511812, 841.8897637795276)

PageRenderer = Callable[[Any, int], None]
CoverRenderer = Callable[[Any, Sequence["PageModule"], int, frozenset[str]], None]
TotalConfigurator = Callable[[int], None]

# Marketplaces the SoldScope rank tracker covers. Japan is not one of them.
RANK_TRACKER_MARKETPLACES = frozenset(
    {
        "US", "CA", "MX", "BR", "DE", "ES", "FR", "IT",
        "UK", "NL", "SE", "IN", "TR", "AE", "SA", "AU",
    }
)
RANK_TRACKER_URL = "https://app.soldscope.com/rank-tracker/{group_id}"


def rank_tracker_marketplace_supported(marketplace: str) -> bool:
    """True when the SoldScope rank tracker covers the marketplace code."""

    code = marketplace.strip().upper()
    if code == "GB":
        code = "UK"
    return code in RANK_TRACKER_MARKETPLACES


def _resolve_rank_support(
    explicit: Optional[bool],
    marketplace: str,
    legacy: Optional[bool],
) -> bool:
    """Explicit rank-tracker flag first, then the marketplace list, then the
    legacy DataDive flag. With none of them, keep the old default (supported)."""

    if explicit is not None:
        return bool(explicit)
    if marketplace.strip():
        return rank_tracker_marketplace_supported(marketplace)
    if legacy is not None:
        return bool(legacy)
    return True


@dataclass(frozen=True)
class LayoutPolicy:
    """Approved structural values for future brand renderers."""

    page_size: tuple[float, float] = A4
    headline_safe_width_ratio: float = 0.96
    headline_max_lines: int = 2
    headline_font_size: float = 17.5
    headline_leading: float = 19.0
    table_font_size: float = 6.35
    table_row_height: float = 16.0
    prior_period_gray_hex: str = "#7B8491"
    negative_change_hex: str = "#FF3B30"
    positive_change_hex: str = "#00A86B"
    numeric_columns_right_aligned: bool = True
    narrative_columns_left_aligned: bool = True
    visual_before_table: bool = True
    require_sales_in_performance_tables: bool = True
    sort_current_period_primary_metric_descending: bool = True
    compact_adjacent_sections: bool = True
    eyebrow_to_headline: float = 23.0
    headline_to_subtitle: float = 16.0
    subtitle_to_visual: float = 18.0
    visual_to_table: float = 18.0
    table_to_bullets: float = 14.0
    bullets_to_callout: float = 12.0
    module_transition: float = 24.0
    minimum_bottom_whitespace: float = 38.0


APPROVED_LAYOUT = LayoutPolicy()


@dataclass(frozen=True)
class PageModule:
    key: str
    toc_label: str
    renderer: PageRenderer
    source: str = ""


@dataclass(frozen=True)
class OptionalSection:
    key: str
    toc_label: str
    pages: tuple[PageModule, ...]
    allowed_brands: frozenset[str] = field(default_factory=frozenset)
    requires_explicit_opt_in: bool = True

    def validate_brand(self, brand_slug: str) -> None:
        if self.allowed_brands and brand_slug not in self.allowed_brands:
            allowed = ", ".join(sorted(self.allowed_brands))
            raise ValueError(
                f"Optional section {self.key!r} is restricted to: {allowed}. "
                f"It cannot be enabled for {brand_slug!r}."
            )


@dataclass(frozen=True)
class CoverItem:
    text: str
    requires_optional_section: str | None = None


@dataclass(frozen=True)
class CoverSpec:
    report_label: str
    period_line: str
    title: str
    overview: str
    contents: tuple[CoverItem, ...]
    contents_heading: str = "REPORT OVERVIEW"
    max_contents_items: int = 8
    period_font_size: float = 8.8
    period_tracking: float = 1.4

    def resolved_contents(self, enabled: frozenset[str]) -> list[str]:
        return [
            item.text
            for item in self.contents
            if item.requires_optional_section is None
            or item.requires_optional_section in enabled
        ]


@dataclass(frozen=True)
class MarketplacePart:
    """Source boundary for a marketplace-specific part of a combined report."""

    code: str
    display_name: str
    currency_symbol: str
    sellerboard_account: str
    adlabs_profile: str
    adlabs_dashboard: str
    rank_tracker_supported: Optional[bool] = None
    datadive_supported: Optional[bool] = None  # legacy flag, read as a fallback

    @property
    def rank_tracking_supported(self) -> bool:
        return _resolve_rank_support(
            self.rank_tracker_supported, self.code, self.datadive_supported
        )

    def validate(self) -> None:
        required = {
            "code": self.code,
            "display_name": self.display_name,
            "currency_symbol": self.currency_symbol,
            "sellerboard_account": self.sellerboard_account,
            "adlabs_profile": self.adlabs_profile,
            "adlabs_dashboard": self.adlabs_dashboard,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Marketplace part is missing: {', '.join(missing)}")


@dataclass(frozen=True)
class MonthlySourceRegistry:
    """Stable brand source settings that should persist between monthly runs."""

    sellerboard_account: str
    sellerboard_grouping: str
    adlabs_profile: str
    adlabs_dashboard: str
    focus_products: tuple[str, ...]
    slack_channel: str = ""
    marketplace: str = ""
    rank_tracker_group_ids: Mapping[str, str] = field(default_factory=dict)
    rank_tracker_urls: Mapping[str, str] = field(default_factory=dict)
    rank_tracker_supported: Optional[bool] = None
    # Legacy DataDive fields, read only as fallbacks.
    rank_radar_ids: Mapping[str, str] = field(default_factory=dict)
    datadive_supported: Optional[bool] = None

    @property
    def rank_tracking_supported(self) -> bool:
        return _resolve_rank_support(
            self.rank_tracker_supported, self.marketplace, self.datadive_supported
        )

    @classmethod
    def from_brand_config(cls, config: Mapping[str, Any]) -> "MonthlySourceRegistry":
        """Build the registry from a brand config shaped like
        `brand-config.example.json`. Each rank-tracker key falls back to its
        DataDive predecessor: `rank_tracker_group_id` to `rank_radar_id`,
        `rank_tracker_url` to `rank_radar_url`, and
        `sources.rank_tracker_marketplace_supported` to
        `sources.datadive_marketplace_supported` or `sources.datadive_supported`."""

        sources = config.get("sources") or {}
        brand = config.get("brand") or {}
        names: list[str] = []
        group_ids: dict[str, str] = {}
        urls: dict[str, str] = {}
        for product in config.get("focus_products") or []:
            name = str(product.get("name") or "")
            names.append(name)
            group_id = product.get("rank_tracker_group_id")
            if group_id in (None, ""):
                group_id = product.get("rank_radar_id")
            if group_id not in (None, ""):
                group_ids[name] = str(group_id)
            url = product.get("rank_tracker_url")
            if not url and product.get("rank_tracker_group_id") not in (None, ""):
                url = RANK_TRACKER_URL.format(group_id=product["rank_tracker_group_id"])
            if not url:
                url = product.get("rank_radar_url")
            if url:
                urls[name] = str(url)

        legacy_supported = sources.get("datadive_marketplace_supported")
        if legacy_supported is None:
            legacy_supported = sources.get("datadive_supported")
        return cls(
            sellerboard_account=str(sources.get("sellerboard_account") or ""),
            sellerboard_grouping=str(sources.get("sellerboard_grouping") or ""),
            adlabs_profile=str(sources.get("adlabs_profile") or ""),
            adlabs_dashboard=str(sources.get("adlabs_dashboard") or ""),
            focus_products=tuple(names),
            slack_channel=str(sources.get("slack_channel") or ""),
            marketplace=str(brand.get("marketplace") or ""),
            rank_tracker_group_ids=group_ids,
            rank_tracker_urls=urls,
            rank_tracker_supported=sources.get("rank_tracker_marketplace_supported"),
            datadive_supported=legacy_supported,
        )

    def validate(self) -> None:
        required = {
            "sellerboard_account": self.sellerboard_account,
            "adlabs_profile": self.adlabs_profile,
            "adlabs_dashboard": self.adlabs_dashboard,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Monthly source registry is missing: {', '.join(missing)}")
        if self.sellerboard_grouping.strip().lower() != "parent":
            raise ValueError("Sellerboard grouping must be 'parent'")
        if not self.focus_products:
            raise ValueError("At least one focus product is required")
        normalized = [product.strip().casefold() for product in self.focus_products]
        if any(not product for product in normalized):
            raise ValueError("Focus product names cannot be blank")
        duplicates = sorted(
            {product for product in normalized if normalized.count(product) > 1}
        )
        if duplicates:
            raise ValueError(f"Duplicate focus products: {duplicates}")


@dataclass(frozen=True)
class MonthlyRunEvidence:
    """Period-specific operator evidence received for one monthly run."""

    sellerboard_current_month: bool = False
    sellerboard_previous_month: bool = False
    sellerboard_parent_grouping_verified: bool = False
    adlabs_dashboard_current_month: bool = False
    adlabs_dashboard_previous_month: bool = False
    rank_tracker_products: frozenset[str] = field(default_factory=frozenset)
    rank_radar_products: frozenset[str] = field(default_factory=frozenset)  # legacy
    meeting_notes_status: str = "missing"
    slack_accessible: bool = True

    def validate(self) -> None:
        allowed = {"missing", "supplied", "none_confirmed"}
        if self.meeting_notes_status not in allowed:
            raise ValueError(
                "meeting_notes_status must be 'missing', 'supplied', or "
                "'none_confirmed'"
            )


def missing_operator_inputs(
    registry: MonthlySourceRegistry,
    evidence: MonthlyRunEvidence,
) -> tuple[str, ...]:
    """Return only the operator inputs still required for the monthly run."""

    registry.validate()
    evidence.validate()
    requests: list[str] = []

    missing_sellerboard_periods: list[str] = []
    if not evidence.sellerboard_current_month:
        missing_sellerboard_periods.append("reporting month")
    if not evidence.sellerboard_previous_month:
        missing_sellerboard_periods.append("comparison month")
    if missing_sellerboard_periods or not evidence.sellerboard_parent_grouping_verified:
        detail = " and ".join(missing_sellerboard_periods) or "both verified months"
        requests.append(
            f"Sellerboard screenshots for {detail}, using the saved account and "
            "Group by parent."
        )

    missing_adlabs_periods: list[str] = []
    if not evidence.adlabs_dashboard_current_month:
        missing_adlabs_periods.append("reporting month")
    if not evidence.adlabs_dashboard_previous_month:
        missing_adlabs_periods.append("comparison month")
    if missing_adlabs_periods:
        requests.append(
            "AdLabs custom-dashboard screenshot showing the "
            + " and ".join(missing_adlabs_periods)
            + " on the saved dashboard."
        )

    if registry.rank_tracking_supported:
        received = {
            product.strip().casefold()
            for product in evidence.rank_tracker_products | evidence.rank_radar_products
        }
        missing_products = [
            product
            for product in registry.focus_products
            if product.strip().casefold() not in received
        ]
        if missing_products:
            requests.append(
                "Full-month SoldScope rank tracker heatmap screenshot for: "
                + ", ".join(missing_products)
                + "."
            )

    if evidence.meeting_notes_status == "missing":
        requests.append(
            "Meeting notes for the reporting month, or confirmation that there "
            "were no meeting notes."
        )

    if not registry.slack_channel.strip() or not evidence.slack_accessible:
        requests.append(
            "Slack channel because it is not registered or cannot be accessed."
        )

    return tuple(requests)


@dataclass
class ReportDefinition:
    brand_slug: str
    title: str
    output_path: Path
    cover_spec: CoverSpec
    cover_renderer: CoverRenderer
    base_pages: tuple[PageModule, ...]
    closing_pages: tuple[PageModule, ...]
    optional_sections: Mapping[str, OptionalSection] = field(default_factory=dict)
    enabled_optional_sections: tuple[str, ...] = ()
    marketplace_parts: tuple[MarketplacePart, ...] = ()
    configure_page_total: TotalConfigurator | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def enabled_set(self) -> frozenset[str]:
        return frozenset(self.enabled_optional_sections)

    def resolved_pages(self) -> tuple[PageModule, ...]:
        enabled = self.enabled_set()
        unknown = enabled - set(self.optional_sections)
        if unknown:
            raise ValueError(f"Unknown optional sections: {sorted(unknown)}")

        pages: list[PageModule] = list(self.base_pages)
        for key in self.enabled_optional_sections:
            section = self.optional_sections[key]
            section.validate_brand(self.brand_slug)
            pages.extend(section.pages)
        pages.extend(self.closing_pages)
        return tuple(pages)

    def validate(self) -> tuple[PageModule, ...]:
        pages = self.resolved_pages()
        if not self.brand_slug.strip():
            raise ValueError("brand_slug is required")
        if not pages:
            raise ValueError("A monthly report must contain body pages")

        marketplace_codes: list[str] = []
        for part in self.marketplace_parts:
            part.validate()
            marketplace_codes.append(part.code.upper())
        duplicate_marketplaces = sorted(
            {code for code in marketplace_codes if marketplace_codes.count(code) > 1}
        )
        if duplicate_marketplaces:
            raise ValueError(
                f"Duplicate marketplace parts: {duplicate_marketplaces}"
            )

        keys = [page.key for page in pages]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"Duplicate page keys: {duplicates}")

        required = {
            "kpi_overview",
            "break_even_guardrail",
            "traffic_segments",
            "top_search_terms",
            "placements",
            "product_focus",
            "sqp_product_view",
            "goals_priorities",
        }
        missing = sorted(required - set(keys))
        if missing:
            raise ValueError(f"Missing required base pages: {missing}")

        if keys[-1] != "goals_priorities":
            raise ValueError("goals_priorities must remain the final body page")

        enabled = self.enabled_set()
        cover_text = " ".join(self.cover_spec.resolved_contents(enabled)).lower()
        for key in enabled:
            label = self.optional_sections[key].toc_label.lower()
            if label not in cover_text:
                raise ValueError(
                    f"Cover contents must name enabled optional section {key!r} "
                    f"using its label {self.optional_sections[key].toc_label!r}."
                )

        return pages


def compose_report(definition: ReportDefinition) -> tuple[PageModule, ...]:
    """Validate the definition and return the final ordered body pages.

    The caller drives the owning branded renderer with the returned pages:
    cover first, then each page with its 1-based number out of the total.
    """

    pages = definition.validate()
    if definition.configure_page_total:
        definition.configure_page_total(len(pages))
    return pages


def legacy_page(renderer: Callable[[Any, int], None]) -> PageRenderer:
    """Adapt an approved brand page renderer to the template interface."""

    def draw(backend: Any, page_number: int) -> None:
        renderer(backend, page_number)

    return draw


def ensure_sources_exist(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not Path(path).exists()]
    if missing:
        raise FileNotFoundError("Missing source images:\n" + "\n".join(missing))

"""Composition engine for the approved Ecom Wizards monthly-report template.

The engine deliberately owns page order, optional-module routing, page totals,
and structural validation. Brand modules still own their exact data and page
renderers. This keeps a root-cause package from leaking into an unrelated brand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


PageRenderer = Callable[[canvas.Canvas, int], None]
CoverRenderer = Callable[[canvas.Canvas, Sequence["PageModule"], int, frozenset[str]], None]
TotalConfigurator = Callable[[int], None]


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
    datadive_supported: bool = True

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


def render_report(definition: ReportDefinition) -> Path:
    pages = definition.validate()
    total = len(pages)
    if definition.configure_page_total:
        definition.configure_page_total(total)

    out = Path(definition.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out), pagesize=APPROVED_LAYOUT.page_size)
    pdf.setTitle(definition.title)
    for key, value in definition.metadata.items():
        if key == "author":
            pdf.setAuthor(value)
        elif key == "subject":
            pdf.setSubject(value)

    definition.cover_renderer(pdf, pages, total, definition.enabled_set())
    pdf.showPage()

    for index, page in enumerate(pages, 1):
        page.renderer(pdf, index)
        if index < total:
            pdf.showPage()

    pdf.save()
    return out


def legacy_page(renderer: Callable[[canvas.Canvas, int], None]) -> PageRenderer:
    """Adapt an approved brand page renderer to the template interface."""

    def draw(pdf: canvas.Canvas, page_number: int) -> None:
        renderer(pdf, page_number)

    return draw


def ensure_sources_exist(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not Path(path).exists()]
    if missing:
        raise FileNotFoundError("Missing source images:\n" + "\n".join(missing))


def monthly_delivery_directory(
    month_name: str,
    desktop: Path | None = None,
    *,
    create: bool = True,
) -> Path:
    """Return the required Desktop delivery folder for a reporting month."""

    clean_month = month_name.strip()
    if not clean_month or Path(clean_month).name != clean_month:
        raise ValueError("month_name must be a plain month label, such as 'July'")
    root = Path(desktop) if desktop is not None else Path.home() / "Desktop"
    destination = root / f"{clean_month} Monthly Reports"
    if create:
        destination.mkdir(parents=True, exist_ok=True)
    return destination

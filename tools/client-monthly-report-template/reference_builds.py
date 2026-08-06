"""Render the approved Swissker base and Pawsan opt-in reference templates."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from template_engine import (
    CoverItem,
    CoverSpec,
    OptionalSection,
    PageModule,
    ReportDefinition,
    ensure_sources_exist,
    legacy_page,
    render_report,
)


def _fit_wrapped_lines(pdf, text, font, preferred_size, minimum_size, max_width, max_lines):
    """Fit text to a bounded number of lines without crossing the safe width."""

    explicit = [line.strip() for line in text.splitlines() if line.strip()]
    size = preferred_size
    while size >= minimum_size:
        lines = []
        for paragraph in explicit:
            current = ""
            for word in paragraph.split():
                candidate = f"{current} {word}".strip()
                if current and stringWidth(candidate, font, size) > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
        if len(lines) <= max_lines and all(
            stringWidth(line, font, size) <= max_width for line in lines
        ):
            return size, lines
        size -= 0.25
    raise ValueError(f"Text cannot fit in {max_lines} lines: {text!r}")


def load_reference_modules(workspace: Path) -> tuple[Any, Any]:
    work = workspace / "work"
    if not work.exists():
        raise FileNotFoundError(f"Workspace work directory not found: {work}")
    sys.path.insert(0, str(work))
    swissker = importlib.import_module("generate_swissker_july_audit_monthly_final")
    pawsan = importlib.import_module("generate_pawsan_july_audit_monthly_final")
    return swissker, pawsan


def approved_cover_renderer(style: Any, spec: CoverSpec):
    """Clone the approved cover while resolving optional contents dynamically."""

    def draw(pdf, pages, total, enabled):
        del pages, total
        page_w, page_h = style.PAGE_W, style.PAGE_H
        left, right, content_w = style.LEFT, style.RIGHT, style.CONTENT_W
        base = style.base if hasattr(style, "base") else style.sw.base

        pdf.setFillColor(base.OBSIDIAN)
        pdf.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        pdf.setStrokeColor(style.GRID)
        pdf.setLineWidth(0.3)
        for gx in range(0, int(page_w) + 40, 40):
            pdf.line(gx, 0, gx, page_h)
        for gy in range(0, int(page_h) + 40, 40):
            pdf.line(0, gy, page_w, gy)

        base.draw_logo(pdf, left, page_h - 132, width=122, white=True)
        pdf.setStrokeColor(style.ORANGE)
        pdf.setLineWidth(4)
        pdf.line(left, page_h - 163, left + 45, page_h - 163)
        base.tracked(
            pdf, left, page_h - 195, spec.report_label,
            style.FONT_BOLD, 11.5, 2.2, style.ORANGE,
        )

        meta_size = spec.period_font_size
        while (
            meta_size > 6.8
            and stringWidth(spec.period_line, style.FONT_BOLD, meta_size) > content_w
        ):
            meta_size -= 0.1
        base.tracked(
            pdf, left, page_h - 216, spec.period_line,
            style.FONT_BOLD, meta_size, spec.period_tracking, style.MUTED,
        )

        title_size, title_lines = _fit_wrapped_lines(
            pdf, spec.title, style.FONT_HEAVY, 39.0, 28.0, content_w, 2,
        )
        pdf.setFont(style.FONT_HEAVY, title_size)
        pdf.setFillColor(style.WHITE)
        title_y = page_h - 305
        title_leading = title_size * 1.08
        for line in title_lines:
            pdf.drawString(left, title_y, line)
            title_y -= title_leading
        pdf.setStrokeColor(style.GRID)
        pdf.setLineWidth(0.6)
        pdf.line(left, page_h - 355, page_w - right, page_h - 355)
        base.wrap_draw(
            pdf, left, page_h - 385, spec.overview,
            style.FONT, 12, content_w, 17, style.MUTED,
        )

        y = 255
        base.tracked(
            pdf, left, y, spec.contents_heading,
            style.FONT_BOLD, 8.5, 2.4, style.ORANGE,
        )
        y -= 30
        items = spec.resolved_contents(enabled)
        if len(items) > spec.max_contents_items:
            raise ValueError(
                f"Cover contents exceed the approved {spec.max_contents_items}-item limit"
            )
        for idx, item in enumerate(items, 1):
            pdf.setFillColor(style.ORANGE)
            pdf.setFont(style.FONT_HEAVY, 13)
            pdf.drawString(left, y, f"{idx:02d}")
            pdf.setFillColor(style.WHITE)
            item_size, item_lines = _fit_wrapped_lines(
                pdf, item, style.FONT, 12.5, 10.0, content_w - 42, 2,
            )
            pdf.setFont(style.FONT, item_size)
            for line in item_lines:
                pdf.drawString(left + 42, y, line)
                y -= 15
            y -= 7

    return draw


def swissker_definition(workspace: Path, out_dir: Path, sw: Any) -> ReportDefinition:
    ensure_sources_exist([sw.IMG_HEAVY_DUTY, sw.IMG_SHINEPOD, sw.IMG_KLEARNAIL])

    base_pages = (
        PageModule("kpi_overview", "KPI overview", legacy_page(sw.page_kpi), "Sellerboard + AdLabs"),
        PageModule("break_even_guardrail", "Break-even ACOS guardrail", legacy_page(sw.page_guardrail), "Sellerboard + AdLabs"),
        PageModule("traffic_segments", "Traffic segments", legacy_page(sw.page_traffic), "AdLabs search terms"),
        PageModule("top_search_terms", "Top search terms", legacy_page(sw.page_top_terms), "AdLabs search terms"),
        PageModule("channel_bid_categories", "Ad type utilisation and bid categories", legacy_page(sw.page_channel_and_bid_categories), "AdLabs audit"),
        PageModule("match_budget", "Match types and budget utilisation", legacy_page(sw.page_match_types_and_budget_caps), "AdLabs"),
        PageModule("placements", "Placement analysis", legacy_page(sw.page_placements), "AdLabs placements"),
        PageModule("product_focus", "Focus-product performance", legacy_page(sw.page_products), "Sellerboard + AdLabs"),
        PageModule("sqp_product_view", "SQP product view", legacy_page(sw.page_sqp), "Amazon SQP"),
        PageModule(
            "organic_heavy_duty", "Heavy Duty organic ranking",
            lambda pdf, number: sw.datadive_page(
                pdf, number, "Organic Ranking - Heavy Duty",
                "Heavy Duty kept strong first-page visibility", sw.IMG_HEAVY_DUTY,
                [
                    "The aggregate set shows 767,258 search volume with a median rank around 18 at the end of July.",
                    "Core terms such as toenail clippers for thick toenails and professional nail clippers held stronger visible ranks than broader fungus or generic rows.",
                    "Meeting notes show Heavy Duty remained the product that needed the most protection: click-fraud checks, Q4 forecast, and factory-direct inventory planning.",
                ],
                "Organic visibility stayed strong enough to justify protecting Heavy Duty, but the paid traffic needs cleaner data before aggressive scaling.",
            ),
            "DataDive Rank Radar",
        ),
        PageModule(
            "organic_shinepod", "ShinePod organic ranking",
            lambda pdf, number: sw.datadive_page(
                pdf, number, "Organic Ranking - ShinePod",
                "ShinePod has visibility, but conversion remains the\nconstraint", sw.IMG_SHINEPOD,
                [
                    "The aggregate set shows 764,747 search volume with a median rank around 78, reflecting broad category visibility but weaker rank quality.",
                    "Dental pod and sonic dental cleaner are the cleaner pockets; broad retainer cleaner terms are still much more competitive.",
                    "The July pricing discussion noted ShinePod price is already low, so discount-led growth should be handled carefully.",
                ],
                "ShinePod should be scaled through targeted pockets and inventory confirmation, not broad discounting.",
            ),
            "DataDive Rank Radar",
        ),
        PageModule(
            "organic_klearnail", "KlearNail organic ranking",
            lambda pdf, number: sw.datadive_page(
                pdf, number, "Organic Ranking - KlearNail",
                "KlearNail needs narrow query control", sw.IMG_KLEARNAIL,
                [
                    "The aggregate set shows 629,586 search volume with a median rank around 89, indicating visibility is still weak on the broadest fungus terms.",
                    "The strongest opportunities are narrower terms where ranks move into the 30-60 range rather than the broadest 101 rows.",
                    "Paid ACOS was high in the product audit, so KlearNail should not absorb broad expansion until conversion improves.",
                ],
                "KlearNail needs selective, rank-aware traffic: protect the pockets that show movement and avoid broad waste.",
            ),
            "DataDive Rank Radar",
        ),
    )

    cover = CoverSpec(
        report_label="PERFORMANCE REPORT - JULY 2026",
        period_line="JULY 1-31, 2026 VS JUNE 1-30, 2026 | HEAVY DUTY, SHINEPOD, KLEARNAIL | AMAZON US",
        title="Swissker Monthly Report",
        overview="A consolidated review of July business performance, advertising efficiency, search visibility, and the strategic priorities guiding the month ahead.",
        contents=(
            CoverItem("KPI overview and break-even ACOS guardrail"),
            CoverItem("Advertising performance and traffic segments"),
            CoverItem("Ad type utilization, bid categories, match types, and budget caps"),
            CoverItem("Placement performance and modifier checks"),
            CoverItem("Focus products, SQP, and DataDive organic ranking"),
            CoverItem("August goals and priorities informed by July performance and meetings"),
        ),
    )

    def configure(total: int) -> None:
        sw.BODY_PAGE_TOTAL = total
        sw.base.BODY_PAGE_TOTAL = total
        sw.base.TABLE_FONT_SIZE = 6.35
        sw.base.TABLE_ROW_H = 16

    return ReportDefinition(
        brand_slug="swissker-us",
        title="Swissker July 2026 Monthly Report - Base Template Reference",
        output_path=out_dir / "Swissker Base Monthly Report Template Reference.pdf",
        cover_spec=cover,
        cover_renderer=approved_cover_renderer(sw, cover),
        base_pages=base_pages,
        closing_pages=(PageModule("goals_priorities", "Goals and priorities", legacy_page(sw.page_goals), "Monthly analysis"),),
        configure_page_total=configure,
        metadata={"author": "Ecom Wizards", "subject": "Approved monthly-report base template"},
    )


def pawsan_definition(workspace: Path, out_dir: Path, pawsan: Any) -> ReportDefinition:
    del workspace
    ensure_sources_exist([pawsan.IMG_GELENK, pawsan.IMG_DARMWOHL, pawsan.IMG_POOP_BAGS])

    base_pages = (
        PageModule("kpi_overview", "KPI overview", legacy_page(pawsan.page_kpi), "Sellerboard + AdLabs"),
        PageModule("break_even_guardrail", "Break-even ACOS guardrail", legacy_page(pawsan.page_guardrail), "Sellerboard + AdLabs"),
        PageModule("traffic_segments", "Traffic segments", legacy_page(pawsan.page_traffic), "AdLabs search terms"),
        PageModule("top_search_terms", "Top search terms", legacy_page(pawsan.page_top_terms), "AdLabs search terms"),
        PageModule("channel_bid_categories", "Ad type utilisation and bid categories", legacy_page(pawsan.page_channel_bid), "AdLabs audit"),
        PageModule("match_budget", "Match types and budget utilisation", legacy_page(pawsan.page_match_budget), "AdLabs"),
        PageModule("placements", "Placement analysis", legacy_page(pawsan.page_placements), "AdLabs placements"),
        PageModule("product_focus", "Focus-product performance", legacy_page(pawsan.page_products), "Sellerboard + AdLabs"),
        PageModule("sqp_product_view", "SQP product view", legacy_page(pawsan.page_sqp), "Amazon SQP"),
        PageModule(
            "organic_gelenk", "Gelenk Aktiv organic ranking",
            lambda pdf, number: pawsan.datadive_page(
                pdf, number, "Organic Ranking - Gelenk Aktiv",
                "Core joint terms stayed visible, but broad demand\nremained expensive", pawsan.IMG_GELENK,
                [
                    "The aggregate Rank Radar set finished July near a median rank of 25, with several branded and high-intent joint terms still on the first page.",
                    "gelenktabletten hund and hund gelenktabletten remained strong visible rows; broader gruenlippmuschel and traumeel terms were more mixed.",
                    "Slack and SQP context show the product can convert on selected terms, but cannot profitably buy every high-volume position under the current offer gap.",
                ],
                "Protect the terms where Pawsan converts at or above market; broad rank should not be defended with unprofitable bids.",
            ),
            "DataDive Rank Radar",
        ),
        PageModule(
            "organic_darmwohl", "Darmwohl organic ranking",
            lambda pdf, number: pawsan.datadive_page(
                pdf, number, "Organic Ranking - Darmwohl",
                "Darmwohl held selective first-page terms amid\nbroad rank pressure", pawsan.IMG_DARMWOHL,
                [
                    "The aggregate set finished July near a median rank of 33, while darmkur hund and darmflora hund remained among the clearest first-page pockets.",
                    "The broader probiotic and digestive-aid terms were materially weaker, which aligns with the unresolved category and product-positioning question.",
                    "SQP conversion improved, but the paid product ACOS of 92.85% shows that visibility alone did not create healthy economics.",
                ],
                "Use the rank pockets to guide a narrower test; settle the category and offer before attempting another broad push.",
            ),
            "DataDive Rank Radar",
        ),
        PageModule(
            "organic_poop_bags", "Poop Bags organic ranking",
            lambda pdf, number: pawsan.datadive_page(
                pdf, number, "Organic Ranking - Poop Bags",
                "Poop Bag rankings softened as stockouts interrupted\nmomentum", pawsan.IMG_POOP_BAGS,
                [
                    "The aggregate set finished July near a median rank of 40, while biologically degradable long-tail terms stayed closer to the first page.",
                    "Broad head terms such as hundekotbeutel and kotbeutel fuer hunde ended materially weaker than the strongest long-tail rows.",
                    "The July Slack analysis attributed roughly €9.7K in lost revenue to stockouts, so the ranking decline should not be read as a pure advertising failure.",
                ],
                "Inventory continuity is the first ranking lever. Restore stock before judging whether broader Poop Bag advertising needs structural change.",
            ),
            "DataDive Rank Radar",
        ),
    )

    root_cause = OptionalSection(
        key="pawsan_root_cause",
        toc_label="root-cause overview",
        allowed_brands=frozenset({"pawsan-de"}),
        pages=(
            PageModule("root_cause_overview", "Root-cause overview and key numbers", legacy_page(pawsan.page_root_cause_overview), "Pawsan root-cause document"),
            PageModule("root_cause_keywords", "Keyword verdicts", legacy_page(pawsan.page_root_cause_keywords), "Pawsan root-cause document"),
            PageModule("root_cause_execution", "Executed actions", legacy_page(pawsan.page_root_cause_actions), "Pawsan root-cause document"),
        ),
    )

    cover = CoverSpec(
        report_label="PERFORMANCE REPORT - JULY 2026",
        period_line="JULY 1-31, 2026 VS JUNE 1-30, 2026 | GELENK AKTIV, DARMWOHL, POOP BAGS | AMAZON DE",
        title="Pawsan Monthly Report",
        overview="A consolidated review of July business performance, advertising efficiency, search visibility, and the operating priorities required for a clean account handover.",
        contents=(
            CoverItem("KPI overview and break-even ACOS guardrail"),
            CoverItem("Traffic, search-term, ad-type, match-type, and placement diagnostics"),
            CoverItem("AdLabs audit modules for bid categories and budget utilization"),
            CoverItem("Product economics and product-level SQP demand signals"),
            CoverItem("DataDive organic-ranking views for all three focus products"),
            CoverItem("Root-cause overview, key numbers, verdicts, and completed execution", "pawsan_root_cause"),
            CoverItem("August goals and a practical handover priority list"),
        ),
        period_font_size=8.5,
        period_tracking=1.25,
    )

    def configure(total: int) -> None:
        pawsan.BODY_PAGE_TOTAL = total
        pawsan.sw.base.BODY_PAGE_TOTAL = total
        pawsan.sw.base.TABLE_FONT_SIZE = 6.35
        pawsan.sw.base.TABLE_ROW_H = 16

    return ReportDefinition(
        brand_slug="pawsan-de",
        title="Pawsan July 2026 Monthly Report - Optional Module Reference",
        output_path=out_dir / "Pawsan Monthly Report Template With Root Cause Opt-In.pdf",
        cover_spec=cover,
        cover_renderer=approved_cover_renderer(pawsan, cover),
        base_pages=base_pages,
        optional_sections={root_cause.key: root_cause},
        enabled_optional_sections=(root_cause.key,),
        closing_pages=(PageModule("goals_priorities", "Goals and priorities", legacy_page(pawsan.page_goals), "Monthly analysis"),),
        configure_page_total=configure,
        metadata={"author": "Ecom Wizards", "subject": "Approved monthly-report optional-module reference"},
    )


def verify_pdf(path: Path, expected_body_pages: int) -> None:
    reader = PdfReader(str(path))
    expected_total = expected_body_pages + 1
    if len(reader.pages) != expected_total:
        raise ValueError(f"{path.name}: expected {expected_total} pages, got {len(reader.pages)}")
    a4_w, a4_h = 595.28, 841.89
    for index, page in enumerate(reader.pages, 1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - a4_w) > 1 or abs(height - a4_h) > 1:
            raise ValueError(f"{path.name}: page {index} is not A4 ({width:.2f} x {height:.2f})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fixture", choices=("swissker", "pawsan", "all"), default="all")
    args = parser.parse_args()

    sw, pawsan = load_reference_modules(args.workspace.resolve())
    definitions = []
    if args.fixture in {"swissker", "all"}:
        definitions.append(swissker_definition(args.workspace, args.output_dir, sw))
    if args.fixture in {"pawsan", "all"}:
        definitions.append(pawsan_definition(args.workspace, args.output_dir, pawsan))

    for definition in definitions:
        path = render_report(definition)
        verify_pdf(path, len(definition.resolved_pages()))
        print(path)


if __name__ == "__main__":
    main()

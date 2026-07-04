# Branding — the one place this is documented

All branded output (audit `.docx`/`.pdf`, covers, the three audit `.xlsx` workbooks) takes its
agency identity from ONE local file; the repo ships only the mechanism. Do not scatter branding
rules across other READMEs, configs, or memories — extend this file.

## Where things live

| What | Where | Tracked? |
|---|---|---|
| Agency identity (name, URL, palettes, fonts) | `_local/branding/branding.json` | no (gitignored) |
| Agency brand-guide notes for operators | `_local/branding/brand-notes.md` | no |
| Binary assets (font, logos, mark) | `tools/amazon-ad-audit/brand/` | no (regenerate: `prepare_brand_assets.py`) |
| Schema + neutral template | `tools/amazon-ad-audit/branding.TEMPLATE.json` | yes |
| Agent-style fallbacks | `branding.EXAMPLE-claude.json` / `branding.EXAMPLE-codex.json` | yes |
| Loader | `tools/amazon-ad-audit/branding.py` | yes |
| Per-document overrides (`prepared_by`, `cover_subtitle`, `doc_label`, `first_time`, `brand_dir`) | client config `branding` block | template yes, client configs no |

## Resolution order

1. `_local/branding/branding.json` (copy the TEMPLATE there and fill it in; path override via
   config `branding.branding_json`).
2. No local file → `branding.EXAMPLE-claude.json` under Claude, `branding.EXAMPLE-codex.json`
   under Codex (env-detected). Footers stay generic (no agency name/URL).
3. Built-in neutral defaults — rendering always works.

Consumers: `render_branded.py` + `brand_cover.py` (docs), `ew_audit_style.py` →
`build_audit_workbook.py` / `build_sqp_workbook.py` / `build_master_workbook.py` (xlsx banners,
"Prepared by"), `narrative_scaffold.py` (byline), `md_to_docx.py` (fallback renderer).

## Document layout rules (agency-independent quality bar)

- Never end a page with an orphaned note, small paragraph, or a heading + intro separated from
  its content. Wrap `heading + intro + first content block` in a keep-together container
  (`break-inside: avoid`) and set `orphans/widows` on paragraphs.
- Documents keep a WHITE page background. Accent colors are for rules, eyebrows, KPI top-borders,
  callouts, and covers — never full-page backgrounds.
- Tables: dark ink header row, zebra rows, hairline horizontal borders only, tabular numbers.
- KPI cards: light panel, accent top border, big number + small-caps label.
- Neutrals dominate any surface (~70%); accent usage stays small (≤5%).

## Toolchain notes (macOS)

- SVG → PNG and HTML → PDF go through **headless Chrome** (no rsvg/inkscape/cairosvg present).
  Chrome binary override: env `EW_CHROME` or `BRAND_CHROME`.
- QA on generated pages: `sips` for image checks + `pypdf` for PDF page counts.
- PDF running footers are `@page` margin boxes (`@bottom-left`/`@bottom-right`).
- The variable font is embedded base64 into the PDF HTML; if the font file is missing the PDF
  falls back to system fonts instead of failing.

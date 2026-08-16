# Branding: the mechanism

All branded output (the audit `.docx`, covers, the three audit `.xlsx` workbooks) takes its
agency identity from ONE local file; this repo ships only the mechanism. Do not scatter branding
rules across other READMEs, configs, or memories.

**This file owns the mechanism — resolution order, schema, consumers, toolchain. It does not own
the values.** Since 16.08.2026 the palette, type scale, page geometry, header/footer contract and
the routing table for every client-facing artifact live in the `ecom-wizards-brand` skill in
`company-ai-skills`, and `_local/branding/branding.json` is a symlink to that skill's copy,
installed by `skills/ecom-wizards-brand/scripts/fetch-brand-kit.py` and enforced by the
`brand-identity-file` check in `company-setup/roles.json`.

This repo is public, which is why the identity is gitignored here — and that is exactly why it
cannot be canonical here. Extend the skill for a values or contract change; extend this file for
a mechanism change.

## Where things live

| What | Where | Tracked? |
|---|---|---|
| Agency identity (name, URL, palettes, fonts) | `_local/branding/branding.json` | no (gitignored) |
| Agency brand-guide notes for operators | `_local/branding/brand-notes.md` | no |
| Binary assets (font, logos, mark) | `tools/amazon-ad-audit/brand/` | no (regenerate: `prepare_brand_assets.py`) |
| Schema + neutral template | `tools/amazon-ad-audit/branding.TEMPLATE.json` | yes |
| Agent-neutral fallback | `branding.EXAMPLE-neutral.json` | yes |
| Legacy compatibility aliases | `branding.EXAMPLE-claude.json` / `branding.EXAMPLE-codex.json` | yes |
| Loader | `tools/amazon-ad-audit/branding.py` | yes |
| Per-document overrides (`prepared_by`, `cover_subtitle`, `doc_label`, `first_time`, `brand_dir`) | client config `branding` block | template yes, client configs no |

## Resolution order

1. `_local/branding/branding.json` (copy the TEMPLATE there and fill it in; path override via
   config `branding.branding_json`).
2. No local file → `branding.EXAMPLE-neutral.json`, regardless of runtime. Footers stay generic
   (no agency name/URL). The legacy agent-named examples contain identical values for compatibility.
3. Built-in neutral defaults. Rendering always works.

Consumers: `render_branded.py` + `brand_cover.py` (docs), `ew_audit_style.py` →
`build_audit_workbook.py` / `build_sqp_workbook.py` / `build_master_workbook.py` (xlsx banners,
"Prepared by"), `narrative_scaffold.py` (byline), `md_to_docx.py` (fallback renderer).

Specialist builders with an explicit approved branding path call
`branding.activate_branding(config)` before importing shared renderers. This makes that approved
identity the process-local default and prevents import-time example styling from leaving stale
renderer globals behind.

The native Google Doc is the deliverable. Body styling, footer fields, Inter, KPI cards, tables, and
figures survive conversion. Cover-section geometry and the right header zone do not survive every
conversion. Normalize and verify those two surfaces in the native Doc after import.

## Document layout rules (agency-independent quality bar)

- Cover subtitles should say what the document is. Keep them plain and factual.
  Avoid metaphors like leaks, engine, unlocked, or hidden. Avoid reveal language
  like "here is" or "what you have not switched on." Avoid balanced ad-copy
  constructions like "X, and the Y to fix it."
- Never end a page with an orphaned note, small paragraph, or a heading + intro separated from
  its content. Wrap `heading + intro + first content block` in a keep-together container
  (`break-inside: avoid`) and set `orphans/widows` on paragraphs.
- Documents keep a WHITE page background. Accent colors are for rules, eyebrows, KPI top-borders,
  callouts, and covers. Never use full-page backgrounds.
- Tables: dark ink header row, zebra rows, hairline horizontal borders only, tabular numbers.
- KPI cards: light panel, accent top border, big number + small-caps label.
- Neutrals dominate any surface (~70%); accent usage stays small (≤5%).

## Audit running header and footer (approved V2 treatment)

- The default report label is `Account Audit`. Preserve explicit client-specific `branding.doc_label` overrides.
- The first-time cover must fill the complete A4 first page in the native Google Doc. Use a zero-margin first section, a next-page section break before body content, and no first-page header or footer.
- Put the full black agency lockup at the left of every content-page header. Preserve its proportions and required clear space. Do not substitute the standalone mark.
- Put `<REPORT LABEL> · <MONTH YYYY>` at the right content edge in uppercase Inter and the configured Mist gray.
- Use a text-only three-column footer on every content page: `<Report label> · <Client>` at left, `page X of Y` centered, and the agency website at right.
- Use real `PAGE` and `NUMPAGES` fields. They import as live Google Docs page numbers. Keep the same Inter size, color, and baseline across all three footer zones.
- Keep the three-zone footer treatment unchanged. In the header, use the native-safe two-zone behavior from the renderer and run `native_doc_normalize.py` after conversion. Google Docs can flatten an imported fixed table or land the first tab on its centre stop, so the native readback and visual check are mandatory.
- Do not show the standalone rocket mark in the footer.
- Verify the cover and every content page directly in the native Doc. Check full-page cover geometry, logo proportions, right-edge header alignment, resolved page totals, clipping, overlap, and content reflow before delivery.

## Toolchain notes (macOS)

- SVG → PNG goes through **headless Chrome** (no rsvg/inkscape/cairosvg present), in
  `prepare_brand_assets.py`. Chrome binary override: env `EW_CHROME` or `BRAND_CHROME`.
- QA on generated pages: `sips` for image checks. Page counts come from the delivered
  Google Doc, which resolves `NUMPAGES` on open.
- There is no PDF deliverable or QA export. `render_branded.py` creates a DOCX intermediate, which
  is converted and normalized into the sole deliverable: a native Google Doc. Create a PDF only
  when the operator explicitly requests one.

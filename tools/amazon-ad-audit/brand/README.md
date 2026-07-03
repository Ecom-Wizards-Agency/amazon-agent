# Brand assets (LOCAL ONLY — gitignored)

`render_branded.py` reads the Ecom Wizards brand assets from this folder to build the branded audit
document (.docx + PDF). The binaries here are **gitignored** (the repo is public) — only this README and
`.gitkeep` are committed.

## Regenerate

```bash
python3 tools/amazon-ad-audit/prepare_brand_assets.py
```

That reads your **local** pCloud brand sources (logo SVGs + the Inter variable font) and writes:

| File | What | Source |
|---|---|---|
| `logo_white.png` | white lockup, transparent (dark cover) | `logo_white_no_background.svg` via headless Chrome |
| `logo_black.png` | black lockup, transparent | `logo_black_no_background.svg` via headless Chrome |
| `mark_black.png` | rocket mark only (footers) | cropped from `logo_black.png` |
| `Inter-Variable.ttf` | Inter variable font (all weights) | pCloud InDesign template fonts |

Override any source path with env vars: `EW_LOGO_SVG_DIR`, `EW_INTER_TTF`, `EW_CHROME`.

## Notes
- **Font is Inter** (the website typeface), not Geist. The brand-guide PDF lists Geist primary / Inter
  fallback, but the site — and therefore these documents — use Inter.
- macOS has no rsvg/inkscape/cairosvg, so SVG→PNG goes through headless Chrome. See the
  `ecom-wizards-brand-doc-pipeline` memory for the full toolchain (Chrome for SVG→PNG + HTML→PDF, `sips`
  + `pypdf` for QA, `@page` margin-box footers).

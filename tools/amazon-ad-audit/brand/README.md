# Brand assets (LOCAL ONLY — gitignored)

Binary brand assets read by `render_branded.py` / `brand_cover.py`: the variable font, logo
lockups, and the footer mark. The binaries are **gitignored** (the repo is public) — only this
README and `.gitkeep` are committed.

Everything else branding-related is documented in ONE place: **`../BRANDING.md`** (resolution
order, schema, layout rules, toolchain). Agency identity lives in `_local/branding/branding.json`;
agency brand-guide notes in `_local/branding/brand-notes.md`.

## Regenerate (Ecom Wizards operators)

```bash
python3 tools/amazon-ad-audit/prepare_brand_assets.py
```

Reads your local pCloud brand sources and writes `logo_white.png`, `logo_black.png`,
`mark_black.png`, `Inter-Variable.ttf` here. Source-path overrides: `EW_PCLOUD_ROOT`,
`EW_LOGO_SVG_DIR`, `EW_INTER_TTF`, `EW_CHROME`.

Other agencies: drop your own font + logos here (filenames configurable in `branding.json`
`assets`) — see `../BRANDING.md`.

# New client setup: SB video briefs

1. Copy `config.TEMPLATE.json` to `config.<client>-<market>-<product-line>.json` (stays local, gitignored). Fill every `<...>`; never carry values from another client's config. **One config per product line**, matching the one-Creative-Reference-doc-per-product-line rule.
2. Required before the first run: Seller Central account name (POE `--expect-account`), marketplace + language, product line, target ASIN(s), DataDive niche id, AdLabs profile_id, break-even ACOS (mark ASSUMED if unconfirmed), and the client's Drive creative folder on the desktop mount.
3. Brand kit and footage locations can start as "none": the reference doc then carries them as open asset requests, and the brief flags the gap on the specific card that needs them.
4. Build the Creative Reference & Asset Library before the first brief (`skills/amazon-sb-video-briefs/references/creative-reference-doc.md`). The brief draws its claims and its differentiation from it.
5. Run via `/video-brief <client>-<market>`. The skill (`skills/amazon-sb-video-briefs/SKILL.md`) owns the workflow; this folder only holds the config contract.

Rendering both documents needs the repo `.venv` python (it has python-docx). Call `render_branded.render(cfg, outdir, md_path, cover=False)` from `tools/amazon-ad-audit`. `metrics.json` in `outdir` must exist but must NOT contain `custom_kpis`, so the KPI card strip is suppressed: `{"currency": "USD"}` is enough.

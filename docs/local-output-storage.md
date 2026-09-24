# Local Output Storage

**Local policy overrides these generic defaults.** Before choosing a durable
destination or deciding whether to retain a local artifact, read
`_local/storage-routing.md` when it exists. That file is a symlink the
company-setup bootstrap creates, pointing at
`company-ai-skills/skills/company-setup/references/storage-routing.md`; it is
gitignored, so a bare clone does not have it until setup runs. It may override
the saving, delivery, retention and cleanup paths below. An explicit safe target
from the operator for the current task wins over both. Security, permission and
client-visibility guardrails never become optional. If the local policy path
exists but is unreadable or stale, stop and report it instead of silently using
the generic defaults.

Never save generated files, exports, evidence, screenshots, review trackers, working notes, or client-specific output inside SOP or help-library folders. SOP folders should contain SOP/source documentation only.

The base local artifact folders are present after clone through `.gitkeep` files, but real files inside them are ignored and must not sync to GitHub. New generated work should use lowercase `output/`; uppercase `Output/` is only a legacy ignored alias.

Top-level folder roles:

- `output/`: generated work and analysis, such as SEO, opportunity data, ads files, reporting, inventory outputs, and catalog drafts.
- `evidence/`: screenshots, UI proof, warning captures, visible tables, and operator notes.
- `downloads/`: temporary raw Amazon exports before processing.
- `_local-output/`: one-off local staging or migration scratch space.
- `.codex-tmp/`: Codex one-shot scratch only (throwaway inspector scripts, probe output). Never a home for client deliverables: anything worth keeping moves to `output/{client}/{workflow}/` in the same session, and the folder is purged at least monthly.
- `review-tracking/`: legacy ignored folder only. Keep existing local files there if they already exist, but do not create new review-management work there by default.

These are the only sanctioned scratch roots. `tmp/`, `.tmp/`, `outputs/` and uppercase `Output/` are retired roots (consolidated into `output/` on 12.08.2026): they stay in `.gitignore` as tombstones, and nothing new gets created in them.

Use ongoing client-first paths for new artifacts:

- `output/{client}/{workflow}/`
- `downloads/{client}/{source}/`
- `evidence/{client}/{workflow}/`
- `output/{client}/review-management/`

Client folder rules (normalized 2026-07-04; do not let variants drift back):

- `{client}` is one lowercase-kebab slug per client (`acme`, `globex-brands`): no spaces, no capitals, no marketplace suffixes. Marketplace/country and dates belong in filenames (or a workflow subfolder), never in the client folder name.
- Before saving, list the artifact folder and REUSE the existing client folder; match the client slug in `tools/*/config.<slug>*.json` when one exists. Never create a spelling variant of an existing client folder ("Acme US" next to `acme`).
- No loose files at the `output/` root: everything lives under `output/{client}/{workflow}/` (internal/agency work goes under `output/ecom-wizards/`; run-scoped folders like `reshipment-plans-<date>/` count as workflow folders).

Review management is ongoing and client-specific; update the same client folder over time. Keep support drafts under `output/{client}/support-prep/` and support evidence under `evidence/{client}/support-prep/`; use Notion for live support-case tracking.

Team-vault run notes: every client workrun also leaves one markdown run note in the shared team vault at `<team-vault>/Clients/<Client>/Runs/YYYY-MM-DD-<workflow>.md` when the client already has a folder there, resolved the same way as handoff notes (`AMAZON_AGENT_TEAM_VAULT` env var or `_local/team-vault-path.txt`); otherwise the note stays in the repo's `output/<client>/<workflow>/`. Client slug to vault folder: match the `slug:` in each vault client hub's frontmatter first (canonical, so a slug can live under a differently-named folder), then a case-insensitive folder-name match with spaces treated as hyphens. The note is a short human-readable record: what ran, key findings and decisions, which artifacts were delivered and where they live (link Drive or repo paths; never copy XLSX/CSV or other binaries into the vault). Never create a new client folder in the vault just to place a run note, and never write run notes into a personal vault.

Controlled workflow names:

- `seo`
- `opportunity-data`
- `ads`
- `reporting`
- `inventory`
- `catalog`
- `account-check`
- `support-prep`
- `sop-maintenance`
- `creator-connections`
- `onboarding`
- `offboarding`

Do not create a separate global overview tracker by default. If a workflow needs local context, put `README.md` or `operator-note.md` inside the relevant workflow folder. Use Notion for ongoing team status.

## Durable Storage

This repository supplies temporary `downloads/`, `output/` and `evidence/`
defaults only. New files use `tools/artifactctl/artifactctl`: register exact
paths under a run, complete the run with its real outcome, and leave weekly
verification, quarantine, restoration, and purge to the machine-local policy.
When no local policy is installed, keep files in the gitignored defaults and
report that no durable route was available rather than guessing or copying the
same artifact to several systems.

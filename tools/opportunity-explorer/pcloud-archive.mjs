/**
 * Archive POE runs from the repo's working tree to the pCloud client archive.
 *
 * POE snapshots are NOT reproducible: Amazon serves trailing windows only, so a
 * capture cannot be re-fetched later. `output/<slug>/opportunity-data/` is the hot
 * working copy on one machine; this mirrors it to the shared pCloud archive so the
 * history survives that machine.
 *
 * Target:
 *   <pcloud>/1_Delivery/1.1_Clients/<Client>/_Data/opportunity-data/<mp>/<YYYY-MM-DD>_<niche>/
 *
 * <Client> is resolved from the slug through the team vault's client hub notes,
 * the same two-step rule as build_keyword_workbook.py's vault_client_dir(): the
 * canonical `slug:` frontmatter first, then a case-insensitive folder-name match
 * with spaces treated as hyphens. Vault and pCloud folder names were aligned on
 * 29.07.2026, so the vault folder name IS the pCloud folder name.
 *
 * Never creates a client folder. One invented here syncs to every teammate, and a
 * near-miss spelling next to the real folder is worse than no archive at all, so an
 * unmatched client reports and skips.
 */

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");

const TEAM_VAULT_ENV = "AMAZON_AGENT_TEAM_VAULT";
const TEAM_VAULT_POINTER = path.join(REPO, "_local", "team-vault-path.txt");
const PCLOUD_ENV = "EW_PCLOUD_ROOT";
const PCLOUD_POINTER = path.join(REPO, "_local", "pcloud-path.txt");

function firstLine(file) {
  try {
    for (const line of fs.readFileSync(file, "utf8").split("\n")) {
      const t = line.trim();
      if (t && !t.startsWith("#")) return t;
    }
  } catch { /* missing pointer file is normal */ }
  return "";
}

function expand(p) {
  return p.startsWith("~") ? path.join(process.env.HOME || "", p.slice(1)) : p;
}

/** Root of the shared team vault, or "" when there is none on this machine. */
export function teamVaultRoot() {
  for (const c of [process.env[TEAM_VAULT_ENV] || "", firstLine(TEAM_VAULT_POINTER)]) {
    if (!c) continue;
    const root = expand(c);
    if (fs.existsSync(path.join(root, "Clients"))) return root;
  }
  return "";
}

/** Root of the pCloud Amazon Wizards share, or "" when not configured/mounted. */
export function pcloudRoot() {
  for (const c of [process.env[PCLOUD_ENV] || "", firstLine(PCLOUD_POINTER)]) {
    if (!c) continue;
    const root = expand(c);
    if (fs.existsSync(path.join(root, "1_Delivery", "1.1_Clients"))) return root;
  }
  return "";
}

/** The canonical `slug:` from a client folder's hub-note frontmatter, or "". */
function hubNoteSlug(clientsDir, name) {
  let head;
  try {
    head = fs.readFileSync(path.join(clientsDir, name, `${name}.md`), "utf8").slice(0, 2048);
  } catch {
    return "";
  }
  if (!head.startsWith("---")) return "";
  for (const line of head.split("\n").slice(1)) {
    if (line.trim() === "---") break;
    if (line.startsWith("slug:")) return line.slice(5).trim().toLowerCase();
  }
  return "";
}

/** Client FOLDER NAME for this slug, per the vault hub notes. "" when unmatched. */
export function vaultClientName(vaultRoot, slug) {
  if (!vaultRoot || !slug) return "";
  const clientsDir = path.join(vaultRoot, "Clients");
  const wanted = slug.trim().toLowerCase();
  let folders;
  try {
    folders = fs.readdirSync(clientsDir)
      .filter((n) => fs.statSync(path.join(clientsDir, n)).isDirectory())
      .sort();
  } catch {
    return "";
  }
  for (const n of folders) if (hubNoteSlug(clientsDir, n) === wanted) return n;
  for (const n of folders) if (n.toLowerCase().replace(/ /g, "-") === wanted) return n;
  return "";
}

/**
 * Split a POE export filename into {date, marketplace, niche}.
 * Handles all three emitted shapes:
 *   2026-07-21_poe_us-greens-powder_returns.csv
 *   2026-07-21_poe_us_super-greens-powder_related-niches.csv
 *   2026-07-21_us-greens-powder_NicheDetailsProductsTab.csv
 * Returns null when the name does not parse, so the caller can quarantine it
 * rather than guess a destination.
 */
export function parseExportName(name) {
  const m = name.match(/^(\d{4}-\d{2}-\d{2})_(?:poe_)?([a-z]{2})[-_](.+)_([^_]+)\.([a-z]+)$/i);
  if (!m) return null;
  return { date: m[1], marketplace: m[2].toLowerCase(), niche: m[3] };
}

function md5(file) {
  return crypto.createHash("md5").update(fs.readFileSync(file)).digest("hex");
}

/**
 * Mirror one client's opportunity-data into the pCloud archive.
 * Returns a summary; never throws for a missing client, reports instead.
 */
export function archiveClient(slug, { srcDir, dryRun = false, log = console.log } = {}) {
  const out = { slug, copied: 0, skipped: 0, unsorted: 0, errors: [], target: "" };

  const vault = teamVaultRoot();
  if (!vault) { out.errors.push(`no team vault (set ${TEAM_VAULT_ENV} or _local/team-vault-path.txt)`); return out; }

  const pcloud = pcloudRoot();
  if (!pcloud) { out.errors.push(`pCloud not configured or not mounted (set ${PCLOUD_ENV} or _local/pcloud-path.txt)`); return out; }

  const client = vaultClientName(vault, slug);
  if (!client) { out.errors.push(`slug "${slug}" matches no client folder in the vault - not archiving`); return out; }

  const clientDir = path.join(pcloud, "1_Delivery", "1.1_Clients", client);
  if (!fs.existsSync(clientDir)) { out.errors.push(`no pCloud folder "${client}" - not creating one`); return out; }

  const src = srcDir || path.join(REPO, "output", slug, "opportunity-data");
  if (!fs.existsSync(src)) { out.errors.push(`nothing to archive: ${src} does not exist`); return out; }

  const base = path.join(clientDir, "_Data", "opportunity-data");
  out.target = base;

  // Provenance for files whose name carries no marketplace/niche. Some clients
  // capture per product (output/<slug>/<product>/opportunity-data/) and emit
  // identical filenames in every product folder, so a flat _unsorted/ would have
  // them overwrite each other. Keying by the source folder keeps them distinct.
  const context = path.basename(path.dirname(src));

  // Copy one file, MD5-verified. Same discipline as the Drive delivery path, so a
  // half-finished copy is never mistaken for done.
  const copyFile = (from, to, label) => {
    if (fs.existsSync(to)) {
      if (md5(from) === md5(to)) { out.skipped++; return; }
      // Different content at the same path means two distinct captures are
      // colliding. Overwriting would silently destroy one, so refuse and report.
      out.errors.push(`collision, not overwritten: ${label} -> ${path.relative(base, to)}`);
      return;
    }
    log(`  ${dryRun ? "WOULD COPY" : "COPY"}  ${label}`);
    if (dryRun) { out.copied++; return; }
    try {
      fs.mkdirSync(path.dirname(to), { recursive: true });
      fs.copyFileSync(from, to);
      if (md5(from) !== md5(to)) { out.errors.push(`MD5 mismatch after copy: ${label}`); return; }
      out.copied++;
    } catch (e) {
      out.errors.push(`${label}: ${e.message}`);
    }
  };

  // Run-scoped subfolders (e.g. 2026-07-23_de-collagen-pulver_all-51/ with its own
  // niches/ and raw/) are copied verbatim. The archive mirrors the capture, it does
  // not reorganise it, so nothing depends on guessing what a nested file is.
  const copyTree = (fromDir, toDir, rel) => {
    for (const name of fs.readdirSync(fromDir).sort()) {
      if (name === ".DS_Store") continue;
      const from = path.join(fromDir, name);
      const to = path.join(toDir, name);
      if (fs.statSync(from).isDirectory()) copyTree(from, to, path.join(rel, name));
      else copyFile(from, to, path.join(rel, name));
    }
  };

  for (const name of fs.readdirSync(src).sort()) {
    if (name === ".DS_Store") continue;
    const from = path.join(src, name);
    const isDir = fs.statSync(from).isDirectory();

    // Directory names follow the same convention as files, so a run folder lands
    // beside the loose exports of the same niche instead of in a parallel tree.
    const parsed = parseExportName(isDir ? `${name}.json` : name);
    const dest = parsed
      ? path.join(base, parsed.marketplace, `${parsed.date}_${parsed.niche}`)
      : path.join(base, "_unsorted", context);
    if (!parsed) out.unsorted++;

    if (isDir) copyTree(from, path.join(dest, name), name);
    else copyFile(from, path.join(dest, name), name);
  }

  return out;
}

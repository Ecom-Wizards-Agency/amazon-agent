#!/usr/bin/env node
/*
 * Refresh the local Amazon help libraries from a logged-in CDP browser.
 *
 * Libraries (keys in help-capture.config.json):
 *   seller-help  "Amazon Seller Help/"            Seller Central Help articles
 *   ads-support  "Advertising Help After Login/"  Amazon Ads Support Center
 *   ads-docs     "Amazon Ads Help/"               Amazon Ads Advanced Tools Center
 *
 * Subcommands:
 *   plan    --library <key|all> [--include-linked] [--json]
 *           Files only. Lists every page with its tracked state
 *           (ok | shell | missing-file | uncaptured-linked) and counts.
 *   capture --library <key> [--only shells|changed|all|uncaptured] [--ids a,b] [--limit N] [--force]
 *           Browser. Visits each page in one task tab, writes staging files to
 *           _local/knowledge-sweep/help-refresh/<library>/<id>.md and <id>.json
 *           plus a run summary. Never writes into the tracked library.
 *   diff    --library <key>
 *           Files only. Compares staged bodies with tracked bodies and writes
 *           diff-report.md and diff-report.json in the staging dir.
 *   apply   --library <key> --approved [--include-new]
 *           Files only. Copies changed and shell-now-filled staged files over
 *           the tracked files and updates the index and missing list. Refuses
 *           without --approved. --include-new also lands staged pages that have
 *           no tracked file yet (for example captured linked URLs).
 *
 * BROWSER RULE (attended only). capture runs only in an attended session and
 * only through the session launcher, never directly and never from a
 * scheduled or Slack run:
 *
 *   node tools/browserctl/browserctl.mjs run -- node tools/knowledge/help_capture.mjs capture --library seller-help --only shells
 *
 * The launcher resolves the session (attended default, see
 * tools/browserctl/README.md "Shared Amazon session") and the task lock.
 * seller-help binds the US Seller Central region task; the ads libraries use a
 * plain "amazon-help-capture" task. The task page is released in a finally
 * block with outcome success or error. Any /ap/ page (sign-in, SSO, MFA, challenge) or an account
 * chooser stops the whole run with status login-required: complete login
 * through the browserctl authentication broker, then rerun (checkpointing skips
 * pages already staged ok today unless --force).
 *
 * Safety: read-only page reads. The extractor (help_extract.js) never clicks,
 * types or reads cookies or storage. Before staging, the detected account label
 * is replaced with the "Example Brand" placeholder and merchant tokens, amzn1.
 * identifiers, mons_sel_ parameter values, entityId values and non-Amazon
 * email addresses are redacted; counts land in each sidecar. plan, diff and
 * apply never load the browser modules.
 */

import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(HERE, "../..");
export const CONFIG_PATH = path.join(HERE, "help-capture.config.json");
export const EXTRACTOR = fs.readFileSync(path.join(HERE, "help_extract.js"), "utf8")
  .replace(/^\s*\/\*[\s\S]*?\*\/\s*/, "").trim().replace(/;\s*$/, "");

export const CLASSES = [
  "unchanged", "changed", "shell-now-filled", "still-shell", "new",
  "missing", "login-required", "extraction-failed",
];
const APPLY_CLASSES = new Set(["changed", "shell-now-filled"]);
const GENERIC_LABELS = new Set([
  "help", "amazon", "en", "united states", "new seller central", "seller central",
  "sponsored ads", "support center", "example brand",
]);
const ACCOUNT_CHOOSER_URL = /account-switcher|select-account|merchant-picker|choose-account/i;

// ---------------------------------------------------------------- config

export function loadConfig(configPath = CONFIG_PATH) {
  return JSON.parse(fs.readFileSync(configPath, "utf8"));
}

export function libraryConfig(config, key) {
  const lib = config.libraries?.[key];
  if (!lib) {
    throw new Error(`unknown library '${key}'. Known: ${Object.keys(config.libraries || {}).join(", ")}`);
  }
  return { ...config.defaults, ...lib, key, staging_root: config.staging_root };
}

export function todayLocal(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

// ---------------------------------------------------------------- markdown helpers

export function splitFrontmatter(text) {
  const source = String(text).replace(/^﻿/, "");
  const match = /^---\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/.exec(source);
  if (!match) return { entries: [], body: source };
  const entries = [];
  for (const line of match[1].split(/\r?\n/)) {
    const kv = /^([A-Za-z0-9_-]+):\s?(.*)$/.exec(line);
    if (kv) entries.push([kv[1], parseFrontmatterValue(kv[2])]);
  }
  return { entries, body: source.slice(match[0].length) };
}

export function parseFrontmatterValue(raw) {
  const value = String(raw).trim();
  if (value.startsWith("\"")) {
    try { return JSON.parse(value); } catch { /* fall through */ }
  }
  return value;
}

export function normalizeBody(body) {
  return String(body).split(/\r?\n/)
    .map((line) => line.replace(/[ \t ]+/g, " ").trim())
    .filter(Boolean)
    .join("\n");
}

/** sha256 of the whitespace-normalised body; frontmatter excluded. */
export function bodyHash(text) {
  return createHash("sha256").update(normalizeBody(splitFrontmatter(text).body)).digest("hex");
}

export function countWords(text) {
  return String(text).split(/\s+/).filter((token) => /[\p{L}\p{N}]/u.test(token)).length;
}

export function isShellBody(body, lib) {
  return new RegExp(lib.shell_line_pattern || "^[ \\t]*Loading[ \\t]*$", "m").test(String(body));
}

export function renderFrontmatter(entries) {
  return `---\n${entries.map(([key, value]) => `${key}: ${JSON.stringify(String(value))}`).join("\n")}\n---\n`;
}

export function renderArticle({ entries, title, body }) {
  const text = String(body || "").trim();
  return `${renderFrontmatter(entries)}\n# ${title}\n\n${text ? `${text}\n` : ""}`;
}

/** Drop a leading "# Title" line the extractor read from the page. */
export function stripLeadingTitle(markdown) {
  const text = String(markdown || "").replace(/^\s+/, "");
  const match = /^# ([^\n]+)\n*/.exec(text);
  if (!match) return { title: "", body: text.trim() };
  return { title: match[1].trim(), body: text.slice(match[0].length).trim() };
}

export function stagedFrontmatterEntries({ trackedEntries = [], lib, page, title, today }) {
  if (trackedEntries.length) {
    const entries = trackedEntries.map(([key, value]) => [key, key === "downloaded_at" ? today : value]);
    if (!entries.some(([key]) => key === "downloaded_at")) entries.push(["downloaded_at", today]);
    return entries;
  }
  const defaults = lib.frontmatter_defaults || {};
  const entries = [];
  for (const key of lib.frontmatter_keys || []) {
    let value;
    if (key === "title") value = page.title || title;
    else if (key === "source_url") value = page.url;
    else if (key === "downloaded_at") value = today;
    else if (key === "section") value = page.section || defaults.section;
    else value = defaults[key];
    if (value !== undefined && value !== null && value !== "") entries.push([key, value]);
  }
  return entries;
}

export function slugify(text) {
  return String(text).normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80).replace(/-+$/g, "") || "page";
}

// ---------------------------------------------------------------- scrub

const escapeRegex = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function scrubText(text, { accountLabel = "", lib }) {
  const counts = { account_label: 0, merchant_token: 0, amzn1: 0, mons_sel: 0, entity_id: 0, email: 0 };
  // Percent-decode encoded tokens (sign-in return_to URLs) so the patterns below see them.
  let out = String(text ?? "").replace(/\S*%[0-9A-Fa-f]{2}\S*/g, (token) => {
    let decoded = token;
    for (let i = 0; i < 3 && /%[0-9A-Fa-f]{2}/.test(decoded); i += 1) {
      try { decoded = decodeURIComponent(decoded); } catch { break; }
    }
    return decoded;
  });
  const placeholder = lib.account_placeholder || "Example Brand";
  const label = String(accountLabel || "").replace(/\s+/g, " ").trim();
  if (label.length >= 3 && label !== placeholder && !GENERIC_LABELS.has(label.toLowerCase())) {
    const pattern = label.split(" ").map(escapeRegex).join("\\s+");
    out = out.replace(new RegExp(`(?<![\\p{L}\\p{N}])${pattern}(?![\\p{L}\\p{N}])`, "gu"), () => { counts.account_label += 1; return placeholder; });
  }
  const publicIds = new Set(lib.public_marketplace_ids || []);
  out = out.replace(/\bA(?=[A-Z0-9]{0,12}[0-9])[A-Z0-9]{12,13}\b/g, (token) => {
    if (publicIds.has(token)) return token;
    counts.merchant_token += 1;
    return "MERCHANT_ID_REDACTED";
  });
  out = out.replace(/\bamzn1\.[A-Za-z0-9._-]*[A-Za-z0-9]/g, (token) => {
    if (token === "amzn1.REDACTED") return token;
    counts.amzn1 += 1;
    return "amzn1.REDACTED";
  });
  const keep = new Set(lib.keep_mons_sel_params || []);
  out = out.replace(/\b(mons_sel_[A-Za-z_]+)=([^&\s)"'\]<>]+)/g, (whole, name, value) => {
    if (keep.has(name) || value === "REDACTED") return whole;
    counts.mons_sel += 1;
    return `${name}=REDACTED`;
  });
  out = out.replace(/\b(entityId=)(ENTITY[A-Z0-9_]+)/g, (whole, prefix, value) => {
    if (value === "ENTITY_EXAMPLE") return whole;
    counts.entity_id += 1;
    return `${prefix}ENTITY_EXAMPLE`;
  });
  const allowed = [...(lib.allowed_email_domains || ["amazon.com"]), "example.com"].map((d) => d.toLowerCase());
  out = out.replace(/[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})/g, (whole, domain) => {
    const host = domain.toLowerCase();
    if (allowed.some((d) => host === d || host.endsWith(`.${d}`))) return whole;
    counts.email += 1;
    return "redacted@example.com";
  });
  return { text: out, counts };
}

export function mergeCounts(...all) {
  const total = {};
  for (const counts of all) for (const [key, value] of Object.entries(counts || {})) total[key] = (total[key] || 0) + value;
  return total;
}

// ---------------------------------------------------------------- pages and plan

export function normalizeUrl(url) {
  try {
    const u = new URL(String(url).trim());
    u.hash = "";
    return `${u.protocol}//${u.host.toLowerCase()}${u.pathname.replace(/\/+$/, "")}${u.search}`;
  } catch {
    return String(url || "").trim().replace(/\/+$/, "");
  }
}

export function pageIdFromUrl(url, pattern) {
  if (!pattern) return null;
  const match = new RegExp(pattern).exec(String(url || ""));
  return match ? match[1] : null;
}

function libPaths(lib, repoRoot) {
  const root = path.join(repoRoot, lib.root);
  return {
    root,
    index: path.join(root, lib.index),
    articles: path.join(root, lib.articles_dir),
    missing: lib.missing_list ? path.join(root, lib.missing_list) : null,
    linked: lib.linked_list ? path.join(root, lib.linked_list) : null,
  };
}

function listMarkdown(dirAbs, rootAbs) {
  if (!fs.existsSync(dirAbs)) return [];
  const out = [];
  for (const entry of fs.readdirSync(dirAbs, { withFileTypes: true })) {
    const abs = path.join(dirAbs, entry.name);
    if (entry.isDirectory()) out.push(...listMarkdown(abs, rootAbs));
    else if (entry.isFile() && entry.name.endsWith(".md")) out.push(path.relative(rootAbs, abs).split(path.sep).join("/"));
  }
  return out.sort();
}

export function readLinkedUrls(lib, repoRoot) {
  const { linked } = libPaths(lib, repoRoot);
  if (!linked || !fs.existsSync(linked)) return [];
  return fs.readFileSync(linked, "utf8").split(/\r?\n/).map((line) => line.trim()).filter((line) => /^https?:\/\//.test(line));
}

/** Every page the library knows: index entries, unindexed tracked files and (optionally) linked URLs. */
export function loadPages(lib, repoRoot, { includeLinked = false } = {}) {
  const paths = libPaths(lib, repoRoot);
  const indexText = fs.readFileSync(paths.index, "utf8");
  const index = JSON.parse(indexText);
  const files = listMarkdown(paths.articles, paths.root);
  const byUrl = new Map();
  const byIdSuffix = new Map();
  const frontmatterOf = new Map();
  for (const rel of files) {
    const { entries } = splitFrontmatter(fs.readFileSync(path.join(paths.root, rel), "utf8"));
    const fm = Object.fromEntries(entries);
    frontmatterOf.set(rel, fm);
    for (const key of ["source_url", "resolved_url"]) if (fm[key]) byUrl.set(normalizeUrl(fm[key]), rel);
    const suffix = /-([A-Z0-9]{6,})\.md$/.exec(rel);
    if (suffix) byIdSuffix.set(suffix[1], rel);
  }
  const f = lib.fields || {};
  const pages = [];
  const seen = new Map();
  const claimed = new Set();
  const addPage = (page) => {
    if (seen.has(page.id)) return seen.get(page.id);
    seen.set(page.id, page);
    pages.push(page);
    if (page.file) claimed.add(page.file);
    return page;
  };
  const resolveFile = (entry, id, ordinalGlob) => {
    const fromField = f.file && entry[f.file] ? String(entry[f.file]) : null;
    if (fromField) return fromField;
    const url = normalizeUrl(entry[f.url || "url"]);
    if (byUrl.has(url)) return byUrl.get(url);
    if (id && byIdSuffix.has(id)) return byIdSuffix.get(id);
    if (ordinalGlob) return files.find((rel) => rel.startsWith(ordinalGlob)) || null;
    return null;
  };
  if (lib.grouped_by_section) {
    for (const [section, entries] of Object.entries(index[lib.pages_path] || {})) {
      entries.forEach((entry, i) => {
        const seq = String(i + 1).padStart(3, "0");
        const id = `${section}-${seq}`;
        const file = resolveFile(entry, null, `${lib.articles_dir}/${section}/${seq}-`);
        addPage({ id, title: entry[f.title || "title"], url: entry[f.url || "url"], file, section, origin: "index" });
      });
    }
  } else {
    for (const listName of [lib.pages_path, ...(lib.extra_index_lists || [])]) {
      for (const entry of index[listName] || []) {
        const url = entry[f.url || "url"];
        const id = (f.id && entry[f.id]) || pageIdFromUrl(url, lib.id_from_url);
        if (!id) continue;
        const existing = seen.get(id);
        if (existing) {
          if (!existing.file) { existing.file = resolveFile(entry, id); if (existing.file) claimed.add(existing.file); }
          continue;
        }
        addPage({ id, title: entry[f.title || "title"], url, file: resolveFile(entry, id), section: null, origin: "index" });
      }
    }
  }
  for (const rel of files) {
    if (claimed.has(rel)) continue;
    const fm = frontmatterOf.get(rel) || {};
    const id = pageIdFromUrl(fm.source_url, lib.id_from_url) || /-([A-Z0-9]{6,})\.md$/.exec(rel)?.[1]
      || rel.replace(/\.md$/, "").replace(/[\\/]/g, "-");
    if (seen.has(id)) continue;
    addPage({ id, title: fm.title || id, url: fm.source_url || "", file: rel, section: fm.section || null, origin: "file-only" });
  }
  if (includeLinked) {
    for (const url of readLinkedUrls(lib, repoRoot)) {
      const id = pageIdFromUrl(url, lib.id_from_url) || slugify(url);
      if (seen.has(id)) continue;
      const file = byUrl.get(normalizeUrl(url)) || byIdSuffix.get(id) || null;
      addPage({ id, title: "", url, file, section: lib.frontmatter_defaults?.section || null, origin: "linked" });
    }
  }
  return { index, indexText, pages, files };
}

export function detectState(page, lib, repoRoot) {
  const abs = page.file ? path.join(repoRoot, lib.root, page.file) : null;
  if (!abs || !fs.existsSync(abs)) {
    return { state: page.origin === "linked" ? "uncaptured-linked" : "missing-file", words: 0, thin: false, bytes: 0 };
  }
  const text = fs.readFileSync(abs, "utf8");
  const { body } = splitFrontmatter(text);
  const words = countWords(body);
  const shell = isShellBody(body, lib);
  return {
    state: shell ? "shell" : "ok", words, thin: !shell && words < lib.min_body_words,
    bytes: Buffer.byteLength(text), body_sha256: bodyHash(text),
  };
}

export function planLibrary(lib, { repoRoot = REPO_ROOT, includeLinked = false } = {}) {
  const { pages } = loadPages(lib, repoRoot, { includeLinked });
  const rows = pages.map((page) => ({ ...page, ...detectState(page, lib, repoRoot) }));
  const counts = { total: rows.length, ok: 0, shell: 0, "missing-file": 0, "uncaptured-linked": 0, ok_thin: 0 };
  for (const row of rows) {
    counts[row.state] += 1;
    if (row.state === "ok" && row.thin) counts.ok_thin += 1;
  }
  return { library: lib.key, root: lib.root, include_linked: includeLinked, counts, pages: rows };
}

// ---------------------------------------------------------------- capture helpers (pure)

export function isLoginUrl(url, lib) {
  return new RegExp(lib.login_url_pattern || "/ap/").test(String(url || ""));
}

export function isAccountChooserUrl(url) {
  return ACCOUNT_CHOOSER_URL.test(String(url || ""));
}

/** A redirect away from the requested article id (for example to the hub) means the page is gone. */
export function redirectedAway(page, finalUrl, lib) {
  if (!lib.missing_on_redirect || !page.id || !finalUrl) return false;
  const want = pageIdFromUrl(page.url, lib.id_from_url) || page.id;
  try {
    const final = new URL(finalUrl);
    if (lib.origin && final.host !== new URL(lib.origin).host) return false;
    return !final.pathname.split("/").includes(want);
  } catch { return false; }
}

export function navigationUrl(page, lib) {
  const u = new URL(page.url);
  for (const [key, value] of Object.entries(lib.navigate_query || {})) {
    if (!u.searchParams.has(key)) u.searchParams.set(key, value);
  }
  return u.toString();
}

export function shouldSkipCheckpoint(sidecar, today, force = false) {
  return !force && !!sidecar && sidecar.status === "ok" && String(sidecar.captured_at || "").startsWith(today);
}

export function selectTargets(planPages, { only = "all", ids = null, onlyExplicit = false, diffReport = null } = {}) {
  let pool = planPages;
  if (ids && ids.length) {
    const wanted = new Set(ids);
    const unknown = ids.filter((id) => !planPages.some((page) => page.id === id));
    if (unknown.length) throw new Error(`unknown ids: ${unknown.join(", ")}`);
    pool = planPages.filter((page) => wanted.has(page.id));
    if (!onlyExplicit) return pool;
  }
  if (only === "shells") return pool.filter((page) => page.state === "shell");
  if (only === "uncaptured") return pool.filter((page) => page.state === "uncaptured-linked");
  if (only === "all") return pool.filter((page) => page.state !== "uncaptured-linked");
  if (only === "changed") {
    if (!diffReport) throw new Error("--only changed needs a diff-report.json; run diff first");
    const changed = new Set(diffReport.entries.filter((e) => e.class === "changed").map((e) => e.id));
    return pool.filter((page) => changed.has(page.id));
  }
  throw new Error(`unknown --only '${only}' (shells|changed|all|uncaptured)`);
}

/** Turn one extractor result into staged article text and its sidecar. */
export function buildStaged({ page, lib, result, trackedText = null, today, capturedAt }) {
  const sidecar = {
    id: page.id, url: page.url, title: page.title || "", file: page.file || null,
    status: result.status, word_count: result.wordCount || 0, thin: false,
    body_sha256: null, captured_at: capturedAt, container: result.container || "",
    final_url: "", scrub_counts: {}, error: result.error ? scrubText(result.error, { accountLabel: result.accountLabel, lib }).text : undefined,
  };
  const label = result.accountLabel || "";
  const finalUrl = scrubText(result.url || "", { accountLabel: label, lib });
  sidecar.final_url = finalUrl.text;
  if (!["ok", "shell"].includes(result.status)) {
    sidecar.scrub_counts = finalUrl.counts;
    return { text: null, sidecar };
  }
  const body = scrubText(result.bodyMarkdown || "", { accountLabel: label, lib });
  const stripped = stripLeadingTitle(body.text);
  const pageTitle = scrubText(result.title || "", { accountLabel: label, lib });
  const title = stripped.title || pageTitle.text || page.title || page.id;
  const trackedEntries = trackedText ? splitFrontmatter(trackedText).entries : [];
  const entries = stagedFrontmatterEntries({ trackedEntries, lib, page, title, today });
  const text = renderArticle({ entries, title, body: stripped.body });
  sidecar.title = title;
  sidecar.word_count = countWords(stripped.body);
  sidecar.thin = result.status === "ok" && sidecar.word_count < lib.min_body_words;
  sidecar.body_sha256 = bodyHash(text);
  sidecar.scrub_counts = mergeCounts(finalUrl.counts, body.counts, pageTitle.counts);
  if (sidecar.scrub_counts.account_label && !/\s/.test(label.trim())) {
    sidecar.review_notes = [`single-word account label replaced ${sidecar.scrub_counts.account_label} time(s); check the staged text for over-replacement`];
  }
  return { text, sidecar };
}

// ---------------------------------------------------------------- diff (pure)

export function classifyDiff({ stagedStatus, trackedState, stagedHash, trackedHash }) {
  if (stagedStatus === "login-required") return "login-required";
  if (stagedStatus === "missing") return "missing";
  if (stagedStatus === "shell") {
    return trackedState === "ok" ? "extraction-failed" : "still-shell";
  }
  if (stagedStatus !== "ok" || !stagedHash) return "extraction-failed";
  if (trackedState === "missing-file" || trackedState === "uncaptured-linked" || !trackedState) return "new";
  if (trackedState === "shell") return "shell-now-filled";
  return stagedHash === trackedHash ? "unchanged" : "changed";
}

// ---------------------------------------------------------------- index and missing list (pure)

/** Update bytes / downloaded_at on every index entry for these pages, only where the entry has the key. */
export function updateIndexEntries(index, lib, updates) {
  const f = lib.fields || {};
  const bytesKey = f.bytes || "bytes";
  const dateKey = f.downloaded_at || "downloaded_at";
  const changes = [];
  const lists = [];
  if (lib.grouped_by_section) {
    for (const [section, entries] of Object.entries(index[lib.pages_path] || {})) lists.push([`${lib.pages_path}.${section}`, entries]);
  } else {
    for (const name of [lib.pages_path, ...(lib.extra_index_lists || [])]) if (Array.isArray(index[name])) lists.push([name, index[name]]);
  }
  for (const update of updates) {
    const wantUrl = normalizeUrl(update.url);
    for (const [listName, entries] of lists) {
      entries.forEach((entry, position) => {
        const entryId = (f.id && entry[f.id]) || pageIdFromUrl(entry[f.url || "url"], lib.id_from_url);
        const match = (update.id && entryId === update.id)
          || (update.file && f.file && entry[f.file] === update.file)
          || (wantUrl && normalizeUrl(entry[f.url || "url"]) === wantUrl);
        if (!match) return;
        if (Object.hasOwn(entry, bytesKey) && update.bytes !== undefined && entry[bytesKey] !== update.bytes) {
          changes.push({ list: listName, position, id: update.id, key: bytesKey, from: entry[bytesKey], to: update.bytes });
          entry[bytesKey] = update.bytes;
        }
        if (Object.hasOwn(entry, dateKey) && update.downloaded_at && entry[dateKey] !== update.downloaded_at) {
          changes.push({ list: listName, position, id: update.id, key: dateKey, from: entry[dateKey], to: update.downloaded_at });
          entry[dateKey] = update.downloaded_at;
        }
      });
    }
  }
  return changes;
}

/** Build a new index entry shaped like the existing entries of the target list. */
export function newIndexEntry(template, values) {
  const keys = template ? Object.keys(template) : ["title", "url", "file", "bytes"];
  const entry = {};
  for (const key of keys) if (values[key] !== undefined) entry[key] = values[key];
  return entry;
}

export function appendMissing(list, entries) {
  const out = Array.isArray(list) ? [...list] : [];
  const have = new Set(out.map((item) => (item && typeof item === "object" ? item.id || item.url : item)));
  let added = 0;
  for (const entry of entries) {
    if (have.has(entry.id) || have.has(entry.url)) continue;
    out.push(entry);
    have.add(entry.id);
    added += 1;
  }
  return { list: out, added };
}

export function addMissingToIndex(index, entries) {
  const { list, added } = appendMissing(index.missing, entries);
  index.missing = list;
  if (Object.hasOwn(index, "missing_count")) index.missing_count = list.length;
  return added;
}

/** Serialise like the original file: same ASCII escaping and trailing newline. */
export function serializeJsonLike(originalText, value) {
  let text = JSON.stringify(value, null, 2);
  const original = String(originalText ?? "");
  if (original && !/[^\x00-\x7f]/.test(original)) {
    text = text.replace(/[\u0080-￿]/g, (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, "0")}`);
  }
  if (original.endsWith("\n")) text += "\n";
  return text;
}

export function newFilePath(lib, page, files) {
  const section = page.section || "";
  const prefix = lib.grouped_by_section ? `${lib.articles_dir}/${section}/` : `${lib.articles_dir}/`;
  let max = 0;
  for (const rel of files) {
    if (!rel.startsWith(prefix) || rel.slice(prefix.length).includes("/")) continue;
    const n = Number(/^(\d+)-/.exec(rel.slice(prefix.length))?.[1] || 0);
    if (n > max) max = n;
  }
  const name = (lib.new_file_pattern || "{seq}-{slug}-{id}.md")
    .replace("{section}/", "")
    .replace("{seq}", String(max + 1).padStart(3, "0"))
    .replace("{slug}", slugify(page.title || page.id))
    .replace("{id}", page.id);
  return `${prefix}${name}`;
}

// ---------------------------------------------------------------- staging IO

export function stagingDirFor(lib, repoRoot = REPO_ROOT) {
  return path.join(repoRoot, lib.staging_root, lib.key);
}

function readJson(file, fallback = null) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch { return fallback; }
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

const safeId = (id) => String(id).replace(/[^A-Za-z0-9._-]/g, "_");

export function readSidecars(stagingDir) {
  if (!fs.existsSync(stagingDir)) return [];
  return fs.readdirSync(stagingDir)
    .filter((name) => name.endsWith(".json") && !/^(diff-report|run-summary)/.test(name))
    .map((name) => readJson(path.join(stagingDir, name)))
    .filter((value) => value && value.id);
}

export function writeStaged(stagingDir, staged) {
  fs.mkdirSync(stagingDir, { recursive: true });
  const base = path.join(stagingDir, safeId(staged.sidecar.id));
  if (staged.text !== null) fs.writeFileSync(`${base}.md`, staged.text);
  else if (fs.existsSync(`${base}.md`)) fs.rmSync(`${base}.md`);
  writeJson(`${base}.json`, staged.sidecar);
}

// ---------------------------------------------------------------- commands

export function runDiff(lib, { repoRoot = REPO_ROOT, stagingDir = stagingDirFor(lib, repoRoot), now = new Date() } = {}) {
  const plan = planLibrary(lib, { repoRoot, includeLinked: true });
  const byId = new Map(plan.pages.map((page) => [page.id, page]));
  const entries = [];
  for (const sidecar of readSidecars(stagingDir).sort((a, b) => String(a.id).localeCompare(String(b.id)))) {
    const page = byId.get(sidecar.id) || { id: sidecar.id, title: sidecar.title, url: sidecar.url, file: null, state: null };
    const stagedFile = path.join(stagingDir, `${safeId(sidecar.id)}.md`);
    let stagedStatus = sidecar.status;
    let reason = sidecar.error || "";
    let stagedHash = sidecar.body_sha256 || null;
    if (["ok", "shell"].includes(stagedStatus)) {
      if (!fs.existsSync(stagedFile)) { stagedStatus = "extraction-failed"; reason = "staged markdown file missing"; }
      else if (bodyHash(fs.readFileSync(stagedFile, "utf8")) !== stagedHash) {
        stagedStatus = "extraction-failed"; reason = "staged markdown no longer matches its sidecar hash";
      }
    }
    const cls = classifyDiff({ stagedStatus, trackedState: page.state, stagedHash, trackedHash: page.body_sha256 || null });
    if (!reason && cls === "missing") reason = sidecar.final_url ? `final url ${sidecar.final_url}` : "not found";
    entries.push({
      id: sidecar.id, title: sidecar.title || page.title || "", url: page.url || sidecar.url, section: page.section || null,
      class: cls, tracked_state: page.state || null, tracked_file: page.file || null,
      staged_file: fs.existsSync(stagedFile) ? path.relative(repoRoot, stagedFile) : null,
      tracked_sha256: page.body_sha256 || null, staged_sha256: stagedHash,
      tracked_words: page.words || 0, staged_words: sidecar.word_count || 0,
      staged_status: sidecar.status, captured_at: sidecar.captured_at || null,
      final_url: sidecar.final_url || "", reason,
    });
  }
  const counts = Object.fromEntries(CLASSES.map((cls) => [cls, 0]));
  for (const entry of entries) counts[entry.class] += 1;
  const report = { library: lib.key, generated_at: now.toISOString(), staging_dir: path.relative(repoRoot, stagingDir), counts, entries };
  writeJson(path.join(stagingDir, "diff-report.json"), report);
  fs.writeFileSync(path.join(stagingDir, "diff-report.md"), renderDiffMarkdown(report));
  return report;
}

export function renderDiffMarkdown(report) {
  const lines = [`# Help capture diff: ${report.library}`, "", `Generated: ${report.generated_at}`, "", "## Counts", ""];
  for (const [cls, n] of Object.entries(report.counts)) lines.push(`- ${cls}: ${n}`);
  for (const cls of CLASSES) {
    const rows = report.entries.filter((entry) => entry.class === cls);
    if (!rows.length || cls === "unchanged") continue;
    lines.push("", `## ${cls} (${rows.length})`, "", "| id | title | tracked words | staged words | note |", "| --- | --- | --- | --- | --- |");
    for (const row of rows) {
      const cell = (value) => String(value ?? "").replace(/\|/g, "\\|");
      lines.push(`| ${cell(row.id)} | ${cell(row.title)} | ${row.tracked_words} | ${row.staged_words} | ${cell(row.reason)} |`);
    }
  }
  return `${lines.join("\n")}\n`;
}

export function runApply(lib, {
  repoRoot = REPO_ROOT, stagingDir = stagingDirFor(lib, repoRoot), approved = false, includeNew = false, today = todayLocal(),
} = {}) {
  if (!approved) {
    return { refused: true, message: "apply refused: pass --approved after reviewing diff-report.md" };
  }
  const report = readJson(path.join(stagingDir, "diff-report.json"));
  if (!report || report.library !== lib.key) throw new Error(`no diff-report.json for ${lib.key} in ${stagingDir}; run diff first`);
  const paths = libPaths(lib, repoRoot);
  const { index, indexText, files } = loadPages(lib, repoRoot, { includeLinked: true });
  const result = { written: [], created: [], skipped: [], index_changes: [], missing_added: 0, index_written: false, missing_file: null };
  const classes = new Set(APPLY_CLASSES);
  if (includeNew) classes.add("new");
  const updates = [];
  const knownFiles = [...files];
  for (const entry of report.entries) {
    if (!classes.has(entry.class)) continue;
    const stagedAbs = path.join(stagingDir, `${safeId(entry.id)}.md`);
    if (!fs.existsSync(stagedAbs)) { result.skipped.push({ id: entry.id, reason: "staged file missing" }); continue; }
    const text = fs.readFileSync(stagedAbs, "utf8");
    if (bodyHash(text) !== entry.staged_sha256) { result.skipped.push({ id: entry.id, reason: "staged file changed since diff; rerun diff" }); continue; }
    let rel = entry.tracked_file;
    if (entry.class === "new") {
      rel = rel || newFilePath(lib, { id: entry.id, title: entry.title, section: entry.section }, knownFiles);
      knownFiles.push(rel);
      if (fs.existsSync(path.join(paths.root, rel))) { result.skipped.push({ id: entry.id, reason: `target ${rel} already exists; rerun diff` }); continue; }
    } else {
      const trackedAbs = path.join(paths.root, rel);
      if (!fs.existsSync(trackedAbs) || bodyHash(fs.readFileSync(trackedAbs, "utf8")) !== entry.tracked_sha256) {
        result.skipped.push({ id: entry.id, reason: "tracked file changed since diff; rerun diff" }); continue;
      }
    }
    const abs = path.resolve(paths.root, rel);
    if (!abs.startsWith(paths.articles + path.sep)) { result.skipped.push({ id: entry.id, reason: `target ${rel} is outside ${lib.articles_dir}/` }); continue; }
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, text);
    const bytes = Buffer.byteLength(text);
    (entry.class === "new" ? result.created : result.written).push({ id: entry.id, class: entry.class, file: path.join(lib.root, rel), bytes });
    updates.push({ id: entry.id, url: entry.url, file: rel, bytes, downloaded_at: today });
    if (entry.class === "new" && lib.new_entries_list && Array.isArray(index[lib.new_entries_list])) {
      const list = index[lib.new_entries_list];
      const values = { title: entry.title, url: entry.url, file: rel, bytes, id: entry.id, downloaded_at: today };
      try { values.path = new URL(entry.url).pathname; } catch { /* keep */ }
      list.push(newIndexEntry(list[0], values));
      result.index_changes.push({ list: lib.new_entries_list, position: list.length - 1, id: entry.id, key: "(new entry)", to: rel });
    }
  }
  result.index_changes.push(...updateIndexEntries(index, lib, updates));
  const missing = report.entries.filter((entry) => entry.class === "missing")
    .map((entry) => ({ id: entry.id, title: entry.title, url: entry.url, reason: entry.reason || "missing", final_url: entry.final_url || "", detected_at: today }));
  if (missing.length) {
    // The index key is updated only where the library already keeps one; the
    // _index/*-missing.json list is created when absent.
    if (Array.isArray(index.missing)) {
      const before = index.missing.length;
      if (addMissingToIndex(index, missing)) result.index_changes.push({ list: "missing", key: "missing", from: before, to: index.missing.length });
    }
    if (paths.missing) {
      const originalText = fs.existsSync(paths.missing) ? fs.readFileSync(paths.missing, "utf8") : "";
      const current = originalText ? JSON.parse(originalText) : [];
      if (!Array.isArray(current)) throw new Error(`${lib.missing_list} is not a JSON array; refusing to overwrite it`);
      const merged = appendMissing(current, missing);
      if (merged.added || !originalText) {
        fs.mkdirSync(path.dirname(paths.missing), { recursive: true });
        fs.writeFileSync(paths.missing, serializeJsonLike(originalText || "\n", merged.list));
        result.missing_file = path.join(lib.root, lib.missing_list);
      }
      result.missing_added = merged.added;
    }
  }
  if (result.index_changes.length) {
    fs.writeFileSync(paths.index, serializeJsonLike(indexText, index));
    result.index_written = true;
  }
  return result;
}

async function runCapture(lib, opts) {
  const repoRoot = opts.repoRoot || REPO_ROOT;
  const stagingDir = stagingDirFor(lib, repoRoot);
  const today = todayLocal();
  const plan = planLibrary(lib, { repoRoot, includeLinked: Boolean(lib.linked_list) });
  const diffReport = readJson(path.join(stagingDir, "diff-report.json"));
  const selected = selectTargets(plan.pages, { only: opts.only, ids: opts.ids, onlyExplicit: opts.onlyExplicit, diffReport });
  const sidecars = new Map(readSidecars(stagingDir).map((s) => [s.id, s]));
  const skipped = selected.filter((page) => shouldSkipCheckpoint(sidecars.get(page.id), today, opts.force));
  let targets = selected.filter((page) => !skipped.includes(page));
  if (opts.limit) targets = targets.slice(0, opts.limit);
  const startedAt = new Date();
  const summary = {
    library: lib.key, status: "complete", started_at: startedAt.toISOString(), finished_at: null,
    only: opts.only, ids: opts.ids || null, selected: selected.length, skipped_checkpoint: skipped.length,
    targets: targets.length, visited: 0, ok: 0, thin: 0, shell: 0, missing: 0, login_required: 0, failed: 0,
    shells_remaining: 0, message: "",
  };
  const finish = () => {
    summary.finished_at = new Date().toISOString();
    const after = new Map(readSidecars(stagingDir).map((s) => [s.id, s]));
    summary.shells_remaining = plan.pages.filter((page) => page.state === "shell" && after.get(page.id)?.status !== "ok").length;
    const stamp = summary.started_at.replace(/[:.]/g, "-");
    writeJson(path.join(stagingDir, `run-summary-${stamp}.json`), summary);
    console.log(`visited=${summary.visited} ok=${summary.ok} thin=${summary.thin} shells_remaining=${summary.shells_remaining} `
      + `login_required=${summary.login_required} missing=${summary.missing} failed=${summary.failed} `
      + `skipped_checkpoint=${summary.skipped_checkpoint} status=${summary.status}`);
    if (summary.message) console.log(summary.message);
    return summary;
  };
  if (!targets.length) {
    summary.message = "nothing to capture";
    return finish();
  }

  // Browser modules load only here so plan/diff/apply and the tests never touch a session.
  const { ensureChrome, evaluate } = await import("../report-fetcher/cdp.mjs");
  const tabs = await import("../browserctl/task-tabs.mjs");
  await ensureChrome();
  const rt = lib.region_task || {};
  const spec = rt.kind === "seller-central-region"
    ? tabs.sellerCentralRegionTask({ marketplace: rt.marketplace, origin: rt.origin })
    : { taskId: tabs.taskIdFor(rt.workflow || "amazon-help-capture", `${lib.key}|${lib.origin}`),
      workflow: rt.workflow || "amazon-help-capture", initialUrl: "about:blank" };
  const taskPage = await tabs.acquireTaskPageWithRegionWait(spec);
  let outcome = "success";
  try {
    for (const page of targets) {
      summary.visited += 1;
      const trackedAbs = page.file ? path.join(repoRoot, lib.root, page.file) : null;
      const trackedText = trackedAbs && fs.existsSync(trackedAbs) ? fs.readFileSync(trackedAbs, "utf8") : null;
      let result;
      try {
        const nav = await taskPage.session.send("Page.navigate", { url: navigationUrl(page, lib) });
        if (nav?.errorText) throw new Error(`navigation failed: ${nav.errorText}`);
        result = await pollExtract(taskPage.session, evaluate, lib);
      } catch (error) {
        if (/^TASK_TAB_/.test(error?.code || "")) throw error;
        // cdp.mjs evaluate closes the session on its hard timeout; later pages cannot run.
        if (/timed out|closed|not open/i.test(error?.message || "")) {
          writeStaged(stagingDir, buildStaged({ page, lib, result: { status: "extraction-failed", error: error.message, url: "" }, today, capturedAt: new Date().toISOString() }));
          summary.failed += 1;
          throw error;
        }
        result = { status: "extraction-failed", error: error.message, url: "" };
      }
      if (result.status !== "login-required" && (isLoginUrl(result.url, lib) || isAccountChooserUrl(result.url))) {
        result = { ...result, status: "login-required" };
      }
      if (result.status !== "login-required" && result.status !== "extraction-failed" && redirectedAway(page, result.url, lib)) {
        result = { ...result, status: "missing", error: "redirected away from the article id" };
      }
      const staged = buildStaged({ page, lib, result, trackedText, today, capturedAt: new Date().toISOString() });
      writeStaged(stagingDir, staged);
      const s = staged.sidecar;
      console.error(`  ${page.id}: ${s.status}${s.thin ? " (thin)" : ""} words=${s.word_count} ${s.title ? `"${s.title.slice(0, 60)}"` : ""}`);
      if (s.status === "ok") { summary.ok += 1; if (s.thin) summary.thin += 1; }
      else if (s.status === "shell") summary.shell += 1;
      else if (s.status === "missing") summary.missing += 1;
      else if (s.status === "login-required") {
        summary.login_required += 1;
        summary.status = "login-required";
        summary.message = isAccountChooserUrl(result.url)
          ? `LOGIN REQUIRED: ${lib.origin} stopped at an account chooser (${s.final_url}). Select the account in the browser, then rerun.`
          : `LOGIN REQUIRED: ${lib.origin} redirected to sign-in (${s.final_url}). Complete login through browserctl auth, then rerun; pages already staged ok today are skipped.`;
        outcome = "error";
        break;
      } else summary.failed += 1;
    }
  } catch (error) {
    outcome = "error";
    summary.status = "error";
    summary.message = `capture stopped: ${error.message}`;
  } finally {
    await tabs.releaseTaskPage(taskPage, { outcome }).catch(() => {});
  }
  return finish();
}

async function pollExtract(session, evaluate, lib) {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const start = Date.now();
  const deadline = start + lib.poll_timeout_ms;
  const stableNeeded = Math.max(1, (lib.thin_stable_polls || 3) - 1);
  let last = null;
  let lastError = null;
  let prevWords = -1;
  let stable = 0;
  await sleep(Math.min(1500, lib.poll_interval_ms));
  for (;;) {
    let r = null;
    try {
      r = await evaluate(session, EXTRACTOR, 15000);
      lastError = null;
    } catch (error) {
      // The tab keeps navigating for a moment, which destroys the eval context.
      if (/^TASK_TAB_/.test(error?.code || "") || /TASK_TAB_/.test(error?.message || "")) throw error;
      if (!/Execution context was destroyed|Cannot find context|Inspected target navigated|context.*destroyed/i.test(error.message)) throw error;
      lastError = error;
    }
    if (r) {
      last = r;
      if (r.status === "login-required" || isLoginUrl(r.url, lib) || isAccountChooserUrl(r.url)) return { ...r, status: "login-required" };
      if (r.status === "missing") return r;
      if (r.status === "ok" && r.wordCount >= lib.min_body_words) return r;
      stable = r.status === "ok" && r.wordCount === prevWords ? stable + 1 : 0;
      prevWords = r.wordCount;
      if (r.status === "ok" && stable >= stableNeeded && Date.now() - start >= 5000) return r;
    }
    if (Date.now() >= deadline) break;
    await sleep(lib.poll_interval_ms);
  }
  if (!last) return { status: "extraction-failed", error: lastError?.message || "no extractor result", url: "" };
  return last;
}

// ---------------------------------------------------------------- CLI

function parseArgs(argv) {
  const opts = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) { opts._.push(arg); continue; }
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (next !== undefined && !next.startsWith("--")) { opts[key] = next; i += 1; } else opts[key] = true;
  }
  return opts;
}

function usage(code = 1) {
  console.error("usage: help_capture.mjs plan --library <seller-help|ads-support|ads-docs|all> [--include-linked] [--json]");
  console.error("       help_capture.mjs capture --library <key> [--only shells|changed|all|uncaptured] [--ids a,b] [--limit N] [--force]");
  console.error("       help_capture.mjs diff --library <key>");
  console.error("       help_capture.mjs apply --library <key> --approved [--include-new]");
  console.error("capture is attended only: node tools/browserctl/browserctl.mjs run -- node tools/knowledge/help_capture.mjs capture ...");
  process.exit(code);
}

function printPlan(plan, { json }) {
  if (!json) {
    const pad = (value, width) => String(value).slice(0, width).padEnd(width);
    console.log(`\n== ${plan.library} (${plan.root})`);
    console.log(`${pad("id", 24)} ${pad("state", 18)} ${pad("words", 6)} title`);
    for (const page of plan.pages) {
      console.log(`${pad(page.id, 24)} ${pad(page.state + (page.thin ? "*" : ""), 18)} ${pad(page.words, 6)} ${(page.title || page.url || "").slice(0, 70)}`);
    }
    console.log("(* = ok but under min_body_words)");
  }
  const counts = plan.counts;
  console.log(`counts ${plan.library}: total=${counts.total} ok=${counts.ok} (thin ${counts.ok_thin}) shell=${counts.shell} `
    + `missing-file=${counts["missing-file"]} uncaptured-linked=${counts["uncaptured-linked"]}`);
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const opts = parseArgs(rest);
  if (!cmd || opts.help) usage(cmd ? 0 : 1);
  const config = loadConfig();
  const key = opts.library;
  if (!key || key === true) { console.error("--library is required"); usage(); }

  if (cmd === "plan") {
    const keys = key === "all" ? Object.keys(config.libraries) : [key];
    const plans = keys.map((k) => planLibrary(libraryConfig(config, k), { includeLinked: Boolean(opts["include-linked"]) }));
    for (const plan of plans) printPlan(plan, { json: Boolean(opts.json) });
    const out = plans.map((plan) => ({
      library: plan.library, include_linked: plan.include_linked, counts: plan.counts,
      pages: plan.pages.map(({ id, title, url, file, state, words, thin, origin }) => ({ id, title, url, file, state, words, thin, origin })),
    }));
    console.log(JSON.stringify(out.length === 1 ? out[0] : out, null, opts.json ? 2 : 0));
    return 0;
  }
  if (key === "all") { console.error(`${cmd} takes one library key, not all`); return 1; }
  const lib = libraryConfig(config, key);

  if (cmd === "capture") {
    const only = typeof opts.only === "string" ? opts.only : "all";
    const ids = typeof opts.ids === "string" ? opts.ids.split(",").map((s) => s.trim()).filter(Boolean) : null;
    const limit = opts.limit ? Number(opts.limit) : 0;
    if (opts.limit && (!Number.isSafeInteger(limit) || limit <= 0)) { console.error("--limit must be a whole number above 0"); return 1; }
    const summary = await runCapture(lib, { only, onlyExplicit: typeof opts.only === "string", ids, limit, force: Boolean(opts.force) });
    if (summary.status === "login-required") return 2;
    return summary.status === "complete" && summary.failed === 0 ? 0 : 1;
  }
  if (cmd === "diff") {
    const report = runDiff(lib);
    console.log(`diff ${lib.key}: ${Object.entries(report.counts).map(([cls, n]) => `${cls}=${n}`).join(" ")}`);
    console.log(`wrote ${path.join(report.staging_dir, "diff-report.md")} and diff-report.json`);
    return 0;
  }
  if (cmd === "apply") {
    const result = runApply(lib, { approved: Boolean(opts.approved), includeNew: Boolean(opts["include-new"]) });
    if (result.refused) { console.error(result.message); return 1; }
    for (const item of result.written) console.log(`updated ${item.file} (${item.class}, ${item.bytes} bytes)`);
    for (const item of result.created) console.log(`created ${item.file} (${item.bytes} bytes)`);
    for (const item of result.skipped) console.log(`skipped ${item.id}: ${item.reason}`);
    for (const change of result.index_changes) console.log(`index ${change.list}[${change.position ?? ""}] ${change.id ?? ""} ${change.key}: ${change.from ?? ""} -> ${change.to}`);
    if (result.missing_file) console.log(`missing list ${result.missing_file}: +${result.missing_added}`);
    console.log(`apply ${lib.key}: updated=${result.written.length} created=${result.created.length} skipped=${result.skipped.length} `
      + `index_changes=${result.index_changes.length} index_written=${result.index_written}`);
    return 0;
  }
  usage();
  return 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((code) => process.exit(code ?? 0), (error) => {
    console.error(error?.stack || String(error));
    process.exit(1);
  });
}

#!/usr/bin/env node
/*
 * Check when each captured MAG SOP was last revised on its source site (a
 * BookStack instance behind a login), using the operator's logged-in CDP
 * browser. Every entry in "MAG SOPs/_index/sop-index.json" carries the page url.
 *
 * Subcommands:
 *   plan  [--index PATH] [--json]
 *         Files only. Lists active index entries (not archived, status not
 *         merged) with url, file, status and the last revised_at and
 *         revision_checked_at, plus counts.
 *   check [--index PATH] [--limit N] [--ids a,b | --files x,y] [--force]
 *         [--out "MAG SOPs/_index/sop-revisions.json"] [--delay-ms 1500]
 *         [--recapture --operator-approved]
 *         Browser. Visits each page in one task tab and records url, file,
 *         http_or_nav_status (ok | login-required | not-found | error),
 *         revised_at, revision_number, page_title and checked_at. Writes the
 *         output JSON (sorted by file; the only dates are checked_at and
 *         revised_at) and a summary line.
 *   diff  --previous PATH --current PATH
 *         Files only. Entries whose revised_at changed, newly not-found pages
 *         and new entries, with counts.
 *   apply --from "MAG SOPs/_index/sop-revisions.json" --approved [--index PATH]
 *         Files only. Writes revised_at and revision_checked_at into the
 *         matching index entries and nothing else. Refuses without --approved.
 *
 * Entry ids (for --ids and the checkpoint) are the index file path without
 * ".md", with "/" replaced by "__", for example "catalog__some-sop-page".
 *
 * BROWSER RULE (attended only). check runs only in an attended session and
 * only through the session launcher, never directly and never from a scheduled
 * or Slack run:
 *
 *   node tools/browserctl/browserctl.mjs run -- node tools/knowledge/sop_revision_check.mjs check --limit 20
 *
 * The launcher resolves the session (attended default, see
 * tools/browserctl/README.md "Shared Amazon session") and the task lock. check
 * acquires one plain task page (workflow "mag-sop-revision", keyed on the SOP
 * site origin taken from the first url; no Seller Central region task) and
 * releases it in a finally block. Pages are opened with Page.navigate at a
 * human pace: --delay-ms between pages, default 1500, minimum 1000.
 *
 * LOGIN. A login page (url containing /login, a password field, no BookStack
 * page body, or a redirect to another origin) stops the whole run with status
 * login-required and exit code 2. The tool never types anything: the operator
 * logs in once in the attended browser, then reruns. A checkpoint sidecar per
 * entry under _local/knowledge-sop-triage/revision-check/<id>.json lets the
 * rerun skip entries checked today (ok or not-found) unless --force.
 *
 * METADATA ONLY. check reads page metadata (title, the "Updated <time> by
 * <name>" line and the revision count) and never the editor's name. It never
 * re-captures a page body unless --recapture is given together with
 * --operator-approved, which needs an explicit per-run operator instruction
 * (re-capturing MAG pages is operator-gated). With both flags, entries whose
 * revised_at is after the index captured_at get their body written to
 * _local/knowledge-sop-triage/revision-check/recaptured/<file> for a human to
 * diff. The tracked SOP file is never overwritten.
 *
 * revised_at precision. The <time datetime> attribute gives an exact UTC
 * instant; BookStack's title attribute ("Mon, Mar 4, 2024 12:00 PM", server
 * local time) gives a day; relative text only ("3 weeks ago") gives the latest
 * possible day plus revised_earliest, and changed_since_capture is then
 * "uncertain" when the capture date falls inside that window.
 *
 * Index formatting. apply writes the index exactly as tools/slim_sop_index.py
 * does (json.dumps ensure_ascii=False, indent=1, trailing newline; keys in its
 * KEEP_FIELDS order). If the existing index does not round-trip byte for byte,
 * apply runs python3 tools/slim_sop_index.py afterwards to normalise it.
 *
 * plan, diff and apply never load the browser modules.
 */

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(HERE, "../..");
export const DEFAULT_INDEX = "MAG SOPs/_index/sop-index.json";
export const DEFAULT_OUT = "MAG SOPs/_index/sop-revisions.json";
export const CHECKPOINT_DIR = "_local/knowledge-sop-triage/revision-check";
export const WORKFLOW = "mag-sop-revision";
export const MIN_DELAY_MS = 1000;
export const STATUSES = ["ok", "login-required", "not-found", "error"];
/** Field order of tools/slim_sop_index.py KEEP_FIELDS (a test keeps them in sync). */
export const KEEP_FIELDS = [
  "title", "category", "chapter", "url", "captured_at", "file", "body_length", "image_count", "status",
  "superseded_by", "merge_into", "triaged_on", "flags", "knowledge_value", "revised_at", "revision_checked_at",
];
export const EXTRACTOR = fs.readFileSync(path.join(HERE, "sop_revision_extract.js"), "utf8")
  .replace(/^\s*\/\*[\s\S]*?\*\/\s*/, "").trim().replace(/;\s*$/, "");

/** The extractor expression with its options bound. */
export function extractorExpression({ wantBody = false } = {}) {
  return `(() => { const __SOP_REVISION_OPTIONS__ = ${JSON.stringify({ wantBody: Boolean(wantBody) })}; return ${EXTRACTOR}; })()`;
}

export function todayLocal(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

const resolvePath = (p, repoRoot = REPO_ROOT) => path.resolve(repoRoot, String(p));

function readJson(file, fallback = null) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch { return fallback; }
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

// ---------------------------------------------------------------- index (pure)

export function entryId(file) {
  return String(file || "").replace(/\.md$/, "").replace(/[^A-Za-z0-9._-]+/g, "__");
}

export function isActive(entry) {
  return Boolean(entry && entry.url && entry.file) && !entry.archived && entry.status !== "merged";
}

export function activeEntries(index) {
  return (index.captured || []).filter(isActive).map((entry) => ({ ...entry, id: entryId(entry.file) }));
}

export function planIndex(index, { checkpointDir = null, today = todayLocal() } = {}) {
  const all = index.captured || [];
  const active = activeEntries(index);
  const counts = {
    index_entries: all.length, active: active.length,
    excluded_archived: all.filter((e) => e.archived).length,
    excluded_merged: all.filter((e) => !e.archived && e.status === "merged").length,
    by_status: {}, with_revised_at: 0, with_revision_checked_at: 0, checked_today: 0,
  };
  const rows = active.map((entry) => {
    counts.by_status[entry.status || "none"] = (counts.by_status[entry.status || "none"] || 0) + 1;
    if (entry.revised_at) counts.with_revised_at += 1;
    if (entry.revision_checked_at) counts.with_revision_checked_at += 1;
    const sidecar = checkpointDir ? readJson(path.join(checkpointDir, `${entry.id}.json`)) : null;
    const checkedToday = shouldSkipCheckpoint(sidecar, today, false);
    if (checkedToday) counts.checked_today += 1;
    return {
      id: entry.id, file: entry.file, url: entry.url, status: entry.status || null,
      revised_at: entry.revised_at || null, revision_checked_at: entry.revision_checked_at || null,
      checked_today: checkedToday,
    };
  });
  return { counts, entries: rows };
}

export function selectEntries(active, { ids = null, files = null } = {}) {
  if (ids && files) throw new Error("use --ids or --files, not both");
  if (ids && ids.length) {
    const unknown = ids.filter((id) => !active.some((entry) => entry.id === id));
    if (unknown.length) throw new Error(`unknown or inactive ids: ${unknown.join(", ")}`);
    const wanted = new Set(ids);
    return active.filter((entry) => wanted.has(entry.id));
  }
  if (files && files.length) {
    const unknown = files.filter((file) => !active.some((entry) => entry.file === file));
    if (unknown.length) throw new Error(`unknown or inactive files: ${unknown.join(", ")}`);
    const wanted = new Set(files);
    return active.filter((entry) => wanted.has(entry.file));
  }
  return active;
}

export function originOf(url) {
  try { return new URL(url).origin; } catch { return ""; }
}

// ---------------------------------------------------------------- dates (pure)

const DAY_MS = 86_400_000;
const isoDate = (ms) => new Date(ms).toISOString().slice(0, 10);
const dayMs = (iso) => Date.parse(`${String(iso).slice(0, 10)}T00:00:00Z`);

function shiftDate(todayIso, unit, amount) {
  const d = new Date(dayMs(todayIso));
  if (unit === "year") d.setUTCFullYear(d.getUTCFullYear() - amount);
  else if (unit === "month") d.setUTCMonth(d.getUTCMonth() - amount);
  else if (unit === "week") d.setUTCDate(d.getUTCDate() - amount * 7);
  else if (unit === "day") d.setUTCDate(d.getUTCDate() - amount);
  return d.getTime();
}

/**
 * Convert BookStack/Carbon relative text ("3 weeks ago", "1 year ago",
 * "yesterday", "5 minutes ago") against the check date. Carbon floors, so
 * "N units ago" means N to N+1 units back: { latest, earliest } are the ISO
 * days bounding that window (inclusive).
 */
export function parseRelative(text, today) {
  const raw = String(text || "").trim().toLowerCase();
  if (!raw) return null;
  if (/^(just now|now|today)$/.test(raw)) return { latest: today, earliest: today };
  if (raw === "yesterday") { const d = isoDate(shiftDate(today, "day", 1)); return { latest: d, earliest: d }; }
  const m = /^(\d+|an?|one)\s+(second|minute|hour|day|week|month|year)s?\s+(ago|before|from now|after)$/.exec(raw);
  if (!m) return null;
  if (m[3] === "from now" || m[3] === "after") return { latest: today, earliest: today };
  const n = /^\d+$/.test(m[1]) ? Number(m[1]) : 1;
  const unit = m[2];
  if (unit === "second" || unit === "minute" || unit === "hour") {
    const hours = unit === "hour" ? n + 1 : 1;
    return { latest: today, earliest: isoDate(dayMs(today) - Math.ceil(hours / 24) * DAY_MS) };
  }
  return { latest: isoDate(shiftDate(today, unit, n)), earliest: isoDate(shiftDate(today, unit, n + 1)) };
}

/** Turn extractor output into the revised_* fields of a record. */
export function resolveRevised(result, today) {
  if (result && result.revisedIso) {
    return { revised_at: result.revisedIso, revised_precision: result.revisedPrecision || (result.revisedIso.length > 10 ? "exact" : "day") };
  }
  const relative = parseRelative(result?.revisedText, today);
  if (relative) {
    return relative.earliest === relative.latest
      ? { revised_at: relative.latest, revised_precision: "day" }
      : { revised_at: relative.latest, revised_precision: "relative", revised_earliest: relative.earliest };
  }
  return { revised_at: null, revised_precision: null };
}

/** changed | unchanged | uncertain | unknown, against the index captured_at. */
export function classifyChange(record, capturedAt) {
  if (!record || !record.revised_at || !capturedAt) return "unknown";
  const captured = Date.parse(capturedAt);
  if (!Number.isFinite(captured)) return "unknown";
  if (record.revised_precision === "exact") {
    const revised = Date.parse(record.revised_at);
    if (!Number.isFinite(revised)) return "unknown";
    return revised > captured ? "changed" : "unchanged";
  }
  const capturedDay = dayMs(isoDate(captured));
  const latest = dayMs(record.revised_at);
  const earliest = record.revised_precision === "relative" && record.revised_earliest ? dayMs(record.revised_earliest) : latest;
  if (earliest > capturedDay) return "changed";
  if (latest < capturedDay) return "unchanged";
  return "uncertain";
}

// ---------------------------------------------------------------- check records (pure)

export function isLoginUrl(url, origin) {
  const text = String(url || "");
  if (/\/login(?:[/?#]|$)/i.test(text) || /\/(?:saml2|oidc)\//i.test(text)) return true;
  if (origin && /^https?:/i.test(text) && originOf(text) && originOf(text) !== origin) return true;
  return false;
}

/** Final status for one extractor result; login wins over everything. */
export function statusFor(result, origin) {
  if (!result) return "error";
  if (result.status === "login-required" || result.isLogin || isLoginUrl(result.url, origin)) return "login-required";
  if (result.status === "not-found") return "not-found";
  if (result.status !== "ok") return "error";
  return "ok";
}

export function buildRecord({ entry, result, today, origin }) {
  const status = statusFor(result, origin);
  const record = {
    file: entry.file, url: entry.url, http_or_nav_status: status,
    revised_at: null, revised_precision: null, revision_number: null, page_title: null,
    changed_since_capture: "unknown", checked_at: today,
  };
  if (result && typeof result.title === "string" && result.title) record.page_title = result.title;
  if (status === "ok") {
    Object.assign(record, resolveRevised(result, today));
    if (Number.isInteger(result.revisionCount)) record.revision_number = result.revisionCount;
    record.changed_since_capture = classifyChange(record, entry.captured_at);
    if (!record.revised_at) {
      record.http_or_nav_status = "error";
      record.error = result.updatedFound ? `could not parse the Updated line "${String(result.revisedText).slice(0, 60)}"` : "no Updated meta line found";
    }
  } else if (status === "error") {
    record.error = String(result?.error || "extraction failed").slice(0, 300);
  }
  const finalUrl = result?.url ? String(result.url) : "";
  if (status !== "login-required" && finalUrl && finalUrl.replace(/[#?].*$/, "").replace(/\/+$/, "") !== String(entry.url).replace(/\/+$/, "")) {
    record.final_url = finalUrl.replace(/[#?].*$/, "");
  }
  if (!record.revised_earliest) delete record.revised_earliest;
  return record;
}

export function shouldSkipCheckpoint(sidecar, today, force = false) {
  return !force && !!sidecar && ["ok", "not-found"].includes(sidecar.http_or_nav_status) && sidecar.checked_at === today;
}

/** Merge new records into an existing output; one record per file, sorted by file. */
export function mergeRecords(existing, records) {
  const byFile = new Map();
  for (const record of existing?.entries || []) byFile.set(record.file, record);
  for (const record of records) byFile.set(record.file, record);
  return [...byFile.values()].sort((a, b) => (a.file < b.file ? -1 : a.file > b.file ? 1 : 0));
}

export function renderOutput({ indexPath, entries }) {
  return `${JSON.stringify({ index: indexPath, entries }, null, 1)}\n`;
}

export function summarize(records, extra = {}) {
  const summary = {
    checked: records.length, ok: 0, changed_since_capture: 0, uncertain: 0,
    "login-required": 0, "not-found": 0, error: 0, ...extra,
  };
  for (const record of records) {
    summary[record.http_or_nav_status] = (summary[record.http_or_nav_status] || 0) + 1;
    if (record.changed_since_capture === "changed") summary.changed_since_capture += 1;
    if (record.changed_since_capture === "uncertain") summary.uncertain += 1;
  }
  return summary;
}

// ---------------------------------------------------------------- diff (pure)

function revisedWindow(record) {
  const latest = dayMs(record.revised_at);
  const earliest = record.revised_precision === "relative" && record.revised_earliest ? dayMs(record.revised_earliest) : latest;
  return [earliest, latest];
}

/** A relative-only date moves with the check day; it counts as changed only when the windows do not overlap. */
export function revisedChanged(previous, current) {
  if (!previous?.revised_at || !current?.revised_at) return false;
  if (previous.revised_at === current.revised_at) return false;
  if (previous.revised_precision === "relative" || current.revised_precision === "relative") {
    const [a1, a2] = revisedWindow(previous);
    const [b1, b2] = revisedWindow(current);
    return a2 < b1 || b2 < a1;
  }
  if (previous.revised_precision !== current.revised_precision) {
    return previous.revised_at.slice(0, 10) !== current.revised_at.slice(0, 10);
  }
  return true;
}

export function diffRevisions(previous, current) {
  const before = new Map((previous?.entries || []).map((record) => [record.file, record]));
  const out = { revised_changed: [], newly_not_found: [], new_entries: [] };
  for (const record of current?.entries || []) {
    const old = before.get(record.file);
    if (record.http_or_nav_status === "not-found" && old?.http_or_nav_status !== "not-found") {
      out.newly_not_found.push({ file: record.file, url: record.url, previous_status: old ? old.http_or_nav_status : null });
    }
    if (!old) { out.new_entries.push({ file: record.file, url: record.url, status: record.http_or_nav_status, revised_at: record.revised_at }); continue; }
    if (revisedChanged(old, record)) {
      out.revised_changed.push({ file: record.file, url: record.url, from: old.revised_at, to: record.revised_at });
    }
  }
  out.counts = {
    revised_changed: out.revised_changed.length, newly_not_found: out.newly_not_found.length, new_entries: out.new_entries.length,
  };
  return out;
}

// ---------------------------------------------------------------- apply (pure + IO)

/** Same bytes as Python json.dumps(value, ensure_ascii=False, indent=1) + "\n" for this index's value types. */
export function serializeIndex(value) {
  return `${JSON.stringify(value, null, 1)}\n`;
}

/** Rebuild an entry with KEEP_FIELDS first (slim_sop_index.py order), then any other keys in their order. */
export function orderEntry(entry) {
  const out = {};
  for (const key of KEEP_FIELDS) if (Object.hasOwn(entry, key)) out[key] = entry[key];
  for (const key of Object.keys(entry)) if (!Object.hasOwn(out, key)) out[key] = entry[key];
  return out;
}

/**
 * Write revised_at and revision_checked_at from revision records into the
 * index entries with the same file and url. Only ok records with a revised_at
 * apply. Returns { changed, unchanged, skipped }.
 */
export function applyRevisionsToIndex(index, records) {
  const result = { changed: [], unchanged: 0, skipped: [] };
  const byFile = new Map();
  (index.captured || []).forEach((entry, position) => byFile.set(entry.file, position));
  for (const record of records) {
    if (record.http_or_nav_status !== "ok" || !record.revised_at || !record.checked_at) {
      result.skipped.push({ file: record.file, reason: `status ${record.http_or_nav_status}${record.revised_at ? "" : ", no revised_at"}` });
      continue;
    }
    const position = byFile.get(record.file);
    if (position === undefined) { result.skipped.push({ file: record.file, reason: "not in the index" }); continue; }
    const entry = index.captured[position];
    if (String(entry.url).replace(/\/+$/, "") !== String(record.url).replace(/\/+$/, "")) {
      result.skipped.push({ file: record.file, reason: "url differs from the index entry" });
      continue;
    }
    if (entry.revised_at === record.revised_at && entry.revision_checked_at === record.checked_at) { result.unchanged += 1; continue; }
    result.changed.push({ file: record.file, revised_at: [entry.revised_at ?? null, record.revised_at], revision_checked_at: [entry.revision_checked_at ?? null, record.checked_at] });
    index.captured[position] = orderEntry({ ...entry, revised_at: record.revised_at, revision_checked_at: record.checked_at });
  }
  return result;
}

export function runApply({ fromPath, indexPath, approved = false, repoRoot = REPO_ROOT, normalize = true } = {}) {
  if (!approved) return { refused: true, message: "apply refused: pass --approved after reviewing the check output and diff" };
  const revisions = readJson(fromPath);
  if (!revisions || !Array.isArray(revisions.entries)) throw new Error(`${fromPath} has no entries list; run check first`);
  const indexText = fs.readFileSync(indexPath, "utf8");
  const index = JSON.parse(indexText);
  const roundTrips = serializeIndex(index) === indexText;
  const result = applyRevisionsToIndex(index, revisions.entries);
  result.index_written = false;
  result.normalized = false;
  if (result.changed.length) {
    fs.writeFileSync(indexPath, serializeIndex(index));
    result.index_written = true;
    const slim = path.join(repoRoot, "tools/slim_sop_index.py");
    if (!roundTrips && normalize && path.resolve(indexPath) === path.join(repoRoot, DEFAULT_INDEX) && fs.existsSync(slim)) {
      const run = spawnSync("python3", [slim], { cwd: repoRoot, encoding: "utf8" });
      result.normalized = run.status === 0;
      result.normalize_output = `${run.stdout || ""}${run.stderr || ""}${run.error ? run.error.message : ""}`.trim();
    }
  }
  result.round_trips = roundTrips;
  return result;
}

// ---------------------------------------------------------------- recapture (pure)

export function renderRecapture({ entry, result, capturedAt }) {
  const title = result.title || entry.title || entry.file;
  const fm = [["title", title], ["category", entry.category || ""], ["source_url", entry.url], ["captured_at", capturedAt]];
  const body = String(result.bodyMarkdown || "").trim();
  return `---\n${fm.map(([k, v]) => `${k}: ${JSON.stringify(String(v))}`).join("\n")}\n---\n\n# ${title}\n\nSource: ${entry.url}\n\n${body ? `${body}\n` : ""}`;
}

/** Path under the recapture dir; refuses anything that would escape it. */
export function recapturePath(checkpointDir, file) {
  const base = path.resolve(checkpointDir, "recaptured");
  const target = path.resolve(base, file);
  if (!target.startsWith(base + path.sep)) throw new Error(`recapture path escapes ${base}: ${file}`);
  return target;
}

// ---------------------------------------------------------------- check (browser)

async function pollExtract(session, evaluate, { wantBody = false, timeoutMs = 20000, intervalMs = 1000 } = {}) {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const expression = extractorExpression({ wantBody });
  const deadline = Date.now() + timeoutMs;
  let last = null;
  let lastError = null;
  await sleep(Math.min(1000, intervalMs));
  for (;;) {
    let r = null;
    try {
      r = await evaluate(session, expression, 15000);
      lastError = null;
    } catch (error) {
      if (/TASK_TAB_/.test(`${error?.code || ""} ${error?.message || ""}`)) throw error;
      if (!/Execution context was destroyed|Cannot find context|Inspected target navigated|context.*destroyed/i.test(error.message)) throw error;
      lastError = error;
    }
    if (r) {
      last = r;
      const settled = r.readyState === "complete";
      if (r.status === "login-required" && (settled || r.hasPasswordField || /\/login/i.test(r.url))) return r;
      if (r.status === "not-found" && settled) return r;
      if (r.status === "ok" && r.updatedFound && (r.revisedIso || settled)) return r;
      if (r.status === "error") return r;
    }
    if (Date.now() >= deadline) break;
    await sleep(intervalMs);
  }
  if (!last) return { status: "error", error: lastError?.message || "no extractor result", url: "" };
  return last;
}

export async function runCheck(opts = {}) {
  const repoRoot = opts.repoRoot || REPO_ROOT;
  const indexPath = resolvePath(opts.index || DEFAULT_INDEX, repoRoot);
  const outPath = resolvePath(opts.out || DEFAULT_OUT, repoRoot);
  const checkpointDir = path.join(repoRoot, CHECKPOINT_DIR);
  const today = todayLocal();
  const delayMs = Math.max(MIN_DELAY_MS, opts.delayMs ?? 1500);
  const recapture = Boolean(opts.recapture);
  if (recapture && !opts.operatorApproved) {
    return { status: "refused", message: "--recapture needs --operator-approved: re-capturing MAG pages needs an explicit per-run operator instruction" };
  }
  const index = JSON.parse(fs.readFileSync(indexPath, "utf8"));
  const selected = selectEntries(activeEntries(index), { ids: opts.ids, files: opts.files });
  const skipped = selected.filter((entry) => shouldSkipCheckpoint(readJson(path.join(checkpointDir, `${entry.id}.json`)), today, opts.force));
  let targets = selected.filter((entry) => !skipped.includes(entry));
  if (opts.limit) targets = targets.slice(0, opts.limit);
  const origin = originOf(targets[0]?.url || selected[0]?.url || "");
  const offOrigin = targets.filter((entry) => originOf(entry.url) !== origin);
  if (offOrigin.length) throw new Error(`entries on another origin than ${origin}: ${offOrigin.map((e) => e.file).join(", ")}`);

  const records = [];
  const run = { status: "complete", message: "", recaptured: [] };
  const finish = () => {
    const existing = readJson(outPath);
    const merged = mergeRecords(existing, records);
    if (records.length || !existing) {
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, renderOutput({ indexPath: path.relative(repoRoot, indexPath).split(path.sep).join("/"), entries: merged }));
    }
    const summary = summarize(records, { skipped_checkpoint: skipped.length, selected: selected.length, targets: targets.length });
    if (run.status === "login-required") summary["login-required"] += 1;
    summary.status = run.status;
    summary.recaptured = run.recaptured.length;
    console.log(`checked=${summary.checked} ok=${summary.ok} changed_since_capture=${summary.changed_since_capture} uncertain=${summary.uncertain} `
      + `login-required=${summary["login-required"]} not-found=${summary["not-found"]} error=${summary.error} `
      + `skipped_checkpoint=${summary.skipped_checkpoint} recaptured=${summary.recaptured} status=${summary.status}`);
    console.log(`wrote ${path.relative(repoRoot, outPath)}`);
    if (run.message) console.log(run.message);
    return summary;
  };
  if (!targets.length) {
    run.message = "nothing to check";
    return finish();
  }

  // Browser modules load only here so plan/diff/apply and the tests never touch a session.
  const { ensureChrome, evaluate } = await import("../report-fetcher/cdp.mjs");
  const tabs = await import("../browserctl/task-tabs.mjs");
  await ensureChrome();
  const spec = { taskId: tabs.taskIdFor(WORKFLOW, origin), workflow: WORKFLOW, initialUrl: "about:blank" };
  const taskPage = await tabs.acquireTaskPageWithRegionWait(spec);
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  let outcome = "success";
  try {
    for (const [i, entry] of targets.entries()) {
      if (i > 0) await sleep(delayMs);
      let result;
      try {
        const nav = await taskPage.session.send("Page.navigate", { url: entry.url });
        if (nav?.errorText) throw new Error(`navigation failed: ${nav.errorText}`);
        result = await pollExtract(taskPage.session, evaluate);
      } catch (error) {
        if (/^TASK_TAB_/.test(error?.code || "")) throw error;
        if (/timed out|closed|not open/i.test(error?.message || "")) throw error;
        result = { status: "error", error: error.message, url: "" };
      }
      const record = buildRecord({ entry, result, today, origin });
      if (record.http_or_nav_status === "login-required") {
        run.status = "login-required";
        run.message = `LOGIN REQUIRED: ${origin} showed a login page (${String(result?.url || "").replace(/[?#].*$/, "")}). `
          + "Log in once yourself in the attended browser; this tool never types credentials. Then rerun: entries checked today are skipped.";
        outcome = "error";
        break;
      }
      if (recapture && record.changed_since_capture === "changed") {
        const full = await pollExtract(taskPage.session, evaluate, { wantBody: true, timeoutMs: 5000 });
        if (statusFor(full, origin) === "ok" && full.bodyMarkdown) {
          const target = recapturePath(path.join(repoRoot, CHECKPOINT_DIR), entry.file);
          fs.mkdirSync(path.dirname(target), { recursive: true });
          fs.writeFileSync(target, renderRecapture({ entry, result: full, capturedAt: new Date().toISOString().replace(/\.\d{3}Z$/, "Z") }));
          run.recaptured.push(path.relative(repoRoot, target));
        }
      }
      records.push(record);
      writeJson(path.join(checkpointDir, `${entry.id}.json`), { id: entry.id, ...record });
      console.error(`  ${entry.id}: ${record.http_or_nav_status} revised_at=${record.revised_at ?? "-"} ${record.changed_since_capture}`);
    }
  } catch (error) {
    outcome = "error";
    run.status = "error";
    run.message = `check stopped: ${error.message}`;
  } finally {
    await tabs.releaseTaskPage(taskPage, { outcome }).catch(() => {});
  }
  return finish();
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

const listArg = (value) => (typeof value === "string" ? value.split(",").map((s) => s.trim()).filter(Boolean) : null);

function usage(code = 1) {
  console.error("usage: sop_revision_check.mjs plan [--index PATH] [--json]");
  console.error("       sop_revision_check.mjs check [--index PATH] [--limit N] [--ids a,b | --files x,y] [--out PATH] [--delay-ms 1500] [--force] [--recapture --operator-approved]");
  console.error("       sop_revision_check.mjs diff --previous PATH --current PATH");
  console.error("       sop_revision_check.mjs apply --from PATH --approved [--index PATH]");
  console.error("check is attended only: node tools/browserctl/browserctl.mjs run -- node tools/knowledge/sop_revision_check.mjs check ...");
  process.exit(code);
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const opts = parseArgs(rest);
  if (!cmd || opts.help) usage(cmd ? 0 : 1);
  const indexPath = resolvePath(typeof opts.index === "string" ? opts.index : DEFAULT_INDEX);

  if (cmd === "plan") {
    const plan = planIndex(JSON.parse(fs.readFileSync(indexPath, "utf8")), { checkpointDir: path.join(REPO_ROOT, CHECKPOINT_DIR) });
    if (opts.json) { console.log(JSON.stringify(plan, null, 2)); return 0; }
    const pad = (value, width) => String(value ?? "-").slice(0, width).padEnd(width);
    console.log(`${pad("status", 13)} ${pad("revised_at", 20)} ${pad("checked", 10)} file`);
    for (const row of plan.entries) {
      console.log(`${pad(row.status, 13)} ${pad(row.revised_at, 20)} ${pad(row.revision_checked_at, 10)} ${row.file}`);
    }
    const c = plan.counts;
    console.log(`counts: index_entries=${c.index_entries} active=${c.active} excluded_archived=${c.excluded_archived} excluded_merged=${c.excluded_merged} `
      + `${Object.entries(c.by_status).map(([k, v]) => `status.${k}=${v}`).join(" ")} with_revised_at=${c.with_revised_at} `
      + `with_revision_checked_at=${c.with_revision_checked_at} checked_today=${c.checked_today}`);
    return 0;
  }
  if (cmd === "check") {
    const limit = opts.limit ? Number(opts.limit) : 0;
    if (opts.limit && (!Number.isSafeInteger(limit) || limit <= 0)) { console.error("--limit must be a whole number above 0"); return 1; }
    const delayMs = opts["delay-ms"] !== undefined ? Number(opts["delay-ms"]) : 1500;
    if (!Number.isFinite(delayMs) || delayMs < MIN_DELAY_MS) { console.error(`--delay-ms must be at least ${MIN_DELAY_MS}`); return 1; }
    const summary = await runCheck({
      index: indexPath, out: typeof opts.out === "string" ? opts.out : DEFAULT_OUT, limit, delayMs,
      ids: listArg(opts.ids), files: listArg(opts.files), force: Boolean(opts.force),
      recapture: Boolean(opts.recapture), operatorApproved: Boolean(opts["operator-approved"]),
    });
    if (summary.status === "refused") { console.error(summary.message); return 1; }
    if (summary.status === "login-required") return 2;
    return summary.status === "complete" && summary.error === 0 ? 0 : 1;
  }
  if (cmd === "diff") {
    if (typeof opts.previous !== "string" || typeof opts.current !== "string") usage();
    const previous = readJson(resolvePath(opts.previous));
    const current = readJson(resolvePath(opts.current));
    if (!previous || !current) { console.error("could not read --previous or --current"); return 1; }
    const diff = diffRevisions(previous, current);
    for (const row of diff.revised_changed) console.log(`revised  ${row.file}: ${row.from} -> ${row.to}`);
    for (const row of diff.newly_not_found) console.log(`notfound ${row.file} (was ${row.previous_status ?? "absent"})`);
    for (const row of diff.new_entries) console.log(`new      ${row.file} (${row.status}, revised_at ${row.revised_at ?? "-"})`);
    console.log(`diff: revised_changed=${diff.counts.revised_changed} newly_not_found=${diff.counts.newly_not_found} new_entries=${diff.counts.new_entries}`);
    return 0;
  }
  if (cmd === "apply") {
    const fromPath = resolvePath(typeof opts.from === "string" ? opts.from : DEFAULT_OUT);
    const result = runApply({ fromPath, indexPath, approved: Boolean(opts.approved) });
    if (result.refused) { console.error(result.message); return 1; }
    for (const row of result.changed) console.log(`updated ${row.file}: revised_at ${row.revised_at[0] ?? "-"} -> ${row.revised_at[1]}`);
    for (const row of result.skipped) console.log(`skipped ${row.file}: ${row.reason}`);
    if (!result.round_trips) console.log(`index did not round-trip; normalised with slim_sop_index.py: ${result.normalized} ${result.normalize_output || ""}`);
    console.log(`apply: changed=${result.changed.length} unchanged=${result.unchanged} skipped=${result.skipped.length} index_written=${result.index_written}`);
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

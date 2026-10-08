// Tests for tools/knowledge/sop_revision_check.mjs pure helpers, the in-page
// extractor (on fixture HTML) and the file-only plan, diff and apply commands.
// Run: node --test tools/knowledge/tests/sop-revision-check.test.mjs
// No browser, port or network is touched: sop_revision_check.mjs loads its
// browser modules only inside runCheck after its refusal and selection steps,
// which these tests never pass.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import vm from "node:vm";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import {
  EXTRACTOR, KEEP_FIELDS, REPO_ROOT, extractorExpression, entryId, isActive, activeEntries, planIndex,
  selectEntries, parseRelative, resolveRevised, classifyChange, isLoginUrl, statusFor, buildRecord,
  shouldSkipCheckpoint, mergeRecords, renderOutput, summarize, revisedChanged, diffRevisions,
  serializeIndex, orderEntry, applyRevisionsToIndex, runApply, renderRecapture, recapturePath, runCheck,
} from "../sop_revision_check.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIXTURES = path.join(HERE, "fixtures", "bookstack");
const KNOWLEDGE = path.resolve(HERE, "..");
const TODAY = "2026-10-06";
const ORIGIN = "https://sop.example.com";
const CAPTURED = "2026-05-12T07:07:49Z";

const read = (file) => fs.readFileSync(file, "utf8");
const fixture = (name) => read(path.join(FIXTURES, name));
const pythonAvailable = spawnSync("python3", ["--version"]).status === 0;

// ---- minimal HTML parser for the fixtures (fixture HTML is well formed)
const VOID = new Set(["br", "img", "hr", "input", "meta", "link"]);
const decode = (text) => text.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
  .replace(/&quot;/g, "\"").replace(/&#39;/g, "'").replace(/&nbsp;/g, " ");
function element(tag, attrs = {}) {
  return {
    nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], attrs,
    getAttribute(name) { return Object.hasOwn(this.attrs, name) ? this.attrs[name] : null; },
  };
}
function parseHtml(html) {
  const root = element("html-root");
  const stack = [root];
  const re = /<!--[\s\S]*?-->|<(\/?)([a-zA-Z0-9-]+)([^>]*)>|([^<]+)/g;
  let m;
  while ((m = re.exec(html))) {
    const top = stack[stack.length - 1];
    if (m[4] !== undefined) { top.childNodes.push({ nodeType: 3, nodeValue: decode(m[4]) }); continue; }
    if (!m[2]) continue;
    const tag = m[2].toLowerCase();
    if (m[1]) {
      while (stack.length > 1 && stack.pop().tagName !== tag.toUpperCase());
      continue;
    }
    const attrs = {};
    for (const a of m[3].matchAll(/([a-zA-Z-]+)(?:="([^"]*)")?/g)) attrs[a[1]] = a[2] === undefined ? "" : decode(a[2]);
    const el = element(tag, attrs);
    top.childNodes.push(el);
    if (!VOID.has(tag) && !m[3].trim().endsWith("/")) stack.push(el);
  }
  return root;
}
const helpers = () => vm.runInNewContext(EXTRACTOR, {});
const titleOf = (html) => /<title>([^<]*)<\/title>/.exec(html)?.[1] || "";
function extractFixture(name, context = {}) {
  const html = fixture(name);
  return helpers().extract(parseHtml(html), { docTitle: titleOf(html), readyState: "complete", ...context });
}

function tempIndex() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sop-revision-test-"));
  const indexPath = path.join(dir, "sop-index.json");
  fs.copyFileSync(path.join(FIXTURES, "tiny-index.json"), indexPath);
  return { dir, indexPath };
}

function okRecord(overrides = {}) {
  return {
    file: "catalog/add-items-to-the-store.md", url: `${ORIGIN}/books/catalog/page/add-items-to-the-store`,
    http_or_nav_status: "ok", revised_at: "2026-08-14T07:30:00Z", revised_precision: "exact",
    revision_number: 7, page_title: "Add Items To The Store", changed_since_capture: "changed", checked_at: TODAY,
    ...overrides,
  };
}

// ---------------------------------------------------------------- extractor

test("EXTRACTOR compiles, binds its options and is a plain helper bag outside a browser", () => {
  assert.doesNotThrow(() => new Function(`return ${EXTRACTOR}`));
  assert.doesNotThrow(() => new Function(`return ${extractorExpression({ wantBody: true })}`));
  const h = helpers();
  for (const name of ["extract", "toMarkdown", "parseAbsolute", "readUpdated", "readRevisionCount"]) {
    assert.equal(typeof h[name], "function", name);
  }
  // With the option wrapper and still no document, the helpers come back unchanged.
  assert.equal(typeof vm.runInNewContext(extractorExpression({ wantBody: true }), {}).extract, "function");
});

test("title attribute: revised day, revision number, title and body, never the editor name", () => {
  const r = extractFixture("page-title.html", { url: `${ORIGIN}/books/catalog/page/add-items-to-the-store`, wantBody: true });
  assert.equal(r.status, "ok");
  assert.equal(r.title, "Add Items To The Store");
  assert.equal(r.revisedIso, "2024-03-04");
  assert.equal(r.revisedPrecision, "day");
  assert.equal(r.revisedSource, "title");
  assert.equal(r.revisedText, "2 years ago");
  assert.equal(r.revisionCount, 7);
  assert.equal(r.bodyMarkdown, fixture("page-title.expected.md").trim());
  assert.equal(JSON.stringify(r).includes("Example Editor"), false);
  assert.equal(r.bodyMarkdown.includes("Footer text"), false);
  const metaOnly = extractFixture("page-title.html", { url: `${ORIGIN}/books/catalog/page/add-items-to-the-store` });
  assert.equal(metaOnly.bodyMarkdown, "", "body only when asked");
});

test("datetime attribute wins and becomes an exact UTC instant", () => {
  const r = extractFixture("page-datetime.html", { url: `${ORIGIN}/books/general/page/datetime-page` });
  assert.equal(r.status, "ok");
  assert.equal(r.revisedIso, "2026-08-14T07:30:00Z");
  assert.equal(r.revisedPrecision, "exact");
  assert.equal(r.revisedSource, "datetime");
  assert.equal(r.revisionCount, null);
});

test("relative text only: the extractor reports it, the Node side converts it against the check date", () => {
  const r = extractFixture("page-relative.html", { url: `${ORIGIN}/books/general/page/relative-page` });
  assert.equal(r.status, "ok");
  assert.equal(r.revisedIso, "");
  assert.equal(r.revisedSource, "relative");
  assert.equal(r.revisedText, "3 weeks ago");
  assert.equal(r.revisionCount, 3, "number inside the /revisions link");
  assert.deepEqual(resolveRevised(r, TODAY), { revised_at: "2026-09-15", revised_precision: "relative", revised_earliest: "2026-09-08" });
});

test("parseAbsolute handles BookStack title and ISO forms and rejects junk", () => {
  const { parseAbsolute } = helpers();
  assert.deepEqual({ ...parseAbsolute("Mon, Mar 4, 2024 12:00 PM") }, { iso: "2024-03-04", precision: "day" });
  assert.deepEqual({ ...parseAbsolute("2024-03-04 12:00:00") }, { iso: "2024-03-04", precision: "day" });
  assert.deepEqual({ ...parseAbsolute("2024-03-04T23:30:00-02:00") }, { iso: "2024-03-05T01:30:00Z", precision: "exact" });
  assert.deepEqual({ ...parseAbsolute("4 September 2025") }, { iso: "2025-09-04", precision: "day" });
  assert.equal(parseAbsolute("Feb 30, 2024"), null);
  assert.equal(parseAbsolute("3 weeks ago"), null);
  assert.equal(parseAbsolute(""), null);
});

test("login and not-found pages are detected", () => {
  const login = extractFixture("login.html", { url: `${ORIGIN}/login` });
  assert.equal(login.status, "login-required");
  assert.equal(login.isLogin, true);
  assert.equal(login.hasPasswordField, true);
  // A password field alone is enough, whatever the url.
  assert.equal(extractFixture("login.html", { url: `${ORIGIN}/books/x/page/y` }).status, "login-required");
  const missing = extractFixture("not-found.html", { url: `${ORIGIN}/books/x/page/gone` });
  assert.equal(missing.status, "not-found");
  // No page body and no not-found signal means the session is not showing the page.
  const bare = helpers().extract(parseHtml("<html><body><main><p>Welcome</p></main></body></html>"), { url: `${ORIGIN}/`, docTitle: "Example SOPs" });
  assert.equal(bare.status, "login-required");
  const status404 = extractFixture("page-datetime.html", { url: `${ORIGIN}/books/x/page/y`, httpStatus: 404 });
  assert.equal(status404.status, "not-found");
});

test("isLoginUrl and statusFor: /login, SSO paths and an off-origin redirect stop the run", () => {
  assert.equal(isLoginUrl(`${ORIGIN}/login`, ORIGIN), true);
  assert.equal(isLoginUrl(`${ORIGIN}/login?redirect=1`, ORIGIN), true);
  assert.equal(isLoginUrl(`${ORIGIN}/saml2/login`, ORIGIN), true);
  assert.equal(isLoginUrl("https://idp.example.org/authorize", ORIGIN), true);
  assert.equal(isLoginUrl(`${ORIGIN}/books/catalog/page/login-tips`, ORIGIN), false);
  assert.equal(statusFor({ status: "ok", url: "https://idp.example.org/x" }, ORIGIN), "login-required");
  assert.equal(statusFor({ status: "not-found", url: `${ORIGIN}/x` }, ORIGIN), "not-found");
  assert.equal(statusFor({ status: "error", url: "" }, ORIGIN), "error");
  assert.equal(statusFor(null, ORIGIN), "error");
});

// ---------------------------------------------------------------- dates and classification

test("parseRelative converts Carbon relative text against a fixed date", () => {
  assert.deepEqual(parseRelative("3 weeks ago", TODAY), { latest: "2026-09-15", earliest: "2026-09-08" });
  assert.deepEqual(parseRelative("1 year ago", TODAY), { latest: "2025-10-06", earliest: "2024-10-06" });
  assert.deepEqual(parseRelative("2 months ago", TODAY), { latest: "2026-08-06", earliest: "2026-07-06" });
  assert.deepEqual(parseRelative("5 days ago", TODAY), { latest: "2026-10-01", earliest: "2026-09-30" });
  assert.deepEqual(parseRelative("an hour ago", TODAY), { latest: TODAY, earliest: "2026-10-05" });
  assert.deepEqual(parseRelative("yesterday", TODAY), { latest: "2026-10-05", earliest: "2026-10-05" });
  assert.deepEqual(parseRelative("Just now", TODAY), { latest: TODAY, earliest: TODAY });
  assert.equal(parseRelative("last spring", TODAY), null);
  assert.deepEqual(resolveRevised({ revisedText: "yesterday" }, TODAY), { revised_at: "2026-10-05", revised_precision: "day" });
  assert.deepEqual(resolveRevised({ revisedText: "" }, TODAY), { revised_at: null, revised_precision: null });
});

test("classifyChange compares revised_at with the index captured_at at the right precision", () => {
  assert.equal(classifyChange({ revised_at: "2026-05-12T08:00:00Z", revised_precision: "exact" }, CAPTURED), "changed");
  assert.equal(classifyChange({ revised_at: "2026-05-12T07:00:00Z", revised_precision: "exact" }, CAPTURED), "unchanged");
  assert.equal(classifyChange({ revised_at: "2026-05-13", revised_precision: "day" }, CAPTURED), "changed");
  assert.equal(classifyChange({ revised_at: "2026-05-11", revised_precision: "day" }, CAPTURED), "unchanged");
  assert.equal(classifyChange({ revised_at: "2026-05-12", revised_precision: "day" }, CAPTURED), "uncertain");
  assert.equal(classifyChange({ revised_at: "2026-09-15", revised_precision: "relative", revised_earliest: "2026-09-08" }, CAPTURED), "changed");
  assert.equal(classifyChange({ revised_at: "2026-06-06", revised_precision: "relative", revised_earliest: "2026-05-06" }, CAPTURED), "uncertain");
  assert.equal(classifyChange({ revised_at: "2025-10-06", revised_precision: "relative", revised_earliest: "2024-10-06" }, CAPTURED), "unchanged");
  assert.equal(classifyChange({ revised_at: null }, CAPTURED), "unknown");
  assert.equal(classifyChange({ revised_at: "2026-05-13", revised_precision: "day" }, ""), "unknown");
});

// ---------------------------------------------------------------- records, checkpoint, output

test("buildRecord keeps only the agreed fields and flags a missing Updated line as an error", () => {
  const entry = { file: "catalog/add-items-to-the-store.md", url: `${ORIGIN}/books/catalog/page/add-items-to-the-store`, captured_at: CAPTURED };
  const result = extractFixture("page-datetime.html", { url: entry.url });
  const record = buildRecord({ entry, result, today: TODAY, origin: ORIGIN });
  assert.deepEqual(record, {
    file: entry.file, url: entry.url, http_or_nav_status: "ok", revised_at: "2026-08-14T07:30:00Z",
    revised_precision: "exact", revision_number: null, page_title: "Datetime Page",
    changed_since_capture: "changed", checked_at: TODAY,
  });
  const noMeta = buildRecord({ entry, result: { ...result, revisedIso: "", revisedText: "", updatedFound: false }, today: TODAY, origin: ORIGIN });
  assert.equal(noMeta.http_or_nav_status, "error");
  assert.match(noMeta.error, /no Updated meta line/);
  const redirected = buildRecord({ entry, result: { ...result, url: `${ORIGIN}/books/catalog/page/renamed-page?x=1` }, today: TODAY, origin: ORIGIN });
  assert.equal(redirected.final_url, `${ORIGIN}/books/catalog/page/renamed-page`);
  const login = buildRecord({ entry, result: { status: "ok", url: `${ORIGIN}/login` }, today: TODAY, origin: ORIGIN });
  assert.equal(login.http_or_nav_status, "login-required");
  assert.equal(login.final_url, undefined);
});

test("checkpoint skips ok and not-found entries checked today unless forced", () => {
  assert.equal(shouldSkipCheckpoint({ http_or_nav_status: "ok", checked_at: TODAY }, TODAY), true);
  assert.equal(shouldSkipCheckpoint({ http_or_nav_status: "not-found", checked_at: TODAY }, TODAY), true);
  assert.equal(shouldSkipCheckpoint({ http_or_nav_status: "ok", checked_at: TODAY }, TODAY, true), false);
  assert.equal(shouldSkipCheckpoint({ http_or_nav_status: "ok", checked_at: "2026-10-05" }, TODAY), false);
  assert.equal(shouldSkipCheckpoint({ http_or_nav_status: "error", checked_at: TODAY }, TODAY), false);
  assert.equal(shouldSkipCheckpoint(null, TODAY), false);
});

test("output merges by file, sorts by file and renders the same bytes twice", () => {
  const existing = { entries: [okRecord({ file: "z/last.md" }), okRecord({ file: "a/first.md", revised_at: "2026-01-01", revised_precision: "day" })] };
  const merged = mergeRecords(existing, [okRecord({ file: "a/first.md" }), okRecord({ file: "m/middle.md" })]);
  assert.deepEqual(merged.map((r) => r.file), ["a/first.md", "m/middle.md", "z/last.md"]);
  assert.equal(merged[0].revised_at, "2026-08-14T07:30:00Z");
  const once = renderOutput({ indexPath: "MAG SOPs/_index/sop-index.json", entries: merged });
  const twice = renderOutput({ indexPath: "MAG SOPs/_index/sop-index.json", entries: mergeRecords(JSON.parse(once), []) });
  assert.equal(once, twice);
  assert.equal(/generated_at|started_at|finished_at/.test(once), false);
  const summary = summarize([okRecord(), okRecord({ changed_since_capture: "uncertain" }), okRecord({ http_or_nav_status: "not-found", changed_since_capture: "unknown" })]);
  assert.deepEqual({ checked: summary.checked, ok: summary.ok, changed: summary.changed_since_capture, uncertain: summary.uncertain, nf: summary["not-found"] },
    { checked: 3, ok: 2, changed: 1, uncertain: 1, nf: 1 });
});

// ---------------------------------------------------------------- plan and selection

test("plan lists active entries only (not archived, not merged) with counts", () => {
  const index = JSON.parse(fixture("tiny-index.json"));
  const plan = planIndex(index, { today: TODAY });
  assert.deepEqual(plan.counts, {
    index_entries: 4, active: 2, excluded_archived: 2, excluded_merged: 0,
    by_status: { "needs-update": 1, superseded: 1 }, with_revised_at: 0, with_revision_checked_at: 0, checked_today: 0,
  });
  assert.deepEqual(plan.entries.map((e) => e.id), ["catalog__add-items-to-the-store", "general__relative-page"]);
  assert.equal(isActive({ url: "u", file: "f.md", status: "merged" }), false);
  assert.equal(entryId("_archive/catalog/x y.md"), "_archive__catalog__x__y");
});

test("selectEntries honours --ids and --files and rejects unknown or inactive ones", () => {
  const active = activeEntries(JSON.parse(fixture("tiny-index.json")));
  assert.deepEqual(selectEntries(active, { ids: ["general__relative-page"] }).map((e) => e.file), ["general/relative-page.md"]);
  assert.deepEqual(selectEntries(active, { files: ["catalog/add-items-to-the-store.md"] }).map((e) => e.id), ["catalog__add-items-to-the-store"]);
  assert.throws(() => selectEntries(active, { ids: ["_archive__catalog__archived-page"] }), /unknown or inactive ids/);
  assert.throws(() => selectEntries(active, { files: ["nope.md"] }), /unknown or inactive files/);
  assert.throws(() => selectEntries(active, { ids: ["a"], files: ["b"] }), /not both/);
  assert.equal(selectEntries(active).length, 2);
});

// ---------------------------------------------------------------- diff

test("diff reports revised changes, newly not-found pages and new entries", () => {
  const previous = { entries: [
    okRecord({ file: "a.md", revised_at: "2026-01-01", revised_precision: "day" }),
    okRecord({ file: "b.md", revised_at: "2026-09-15", revised_precision: "relative", revised_earliest: "2026-09-08" }),
    okRecord({ file: "c.md" }),
    okRecord({ file: "d.md", revised_at: "2026-08-14T07:30:00Z" }),
  ] };
  const current = { entries: [
    okRecord({ file: "a.md", revised_at: "2026-09-01", revised_precision: "day" }),
    okRecord({ file: "b.md", revised_at: "2026-09-22", revised_precision: "relative", revised_earliest: "2026-09-15" }),
    okRecord({ file: "c.md", http_or_nav_status: "not-found", revised_at: null }),
    okRecord({ file: "d.md", revised_at: "2026-08-14", revised_precision: "day" }),
    okRecord({ file: "e.md" }),
    okRecord({ file: "f.md", http_or_nav_status: "not-found", revised_at: null }),
  ] };
  const diff = diffRevisions(previous, current);
  assert.deepEqual(diff.counts, { revised_changed: 1, newly_not_found: 2, new_entries: 2 });
  assert.deepEqual(diff.revised_changed[0], { file: "a.md", url: okRecord().url, from: "2026-01-01", to: "2026-09-01" });
  assert.deepEqual(diff.newly_not_found.map((r) => [r.file, r.previous_status]), [["c.md", "ok"], ["f.md", null]]);
  assert.deepEqual(diff.new_entries.map((r) => r.file), ["e.md", "f.md"]);
  assert.equal(revisedChanged(
    { revised_at: "2026-06-01", revised_precision: "relative", revised_earliest: "2026-05-01" },
    { revised_at: "2026-09-01", revised_precision: "relative", revised_earliest: "2026-08-01" }), true);
});

// ---------------------------------------------------------------- apply

test("KEEP_FIELDS matches tools/slim_sop_index.py", () => {
  const source = read(path.join(REPO_ROOT, "tools/slim_sop_index.py"));
  const block = /KEEP_FIELDS = \[([\s\S]*?)\]/.exec(source)[1];
  assert.deepEqual([...block.matchAll(/"([^"]+)"/g)].map((m) => m[1]), KEEP_FIELDS);
});

test("serializeIndex reproduces the Python index bytes", () => {
  const text = fixture("tiny-index.json");
  assert.equal(serializeIndex(JSON.parse(text)), text);
  const tricky = { s: "tab\tnew\nline \"q\" back\\ ctrl\u0001 é “x”  ", n: [1, -2, 0], e: [], o: {}, z: null, b: true };
  const js = serializeIndex(tricky);
  if (pythonAvailable) {
    const py = spawnSync("python3", ["-c", "import json,sys; d=json.loads(sys.stdin.read()); sys.stdout.write(json.dumps(d, ensure_ascii=False, indent=1) + '\\n')"],
      { input: js, encoding: "utf8" });
    assert.equal(py.status, 0, py.stderr);
    assert.equal(py.stdout, js);
  }
});

test("apply refuses without --approved, writes only revised_at and revision_checked_at, and is idempotent", () => {
  const { dir, indexPath } = tempIndex();
  const before = read(indexPath);
  const fromPath = path.join(dir, "sop-revisions.json");
  const records = [
    okRecord(),
    okRecord({ file: "general/relative-page.md", url: `${ORIGIN}/books/general/page/relative-page`, http_or_nav_status: "not-found", revised_at: null }),
    okRecord({ file: "missing/nowhere.md", url: `${ORIGIN}/books/missing/page/nowhere` }),
    okRecord({ file: "general/relative-page.md", url: `${ORIGIN}/books/other/page/elsewhere` }),
  ];
  fs.writeFileSync(fromPath, renderOutput({ indexPath: "x", entries: records }));
  const refused = runApply({ fromPath, indexPath, approved: false, normalize: false });
  assert.equal(refused.refused, true);
  assert.equal(read(indexPath), before);

  const result = runApply({ fromPath, indexPath, approved: true, normalize: false });
  assert.equal(result.changed.length, 1);
  assert.equal(result.skipped.length, 3);
  assert.equal(result.round_trips, true);
  assert.equal(result.index_written, true);
  const after = JSON.parse(read(indexPath));
  const original = JSON.parse(before);
  const entry = after.captured[0];
  assert.equal(entry.revised_at, "2026-08-14T07:30:00Z");
  assert.equal(entry.revision_checked_at, TODAY);
  const keys = Object.keys(entry);
  assert.deepEqual(keys.slice(-2), ["revised_at", "revision_checked_at"]);
  // Everything else is untouched.
  const { revised_at, revision_checked_at, ...rest } = entry;
  assert.deepEqual(rest, original.captured[0]);
  assert.deepEqual(after.captured.slice(1), original.captured.slice(1));
  assert.deepEqual({ ...after, captured: null }, { ...original, captured: null });
  assert.equal(serializeIndex(after), read(indexPath));
  if (pythonAvailable) {
    const py = spawnSync("python3", ["-c", "import json,sys; p=sys.argv[1]; t=open(p,encoding='utf-8').read(); sys.exit(0 if json.dumps(json.loads(t), ensure_ascii=False, indent=1) + '\\n' == t else 1)", indexPath]);
    assert.equal(py.status, 0, "index bytes equal Python json.dumps");
  }

  const written = read(indexPath);
  const again = runApply({ fromPath, indexPath, approved: true, normalize: false });
  assert.equal(again.changed.length, 0);
  assert.equal(again.unchanged, 1);
  assert.equal(again.index_written, false);
  assert.equal(read(indexPath), written);
});

test("orderEntry puts the new keys in slim_sop_index.py order before archived", () => {
  const entry = orderEntry({ title: "t", file: "f.md", archived: true, knowledge_value: "low", revision_checked_at: TODAY, revised_at: "2026-01-01" });
  assert.deepEqual(Object.keys(entry), ["title", "file", "knowledge_value", "revised_at", "revision_checked_at", "archived"]);
  const index = { captured: [{ title: "t", url: "u", file: "f.md", knowledge_value: "low", archived: true }] };
  const result = applyRevisionsToIndex(index, [{ file: "f.md", url: "u/", http_or_nav_status: "ok", revised_at: "2026-01-01", checked_at: TODAY }]);
  assert.equal(result.changed.length, 1);
  assert.deepEqual(Object.keys(index.captured[0]).slice(-3), ["revised_at", "revision_checked_at", "archived"]);
});

// ---------------------------------------------------------------- recapture guard

test("recapture needs --operator-approved, never targets a tracked path and keeps the SOP file shape", async () => {
  const refused = await runCheck({ recapture: true, operatorApproved: false, repoRoot: os.tmpdir() });
  assert.equal(refused.status, "refused");
  assert.match(refused.message, /operator-approved/);
  const base = path.join(os.tmpdir(), "rc");
  assert.equal(recapturePath(base, "catalog/a.md"), path.join(base, "recaptured", "catalog", "a.md"));
  assert.throws(() => recapturePath(base, "../../MAG SOPs/catalog/a.md"), /escapes/);
  const text = renderRecapture({
    entry: { title: "Index title", category: "Catalog", url: `${ORIGIN}/books/catalog/page/a` },
    result: { title: "Page title", bodyMarkdown: "## Step\n\nDo it." }, capturedAt: "2026-10-06T10:00:00Z",
  });
  assert.equal(text, `---\ntitle: "Page title"\ncategory: "Catalog"\nsource_url: "${ORIGIN}/books/catalog/page/a"\ncaptured_at: "2026-10-06T10:00:00Z"\n---\n\n# Page title\n\nSource: ${ORIGIN}/books/catalog/page/a\n\n## Step\n\nDo it.\n`);
});

test("owned files carry no spaced em-dash", () => {
  const owned = [
    path.join(KNOWLEDGE, "sop_revision_check.mjs"), path.join(KNOWLEDGE, "sop_revision_extract.js"),
    fileURLToPath(import.meta.url), ...fs.readdirSync(FIXTURES).map((name) => path.join(FIXTURES, name)),
  ];
  for (const file of owned) assert.equal(read(file).includes(` ${String.fromCharCode(0x2014)} `), false, file);
});

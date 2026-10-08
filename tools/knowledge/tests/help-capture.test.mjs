// Tests for tools/knowledge/help_capture.mjs pure helpers and file-only commands.
// Run: node --test tools/knowledge/tests/help-capture.test.mjs
// No browser, port or network is touched: help_capture.mjs loads its browser
// modules only inside the capture command, which these tests never call.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

import {
  EXTRACTOR, CLASSES, loadConfig, libraryConfig, splitFrontmatter, normalizeBody, bodyHash,
  countWords, isShellBody, renderFrontmatter, renderArticle, stripLeadingTitle, stagedFrontmatterEntries,
  scrubText, planLibrary, classifyDiff, updateIndexEntries, appendMissing, addMissingToIndex,
  serializeJsonLike, newFilePath, newIndexEntry, isLoginUrl, isAccountChooserUrl, redirectedAway,
  navigationUrl, shouldSkipCheckpoint, selectTargets, buildStaged, writeStaged, runDiff, runApply, slugify,
  pollDecision, finalizePoll,
} from "../help_capture.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIXTURES = path.join(HERE, "fixtures");
const KNOWLEDGE = path.resolve(HERE, "..");
const TODAY = "2026-10-06";

function fixtureLib() {
  const lib = libraryConfig(loadConfig(), "seller-help");
  return {
    ...lib,
    root: "help-library",
    index: "_index/fixture-index.json",
    missing_list: "_index/fixture-missing.json",
    linked_list: "_index/linked.txt",
  };
}

function tempLibrary() {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "help-capture-test-"));
  fs.cpSync(path.join(FIXTURES, "help-library"), path.join(repoRoot, "help-library"), { recursive: true });
  return { repoRoot, stagingDir: path.join(repoRoot, "staging") };
}

const read = (file) => fs.readFileSync(file, "utf8");

// ---- minimal HTML parser for the converter fixture (fixture HTML is well formed)
const VOID = new Set(["br", "img", "hr", "input", "meta", "link"]);
const decode = (text) => text.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
  .replace(/&quot;/g, "\"").replace(/&#39;/g, "'").replace(/&nbsp;/g, " ").replace(/&copy;/g, "©");
function element(tag, attrs = {}) {
  return {
    nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], attrs,
    getAttribute(name) { return Object.hasOwn(this.attrs, name) ? this.attrs[name] : null; },
    hasAttribute(name) { return Object.hasOwn(this.attrs, name); },
  };
}
function parseHtml(html) {
  const root = element("root");
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
    if (tag === "script") {
      const end = html.indexOf("</script>", re.lastIndex);
      const el = element(tag, attrs);
      el.childNodes.push({ nodeType: 3, nodeValue: html.slice(re.lastIndex, end) });
      top.childNodes.push(el);
      re.lastIndex = end + "</script>".length;
      continue;
    }
    const el = element(tag, attrs);
    top.childNodes.push(el);
    if (!VOID.has(tag) && !m[3].trim().endsWith("/")) stack.push(el);
  }
  return root;
}
const extractorHelpers = () => vm.runInNewContext(EXTRACTOR, {});

// ---------------------------------------------------------------- hashing and frontmatter

test("bodyHash ignores frontmatter and whitespace differences", () => {
  const a = "---\ntitle: \"A\"\ndownloaded_at: \"2026-05-12\"\n---\n\n# A\n\nLine one  here.\n\n\nLine two.\n";
  const b = "---\ntitle: \"A changed\"\ndownloaded_at: \"2026-10-06\"\nsource: \"x\"\n---\n# A\n   Line one here.\t\nLine two.";
  assert.equal(bodyHash(a), bodyHash(b));
  assert.notEqual(bodyHash(a), bodyHash(a.replace("Line two.", "Line 2.")));
  assert.equal(normalizeBody("  x  \n\n\t y \n"), "x\ny");
});

test("splitFrontmatter parses quoted values and keeps order", () => {
  const text = read(path.join(FIXTURES, "help-library/articles/001-normal-article-G100.md"));
  const { entries, body } = splitFrontmatter(text);
  assert.deepEqual(entries.map(([k]) => k), ["title", "source_url", "downloaded_at", "source"]);
  assert.equal(entries[0][1], "Normal article");
  assert.match(body, /^\n# Normal article/);
});

test("renderArticle reproduces the tracked frontmatter and body shape", () => {
  const entries = [["title", "Say \"hi\""], ["source_url", "https://example.com/x"], ["downloaded_at", TODAY]];
  const text = renderArticle({ entries, title: "Say hi", body: "Body text.\n" });
  assert.equal(text, "---\ntitle: \"Say \\\"hi\\\"\"\nsource_url: \"https://example.com/x\"\ndownloaded_at: \"2026-10-06\"\n---\n\n# Say hi\n\nBody text.\n");
  assert.deepEqual(splitFrontmatter(text).entries, entries);
  assert.equal(renderFrontmatter([]), "---\n\n---\n");
});

test("stagedFrontmatterEntries keeps tracked keys and only bumps downloaded_at", () => {
  const lib = fixtureLib();
  const tracked = [["title", "T"], ["source_url", "u"], ["library", "L"], ["downloaded_at", "2026-05-13"], ["status", "captured"]];
  assert.deepEqual(stagedFrontmatterEntries({ trackedEntries: tracked, lib, page: {}, title: "x", today: TODAY }),
    [["title", "T"], ["source_url", "u"], ["library", "L"], ["downloaded_at", TODAY], ["status", "captured"]]);
  const fresh = stagedFrontmatterEntries({ lib, page: { title: "Idx title", url: "https://h/x" }, title: "Page", today: TODAY });
  assert.deepEqual(fresh, [["title", "Idx title"], ["source_url", "https://h/x"], ["downloaded_at", TODAY], ["source", "Amazon Seller Central Help"]]);
  const ads = libraryConfig(loadConfig(), "ads-support");
  const linked = stagedFrontmatterEntries({ lib: ads, page: { title: "", url: "https://h/G1", section: null }, title: "Page title", today: TODAY });
  assert.deepEqual(linked.map(([k]) => k), ["title", "source_url", "library", "section", "downloaded_at", "status"]);
  assert.equal(linked[0][1], "Page title");
  assert.equal(linked[3][1], "linked-expansion");
});

test("stripLeadingTitle drops the page H1 only", () => {
  assert.deepEqual(stripLeadingTitle("# Title here\n\nBody\n## Sub"), { title: "Title here", body: "Body\n## Sub" });
  assert.deepEqual(stripLeadingTitle("Body only"), { title: "", body: "Body only" });
});

// ---------------------------------------------------------------- shell, plan, selection

test("isShellBody detects the lone Loading line, not the word inside prose", () => {
  const lib = fixtureLib();
  assert.equal(isShellBody(splitFrontmatter(read(path.join(FIXTURES, "help-library/articles/002-shell-article-G200.md"))).body, lib), true);
  assert.equal(isShellBody(splitFrontmatter(read(path.join(FIXTURES, "help-library/articles/001-normal-article-G100.md"))).body, lib), false);
  assert.equal(isShellBody("Loading pallets is covered below.", lib), false);
  assert.equal(countWords("# Title\n\n- one, two | 3 |"), 4);
});

test("planLibrary classifies fixture pages and linked URLs", () => {
  const lib = fixtureLib();
  const plain = planLibrary(lib, { repoRoot: FIXTURES });
  assert.deepEqual(plain.counts, { total: 4, ok: 2, shell: 1, "missing-file": 1, "uncaptured-linked": 0, ok_thin: 1 });
  const byId = Object.fromEntries(plain.pages.map((p) => [p.id, p]));
  assert.equal(byId.G100.state, "ok");
  assert.equal(byId.G100.thin, false);
  assert.equal(byId.G150.thin, true);
  assert.equal(byId.G200.state, "shell");
  assert.equal(byId.G300.state, "missing-file");
  const linked = planLibrary(lib, { repoRoot: FIXTURES, includeLinked: true });
  assert.equal(linked.counts.total, 5, "G100 in the linked list is already tracked and is not counted twice");
  assert.equal(linked.counts["uncaptured-linked"], 1);
  assert.equal(linked.pages.find((p) => p.id === "G400").state, "uncaptured-linked");
});

test("selectTargets honours --only, --ids and the checkpoint", () => {
  const lib = fixtureLib();
  const { pages } = planLibrary(lib, { repoRoot: FIXTURES, includeLinked: true });
  assert.deepEqual(selectTargets(pages, { only: "shells" }).map((p) => p.id), ["G200"]);
  assert.deepEqual(selectTargets(pages, { only: "uncaptured" }).map((p) => p.id), ["G400"]);
  assert.equal(selectTargets(pages, { only: "all" }).length, 4);
  assert.deepEqual(selectTargets(pages, { ids: ["G400", "G100"] }).map((p) => p.id).sort(), ["G100", "G400"]);
  assert.deepEqual(selectTargets(pages, { ids: ["G400", "G100"], only: "uncaptured", onlyExplicit: true }).map((p) => p.id), ["G400"]);
  assert.throws(() => selectTargets(pages, { ids: ["NOPE"] }), /unknown ids: NOPE/);
  assert.throws(() => selectTargets(pages, { only: "changed" }), /diff-report/);
  const report = { entries: [{ id: "G100", class: "changed" }, { id: "G200", class: "unchanged" }] };
  assert.deepEqual(selectTargets(pages, { only: "changed", diffReport: report }).map((p) => p.id), ["G100"]);
  assert.equal(shouldSkipCheckpoint({ status: "ok", captured_at: `${TODAY}T08:00:00Z` }, TODAY), true);
  assert.equal(shouldSkipCheckpoint({ status: "ok", captured_at: `${TODAY}T08:00:00Z` }, TODAY, true), false);
  assert.equal(shouldSkipCheckpoint({ status: "shell", captured_at: `${TODAY}T08:00:00Z` }, TODAY), false);
  assert.equal(shouldSkipCheckpoint({ status: "ok", captured_at: "2026-10-05T23:00:00Z" }, TODAY), false);
});

test("login, chooser, redirect and navigation URL helpers", () => {
  const lib = fixtureLib();
  assert.equal(isLoginUrl("https://sellercentral.amazon.com/ap/signin?openid=x", lib), true);
  assert.equal(isLoginUrl("https://sellercentral.amazon.com/ap/sso/login", lib), true);
  assert.equal(isLoginUrl("https://sellercentral.amazon.com/help/hub/reference/G100", lib), false);
  assert.equal(isAccountChooserUrl("https://advertising.amazon.com/choose-account?destination=/help"), true);
  const page = { id: "G100", url: "https://sellercentral.amazon.com/help/hub/reference/G100" };
  assert.equal(redirectedAway(page, "https://sellercentral.amazon.com/help/hub/reference/external/G100?x=1", lib), false);
  assert.equal(redirectedAway(page, "https://sellercentral.amazon.com/help/hub/reference/external/G2", lib), true);
  assert.equal(redirectedAway(page, "https://x/G2", { ...lib, missing_on_redirect: false }), false);
  assert.equal(navigationUrl(page, lib), "https://sellercentral.amazon.com/help/hub/reference/G100?mons_sel_locale=en_US");
});

// ---------------------------------------------------------------- scrub

test("scrubText replaces the account label and redacts private tokens", () => {
  const lib = fixtureLib();
  const input = [
    "Acme Widgets Co", "United States",
    "Seller A2B3C4D5E6F7G8 and A9Z8Y7X6W5V4U3 sold in ATVPDKIKX0DER and A1PA6795UKMFR9.",
    "ADVERTISEMENTS stays because it has no digit; ASIN B0ABCDEFGH stays.",
    "Ref amzn1.sellerapps.app.1234-abcd and amzn1.REDACTED.",
    "Link https://sellercentral.amazon.com/x?mons_sel_locale=en_US&mons_sel_dir_mcid=amzn1.merchant.d.ABC&mons_sel_mkid=XYZ123",
    "Ads link https://advertising.amazon.com/cm?entityId=ENTITY2ABCDEF123 and entityId=ENTITY_EXAMPLE.",
    "Mail seller-help@amazon.com, ads@advertising.amazon.com, owner@example.net, redacted@example.com.",
  ].join("\n");
  const { text, counts } = scrubText(input, { accountLabel: " Acme  Widgets Co ", lib });
  assert.match(text, /^Example Brand\nUnited States/);
  assert.match(text, /Seller MERCHANT_ID_REDACTED and MERCHANT_ID_REDACTED sold in ATVPDKIKX0DER and A1PA6795UKMFR9\./);
  assert.match(text, /ADVERTISEMENTS stays/);
  assert.match(text, /B0ABCDEFGH/);
  assert.match(text, /Ref amzn1\.REDACTED and amzn1\.REDACTED\./);
  assert.match(text, /mons_sel_locale=en_US&mons_sel_dir_mcid=REDACTED&mons_sel_mkid=REDACTED/);
  assert.match(text, /entityId=ENTITY_EXAMPLE and entityId=ENTITY_EXAMPLE\./);
  assert.match(text, /seller-help@amazon\.com, ads@advertising\.amazon\.com, redacted@example\.com, redacted@example\.com\./);
  assert.deepEqual(counts, { account_label: 1, merchant_token: 2, amzn1: 2, mons_sel: 2, entity_id: 1, email: 1 });
  const again = scrubText(text, { accountLabel: "Acme Widgets Co", lib });
  assert.equal(again.text, text, "scrub is idempotent");
  assert.ok(Object.values(again.counts).every((n) => n === 0));
  assert.equal(scrubText("Help Help", { accountLabel: "Help", lib }).counts.account_label, 0, "generic labels are not replaced");
});

// ---------------------------------------------------------------- classification

test("classifyDiff covers every class", () => {
  const c = (stagedStatus, trackedState, stagedHash = "h1", trackedHash = "h1") => classifyDiff({ stagedStatus, trackedState, stagedHash, trackedHash });
  assert.equal(c("ok", "ok"), "unchanged");
  assert.equal(c("ok", "ok", "h1", "h2"), "changed");
  assert.equal(c("ok", "shell", "h1", "h2"), "shell-now-filled");
  assert.equal(c("shell", "shell"), "still-shell");
  assert.equal(c("shell", "ok"), "extraction-failed");
  assert.equal(c("ok", "missing-file"), "new");
  assert.equal(c("ok", "uncaptured-linked"), "new");
  assert.equal(c("missing", "ok"), "missing");
  assert.equal(c("login-required", "ok"), "login-required");
  assert.equal(c("extraction-failed", "ok"), "extraction-failed");
  assert.equal(c("ok", "ok", null), "extraction-failed");
  assert.deepEqual(CLASSES.slice().sort(), ["changed", "extraction-failed", "login-required", "missing", "new", "shell-now-filled", "still-shell", "unchanged"]);
});

// ---------------------------------------------------------------- index and missing list

test("updateIndexEntries sets bytes and downloaded_at only where entries have them", () => {
  const ads = libraryConfig(loadConfig(), "ads-support");
  const index = {
    pages: [{ title: "A", url: "https://advertising.amazon.com/help/GAAA111" }],
    captured_pages: [{ title: "A", url: "https://advertising.amazon.com/help/GAAA111", file: "articles/001-a-GAAA111.md", bytes: 10 }],
  };
  const changes = updateIndexEntries(index, ads, [{ id: "GAAA111", url: "https://advertising.amazon.com/help/GAAA111", bytes: 42, downloaded_at: TODAY }]);
  assert.deepEqual(changes, [{ list: "captured_pages", position: 0, id: "GAAA111", key: "bytes", from: 10, to: 42 }]);
  assert.equal(index.captured_pages[0].bytes, 42);
  assert.equal(Object.hasOwn(index.pages[0], "bytes"), false);
  const seller = fixtureLib();
  const sIndex = { pages: [{ id: "G1", url: "https://sellercentral.amazon.com/help/hub/reference/G1", file: "a.md", bytes: 1, downloaded_at: "2026-05-12" }] };
  const sChanges = updateIndexEntries(sIndex, seller, [{ id: "G1", url: "x", bytes: 5, downloaded_at: TODAY }]);
  assert.equal(sChanges.length, 2);
  assert.deepEqual(sIndex.pages[0], { id: "G1", url: "https://sellercentral.amazon.com/help/hub/reference/G1", file: "a.md", bytes: 5, downloaded_at: TODAY });
  const docs = libraryConfig(loadConfig(), "ads-docs");
  const dIndex = { sections: { guides: [{ title: "T", url: "https://advertising.amazon.com/API/docs/en-us/guides/x" }] } };
  assert.deepEqual(updateIndexEntries(dIndex, docs, [{ id: "guides-001", url: "https://advertising.amazon.com/API/docs/en-us/guides/x/", bytes: 9 }]), []);
});

test("appendMissing dedupes and addMissingToIndex creates the key when absent", () => {
  const entry = { id: "G300", url: "u300", reason: "redirect" };
  const first = appendMissing([], [entry, entry]);
  assert.equal(first.added, 1);
  assert.equal(appendMissing(first.list, [entry]).added, 0);
  const index = { pages: [] };
  assert.equal(addMissingToIndex(index, [entry]), 1);
  assert.deepEqual(index.missing, [entry]);
  assert.equal(Object.hasOwn(index, "missing_count"), false);
  const counted = { missing: [], missing_count: 0 };
  addMissingToIndex(counted, [entry]);
  assert.equal(counted.missing_count, 1);
});

test("serializeJsonLike keeps ASCII escaping and the trailing newline of the original", () => {
  const original = read(path.join(FIXTURES, "help-library/_index/fixture-index.json"));
  assert.equal(serializeJsonLike(original, JSON.parse(original)), original);
  assert.match(original, /Seller\\u2019s/);
  assert.equal(serializeJsonLike("{\n  \"a\": \"é\"\n}\n", { a: "é" }), "{\n  \"a\": \"é\"\n}\n");
  assert.equal(serializeJsonLike("[]", []), "[]");
});

test("newFilePath and newIndexEntry follow the library layout", () => {
  const seller = fixtureLib();
  const files = ["articles/001-a-G1.md", "articles/017-b-G2.md"];
  assert.equal(newFilePath(seller, { id: "G400", title: "Brand new: page!" }, files), "articles/018-brand-new-page-G400.md");
  const docs = libraryConfig(loadConfig(), "ads-docs");
  assert.equal(newFilePath(docs, { id: "guides-012", title: "Guide", section: "guides" }, ["articles/guides/011-x.md", "articles/reference/020-y.md"]),
    "articles/guides/012-guide.md");
  assert.deepEqual(newIndexEntry({ title: "", url: "", file: "", bytes: 0 }, { title: "T", url: "U", file: "F", bytes: 3, id: "G" }),
    { title: "T", url: "U", file: "F", bytes: 3 });
  assert.equal(slugify("Amazon’s A-to-z Guarantee"), "amazon-s-a-to-z-guarantee");
});

// ---------------------------------------------------------------- extractor

test("EXTRACTOR compiles and converts fixture HTML to markdown without noise", () => {
  assert.doesNotThrow(() => new Function(`return ${EXTRACTOR}`));
  const helpers = extractorHelpers();
  const root = parseHtml(read(path.join(FIXTURES, "extract-sample.html")));
  const markdown = helpers.toMarkdown(root);
  assert.equal(markdown, read(path.join(FIXTURES, "extract-sample.expected.md")).trim());
  for (const noise of ["Example Brand", "Policies", "Account settings", "English", "Hidden text", "ignored", "1999-2026"]) {
    assert.equal(markdown.includes(noise), false, `noise leaked: ${noise}`);
  }
  assert.equal(helpers.hasLoadingLine("x\nLoading\ny"), true);
  assert.equal(helpers.hasLoadingLine("Loading docks"), false);
});

// ---------------------------------------------------------------- staging, diff, apply end to end (files only)

function extraction(body, overrides = {}) {
  return {
    url: "https://sellercentral.amazon.com/help/hub/reference/G100?mons_sel_locale=en_US&mons_sel_mkid=XYZ123",
    title: "Normal article", isLogin: false, accountLabel: "Acme Widgets Co", wordCount: countWords(body),
    bodyMarkdown: body, status: "ok", container: "#help-content", ...overrides,
  };
}

test("stage, diff, refuse, apply, then a second unchanged capture reports unchanged", () => {
  const lib = fixtureLib();
  const { repoRoot, stagingDir } = tempLibrary();
  const libRoot = path.join(repoRoot, "help-library");
  const plan = planLibrary(lib, { repoRoot, includeLinked: true });
  const page = (id) => plan.pages.find((p) => p.id === id);
  const trackedText = (id) => (page(id).file && fs.existsSync(path.join(libRoot, page(id).file)) ? read(path.join(libRoot, page(id).file)) : null);
  const longBody = (word) => `# Normal article\n\nAcme Widgets Co sees this.\n\n${Array.from({ length: 130 }, (_, i) => `${word}${i}`).join(" ")}`;
  const stage = (id, result) => {
    const staged = buildStaged({ page: page(id), lib, result, trackedText: trackedText(id), today: TODAY, capturedAt: `${TODAY}T09:00:00.000Z` });
    writeStaged(stagingDir, staged);
    return staged;
  };
  const g100 = stage("G100", extraction(longBody("word")));
  assert.equal(g100.sidecar.status, "ok");
  assert.equal(g100.sidecar.scrub_counts.account_label, 1);
  assert.equal(g100.sidecar.scrub_counts.mons_sel, 1);
  assert.match(g100.text, /^---\ntitle: "Normal article"\nsource_url: "https:\/\/sellercentral\.amazon\.com\/help\/hub\/reference\/G100"\ndownloaded_at: "2026-10-06"\nsource: "Amazon Seller Central Help"\n---\n\n# Normal article\n\nExample Brand sees this\./);
  stage("G200", extraction(`# Shell article\n\n${Array.from({ length: 140 }, (_, i) => `filled${i}`).join(" ")}`, { title: "Shell article" }));
  stage("G300", { url: "https://sellercentral.amazon.com/help/hub/reference/external/G2", status: "missing", error: "redirected away from the article id" });
  stage("G400", extraction(`# Linked page\n\n${Array.from({ length: 125 }, (_, i) => `linked${i}`).join(" ")}`, { title: "Linked page" }));
  stage("G150", extraction("# Thin directory\n\nSelling account reviews for seller-fulfilled orders", { title: "Thin directory" }));

  const report = runDiff(lib, { repoRoot, stagingDir });
  assert.deepEqual(report.counts, {
    unchanged: 1, changed: 1, "shell-now-filled": 1, "still-shell": 0, new: 1, missing: 1, "login-required": 0, "extraction-failed": 0,
  });
  assert.ok(fs.existsSync(path.join(stagingDir, "diff-report.md")));
  assert.equal(report.entries.find((e) => e.id === "G150").class, "unchanged");

  const indexPath = path.join(libRoot, "_index/fixture-index.json");
  const before = read(indexPath);
  const refused = runApply(lib, { repoRoot, stagingDir, approved: false, today: TODAY });
  assert.equal(refused.refused, true);
  assert.equal(read(indexPath), before, "refusal writes nothing");

  const applied = runApply(lib, { repoRoot, stagingDir, approved: true, today: TODAY });
  assert.deepEqual(applied.written.map((w) => w.id).sort(), ["G100", "G200"]);
  assert.deepEqual(applied.created, [], "new pages need --include-new");
  assert.equal(read(path.join(libRoot, "articles/001-normal-article-G100.md")), read(path.join(stagingDir, "G100.md")));
  const index = JSON.parse(read(indexPath));
  const g100Entry = index.pages.find((p) => p.id === "G100");
  assert.equal(g100Entry.bytes, Buffer.byteLength(read(path.join(libRoot, g100Entry.file))));
  assert.equal(index.missing.length, 1);
  assert.equal(index.missing[0].id, "G300");
  assert.equal(index.missing_count, 1);
  assert.match(read(indexPath), /Seller\\u2019s retired article/, "index keeps its ASCII escaping");
  assert.equal(JSON.parse(read(path.join(libRoot, "_index/fixture-missing.json")))[0].id, "G300");

  const withNew = runApply(lib, { repoRoot, stagingDir, approved: true, includeNew: true, today: TODAY });
  assert.deepEqual(withNew.created.map((c) => c.file), ["help-library/articles/005-linked-page-G400.md"]);
  assert.equal(withNew.skipped.length, 2, "already-applied pages are skipped because the tracked hash moved");
  assert.equal(JSON.parse(read(indexPath)).pages.at(-1).file, "articles/005-linked-page-G400.md");
  assert.equal(JSON.parse(read(path.join(libRoot, "_index/fixture-missing.json"))).length, 1, "missing list is not duplicated");

  // Second capture of the same unchanged pages: every applied page reports unchanged.
  const replan = planLibrary(lib, { repoRoot, includeLinked: true });
  for (const [id, result] of [
    ["G100", extraction(longBody("word"))],
    ["G200", extraction(`# Shell article\n\n${Array.from({ length: 140 }, (_, i) => `filled${i}`).join(" ")}`, { title: "Shell article" })],
    ["G400", extraction(`# Linked page\n\n${Array.from({ length: 125 }, (_, i) => `linked${i}`).join(" ")}`, { title: "Linked page" })],
  ]) {
    const p = replan.pages.find((x) => x.id === id);
    const staged = buildStaged({ page: p, lib, result, trackedText: read(path.join(libRoot, p.file)), today: TODAY, capturedAt: `${TODAY}T10:00:00.000Z` });
    writeStaged(stagingDir, staged);
  }
  const second = runDiff(lib, { repoRoot, stagingDir });
  for (const id of ["G100", "G200", "G400", "G150"]) {
    assert.equal(second.entries.find((e) => e.id === id).class, "unchanged", id);
  }
  fs.rmSync(repoRoot, { recursive: true, force: true });
});

test("diff flags a staged file edited after capture and login-required sidecars", () => {
  const lib = fixtureLib();
  const { repoRoot, stagingDir } = tempLibrary();
  const plan = planLibrary(lib, { repoRoot });
  const g100 = plan.pages.find((p) => p.id === "G100");
  const staged = buildStaged({ page: g100, lib, result: extraction(`# Normal article\n\n${"text ".repeat(130)}`), trackedText: null, today: TODAY, capturedAt: `${TODAY}T09:00:00Z` });
  writeStaged(stagingDir, staged);
  fs.appendFileSync(path.join(stagingDir, "G100.md"), "\nedited by hand\n");
  writeStaged(stagingDir, buildStaged({ page: plan.pages.find((p) => p.id === "G200"), lib, result: { status: "login-required", url: "https://sellercentral.amazon.com/ap/signin?x=1" }, today: TODAY, capturedAt: "t" }));
  const report = runDiff(lib, { repoRoot, stagingDir });
  assert.equal(report.entries.find((e) => e.id === "G100").class, "extraction-failed");
  assert.equal(report.entries.find((e) => e.id === "G200").class, "login-required");
  assert.equal(fs.existsSync(path.join(stagingDir, "G200.md")), false, "non-content statuses keep no staged markdown");
  fs.rmSync(repoRoot, { recursive: true, force: true });
});

// ---------------------------------------------------------------- config and hygiene

test("config declares the three libraries with the required keys", () => {
  const config = loadConfig();
  assert.deepEqual(Object.keys(config.libraries).sort(), ["ads-docs", "ads-support", "seller-help"]);
  for (const key of Object.keys(config.libraries)) {
    const lib = libraryConfig(config, key);
    for (const field of ["root", "index", "articles_dir", "origin", "region_task", "frontmatter_keys", "fields"]) assert.ok(lib[field], `${key}.${field}`);
    assert.equal(lib.min_body_words, 120);
    assert.equal(lib.account_placeholder, "Example Brand");
  }
  assert.equal(config.libraries["seller-help"].region_task.kind, "plain", "help pages use a plain read-only task tab");
  assert.equal(config.libraries["ads-support"].region_task.workflow, "amazon-help-capture");
  assert.ok(config.libraries["ads-support"].linked_list.endsWith("remaining-linked-urls-2026-05-13.txt"));
});

test("owned files carry no spaced em-dash", () => {
  const owned = [
    path.join(KNOWLEDGE, "help_capture.mjs"), path.join(KNOWLEDGE, "help_extract.js"), path.join(KNOWLEDGE, "help-capture.config.json"),
    fileURLToPath(import.meta.url), ...fs.readdirSync(FIXTURES, { recursive: true }).map((rel) => path.join(FIXTURES, rel)),
  ].filter((file) => fs.statSync(file).isFile());
  for (const file of owned) assert.equal(read(file).includes(` ${String.fromCharCode(0x2014)} `), false, file);
});

// ---------------------------------------------------------------- review regressions

test("scrub decodes percent-encoded sign-in URLs before redacting", () => {
  const lib = fixtureLib();
  const url = "https://sellercentral.amazon.com/ap/signin?openid.return_to=https%3A%2F%2Fsellercentral.amazon.com%2Fhelp%3Fmons_sel_dir_paid%3DA2ABCDEFGH1234%26mons_sel_dir_mcid%3Damzn1.merchant.d.ABCXYZ";
  const { text, counts } = scrubText(url, { lib });
  assert.equal(/A2ABCDEFGH1234|amzn1\.merchant/.test(text), false, text);
  assert.ok(counts.mons_sel >= 1 || counts.merchant_token >= 1);
  assert.ok(counts.amzn1 >= 1 || counts.mons_sel >= 2);
});

test("account label replacement respects word boundaries and spacing", () => {
  const lib = fixtureLib();
  const one = scrubText("Use Home settings. Visit Home. Homeware stays.", { accountLabel: "Home", lib });
  assert.equal(one.text, "Use Example Brand settings. Visit Example Brand. Homeware stays.");
  const two = scrubText("Acme Widgets Co and Acme Widgets Company", { accountLabel: "Acme Widgets Co", lib });
  assert.equal(two.text, "Example Brand and Acme Widgets Company");
  assert.equal(scrubText("Ops at ops@amazon.de and ops@amazon.co.uk", { lib }).counts.email, 0);
  assert.equal(scrubText("Ireland A28R8C7NBKEWEA", { lib }).counts.merchant_token, 0);
  const page = { id: "G100", url: "https://sellercentral.amazon.com/help/hub/reference/G100", file: null, title: "T" };
  const staged = buildStaged({ page, lib, result: extraction("# T\n\nHome is here.", { accountLabel: "Home" }), today: TODAY, capturedAt: "t" });
  assert.match(staged.sidecar.review_notes[0], /single-word account label/);
});

test("login and redirect rules do not turn MFA, off-origin or prefix ids into missing pages", () => {
  const lib = fixtureLib();
  assert.equal(isLoginUrl("https://sellercentral.amazon.com/ap/mfa?arb=1", lib), true);
  assert.equal(isLoginUrl("https://www.amazon.com/ap/cvf/request", lib), true);
  const page = { id: "G20", url: "https://sellercentral.amazon.com/help/hub/reference/G20" };
  assert.equal(redirectedAway(page, "https://sellercentral.amazon.com/help/hub/reference/G200", lib), true, "G20 is not G200");
  assert.equal(redirectedAway(page, "https://www.amazon.com/somewhere", lib), false, "off-origin is not a missing page");
});

test("apply refuses a non-array missing file and leaves an index without a missing key alone", () => {
  const lib = fixtureLib();
  const { repoRoot, stagingDir } = tempLibrary();
  const libRoot = path.join(repoRoot, "help-library");
  const indexPath = path.join(libRoot, "_index/fixture-index.json");
  const index = JSON.parse(read(indexPath));
  delete index.missing;
  fs.writeFileSync(indexPath, serializeJsonLike(read(indexPath), index));
  const plan = planLibrary(lib, { repoRoot });
  writeStaged(stagingDir, buildStaged({ page: plan.pages.find((p) => p.id === "G300"), lib,
    result: { status: "missing", url: "https://sellercentral.amazon.com/help/hub/reference/external/G2" }, today: TODAY, capturedAt: "t" }));
  runDiff(lib, { repoRoot, stagingDir });
  const ok = runApply(lib, { repoRoot, stagingDir, approved: true, today: TODAY });
  assert.equal(Object.hasOwn(JSON.parse(read(indexPath)), "missing"), false);
  assert.equal(ok.missing_added, 1);
  fs.writeFileSync(path.join(libRoot, "_index/fixture-missing.json"), "{\"pages\": []}");
  assert.throws(() => runApply(lib, { repoRoot, stagingDir, approved: true, today: TODAY }), /not a JSON array/);
  fs.rmSync(repoRoot, { recursive: true, force: true });
});

test("noise filter keeps article sections whose ids only contain a noise word", () => {
  const helpers = extractorHelpers();
  const root = parseHtml("<div><div id=\"feedback-manager\"><p>Use Feedback Manager daily.</p></div><div class=\"language-tips\"><p>Listing languages matter.</p></div><div class=\"site-header\"><p>Header junk</p></div></div>");
  assert.equal(helpers.toMarkdown(root), "Use Feedback Manager daily.\n\nListing languages matter.");
});

// ---------------------------------------------------------------- Seller Assistant workspace layout


test("findArticle waits while only the Seller Assistant workspace has rendered", () => {
  const helpers = extractorHelpers();
  const found = helpers.findArticle(parseHtml(read(path.join(FIXTURES, "workspace-early.html"))));
  assert.equal(found.workspace, true);
  assert.equal(found.container, null, "the workspace is never taken as the article");
  assert.equal(found.title, "");
});

test("findArticle takes the article H1 and excludes the workspace once the article arrives", () => {
  const helpers = extractorHelpers();
  const found = helpers.findArticle(parseHtml(read(path.join(FIXTURES, "workspace-late.html"))));
  assert.equal(found.workspace, true);
  assert.equal(found.title, "Delivery with Services");
  assert.equal(found.selector, "article-h1-ancestor");
  const markdown = helpers.toMarkdown(found.container, { skip: found.chromeRoots });
  assert.equal(markdown, read(path.join(FIXTURES, "workspace-late.expected.md")).trim());
  for (const chrome of ["Actions", "Seller Assistant", "New chat", "network error", "No actions required", "canvas"]) {
    assert.equal(markdown.includes(chrome), false, `workspace chrome leaked: ${chrome}`);
  }
});

test("findArticle prefers a known container and still titles from the article H1", () => {
  const helpers = extractorHelpers();
  const found = helpers.findArticle(parseHtml(read(path.join(FIXTURES, "workspace-known-container.html"))));
  assert.equal(found.selector, "known-container");
  assert.equal(found.title, "Manage inventory");
  const markdown = helpers.toMarkdown(found.container, { skip: found.chromeRoots });
  assert.match(markdown, /^The Manage All Inventory tool/);
  assert.equal(/Actions|Seller Assistant/.test(markdown), false);
});

test("toMarkdown drops exact workspace chrome blocks as a safety net", () => {
  const helpers = extractorHelpers();
  const root = parseHtml("<div><h1>Actions</h1><p>New chat</p><p>Real article text stays.</p></div>");
  assert.equal(helpers.toMarkdown(root), "Real article text stays.");
});

test("pollDecision never accepts a stable workspace-only page and finalizePoll keeps it a shell", () => {
  const lib = fixtureLib();
  const chromeOnly = { status: "shell", wordCount: 0, articleFound: false, workspace: true, url: "https://sellercentral.amazon.com/help/hub/reference/G1" };
  let state = { prevWords: -1, stable: 0 };
  for (let i = 0; i < 10; i += 1) {
    const d = pollDecision({ result: chromeOnly, ...state, elapsedMs: 1000 * (i + 1), lib });
    assert.equal(d.done, false);
    state = { prevWords: d.prevWords, stable: d.stable };
  }
  const okWithoutArticle = { ...chromeOnly, status: "ok", wordCount: 57 };
  for (let i = 0; i < 5; i += 1) assert.equal(pollDecision({ result: okWithoutArticle, prevWords: 57, stable: 5, elapsedMs: 15000, lib }).done, false);
  assert.equal(finalizePoll(okWithoutArticle).status, "shell");
  assert.match(finalizePoll(chromeOnly).error, /only the Seller Assistant workspace/);
  const thinArticle = { status: "ok", wordCount: 40, articleFound: true, url: chromeOnly.url };
  assert.equal(pollDecision({ result: thinArticle, prevWords: -1, stable: 0, elapsedMs: 6000, lib }).done, false);
  assert.equal(pollDecision({ result: thinArticle, prevWords: 40, stable: 1, elapsedMs: 6000, lib }).done, true);
  assert.equal(pollDecision({ result: { ...thinArticle, wordCount: 256 }, elapsedMs: 1500, lib }).done, true);
  assert.equal(finalizePoll(null, new Error("x")).status, "extraction-failed");
  const stagedShell = buildStaged({ page: { id: "G1", url: chromeOnly.url, title: "T", file: null }, lib, result: finalizePoll(chromeOnly), today: TODAY, capturedAt: "t" });
  assert.equal(classifyDiff({ stagedStatus: stagedShell.sidecar.status, trackedState: "shell", stagedHash: stagedShell.sidecar.body_sha256, trackedHash: "x" }), "still-shell");
  assert.equal(classifyDiff({ stagedStatus: stagedShell.sidecar.status, trackedState: "ok", stagedHash: stagedShell.sidecar.body_sha256, trackedHash: "x" }), "extraction-failed");
});

test("buildStaged titles from the extractor and removes the duplicated article H1", () => {
  const lib = fixtureLib();
  const page = { id: "G41", url: "https://sellercentral.amazon.com/help/hub/reference/G41", title: "Manage inventory", file: null };
  const known = buildStaged({ page, lib, result: { ...extraction("Body text without a heading."), title: "Manage inventory", articleFound: true }, today: TODAY, capturedAt: "t" });
  assert.match(known.text, /\n---\n\n# Manage inventory\n\nBody text without a heading\.\n$/);
  const withH1 = buildStaged({ page, lib, result: { ...extraction("Help > Inventory\n\n# Manage inventory\n\nBody."), title: "Manage inventory" }, today: TODAY, capturedAt: "t" });
  assert.match(withH1.text, /\n# Manage inventory\n\nHelp > Inventory\n\nBody\.\n$/);
});

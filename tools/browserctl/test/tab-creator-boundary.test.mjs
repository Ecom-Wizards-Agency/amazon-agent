import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const ALLOWED = new Set([
  "tools/report-fetcher/cdp.mjs",
  "tools/browserctl/browserctl.mjs",
  "tools/browserctl/task-tabs.mjs",
]);

function sourceFiles(directory) {
  const files = [];
  for (const name of readdirSync(directory)) {
    if (["node_modules", "test"].includes(name)) continue;
    const path = resolve(directory, name);
    if (statSync(path).isDirectory()) files.push(...sourceFiles(path));
    else if (/\.(?:mjs|js)$/.test(name)) files.push(path);
  }
  return files;
}

test("fresh CDP targets are restricted to anchors and the task-tab controller", () => {
  const offenders = sourceFiles(resolve(ROOT, "tools"))
    .map((path) => ({ path, source: readFileSync(path, "utf8") }))
    .filter(({ source }) => /\bcreatePage\s*\(/.test(source))
    .map(({ path }) => relative(ROOT, path))
    .filter((path) => !ALLOWED.has(path));
  assert.deepEqual(offenders, []);
});

// Import first: browserctl modules fix the policy, lease and lock paths when they
// load, so tests must point them at a temporary directory beforehand. Without
// this, cdp.mjs reads the machine's live browser policy and lease registry.
// A child test process inherits its parent's runtime, so a session the parent
// bound still matches the policy the child reads.
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

if (!process.env.AMAZON_BROWSER_TEST_RUNTIME) {
  const root = mkdtempSync(join(tmpdir(), "report-fetcher-runtime-"));
  mkdirSync(join(root, "runtime"));
  process.env.AMAZON_BROWSER_TEST_RUNTIME = root;
  process.env.AMAZON_BROWSER_RUNTIME_DIR = join(root, "runtime");
  process.env.AMAZON_BROWSER_POLICY = join(root, "runtime", "policy.json");
  process.env.AMAZON_BROWSER_LOCK_DIR = join(root, "locks");
  writeFileSync(process.env.AMAZON_BROWSER_POLICY, JSON.stringify({ schema_version: 1, ports: {
    9222: { profile: join(root, "operator-profile") }, 9223: { profile: join(root, "grimoire-profile") },
  } }));
  process.once("exit", () => rmSync(root, { recursive: true, force: true }));
}

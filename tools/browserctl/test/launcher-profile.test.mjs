import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";

test("launcher verifies the listener profile, symlinks and status evidence", () => {
  const result = spawnSync("python3", ["-B", new URL("./fixtures/launcher-profile.py", import.meta.url).pathname],
    { stdio: "inherit" });
  assert.equal(result.status, 0);
});

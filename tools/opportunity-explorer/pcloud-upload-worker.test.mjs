import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { publishFilesAsync } from "./pcloud-archive.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "poe-upload-worker-test-"));
  const helper = join(root, "helper.py");
  const original = process.env.POE_PCLOUD_SCRIPT;
  t.after(() => {
    if (original === undefined) delete process.env.POE_PCLOUD_SCRIPT;
    else process.env.POE_PCLOUD_SCRIPT = original;
    rmSync(root, { recursive: true, force: true });
  });
  writeFileSync(helper, `#!/usr/bin/env python3
import hashlib, pathlib, sys, time
time.sleep(0.15)
root=pathlib.Path(__file__).parent
cmd=sys.argv[1]
name=pathlib.Path(sys.argv[2]).name
file=root/name
if cmd=='checksum':
    if not file.exists():
        print('API error 2009: missing',file=sys.stderr)
        sys.exit(1)
    print(hashlib.sha1(file.read_bytes()).hexdigest())
elif cmd=='put-stream':
    if sys.argv[3]=='fail':
        print('upload unavailable',file=sys.stderr)
        sys.exit(1)
    file.write_bytes(sys.stdin.buffer.read())
else:
    raise RuntimeError('unexpected command')
`, { mode: 0o700 });
  process.env.POE_PCLOUD_SCRIPT = helper;
}

test("slow checksum-verified uploads leave the main heartbeat timer responsive", async t => {
  fixture(t);
  let heartbeats = 0;
  const timer = setInterval(() => heartbeats++, 20);
  t.after(() => clearInterval(timer));
  const content = '{"synthetic":"POE fixture"}';
  const receipt = await publishFilesAsync([{ name: "niche.json", content }], { remote: "test" });
  assert.ok(heartbeats >= 10, `heartbeat was starved: ${heartbeats}`);
  assert.equal(receipt.status, "archived_verified");
  assert.equal(receipt.local_data_retained, false);
  assert.equal(receipt.artifacts[0].sha1, createHash("sha1").update(content).digest("hex"));
});

test("failed worker upload rejects instead of returning a successful receipt", async t => {
  fixture(t);
  await assert.rejects(publishFilesAsync([{ name: "niche.json", content: "fixture" }], { remote: "fail" }), /upload unavailable/);
});

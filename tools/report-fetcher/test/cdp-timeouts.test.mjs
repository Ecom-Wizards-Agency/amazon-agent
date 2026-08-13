/*
 * Regression tests for the 13.08.2026 account-chooser stall: a live socket
 * whose target stops answering must reject within its budget, never hang the
 * process. See the incident notes in the PR that introduced this file.
 */
import assert from "node:assert/strict";
import test from "node:test";

import { Session, evaluate } from "../cdp.mjs";
import { startFakeCdp } from "./helpers/fake-cdp.mjs";

test("evaluate rejects within budget when Runtime.enable is never answered", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "https://sellercentral.amazon.com/home", behavior: { neverReply: ["Runtime.enable"] } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    const t0 = Date.now();
    // budget 100ms -> hard timer at 5100ms; pre-fix this hung forever
    await assert.rejects(evaluate(s, "1+1", 100), /timed out/);
    const elapsed = Date.now() - t0;
    assert.ok(elapsed < 9000, `rejected in ${elapsed} ms, expected well under 9 s`);
  } finally {
    await fake.close();
  }
});

test("Session.send honors an opt-in timeoutMs", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { neverReply: ["Foo.bar"] } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    const t0 = Date.now();
    await assert.rejects(s.send("Foo.bar", {}, { timeoutMs: 300 }), /CDP Foo\.bar timed out after 300 ms/);
    assert.ok(Date.now() - t0 < 2000);
    s.close();
  } finally {
    await fake.close();
  }
});

test("Session.send without timeoutMs still waits for a slow reply", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { delayMs: 1200, results: { "Foo.slow": { ok: true } } } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    const r = await s.send("Foo.slow");
    assert.deepEqual(r, { ok: true });
    s.close();
  } finally {
    await fake.close();
  }
});

test("Session.open rejects when the WebSocket handshake stalls", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { stallUpgrade: true } }],
  });
  try {
    await assert.rejects(Session.open(fake.wsUrl("T1"), { timeoutMs: 300 }), /handshake timed out/);
  } finally {
    await fake.close();
  }
});

test("Session.open rejects when the target refuses the upgrade", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { refuseUpgrade: true } }],
  });
  try {
    await assert.rejects(Session.open(fake.wsUrl("T1")), /failed to open/);
  } finally {
    await fake.close();
  }
});

test("Inspector.detached rejects every pending send with a named reason", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { detachOn: "Runtime.enable" } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    await assert.rejects(s.send("Runtime.enable"), /CDP target detached: target_closed/);
    s.close();
  } finally {
    await fake.close();
  }
});

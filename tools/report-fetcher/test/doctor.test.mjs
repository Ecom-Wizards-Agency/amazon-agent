/*
 * End-to-end doctor runs against the fake CDP server: the real CLI, the real
 * probe path, scripted target failure modes. Exit-code contract: 0 signed in,
 * 1 conclusively signed out / no tab, 2 indeterminate (retry).
 */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { startFakeCdp } from "./helpers/fake-cdp.mjs";

const RUN = fileURLToPath(new URL("../run.mjs", import.meta.url));

function runDoctor(port) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [RUN, "doctor"], {
      env: { ...process.env, CDP_HOST: "127.0.0.1", CDP_PORT: String(port), CDP_AUTOSTART: "0" },
    });
    let out = "";
    child.stdout.on("data", (c) => { out += c; });
    child.stderr.on("data", (c) => { out += c; });
    child.on("close", (code) => resolve({ code, out }));
  });
}

const factsResult = (facts) => ({ result: { value: facts } });

test("doctor: healthy signed-in tab exits 0 with the live identity", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "UltimaPeak / United States", partnerAccountId: "A1FAKE", merchantId: "amzn1.merchant.o.FAKE", marketplace: null, err: null };
  const fake = await startFakeCdp({
    targets: [{
      id: "T1", url: facts.url,
      behavior: { results: { "Runtime.evaluate": (p) => factsResult(p.expression.includes("GetUserContext") ? identity : facts) } },
    }],
  });
  try {
    const { code, out } = await runDoctor(fake.port);
    assert.equal(code, 0, out);
    assert.match(out, /Login: OK/);
    assert.match(out, /UltimaPeak \/ United States/);
  } finally {
    await fake.close();
  }
});

test("doctor: unprobeable tabs exit 2 INDETERMINATE, never NOT signed in", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [
      { id: "T1", url: "https://sellercentral.amazon.com/home", behavior: { refuseUpgrade: true } },
      { id: "T2", url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace", behavior: { refuseUpgrade: true } },
    ],
  });
  try {
    const { code, out } = await runDoctor(fake.port);
    assert.equal(code, 2, out);
    assert.match(out, /INDETERMINATE/);
    assert.match(out, /Retry doctor/);
    assert.doesNotMatch(out, /NOT signed in/);
  } finally {
    await fake.close();
  }
});

test("doctor: chooser-only session exits 0 but says no account is selected", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace", chooserButtonCount: 3, csrfMeta: false };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: { results: { "Runtime.evaluate": () => factsResult(facts) } } }],
  });
  try {
    const { code, out } = await runDoctor(fake.port);
    assert.equal(code, 0, out);
    assert.match(out, /NO account selected/);
  } finally {
    await fake.close();
  }
});

test("doctor: conclusively signed-out tab exits 1", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/ap/signin", title: "Amazon Sign-In", hasPasswordInput: true };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: { results: { "Runtime.evaluate": () => factsResult(facts) } } }],
  });
  try {
    const { code, out } = await runDoctor(fake.port);
    assert.equal(code, 1, out);
    assert.match(out, /NOT signed in/);
  } finally {
    await fake.close();
  }
});

test("doctor: no Seller Central tab exits 1 with the recovery instruction", { concurrency: false }, async () => {
  const fake = await startFakeCdp({ targets: [{ id: "T1", url: "about:blank" }] });
  try {
    const { code, out } = await runDoctor(fake.port);
    assert.equal(code, 1, out);
    assert.match(out, /no tab open/);
  } finally {
    await fake.close();
  }
});

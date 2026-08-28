import assert from "node:assert/strict";
import test from "node:test";

import { accountMatches, accountPickerUrl, classifyPage, doctorVerdict, probeTab } from "../sc-account.mjs";
import { startFakeCdp } from "./helpers/fake-cdp.mjs";

test("classifyPage recognizes every page kind the 13.08 incident produced", () => {
  const cases = [
    // the full-page chooser, by DOM and by URL (mid-load, no buttons yet)
    [{ url: "https://sellercentral.amazon.com/home", chooserButtonCount: 3, csrfMeta: false },
      { pageKind: "chooser", authState: "authenticated" }],
    [{ url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace?returnTo=%2Fhome", chooserButtonCount: 0 },
      { pageKind: "chooser", authState: "authenticated" }],
    // the authorization-failed page seen next to the chooser on 13.08.2026
    [{ url: "https://sellercentral.amazon.com/authorization/failed-global/?returnTo=%2Famazonsell%2Fmanage-products", csrfMeta: true },
      { pageKind: "auth-failed", authState: "authenticated" }],
    [{ url: "https://sellercentral.amazon.com/authorization/failed-global/", csrfMeta: false },
      { pageKind: "auth-failed", authState: "ambiguous" }],
    // sign-in surfaces
    [{ url: "https://sellercentral.amazon.com/ap/signin?foo=1" }, { pageKind: "sign-in", authState: "logged_out" }],
    [{ url: "https://sellercentral.amazon.com/home", hasPasswordInput: true }, { pageKind: "sign-in", authState: "logged_out" }],
    [{ url: "https://sellercentral.amazon.com/home", title: "Amazon Sign-In" }, { pageKind: "sign-in", authState: "logged_out" }],
    // human challenges beat everything
    [{ url: "https://sellercentral.amazon.com/ap/cvf/request" }, { pageKind: "challenge", authState: "human_challenge" }],
    [{ url: "https://sellercentral.amazon.com/home", hasChallengeInput: true }, { pageKind: "challenge", authState: "human_challenge" }],
    // a normal authenticated app page
    [{ url: "https://sellercentral.amazon.com/business-reports", csrfMeta: true }, { pageKind: "app", authState: "authenticated" }],
    // nothing recognizable: ambiguous, never a confident verdict
    [{ url: "https://sellercentral.amazon.com/somewhere", csrfMeta: false }, { pageKind: "unknown", authState: "ambiguous" }],
    [null, { pageKind: "unknown", authState: "ambiguous" }],
  ];
  for (const [facts, expected] of cases) {
    assert.deepEqual(classifyPage(facts), expected, `facts: ${JSON.stringify(facts)}`);
  }
});

test("accountPickerUrl carries the returnTo and normalizes the origin", () => {
  assert.equal(
    accountPickerUrl("https://sellercentral.amazon.com", "/home"),
    "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace?returnTo=%2Fhome",
  );
  assert.equal(
    accountPickerUrl("https://sellercentral.amazon.de/some/path"),
    "https://sellercentral.amazon.de/account-switcher/default/merchantMarketplace?returnTo=%2Fhome",
  );
  assert.throws(() => accountPickerUrl("not-a-url"), /invalid Seller Central origin/);
});

test("accountMatches matches ids exactly and names as substrings", () => {
  const acct = { displayName: "Example Brand United States", partnerAccountId: "A1EXAMPLEPARTNER", merchantId: "amzn1.merchant.o.XYZ" };
  assert.equal(accountMatches(acct, "A1EXAMPLEPARTNER"), true);
  assert.equal(accountMatches(acct, "example brand"), true);
  assert.equal(accountMatches(acct, "Unrelated Brand"), false);
  assert.equal(accountMatches(acct, null), true); // nothing expected: vacuously true
  assert.equal(accountMatches({}, "anything"), false);
});

test("doctorVerdict never claims NOT signed in over unprobeable tabs", () => {
  const signedIn = { state: "signed-in", pageKind: "app" };
  const chooser = { state: "signed-in", pageKind: "chooser" };
  const signedOut = { state: "signed-out", pageKind: "sign-in" };
  const dead = { state: "indeterminate", reason: "could not attach: CDP WebSocket failed to open" };

  assert.equal(doctorVerdict([]).exitCode, 1);
  assert.equal(doctorVerdict([signedIn, signedOut, dead]).exitCode, 0);
  assert.equal(doctorVerdict([signedOut, signedOut]).exitCode, 1);
  assert.match(doctorVerdict([signedOut]).text, /NOT signed in/);
  // the 13.08 regression: all tabs unprobeable must be INDETERMINATE exit 2
  const v = doctorVerdict([dead, dead]);
  assert.equal(v.exitCode, 2);
  assert.match(v.text, /INDETERMINATE/);
  assert.match(v.text, /could not attach/);
  assert.doesNotMatch(v.text, /NOT signed in/);
  // chooser-only session is authenticated but needs an account selection
  const c = doctorVerdict([chooser]);
  assert.equal(c.exitCode, 0);
  assert.match(c.text, /NO account selected/);
  // a challenge is conclusive and needs a human
  assert.match(doctorVerdict([{ state: "challenge", pageKind: "challenge" }]).text, /human challenge/);
});

function factsResult(facts) {
  return { result: { value: facts } };
}

test("probeTab: dead target is indeterminate, not signed-out", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "https://sellercentral.amazon.com/home", behavior: { refuseUpgrade: true } }],
  });
  try {
    const [page] = JSON.parse(await (await fetch(`http://127.0.0.1:${fake.port}/json/list`)).text());
    const r = await probeTab(page);
    assert.equal(r.state, "indeterminate");
    assert.match(r.reason, /could not attach/);
    assert.equal(r.stale, true);
  } finally {
    await fake.close();
  }
});

test("probeTab: app page resolves identity from the live page", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/business-reports", title: "Business Reports", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand / United States", partnerAccountId: "A1FAKE", merchantId: "amzn1.merchant.o.FAKE", marketplace: "ATVPDKIKX0DER", err: null };
  const fake = await startFakeCdp({
    targets: [{
      id: "T1", url: "https://sellercentral.amazon.com/stale-snapshot-url",
      behavior: { results: { "Runtime.evaluate": (params) => factsResult(params.expression.includes("GetUserContext") ? identity : facts) } },
    }],
  });
  try {
    const [page] = JSON.parse(await (await fetch(`http://127.0.0.1:${fake.port}/json/list`)).text());
    const r = await probeTab(page);
    assert.equal(r.state, "signed-in");
    assert.equal(r.pageKind, "app");
    assert.equal(r.url, facts.url, "url must come from the live page, not the snapshot");
    assert.equal(r.identity.displayName, "Example Brand / United States");
  } finally {
    await fake.close();
  }
});

test("probeTab: chooser page is signed-in/chooser and skips the identity read", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace", chooserButtonCount: 4, csrfMeta: false };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: { results: { "Runtime.evaluate": () => factsResult(facts) } } }],
  });
  try {
    const [page] = JSON.parse(await (await fetch(`http://127.0.0.1:${fake.port}/json/list`)).text());
    const r = await probeTab(page);
    assert.equal(r.state, "signed-in");
    assert.equal(r.pageKind, "chooser");
    assert.equal(r.identity, null);
  } finally {
    await fake.close();
  }
});

test("probeTab: a target that stops answering hits the deadline as indeterminate", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "https://sellercentral.amazon.com/home", behavior: { neverReply: ["Runtime.evaluate"] } }],
  });
  try {
    const [page] = JSON.parse(await (await fetch(`http://127.0.0.1:${fake.port}/json/list`)).text());
    const t0 = Date.now();
    const r = await probeTab(page, { factsTimeoutMs: 500, deadlineMs: 2000 });
    assert.equal(r.state, "indeterminate");
    assert.ok(Date.now() - t0 < 8000, "must not wait out the full evaluate budget");
  } finally {
    await fake.close();
  }
});

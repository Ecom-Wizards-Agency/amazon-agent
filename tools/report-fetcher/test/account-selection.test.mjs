import assert from "node:assert/strict";
import test from "node:test";
import { accountProfileMatches, waitForMarketplaceSelection } from "../account-selection.mjs";
import { switchAccount } from "../sc-account.mjs";

const profile = { accountName: "Allfemme", marketplace: "us", marketplaceLabel: "United States", marketplaceId: "ATVPDKIKX0DER" };

test("exact seller plus the requested marketplace suffix is accepted", () => {
  for (const displayName of ["Allfemme United States", "Allfemme\nUnited States", "Allfemme / United States"]) {
    assert.equal(accountProfileMatches({ displayName, marketplace: null }, profile), true, displayName);
  }
  assert.equal(accountProfileMatches({ displayName: "Allfemme", marketplace: "ATVPDKIKX0DER" }, profile), true);
  assert.equal(accountProfileMatches({ displayName: "Allfemme", marketplace: "US" }, profile), true);
});

test("similar sellers and wrong or unverified marketplaces are rejected", () => {
  for (const displayName of ["Allfemme Plus", "Allfemme Plus United States", "Other Allfemme United States", "Allfemme Canada"]) {
    assert.equal(accountProfileMatches({ displayName, marketplace: "US" }, profile), false, displayName);
  }
  for (const marketplace of ["CA", "A2EUQ1WTGCTBG2", "atvpdkikx0der", "Canada", { unknown: "US" }]) {
    assert.equal(accountProfileMatches({ displayName: "Allfemme United States", marketplace }, profile), false);
  }
  assert.equal(accountProfileMatches({ displayName: "Allfemme", marketplace: null }, profile), false);
});

test("a correct seller label never overrides a missing or inexact configured partner ID", () => {
  const expected = { ...profile, expectedPartnerAccountId: "PARTNER" };
  for (const partnerAccountId of [null, "PARTNER_MORE", "partner", "OTHER"]) {
    assert.equal(accountProfileMatches({ displayName: "Allfemme United States", partnerAccountId }, expected), false);
  }
  assert.equal(accountProfileMatches({ displayName: "Allfemme United States", partnerAccountId: "PARTNER" }, expected), true);
});

test("marketplace options may take longer than the old 500 ms delay to appear", async () => {
  const started = Date.now();
  let reads = 0;
  const hit = await waitForMarketplaceSelection(async () => {
    reads++;
    return Date.now() - started < 650
      ? { count: 0, optionCount: 0, loading: true }
      : { count: 1, x: 10, y: 20, current: false };
  }, "Allfemme / United States", { timeoutMs: 2000, pollMs: 50 });
  assert.equal(hit.x, 10);
  assert.ok(reads > 2);
});

test("duplicate marketplace matches fail immediately without choosing a row", async () => {
  let reads = 0;
  await assert.rejects(waitForMarketplaceSelection(async () => {
    reads++;
    return { count: 2, optionCount: 2 };
  }, "Allfemme / United States"), { code: "ACCOUNT_SWITCH_MARKETPLACE_AMBIGUOUS" });
  assert.equal(reads, 1);
});

test("a loaded list missing the requested marketplace differs from a loading timeout", async () => {
  await assert.rejects(waitForMarketplaceSelection(async () => ({ count: 0, optionCount: 2, loading: false }),
    "United States", { timeoutMs: 0 }), { code: "ACCOUNT_SWITCH_MARKETPLACE_MISSING" });
  for (const hit of [{ count: 0, optionCount: 0 }, { count: 0, optionCount: 2, loading: true }, { count: 1 }]) {
    await assert.rejects(waitForMarketplaceSelection(async () => hit, "United States", { timeoutMs: 0 }),
      { code: "ACCOUNT_SWITCH_MARKETPLACE_TIMEOUT" });
  }
});

test("task control loss is propagated without retrying selection", async () => {
  const error = Object.assign(new Error("lost ownership"), { code: "TASK_TAB_CONTROL_LOST" });
  await assert.rejects(waitForMarketplaceSelection(async () => { throw error; }, "United States"), error);
});

function pickerSession({ expanded = false, accountCount = 1, options = [] } = {}) {
  const clicks = [];
  let probes = 0;
  const session = {
    assertTaskControl: async () => {},
    send: async (method, params) => {
      if (method === "Input.dispatchMouseEvent" && params.type === "mouseReleased") clicks.push(params.x);
      if (method !== "Runtime.evaluate") return {};
      const expression = params.expression;
      let value = true;
      if (expression.includes("inspectPickerSelection")) {
        if (expression.endsWith(',"marketplace")')) value = options[Math.min(probes++, options.length - 1)];
        else value = accountCount === 1 ? { count: 1, x: 10, y: 10, expanded } : { count: 0, accountCount };
      } else if (expression.includes("chooserButtonCount")) {
        value = { url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace", chooserButtonCount: 2 };
      } else if (expression.includes("getBoundingClientRect")) value = { x: 30, y: 30 };
      return { result: { value } };
    },
  };
  return { session, clicks, probes: () => probes };
}

test("shared switcher expands a collapsed seller once and polls until its option appears", async () => {
  const pending = { count: 0, optionCount: 0, loading: true };
  const fixture = pickerSession({ options: [pending, pending, pending, { count: 1, x: 20, y: 20 }] });
  await switchAccount(fixture.session, "https://sellercentral.amazon.com", profile);
  assert.deepEqual(fixture.clicks, [10, 20, 30]);
  assert.ok(fixture.probes() >= 4);
});

test("shared switcher never collapses an already expanded seller while options load", async () => {
  const fixture = pickerSession({ expanded: true,
    options: [{ count: 0, optionCount: 0 }, { count: 1, x: 20, y: 20 }] });
  await switchAccount(fixture.session, "https://sellercentral.amazon.com", profile);
  assert.deepEqual(fixture.clicks, [20, 30]);
});

test("shared switcher does not click duplicate sellers or marketplace options", async () => {
  for (const [fixture, code] of [
    [pickerSession({ accountCount: 2 }), "ACCOUNT_SWITCH_ACCOUNT_AMBIGUOUS"],
    [pickerSession({ options: [{ count: 2, optionCount: 2 }] }), "ACCOUNT_SWITCH_MARKETPLACE_AMBIGUOUS"],
  ]) {
    await assert.rejects(switchAccount(fixture.session, "https://sellercentral.amazon.com",
      { ...profile, parentAccountName: "Agency" }), { code });
    assert.deepEqual(fixture.clicks, []);
  }
});

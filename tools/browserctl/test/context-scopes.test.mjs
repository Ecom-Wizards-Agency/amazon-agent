import assert from "node:assert/strict";
import test from "node:test";
import { assertContextCovers, isRegionalScope, resolveContextScope, sellerCentralScope, scopeForOrigin } from "../context-scopes.mjs";

test("coordination groups follow the supported North America, EU/UK and Australia boundaries", () => {
  for (const [expected, marketplaces] of [
    ["sc:na", ["us", "CA", "mx"]],
    ["sc:eu", ["de", "fr", "it", "es", "nl", "se", "pl", "be", "ie", "uk", "GB"]],
    ["sc:au", ["au"]],
  ]) {
    assert.equal(isRegionalScope(expected), true);
    for (const marketplace of marketplaces) assert.equal(sellerCentralScope({ marketplace }), expected);
  }
  for (const [origin, scope] of [
    ["https://sellercentral.amazon.com/home", "sc:na"],
    ["https://sellercentral.amazon.ca", "sc:na"],
    ["https://sellercentral.amazon.com.mx", "sc:na"],
    ["https://sellercentral.amazon.co.uk", "sc:eu"],
    ["https://sellercentral.amazon.com.be", "sc:eu"],
    ["https://sellercentral.amazon.com.au", "sc:au"],
    ["https://sellercentral.amazon.com.br", "global"],
    ["https://sellercentral.amazon.com.tr", "global"],
  ]) assert.equal(scopeForOrigin(origin), scope);
});

test("same-region origin aliases work while contradictory regions fail before acquisition", () => {
  assert.equal(sellerCentralScope({ marketplace: "fr", origin: "https://sellercentral.amazon.de" }), "sc:eu");
  assert.equal(sellerCentralScope({ marketplace: "mx", origin: "https://sellercentral.amazon.com" }), "sc:na");
  assert.throws(() => sellerCentralScope({ marketplace: "us", origin: "https://sellercentral.amazon.de" }),
    { code: "TASK_TAB_CONTEXT_MISMATCH" });
  assert.throws(() => assertContextCovers("sc:na", { origin: "https://sellercentral.amazon.com.au" }),
    { code: "TASK_TAB_CONTEXT_MISMATCH" });
  assert.equal(assertContextCovers("global", { marketplace: "au" }), "sc:au");
});

test("unsupported groups and legacy exclusive callers remain conservative", () => {
  for (const marketplace of ["br", "tr", "jp", "in", "sg", "ae", "sa", "eg", "za", "zz"]) {
    assert.equal(sellerCentralScope({ marketplace }), "global");
  }
  assert.equal(sellerCentralScope({ marketplace: "us", origin: "https://sellercentral.amazon.com.br" }), "global");
  assert.equal(resolveContextScope({ exclusiveContext: true }), "global");
  assert.equal(resolveContextScope({}), null);
  assert.equal(resolveContextScope({ exclusiveContext: true, sellerCentral: { marketplace: "au" } }), "sc:au");
  assert.throws(() => resolveContextScope({ sellerCentral: { marketplace: "de" } }), { code: "TASK_TAB_CONTEXT_INVALID" });
});

test("origin parsing uses exact hosts and rejects malformed operation descriptors", () => {
  for (const origin of ["about:blank", "https://app.flatfile.pro", "https://www.amazon.com/ap/signin",
    "https://sellercentral.amazon.com.example.org"]) assert.equal(scopeForOrigin(origin), null);
  for (const descriptor of [null, [], {}, { region: "sc:na" }, { marketplace: "Germany" },
    { origin: "not a URL" }, { origin: "https://sellercentral.amazon.com.example.org" },
    { origin: "http://sellercentral.amazon.com" }, { origin: "https://sellercentral.amazon.de:9000" },
    { origin: "https://user:password@sellercentral.amazon.de" }]) {
    assert.throws(() => sellerCentralScope(descriptor), { code: "TASK_TAB_CONTEXT_INVALID" });
  }
  assert.throws(() => assertContextCovers(null, { marketplace: "de" }), { code: "TASK_TAB_CONTEXT_MISMATCH" });
});

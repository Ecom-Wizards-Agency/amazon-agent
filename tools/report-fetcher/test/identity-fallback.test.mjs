import assert from "node:assert/strict";
import test from "node:test";
import { runInNewContext } from "node:vm";
import { identityFromDocument, readIdentity } from "../sc-account.mjs";

const origin = "https://sellercentral.amazon.com";
const metaSelector = 'meta[name="anti-csrftoken-a2z"]';
const nameSelector = '#sc-mkt-picker-switcher-select';
const loginSelector = 'input[type="password"],input[type="email"],#ap_email';
const homeHtml = '<meta name="anti-csrftoken-a2z" content="fixture-token"><div id="sc-mkt-picker-switcher-select"> Example Brand / United States </div>';
const signInHtml = '<html><title>Amazon Sign-In</title><input type="password"></html>';
const context = { partnerAccountId: "PARTNER", merchantId: "MERCHANT", marketplaceSelection: "ATVPDKIKX0DER" };

// Document-shaped fixtures test the shared selectors without implementing an HTML parser.
function doc({ token = null, name = null, selectors = {} } = {}) {
  const nodes = {
    [metaSelector]: token === null ? null : { getAttribute: attr => attr === "content" ? token : null },
    [nameSelector]: name === null ? null : { textContent: name },
    ...selectors,
  };
  return { querySelector: selector => nodes[selector] || null };
}

async function read({ page = doc(), homeDoc = doc({ token: "fixture-token", name: "Example Brand / United States" }),
  html = homeHtml, homeUrl = `${origin}/amazonsell/business`, homeStatus = 200,
  homeError = null, graphqlStatus = 200, graphqlError = null } = {}) {
  const calls = [];
  let parsed = false;
  const session = {
    async send(method, params) {
      if (method === "Runtime.enable") return {};
      assert.equal(method, "Runtime.evaluate");
      const value = await runInNewContext(params.expression, {
        document: page, location: { origin }, URL,
        DOMParser: class {
          parseFromString(actualHtml, type) {
            assert.equal(actualHtml, html);
            assert.equal(type, "text/html");
            parsed = true;
            return homeDoc;
          }
        },
        async fetch(url, options) {
          calls.push({ url, options });
          assert.equal(options.credentials, "include");
          assert.equal(options.mode, "same-origin", "redirects must not escape the current Seller Central origin");
          if (url === `${origin}/home`) {
            if (homeError) throw homeError;
            return { ok: homeStatus === 200, status: homeStatus, url: homeUrl, text: async () => html };
          }
          assert.equal(url, `${origin}/ox-api/graphql`);
          assert.equal(options.method, "POST");
          assert.equal(JSON.parse(options.body).operationName, "GetUserContext");
          if (graphqlError) throw graphqlError;
          return { ok: graphqlStatus === 200, status: graphqlStatus, json: async () => ({ data: { userContext: context } }) };
        },
      });
      return { result: { value: JSON.parse(JSON.stringify(value)) } };
    },
    close() { assert.fail("identity evaluation must complete without closing the session"); },
  };
  return { identity: await readIdentity(session), calls, parsed };
}

function expectIds(identity, source) {
  assert.deepEqual(identity, {
    displayName: "Example Brand / United States", partnerAccountId: "PARTNER", merchantId: "MERCHANT",
    marketplace: "ATVPDKIKX0DER", err: null, source,
  });
}

test("identityFromDocument reads detached picker text, normalizes whitespace, and keeps selector order", () => {
  assert.deepEqual(identityFromDocument(doc({ token: "fixture-token", name: "\n Example Brand  /\n United States " })),
    { token: "fixture-token", displayName: "Example Brand / United States" });
  assert.equal(identityFromDocument(doc({ name: "fallback", selectors: {
    '[data-test="current-account"]': { innerText: "live account", textContent: "other text" },
  } })).displayName, "live account");
  assert.equal(identityFromDocument(doc({ name: "x".repeat(100) })).displayName.length, 80);
  assert.deepEqual(identityFromDocument(doc()), { token: null, displayName: null });
});

test("readIdentity evaluates the page script and keeps the live-page path", async () => {
  const { identity, calls, parsed } = await read({ page: doc({ token: "page-token", name: "Example Brand / United States" }) });
  expectIds(identity, "page");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.headers["anti-csrftoken-a2z"], "page-token");
  assert.equal(parsed, false);
});

test("readIdentity fills all baseline fields from /home on a meta-less report shell", async () => {
  const { identity, calls, parsed } = await read();
  expectIds(identity, "home");
  assert.equal(parsed, true);
  assert.deepEqual(calls.map(call => call.url), [`${origin}/home`, `${origin}/ox-api/graphql`]);
  assert.equal(calls[1].options.headers["anti-csrftoken-a2z"], "fixture-token");
  assert.deepEqual(Object.keys(identity).sort(), ["displayName", "partnerAccountId", "merchantId", "marketplace", "err", "source"].sort());
});

test("readIdentity prefers the live name over the fetched home name", async () => {
  const { identity } = await read({ page: doc({ name: "Live account" }) });
  assert.equal(identity.displayName, "Live account");
  assert.equal(identity.source, "home");
});

for (const [label, options, error] of [
  ["missing home meta", { homeDoc: doc(), html: signInHtml }, /no anti-csrftoken-a2z meta tag/],
  ["home transport failure", { homeError: new Error("network unavailable") }, /network unavailable/],
  ["home HTTP failure", { homeStatus: 503 }, /HTTP 503/],
  ["sign-in redirect", { homeUrl: `${origin}/ap/signin` }, /sign-in page/],
  ["sign-in HTML", { homeDoc: doc({ selectors: { [loginSelector]: {} } }), html: signInHtml }, /sign-in page/],
  ["foreign redirect response", { homeUrl: "https://www.amazon.com/ap/signin" }, /outside the Seller Central origin/],
]) {
  test(`readIdentity fails closed on ${label}`, async () => {
    const { identity, calls } = await read(options);
    assert.match(identity.err, error);
    assert.equal(identity.source, "home");
    assert.equal(identity.merchantId, null);
    assert.equal(identity.partnerAccountId, null);
    assert.equal(identity.marketplace, null);
    assert.equal(calls.length, 1, "must not query GraphQL after failed home verification");
  });
}

for (const [options, error] of [
  [{ graphqlStatus: 403 }, /GetUserContext not authorized \(403\)/],
  [{ graphqlError: new Error("offline") }, /GetUserContext transport failed: Error: offline/],
]) {
  test(`readIdentity preserves GraphQL error semantics: ${error.source}`, async () => {
    const { identity } = await read(options);
    assert.match(identity.err, error);
    assert.equal(identity.displayName, "Example Brand / United States");
    assert.equal(identity.merchantId, null);
    assert.equal(identity.partnerAccountId, null);
    assert.equal(identity.marketplace, null);
  });
}

import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "auth-broker-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
process.env.WIZARDS_AI_BROKER_SOCKET = join(runtime, "no-transport.sock");
delete process.env.WIZARDS_AI_MODE;
const {
  authenticateTarget, classifyAuthenticationPage, publicAuthenticationStatus, requiresCredentialTransport,
  totpPeriodEnd,
} = await import("../auth-broker.mjs");
const { loadBrowserPolicy } = await import("../policy.mjs");
test.after(() => rmSync(runtime, { recursive: true, force: true }));

const base = {
  origin: "https://example.test", path: "/", email: false, password: false,
  otp: false, captcha: false, recovery: false, approval: false, invalid: false,
  rateLimited: false, amazonApp: false,
};

test("Amazon adapter distinguishes app, password, OTP, and human challenge states", () => {
  assert.equal(classifyAuthenticationPage("amazon", { ...base, amazonApp: true }).status, "authenticated");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, password: true }).status, "password_required");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, otp: true }).status, "totp_required");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, captcha: true }).status, "human_challenge");
});

test("FlatFilePro adapter treats login as unauthenticated and app routes as authenticated", () => {
  assert.equal(classifyAuthenticationPage("flatfilepro", {
    ...base, origin: "https://app.flatfile.pro", path: "/login", email: true,
  }).status, "login_required");
  assert.equal(classifyAuthenticationPage("flatfilepro", {
    ...base, origin: "https://app.flatfile.pro", path: "/imports",
  }).status, "authenticated");
});

test("invalid credentials and rate limiting stop rather than retry", () => {
  assert.equal(classifyAuthenticationPage("flatfilepro", { ...base, invalid: true }).status, "authentication_failed");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, rateLimited: true }).status, "human_challenge");
});

test("public authentication statuses cannot include secret values", () => {
  const result = publicAuthenticationStatus({
    status: "authenticated", route: { id: "flatfilepro", adapter: "flatfilepro" },
    port: 9222, targetId: "target", origin: "https://app.flatfile.pro/login?token=secret",
    username: "user@example.test", password: "password-secret", otp: "123456",
  });
  const serialized = JSON.stringify(result);
  assert.deepEqual(Object.keys(result).sort(),
    ["adapter", "origin", "port", "route_id", "status", "targetId"].sort());
  assert.equal(result.origin, "https://app.flatfile.pro");
  assert.equal(/user@example|password-secret|123456|token=/.test(serialized), false);
});

test("1Password service-account mode fails closed onto the credential transport", () => {
  assert.equal(requiresCredentialTransport({
    authentication: { mode: "onepassword_service_account" },
  }), true);
  assert.equal(requiresCredentialTransport({ authentication: { mode: "interactive" } }), false);
});

const ORIGIN = "https://sellercentral.amazon.com";
const PUBLIC_KEYS = ["adapter", "origin", "port", "route_id", "status", "targetId"];

// One scripted login page: each submitted form advances to the next state.
function fakeLogin(pages, { failSubmit = false } = {}) {
  const page = { index: 0, typed: [], submits: 0 };
  const session = {
    async send(method, params) {
      if (method === "Input.insertText") page.typed.push(params.text);
      if (method === "Input.dispatchKeyEvent" && params.type === "rawKeyDown") {
        if (failSubmit) throw new Error("Inspected target navigated or closed");
        page.submits++;
        page.index = Math.min(page.index + 1, pages.length - 1);
      }
      return {};
    },
    close() {},
  };
  page.cdp = {
    assertChrome: async () => ({}),
    listPages: async () => [{ id: page.targetId, url: `${ORIGIN}/ap/signin`, webSocketDebuggerUrl: "ws://fixture" }],
    Session: { open: async () => session },
    evaluate: async (_session, expression) => {
      if (expression === "({origin:location.origin})") return { origin: ORIGIN };
      if (expression.includes("e.focus()")) return { focused: true, start: 0, end: 0, length: 0 };
      if (expression.startsWith("JSON.stringify({url:location.href")) return JSON.stringify({ index: page.index });
      return { ...base, origin: ORIGIN, path: "/ap/signin", url: `${ORIGIN}/ap/signin`, ...pages[page.index] };
    },
  };
  return page;
}

function provider(otp) {
  const route = { id: "seller-central", adapter: "amazon", origins: [ORIGIN] };
  return {
    assertAuthPolicy: () => route,
    loadRouteLogin: (_config, _route, { includeOtp = false } = {}) => ({
      username: "user@example.test", password: "password-secret", ...(includeOtp ? { otp } : {}),
    }),
  };
}

let targetCount = 0;
async function login(pages, otp, options = {}, fixture = {}) {
  const page = fakeLogin(pages, fixture);
  page.targetId = `T${++targetCount}`;
  const result = await authenticateTarget({
    port: 9223, targetId: page.targetId, policy: loadBrowserPolicy(), cdp: page.cdp,
    config: { authentication: { mode: "interactive" } }, authProvider: provider(otp), ...options,
  });
  return { result, page };
}

const PASSWORD = { email: true, password: true };
const CODE = { otp: true };
const APP = { amazonApp: true };

test("a code request without a supplied code returns totp_unavailable and submits nothing", async () => {
  for (const otp of [undefined, "", "   "]) {
    const direct = await login([CODE, APP], otp);
    assert.equal(direct.result.status, "totp_unavailable");
    assert.deepEqual(Object.keys(direct.result).sort(), PUBLIC_KEYS);
    assert.deepEqual(direct.page.typed, []);
    assert.equal(direct.page.submits, 0);
  }
  const afterPassword = await login([PASSWORD, CODE, APP], "", { onOtpSubmitted: () => assert.fail("no code") });
  assert.equal(afterPassword.result.status, "totp_unavailable");
  assert.equal(afterPassword.result.otp_submitted, false);
  assert.deepEqual(afterPassword.page.typed, ["user@example.test", "password-secret"]);
  assert.equal(afterPassword.page.submits, 1);
});

test("a code whose 30-second period ended before the code field appeared is never typed", async () => {
  const fetchedAt = 1_000_000_005_000;
  assert.equal(totpPeriodEnd(fetchedAt), 1_000_000_020_000);
  assert.equal(totpPeriodEnd(1_000_000_020_000), 1_000_000_050_000);
  for (const now of [1_000_000_020_000, 1_000_000_049_000]) {
    const expired = await login([PASSWORD, CODE, APP], "123456", { otpFetchedAt: fetchedAt, clock: () => now });
    assert.equal(expired.result.status, "totp_expired");
    assert.equal(expired.result.otp_submitted, false);
    assert.equal(expired.page.typed.includes("123456"), false);
    assert.equal(expired.page.submits, 1);
  }
  const current = await login([PASSWORD, CODE, APP], "123456", { otpFetchedAt: fetchedAt, clock: () => 1_000_000_019_999 });
  assert.equal(current.result.status, "authenticated");
  assert.deepEqual(current.page.typed, ["user@example.test", "password-secret", "123456"]);
  for (const otpFetchedAt of [Number.NaN, -1, 0, "soon"]) {
    await assert.rejects(login([CODE, APP], "123456", { otpFetchedAt }), /AUTH_OTP_FETCHED_AT_INVALID/);
  }
});

test("callers learn whether this attempt submitted a code, even when the submit throws", async () => {
  let calls = 0;
  const submitted = await login([PASSWORD, CODE, APP], "123456", { onOtpSubmitted: () => { calls++; } });
  assert.equal(submitted.result.status, "authenticated");
  assert.equal(submitted.result.otp_submitted, true);
  assert.equal(calls, 1);
  const none = await login([PASSWORD, APP], "123456", { otpFetchedAt: Date.now() });
  assert.equal(none.result.status, "authenticated");
  assert.equal(none.result.otp_submitted, false);
  calls = 0;
  await assert.rejects(login([CODE, APP], "123456", { onOtpSubmitted: () => { calls++; } }, { failSubmit: true }),
    /navigated or closed/);
  assert.equal(calls, 1);
});

test("without the code options the public status keeps its existing shape", async () => {
  const { result, page } = await login([PASSWORD, CODE, APP], "123456");
  assert.equal(result.status, "authenticated");
  assert.deepEqual(Object.keys(result).sort(), PUBLIC_KEYS);
  assert.deepEqual(page.typed, ["user@example.test", "password-secret", "123456"]);
  const challenge = await login([{ captcha: true }], "123456");
  assert.equal(challenge.result.status, "human_challenge");
  assert.deepEqual(Object.keys(challenge.result).sort(), PUBLIC_KEYS);
});

test("WIZARDS_AI_MODE refuses an operator login before any browser or credential access", async () => {
  process.env.WIZARDS_AI_MODE = "1";
  try {
    await assert.rejects(authenticateTarget({
      port: 9222, targetId: "T", policy: loadBrowserPolicy(), config: { authentication: { mode: "interactive" } },
      cdp: { assertChrome: async () => assert.fail("must not reach the browser") },
      authProvider: { assertAuthPolicy: () => assert.fail("must not resolve a route"),
        loadRouteLogin: () => assert.fail("must not read a credential") },
    }), /BROWSER_SESSION_REFUSED/);
  } finally { delete process.env.WIZARDS_AI_MODE; }
});

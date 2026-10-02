import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { runInNewContext } from "node:vm";

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

// A minimal DOM for the code form's submit-control query: one form holding the
// code input and the given controls. Selectors are tag, #id and [attr="value"]
// parts joined by commas; a control's x position identifies it in a click. A
// control marked outside sits outside the form; formAttr also ties it to the
// form through a form="..." attribute.
function fakeDocument(controls) {
  const form = {};
  const matches = (element, selector) => selector.split(",").some((part) => {
    const [, tag, id, name, value] = part.trim().match(/^([a-z]*)(?:#([\w-]+))?(?:\[([\w-]+)="([^"]*)"\])?$/);
    return (!tag || element.tag === tag) && (!id || element.id === id)
      && (!name || element.attrs[name] === value);
  });
  const elements = [{ tag: "input", name: "code" }, ...controls].map((attrs) => {
    const inside = !attrs.outside;
    const element = {
      tag: attrs.tag, id: attrs.id || "", attrs, disabled: false,
      form: inside || attrs.formAttr ? form : null, inside,
      type: attrs.type ?? (attrs.tag === "button" ? "submit" : "text"),
      name: attrs.name, value: attrs.value, innerText: attrs.text,
      getAttribute: (attribute) => attrs[attribute] ?? null,
      getClientRects: () => (attrs.hidden ? [] : [{}]),
      getBoundingClientRect: () => ({ x: attrs.x ?? 0, y: 0, width: attrs.hidden ? 0 : 20, height: 10 }),
      scrollIntoView() {},
      closest: (selector) => (selector === "form" && inside ? form : null),
      matches: (selector) => matches(element, selector),
    };
    return element;
  });
  const query = (scope) => (selector) => elements.filter((e) => scope(e) && matches(e, selector));
  form.querySelectorAll = query((e) => e.inside);
  form.querySelector = (selector) => form.querySelectorAll(selector)[0] || null;
  form.contains = (element) => element.inside;
  return { querySelectorAll: query(() => true) };
}

// The live Two-Step Verification page: #auth-signin-button and a second,
// unnamed submit control in the code form.
const LIVE_CONTROLS = [
  { tag: "input", type: "submit", id: "auth-signin-button", x: 100 },
  { tag: "button", type: "submit", x: 200 },
];

// One scripted login page. A page advances on Enter or a click (advance "any",
// the default), only on "enter", only on "click", or "never". Every Enter and
// click is recorded with the page index it was sent on. failSubmit (true or a
// message) throws before an Enter or click lands; releaseError throws from the
// mouse release after the click landed; snapshotErrors makes that many change
// snapshots after the first click throw a destroyed-context error.
function fakeLogin(pages, {
  failSubmit = false, releaseError = null, snapshotErrors = 0, controls = LIVE_CONTROLS,
} = {}) {
  const page = { index: 0, typed: [], submits: 0, events: [], clicked: [], snapshotFailures: 0 };
  const advanceOn = (method) => {
    const advance = pages[page.index].advance || "any";
    if (advance === method || advance === "any") {
      page.index = Math.min(page.index + 1, pages.length - 1);
    }
  };
  const session = {
    async send(method, params) {
      if (method === "Input.insertText") page.typed.push(params.text);
      const enter = method === "Input.dispatchKeyEvent" && params.type === "rawKeyDown";
      const click = method === "Input.dispatchMouseEvent" && params.type === "mousePressed";
      if (enter || click) {
        if (failSubmit) throw new Error(failSubmit === true ? "Inspected target navigated or closed" : failSubmit);
        page.submits++;
        page.events.push([page.index, enter ? "enter" : "click"]);
        if (click) page.clicked.push(params.x);
        advanceOn(enter ? "enter" : "click");
      }
      if (releaseError && method === "Input.dispatchMouseEvent" && params.type === "mouseReleased") {
        throw new Error(releaseError);
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
      if (expression.includes("candidates:")) {
        return runInNewContext(expression, { document: fakeDocument(controls) });
      }
      if (expression.includes("scrollIntoView")) return { x: 10, y: 20 };
      if (expression.startsWith("JSON.stringify({url:location.href")) {
        if (page.clicked.length && page.snapshotFailures < snapshotErrors) {
          page.snapshotFailures++;
          throw new Error("Execution context was destroyed.");
        }
        const current = pages[page.index];
        return JSON.stringify({ index: current.snapshotAs ?? page.index,
          ...(expression.includes(",alert:") ? { alert: current.alert || "" } : {}) });
      }
      return { ...base, origin: ORIGIN, path: "/ap/signin", url: `${ORIGIN}/ap/signin`, ...pages[page.index] };
    },
  };
  return page;
}

// The broker's 250 ms polls run immediately so a full wait takes no real time.
async function withFastPolls(run) {
  const realTimeout = globalThis.setTimeout;
  globalThis.setTimeout = (callback, _ms, ...args) => realTimeout(callback, 0, ...args);
  try { return await run(); } finally { globalThis.setTimeout = realTimeout; }
}

function provider(otp, adapter = "amazon") {
  const route = { id: "seller-central", adapter, origins: [ORIGIN] };
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
    config: { authentication: { mode: "interactive" } }, authProvider: provider(otp, fixture.adapter), ...options,
  });
  return { result, page };
}

const PASSWORD = { email: true, password: true };
const CODE = { otp: true };
const APP = { amazonApp: true };
const FETCHED = { otpFetchedAt: 1_000_000_005_000, clock: () => 1_000_000_005_000 };
const codeStep = (page, index) => page.events.filter(([at]) => at === index).map(([, kind]) => kind);

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
  // A click whose send fails with a navigation error is waited out; any other
  // send error propagates. Either way the code counts as submitted.
  calls = 0;
  await withFastPolls(() => assert.rejects(
    login([CODE, APP], "123456", { onOtpSubmitted: () => { calls++; } }, { failSubmit: true }),
    /^Error: AUTH_CODE_FORM_STALLED/));
  assert.equal(calls, 1);
  calls = 0;
  await assert.rejects(login([CODE, APP], "123456", { onOtpSubmitted: () => { calls++; } },
    { failSubmit: "CDP Input.dispatchMouseEvent timed out after 10000 ms" }), /dispatchMouseEvent timed out/);
  assert.equal(calls, 1);
});

test("with the code options, a navigation error from the click's release reads the landed page", async () => {
  const REJECTED = { ...CODE, alert: "The code you entered is not valid.", errorVisible: true };
  for (const [landed, status] of [[APP, "authenticated"], [REJECTED, "totp_rejected"]]) {
    let calls = 0;
    const { result, page } = await login([{ ...CODE, advance: "click" }, landed], "123456",
      { ...FETCHED, onOtpSubmitted: () => { calls++; } },
      { releaseError: "Inspected target navigated or closed" });
    assert.equal(result.status, status);
    assert.equal(result.otp_submitted, true);
    assert.deepEqual(page.events, [[0, "click"]]);
    assert.equal(calls, 1);
  }
});

test("with the code options, a destroyed context while waiting after the click sends nothing more", async () => {
  const REJECTED = { ...CODE, alert: "The code you entered is not valid.", errorVisible: true };
  for (const [landed, status] of [[APP, "authenticated"], [REJECTED, "totp_rejected"]]) {
    let calls = 0;
    const { result, page } = await login([{ ...CODE, advance: "click" }, landed], "123456",
      { ...FETCHED, onOtpSubmitted: () => { calls++; } }, { snapshotErrors: 2 });
    assert.equal(page.snapshotFailures, 2);
    assert.equal(result.status, status);
    assert.deepEqual(page.events, [[0, "click"]]);
    assert.deepEqual(page.typed, ["123456"]);
    assert.equal(calls, 1);
  }
});

test("with the code options, a code form that returns after a submitted code ends the call without a second code", async () => {
  const ERROR = { otp: true, path: "/ap/mfa", invalid: false };
  for (const options of [{}, { otpFetchedAt: Date.now() }]) {
    let calls = 0;
    const { result, page } = await login([CODE, ERROR, ERROR, APP], "123456",
      { ...options, onOtpSubmitted: () => { calls++; } });
    assert.equal(result.status, "totp_rejected");
    assert.equal(result.otp_submitted, true);
    assert.deepEqual(page.typed, ["123456"]);
    assert.equal(page.submits, 1);
    assert.equal(calls, 1);
  }
  // Review F3: without the code options (Grimoire's 9223 login) the code is
  // loaded and submitted again, as on main.
  const plain = await login([PASSWORD, CODE, CODE, APP], "123456");
  assert.equal(plain.result.status, "authenticated");
  assert.deepEqual(Object.keys(plain.result).sort(), PUBLIC_KEYS);
  assert.deepEqual(plain.page.typed, ["user@example.test", "password-secret", "123456", "123456"]);
  assert.equal(plain.page.submits, 3);
});

test("with the code options, the code is submitted by one click on #auth-signin-button and no Enter", async () => {
  let calls = 0;
  const { result, page } = await login([PASSWORD, { ...CODE, advance: "click" }, APP], "123456",
    { ...FETCHED, onOtpSubmitted: () => { calls++; } });
  assert.equal(result.status, "authenticated");
  assert.equal(result.otp_submitted, true);
  assert.equal(calls, 1);
  assert.deepEqual(page.typed, ["user@example.test", "password-secret", "123456"]);
  // The password step keeps Enter; the code step gets exactly one click on the
  // live page's #auth-signin-button (x 100 to 120), not the second control.
  assert.deepEqual(codeStep(page, 0), ["enter"]);
  assert.deepEqual(codeStep(page, 1), ["click"]);
  assert.deepEqual(page.clicked, [110]);
});

test("with the code options, email and password steps keep the full submit sequence", async () => {
  const { result, page } = await withFastPolls(() => login(
    [{ ...PASSWORD, advance: "click" }, { ...CODE, advance: "click" }, APP], "123456", FETCHED));
  assert.equal(result.status, "authenticated");
  // Enter first, then the click fallback, as without the code options.
  assert.deepEqual(codeStep(page, 0), ["enter", "click"]);
  assert.deepEqual(codeStep(page, 1), ["click"]);
});

test("with the code options, a code form that does not advance after its click stalls without a second action", async () => {
  let calls = 0;
  const page = fakeLogin([{ ...CODE, advance: "never" }, APP]);
  page.targetId = `T${++targetCount}`;
  await withFastPolls(() => assert.rejects(authenticateTarget({
    port: 9223, targetId: page.targetId, policy: loadBrowserPolicy(), cdp: page.cdp,
    config: { authentication: { mode: "interactive" } }, authProvider: provider("123456"),
    ...FETCHED, onOtpSubmitted: () => { calls++; },
  }), /^Error: AUTH_CODE_FORM_STALLED: the code was submitted once by one click .*not submitted again$/));
  assert.deepEqual(page.typed, ["123456"]);
  assert.deepEqual(page.events, [[0, "click"]]);
  assert.equal(calls, 1);
});

const twoUnnamed = [{ tag: "button", type: "submit", x: 100 }, { tag: "input", type: "submit", x: 200 }];
// A button without a type attribute is a submit control too.
const untyped = [{ tag: "button", type: "submit", x: 100 }, { tag: "button", x: 200 }];
const hiddenPreferred = [{ tag: "input", type: "submit", id: "auth-signin-button", hidden: true, x: 100 },
  { tag: "button", type: "submit", x: 200 }];
const loneResend = [{ tag: "button", text: "Resend code", x: 200 }];
// Review F1: the real submit sits outside the form subtree, tied to it by a
// form="..." attribute, and the form holds only an untyped resend button.
const preferredByAttribute = [
  { tag: "input", type: "submit", id: "auth-signin-button", outside: true, formAttr: true, x: 100 },
  { tag: "button", text: "Didn't receive the code?", x: 200 },
];
const preferredUnattached = [
  { tag: "input", type: "submit", id: "auth-signin-button", outside: true, x: 100 },
  { tag: "button", text: "Resend code", x: 200 },
];

async function ambiguous(controls, count, adapter) {
  let calls = 0;
  const page = fakeLogin([CODE, APP], { controls });
  page.targetId = `T${++targetCount}`;
  await assert.rejects(authenticateTarget({
    port: 9223, targetId: page.targetId, policy: loadBrowserPolicy(), cdp: page.cdp,
    config: { authentication: { mode: "interactive" } }, authProvider: provider("123456", adapter),
    ...FETCHED, onOtpSubmitted: () => { calls++; },
  }), new RegExp(`^Error: AUTH_CODE_SUBMIT_AMBIGUOUS: the code form has ${count} eligible`));
  assert.deepEqual(page.typed, ["123456"]);
  assert.deepEqual(page.events, []);
  assert.equal(calls, 0);
}

test("with the code options, the amazon adapter clicks only the form's #auth-signin-button", async () => {
  for (const controls of [twoUnnamed, untyped, [], hiddenPreferred, loneResend, preferredUnattached]) {
    await ambiguous(controls, 0, "amazon");
  }
  // Tied to the form by form="...": that control is clicked, never the resend.
  const { result, page } = await login([{ ...CODE, advance: "click" }, APP], "123456", FETCHED,
    { controls: preferredByAttribute });
  assert.equal(result.status, "authenticated");
  assert.deepEqual(page.clicked, [110]);
});

test("with the code options, other adapters click the form's only submit control that is not a resend", async () => {
  for (const [controls, count] of [[twoUnnamed, 2], [untyped, 2], [[], 0], [loneResend, 0]]) {
    await ambiguous(controls, count, "flatfilepro");
  }
  const cases = [
    // One submit control in the form, another outside it: the form's own is clicked.
    [[{ tag: "button", type: "submit", outside: true, x: 100 }, { tag: "button", type: "submit", x: 200 }], 210],
    // A control tied by form="..." belongs to the form; the resend is never a candidate.
    [preferredByAttribute, 110],
    [[{ tag: "button", value: "Send a new code", x: 100 }, { tag: "button", type: "submit", x: 200 }], 210],
    [[{ tag: "button", "aria-label": "Cancel", x: 100 }, { tag: "input", type: "submit", x: 200 }], 210],
  ];
  for (const [controls, x] of cases) {
    const { result, page } = await login([{ ...CODE, advance: "click" }, { path: "/imports" }], "123456", FETCHED,
      { controls, adapter: "flatfilepro" });
    assert.equal(result.status, "authenticated");
    assert.deepEqual(page.clicked, [x]);
  }
});

test("with the code options, an alert after the click ends through the classification, not as a stall", async () => {
  for (const [invalid, status] of [[false, "totp_rejected"], [true, "authentication_failed"]]) {
    // The URL and fields stay the same; only the alert text changes.
    const rejected = { ...CODE, snapshotAs: 0, alert: "The code you entered is not valid.", errorVisible: true, invalid };
    const { result, page } = await withFastPolls(() => login([{ ...CODE, advance: "click" }, rejected], "123456", FETCHED));
    assert.equal(result.status, status);
    assert.equal(result.otp_submitted, true);
    assert.deepEqual(page.events, [[0, "click"]]);
  }
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

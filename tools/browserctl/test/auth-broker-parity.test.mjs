import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";

// A login that passes none of the code options (otpFetchedAt, onOtpSubmitted),
// as Grimoire's 9223 login does, must run the same submit sequence as the
// broker on main before the attended-9222 change. This drives one scripted page
// through both modules and compares every recorded browser and credential call.
const BASELINE = "26c5d90616cf1b959fb329cac0c71c3fbe6a3f2b";
const REPO = resolve(import.meta.dirname, "../../..");

const runtime = mkdtempSync(join(tmpdir(), "auth-broker-parity-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = join(runtime, "runtime");
process.env.AMAZON_BROWSER_POLICY = join(runtime, "runtime", "policy.json");
process.env.AMAZON_BROWSER_LOCK_DIR = join(runtime, "locks");
process.env.WIZARDS_AI_BROKER_SOCKET = join(runtime, "no-transport.sock");
delete process.env.WIZARDS_AI_MODE;
delete process.env.WIZARDS_AI_BROKER_REQUIRED;
mkdirSync(process.env.AMAZON_BROWSER_RUNTIME_DIR, { recursive: true });
test.after(() => rmSync(runtime, { recursive: true, force: true }));

let baselineAvailable = true;
try {
  execFileSync("git", ["-C", REPO, "cat-file", "-e", `${BASELINE}^{commit}`], { stdio: "ignore" });
} catch { baselineAvailable = false; }

// The baseline broker has no cdp option and imports tools/report-fetcher/cdp.mjs
// itself, so its tree gets a stand-in cdp.mjs that forwards to the current fake.
const baselineRoot = join(runtime, "baseline");
if (baselineAvailable) {
  mkdirSync(baselineRoot, { recursive: true });
  const archive = execFileSync("git", ["-C", REPO, "archive", BASELINE, "tools/browserctl"]);
  execFileSync("tar", ["-x", "-C", baselineRoot], { input: archive });
  mkdirSync(join(baselineRoot, "tools/report-fetcher"), { recursive: true });
  writeFileSync(join(baselineRoot, "tools/report-fetcher/cdp.mjs"), `const fake = () => globalThis.__authBrokerParityCdp;
export const assertChrome = (...args) => fake().assertChrome(...args);
export const listPages = (...args) => fake().listPages(...args);
export const evaluate = (...args) => fake().evaluate(...args);
export const Session = { open: (...args) => fake().Session.open(...args) };
`);
}

const modules = baselineAvailable ? {
  baseline: {
    broker: await import(pathToFileURL(join(baselineRoot, "tools/browserctl/auth-broker.mjs")).href),
    policy: await import(pathToFileURL(join(baselineRoot, "tools/browserctl/policy.mjs")).href),
  },
  branch: {
    broker: await import("../auth-broker.mjs"),
    policy: await import("../policy.mjs"),
  },
} : null;

const ORIGIN = "https://sellercentral.amazon.com";
const base = {
  origin: ORIGIN, path: "/ap/signin", url: `${ORIGIN}/ap/signin`, email: false, password: false,
  otp: false, captcha: false, recovery: false, approval: false, invalid: false,
  rateLimited: false, amazonApp: false,
};

// Each page advances on one submit method: Enter (default), a click, requestSubmit,
// or never. Every call the broker makes is recorded in order.
function scriptedLogin(pages, otp) {
  const page = { index: 0, actions: [] };
  const record = (...entry) => page.actions.push(entry);
  const advanceOn = (method) => {
    if ((pages[page.index].advance || "enter") === method) {
      page.index = Math.min(page.index + 1, pages.length - 1);
    }
  };
  const session = {
    async send(method, params, options) {
      record("send", method, params, options);
      if (method === "Input.dispatchKeyEvent" && params.type === "rawKeyDown") advanceOn("enter");
      if (method === "Input.dispatchMouseEvent" && params.type === "mousePressed") advanceOn("click");
      return {};
    },
    close() { record("close"); },
  };
  page.cdp = {
    assertChrome: async () => { record("assertChrome"); return {}; },
    listPages: async () => {
      record("listPages");
      return [{ id: page.targetId, url: `${ORIGIN}/ap/signin`, webSocketDebuggerUrl: "ws://fixture" }];
    },
    Session: { open: async (url) => { record("Session.open", url); return session; } },
    evaluate: async (_session, expression, ...rest) => {
      record("evaluate", expression, ...rest);
      if (expression === "({origin:location.origin})") return { origin: ORIGIN };
      if (expression.includes("e.focus()")) return { focused: true, start: 0, end: 0, length: 0 };
      if (expression.includes("requestSubmit")) { advanceOn("requestSubmit"); return true; }
      if (expression.includes("scrollIntoView")) return { x: 10, y: 20 };
      if (expression.startsWith("JSON.stringify({url:location.href")) return JSON.stringify({ index: page.index });
      const { advance: _advance, ...facts } = pages[page.index];
      return { ...base, ...facts };
    },
  };
  const route = { id: "seller-central", adapter: "amazon", origins: [ORIGIN] };
  page.provider = {
    assertAuthPolicy: (_config, context) => { record("assertAuthPolicy", context); return route; },
    loadRouteLogin: (_config, _route, { includeOtp = false } = {}) => {
      record("loadRouteLogin", includeOtp);
      return { username: "user@example.test", password: "password-secret", ...(includeOtp ? { otp } : {}) };
    },
  };
  return page;
}

let targetCount = 0;
async function drive(name, policyFile, pages, otp) {
  const page = scriptedLogin(pages, otp);
  page.targetId = `${name}-${++targetCount}`;
  const { broker, policy } = modules[name];
  const env = { ...process.env };
  const realTimeout = globalThis.setTimeout;
  // The broker's 250 ms polls run immediately so the 10 s fallbacks take no real time.
  globalThis.setTimeout = (callback, _ms, ...args) => realTimeout(callback, 0, ...args);
  globalThis.__authBrokerParityCdp = page.cdp;
  let outcome;
  try {
    // No code options: the baseline ignores cdp and loads the stand-in module.
    outcome = { result: await broker.authenticateTarget({
      port: 9223, targetId: page.targetId, policy: policy.loadBrowserPolicy(policyFile), cdp: page.cdp,
      config: { authentication: { mode: "interactive" } }, authProvider: page.provider,
    }) };
  } catch (error) {
    outcome = { error: error.message };
  } finally {
    globalThis.setTimeout = realTimeout;
    delete globalThis.__authBrokerParityCdp;
    // The baseline's cdpForPort writes CDP_* and session variables into process.env.
    for (const key of Object.keys(process.env)) if (!(key in env)) delete process.env[key];
    Object.assign(process.env, env);
  }
  if (outcome.result) delete outcome.result.targetId;
  return { ...outcome, actions: page.actions };
}

const POLICIES = [
  ["without routing.default_cdp_port", {}],
  ["with routing.default_cdp_port 9222", { routing: { default_cdp_port: 9222 } }],
];
function policyFiles() {
  return POLICIES.map(([label, extra], index) => {
    const file = join(runtime, `policy-${index}.json`);
    writeFileSync(file, JSON.stringify({ schema_version: 1, ...extra, ports: {
      9222: { profile: join(runtime, "operator-profile") }, 9223: { profile: join(runtime, "grimoire-profile") },
    } }));
    return [label, file];
  });
}

const EMAIL = { email: true };
const PASSWORD = { email: true, password: true };
const PASSWORD_ONLY = { password: true };
const CODE = { otp: true };
const APP = { amazonApp: true };

test("without the code options every submit runs exactly as on main", {
  skip: !baselineAvailable && `baseline commit ${BASELINE} is not in this clone`,
}, async () => {
  const scenarios = {
    "password then code, Enter advances": [[PASSWORD, CODE, APP], "123456"],
    "email step, password step, code": [[EMAIL, PASSWORD_ONLY, CODE, APP], "123456"],
    "code form advances only on a click": [[PASSWORD, { ...CODE, advance: "click" }, APP], "123456"],
    "code form advances only on requestSubmit": [[{ ...CODE, advance: "requestSubmit" }, APP], "123456"],
    "code form never advances": [[{ ...CODE, advance: "never" }], "123456"],
    "password form advances only on a click": [[{ ...PASSWORD, advance: "click" }, APP], "123456"],
    "code loaded with surrounding whitespace": [[CODE, APP], " 123456\n"],
    "already signed in": [[APP], "123456"],
    "human challenge": [[{ captcha: true }], "123456"],
  };
  for (const [label, file] of policyFiles()) {
    for (const [scenario, [pages, otp]] of Object.entries(scenarios)) {
      const main = await drive("baseline", file, pages, otp);
      const branch = await drive("branch", file, pages, otp);
      assert.ok(main.actions.length > 3, `${scenario}: baseline was not driven`);
      const clicked = main.actions.some(([kind, method]) => kind === "send" && method === "Input.dispatchMouseEvent");
      const requested = main.actions.some(([kind, expression]) => kind === "evaluate" && expression.includes("requestSubmit"));
      assert.equal(clicked, /click|requestSubmit|never/.test(scenario), `${scenario}: click fallback`);
      assert.equal(requested, /requestSubmit|never/.test(scenario), `${scenario}: requestSubmit fallback`);
      assert.deepEqual(branch, main, `${label}: ${scenario}`);
    }
  }
});

// The two protections kept for every caller only stop earlier: the branch's
// calls are a prefix of main's, with nothing added before the session closes.
test("without the code options the empty-code and rejected-code refusals only stop earlier", {
  skip: !baselineAvailable && `baseline commit ${BASELINE} is not in this clone`,
}, async () => {
  const scenarios = {
    "no code supplied": [[CODE, APP], undefined, "totp_unavailable"],
    "empty code supplied": [[PASSWORD, CODE, APP], "  ", "totp_unavailable"],
    "code form returns after the code": [[CODE, CODE, APP], "123456", "totp_rejected"],
    "code form returns after a clicked code": [
      [{ ...CODE, advance: "click" }, { ...CODE, advance: "click" }, APP], "123456", "totp_rejected"],
  };
  for (const [label, file] of policyFiles()) {
    for (const [scenario, [pages, otp, status]] of Object.entries(scenarios)) {
      const main = await drive("baseline", file, pages, otp);
      const branch = await drive("branch", file, pages, otp);
      assert.equal(branch.result?.status, status, `${label}: ${scenario}`);
      assert.deepEqual(branch.actions.at(-1), ["close"]);
      const before = branch.actions.slice(0, -1);
      assert.ok(before.length < main.actions.length, `${label}: ${scenario}`);
      assert.deepEqual(before, main.actions.slice(0, before.length), `${label}: ${scenario}`);
    }
  }
});

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import {
  authAttemptStatus, recordAuthAttempt, releaseLease, touchLease,
} from "./lease-registry.mjs";
import { loadBrowserPolicy, policyForPort } from "./policy.mjs";

const AMAZON_AGENT = resolve(import.meta.dirname, "../..");
const CDP_MODULE = resolve(AMAZON_AGENT, "tools/report-fetcher/cdp.mjs");
const CONFIG_PATH = resolve(
  (process.env.WIZARDS_AI_CONFIG || `${homedir()}/os/wizards-ai/config.json`).replace(/^~/, homedir()),
);
const AUTH_MODULE = resolve(
  (process.env.WIZARDS_AUTH_MODULE
    || `${homedir()}/os/wizards-ai/tools/wizards-inventory/auth.mjs`).replace(/^~/, homedir()),
);

const sleep = (ms) => new Promise((resolveSleep) => setTimeout(resolveSleep, ms));

async function cdpForPort(port, policy) {
  const config = policyForPort(port, policy);
  process.env.CDP_PORT = String(port);
  process.env.CDP_PROFILE = config.profile;
  process.env.CDP_START_URL = config.start_url;
  process.env.CDP_BROWSER_MODE = config.mode;
  return import(`${pathToFileURL(CDP_MODULE).href}?auth=${port}-${Date.now()}-${Math.random()}`);
}

function visible(selector) {
  return `[...document.querySelectorAll(${JSON.stringify(selector)})]
    .some(e=>!e.disabled&&e.getClientRects().length>0&&e.getBoundingClientRect().width>0)`;
}

async function inspectPage(cdp, session, adapter) {
  const facts = await cdp.evaluate(session, `(()=>{
    const visible=s=>[...document.querySelectorAll(s)].some(e=>!e.disabled&&e.getClientRects().length>0&&e.getBoundingClientRect().width>0);
    const alert=[...document.querySelectorAll('#auth-error-message-box,.a-alert-error,[role="alert"],.error,.MuiAlert-message')]
      .find(e=>e.getClientRects().length>0&&e.getBoundingClientRect().width>0&&(e.innerText||'').trim());
    const text=(alert?.innerText||'').toLowerCase();
    return {
      origin:location.origin,path:location.pathname,url:location.href,
      email:visible('input[type="email"],input[name="email"],input[autocomplete="username"],#ap_email,#ap_email_login'),
      password:visible('input[type="password"],input[name="password"]'),
      otp:visible('input[name="otpCode"],input[name="code"],input[autocomplete="one-time-code"]'),
      captcha:!!document.querySelector('input[name="guess"],img[src*="captcha"],form[action*="validateCaptcha"],iframe[src*="captcha"],iframe[src*="recaptcha"]'),
      recovery:/account-recovery|forgot-password|password-reset/i.test(location.pathname)
        ||!!document.querySelector('form[action*="account-recovery"],form[action*="password-reset"]'),
      approval:!!document.querySelector('[data-a-name*="approval"],form[action*="cvf"],input[name*="approval"]'),
      amazonApp:!!document.querySelector('meta[name="anti-csrftoken-a2z"]')||location.pathname.includes('/account-switcher'),
      errorVisible:!!alert,
      invalid:/incorrect|not correct|invalid password|invalid email|wrong password|falsch|incorrecte|incorrecta|could not sign in/.test(text),
      rateLimited:/too many|temporarily locked|zu viele|trop de tentatives|try again later/.test(text)
    };
  })()`);
  return classifyAuthenticationPage(adapter, facts);
}

export function classifyAuthenticationPage(adapter, facts) {
  if (facts.captcha || facts.recovery || facts.approval) return { status: "human_challenge", facts };
  if (facts.rateLimited) return { status: "human_challenge", facts };
  if (facts.invalid) return { status: "authentication_failed", facts };
  if (facts.otp) return { status: "totp_required", facts };
  if (facts.password) return { status: "password_required", facts };
  if (facts.email) return { status: "login_required", facts };
  if (adapter === "amazon") {
    return { status: facts.amazonApp ? "authenticated" : "login_required", facts };
  }
  if (adapter === "flatfilepro") {
    const loginPath = /\/(login|signin)(?:\/|$)/i.test(facts.path);
    return { status: loginPath ? "login_required" : "authenticated", facts };
  }
  return { status: "human_challenge", facts };
}

export function publicAuthenticationStatus({
  status, route, port, targetId, origin, retryAt = null,
}) {
  return {
    status,
    ...(retryAt == null ? {} : { retry_at: retryAt }),
    route_id: route.id,
    adapter: route.adapter,
    port: Number(port),
    targetId,
    origin: new URL(origin).origin,
  };
}

async function trustedClick(cdp, session, selector, description) {
  const expression = `(()=>{const e=[...document.querySelectorAll(${JSON.stringify(selector)})]
    .find(e=>!e.disabled&&e.getClientRects().length>0&&e.getBoundingClientRect().width>0);
    if(!e)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();
    return{x:r.x+r.width/2,y:r.y+r.height/2}})()`;
  const point = await cdp.evaluate(session, expression, 10000);
  if (!point || !Number.isFinite(point.x) || !Number.isFinite(point.y)) {
    throw new Error(`AUTH_FORM_UNAVAILABLE: ${description}`);
  }
  for (const type of ["mousePressed", "mouseReleased"]) {
    await session.send("Input.dispatchMouseEvent", {
      type, x: point.x, y: point.y, button: "left", clickCount: 1,
    }, { timeoutMs: 10000 });
  }
}

async function replaceInput(cdp, session, selector, value, description) {
  const expression = `(()=>{const e=[...document.querySelectorAll(${JSON.stringify(selector)})]
    .find(e=>!e.disabled&&e.getClientRects().length>0&&e.getBoundingClientRect().width>0);
    if(!e)return null;e.scrollIntoView({block:'center'});e.focus();
    if(typeof e.select==='function')e.select();else if(typeof e.setSelectionRange==='function')e.setSelectionRange(0,(e.value||'').length);
    return{focused:document.activeElement===e,start:e.selectionStart,end:e.selectionEnd,length:(e.value||'').length}})()`;
  const selected = await cdp.evaluate(session, expression, 10000);
  if (!selected?.focused || (selected.start !== null
      && (selected.start !== 0 || selected.end !== selected.length))) {
    throw new Error(`AUTH_FORM_UNAVAILABLE: ${description}`);
  }
  await session.send("Input.insertText", { text: value }, { timeoutMs: 10000 });
}

async function submitForm(cdp, session) {
  const before = await cdp.evaluate(session, `JSON.stringify({url:location.href,
    email:${visible('input[type="email"],input[name="email"],input[autocomplete="username"],#ap_email,#ap_email_login')},
    password:${visible('input[type="password"],input[name="password"]')},
    otp:${visible('input[name="otpCode"],input[name="code"],input[autocomplete="one-time-code"]')}})`);
  const changed = async () => {
    for (let attempt = 0; attempt < 40; attempt++) {
      try {
        const current = await cdp.evaluate(session, `JSON.stringify({url:location.href,
          email:${visible('input[type="email"],input[name="email"],input[autocomplete="username"],#ap_email,#ap_email_login')},
          password:${visible('input[type="password"],input[name="password"]')},
          otp:${visible('input[name="otpCode"],input[name="code"],input[autocomplete="one-time-code"]')}})`);
        if (current !== before) return true;
      } catch (error) {
        if (!/context|navigation|target|session/i.test(error.message)) throw error;
      }
      await sleep(250);
    }
    return false;
  };
  for (const type of ["rawKeyDown", "keyUp"]) {
    await session.send("Input.dispatchKeyEvent", {
      type, key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13,
    }, { timeoutMs: 10000 });
  }
  if (await changed()) return;
  await trustedClick(cdp, session,
    'button[type="submit"],input[type="submit"],#signInSubmit,#continue', "authentication submit button");
  if (await changed()) return;
  const requested = await cdp.evaluate(session, `(()=>{const button=[...document.querySelectorAll('button[type="submit"],input[type="submit"],#signInSubmit,#continue')]
    .find(e=>!e.disabled&&e.getClientRects().length>0&&e.getBoundingClientRect().width>0);
    const form=button?.form||button?.closest('form');if(!button||!form)return false;
    if(typeof form.requestSubmit==='function')form.requestSubmit();else button.click();return true})()`, 10000);
  if (!requested || !await changed()) throw new Error("AUTH_FORM_UNAVAILABLE: form did not advance");
}

async function fillStep(cdp, session, state, login, getOtp) {
  if (state.status === "password_required") {
    if (state.facts.email) {
      await replaceInput(cdp, session,
        'input[type="email"],input[name="email"],input[autocomplete="username"],#ap_email,#ap_email_login',
        login.username, "login username");
    }
    await replaceInput(cdp, session, 'input[type="password"],input[name="password"]',
      login.password, "login password");
  } else if (state.status === "login_required") {
    await replaceInput(cdp, session,
      'input[type="email"],input[name="email"],input[autocomplete="username"],#ap_email,#ap_email_login',
      login.username, "login username");
  } else if (state.status === "totp_required") {
    const otp = await getOtp();
    await replaceInput(cdp, session,
      'input[name="otpCode"],input[name="code"],input[autocomplete="one-time-code"]',
      otp, "one-time password");
  } else return false;
  await submitForm(cdp, session);
  return true;
}

export async function authenticateTarget({
  port, targetId, policy = loadBrowserPolicy(), configPath = CONFIG_PATH,
} = {}) {
  const cdp = await cdpForPort(port, policy);
  await cdp.assertChrome();
  const page = (await cdp.listPages()).find((candidate) => candidate.id === targetId);
  if (!page) throw new Error("AUTH_TARGET_UNAVAILABLE: target does not exist");
  const session = await cdp.Session.open(page.webSocketDebuggerUrl);
  const config = JSON.parse(readFileSync(configPath, "utf8"));
  const auth = await import(`${pathToFileURL(AUTH_MODULE).href}?broker=${Date.now()}-${Math.random()}`);
  try {
    await session.send("Page.enable", {}, { timeoutMs: 10000 });
    await session.send("Runtime.enable", {}, { timeoutMs: 10000 });
    const initial = await cdp.evaluate(session, `({origin:location.origin})`, 10000);
    const route = auth.assertAuthPolicy(config, { port, origin: initial.origin });
    const output = (status, origin = initial.origin, retryAt = null) =>
      publicAuthenticationStatus({ status, route, port, targetId, origin, retryAt });
    let state = await inspectPage(cdp, session, route.adapter);
    if (state.status === "authenticated") {
      await touchLease({ port, targetId, kind: "activity", policy });
      return output("authenticated");
    }
    if (["human_challenge", "authentication_failed"].includes(state.status)) {
      await releaseLease({ port, targetId, outcome: state.status, policy });
      return output(state.status);
    }
    const cooldown = await authAttemptStatus({
      port, targetId, routeId: route.id, cooldownMs: policy.cleanup.auth_retry_cooldown_ms,
    });
    if (!cooldown.allowed) {
      return output("cooldown", initial.origin, cooldown.retryAt);
    }
    await recordAuthAttempt({ port, targetId, routeId: route.id });
    let login;
    const getLogin = () => {
      login ||= auth.loadRouteLogin(config, route);
      return login;
    };
    for (let step = 0; step < 8; step++) {
      state = await inspectPage(cdp, session, route.adapter);
      if (state.facts.origin !== initial.origin
          && !route.origins.includes(state.facts.origin)) {
        await releaseLease({ port, targetId, outcome: "human_challenge", policy });
        return output("human_challenge", state.facts.origin);
      }
      if (state.status === "authenticated") {
        await touchLease({ port, targetId, kind: "activity", policy });
        return output("authenticated", state.facts.origin);
      }
      if (["human_challenge", "authentication_failed"].includes(state.status)) {
        await releaseLease({ port, targetId, outcome: state.status, policy });
        return output(state.status, state.facts.origin);
      }
      const currentLogin = getLogin();
      const advanced = await fillStep(cdp, session, state, currentLogin,
        () => auth.loadRouteLogin(config, route, { includeOtp: true }).otp);
      if (!advanced) break;
      await sleep(250);
    }
    state = await inspectPage(cdp, session, route.adapter);
    if (state.status !== "authenticated") await releaseLease({ port, targetId, outcome: state.status, policy });
    return output(state.status, state.facts.origin);
  } finally {
    session.close();
  }
}

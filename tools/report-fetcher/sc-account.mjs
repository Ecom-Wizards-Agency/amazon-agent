/*
 * Seller Central account/session primitives shared by the report fetcher, the
 * POE downloader and future CDP runners: page classification (chooser,
 * sign-in, authorization-failed, app), live identity reads (GetUserContext +
 * display name), and the deterministic in-app account switch.
 *
 * The switcher drives Seller Central's own full-page account picker with
 * trusted input events (house rule: switch accounts only via the in-app
 * switcher, never by URL/domain rewriting). The confirm button lives in shadow
 * DOM and ignores synthetic JS clicks; both facts are load-bearing and came
 * out of tools/sc-sqp-competitor/sc_navigator.py and run-poe.mjs.
 *
 * Identity reads use the page's own anti-csrftoken-a2z meta tag to call the
 * same page's /ox-api/graphql GetUserContext, within the sanctioned same-origin
 * read-only carve-out. No cookies, storage or tokens are read beyond that tag.
 */
import { Session, evaluate } from "./cdp.mjs";

export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// The picker's confirm button, by visible label. Add new locales here.
export const CONFIRM_BUTTON_LABELS = ["Select account", "Konto auswählen", "Choose account"];

export function normalizeOrigin(value) {
  try { return new URL(value).origin; }
  catch (_) { throw new Error(`invalid Seller Central origin: ${value}`); }
}

export function accountPickerUrl(origin, returnTo = "/home") {
  return `${normalizeOrigin(origin)}/account-switcher/default/merchantMarketplace?returnTo=${encodeURIComponent(returnTo)}`;
}

// One evaluate gathers every fact classifyPage needs, so a probe costs a single
// round-trip on a possibly-sick target.
export const PAGE_FACTS_JS = `(function(){return {
  url: location.href,
  title: document.title,
  hasPasswordInput: !!document.querySelector('input[type="password"],input[type="email"],#ap_email'),
  hasChallengeInput: !!document.querySelector('input[name="guess"],img[src*="captcha"],input[autocomplete="one-time-code"],input[name="otpCode"]'),
  csrfMeta: !!document.querySelector('meta[name="anti-csrftoken-a2z"]'),
  chooserButtonCount: document.querySelectorAll('button.full-page-account-switcher-account-details').length,
  bodySnippet: ((document.body && document.body.innerText) || "").slice(0, 2000)
};})()`;

// Pure classification so it unit-tests without a browser. Order matters:
// the chooser and the authorization-failed page both contain "auth"-ish URL
// fragments that a naive sign-in regex would misread as logged_out (that
// misread is one root of the 13.08.2026 false "NOT signed in" verdict).
export function classifyPage(facts) {
  const f = facts || {};
  const url = String(f.url || "");
  const body = String(f.bodySnippet || "");
  if (/captcha|\/ap\/cvf|account-recovery/i.test(`${url} ${body}`) || f.hasChallengeInput) {
    return { pageKind: "challenge", authState: "human_challenge" };
  }
  // The account picker is an AUTHENTICATED state: reaching it requires a live
  // session. It just has no seller selected yet.
  if (Number(f.chooserButtonCount || 0) > 0 || /\/account-switcher\//.test(url)) {
    return { pageKind: "chooser", authState: "authenticated" };
  }
  if (/\/authorization\/failed/i.test(url)) {
    return { pageKind: "auth-failed", authState: f.csrfMeta ? "authenticated" : "ambiguous" };
  }
  if (/signin|authportal|\/ax\//i.test(url) || /sign[- ]?in/i.test(String(f.title || "")) || f.hasPasswordInput) {
    return { pageKind: "sign-in", authState: "logged_out" };
  }
  if (f.csrfMeta) return { pageKind: "app", authState: "authenticated" };
  return { pageKind: "unknown", authState: "ambiguous" };
}

export async function inspectPage(session, { timeoutMs = 8000 } = {}) {
  const facts = await evaluate(session, PAGE_FACTS_JS, timeoutMs);
  return { facts, ...classifyPage(facts) };
}

// Compatibility shape for callers that only want the auth verdict string.
export async function inspectAuthenticationState(session) {
  return (await inspectPage(session)).authState;
}

// Resolve the ACTIVE account from the live page: ids from the page's own
// GetUserContext plus the account-switcher display name from the DOM.
// Returns { displayName, partnerAccountId, merchantId, marketplace, err }.
// Never throws for identity problems; `err` names them instead.
const IDENTITY_JS = `(async function(){
  var out = { displayName: null, partnerAccountId: null, merchantId: null, marketplace: null, err: null };
  var meta = document.querySelector('meta[name="anti-csrftoken-a2z"]');
  if (!meta) {
    out.err = "no anti-csrftoken-a2z meta tag on this page (sign-in and account-chooser pages have none)";
  } else {
    try {
      var res = await fetch(location.origin + "/ox-api/graphql", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json", "Accept": "application/json", "anti-csrftoken-a2z": meta.getAttribute("content") },
        body: JSON.stringify({ operationName: "GetUserContext", variables: {},
          query: "query GetUserContext { userContext { partnerAccountId obfuscatedCustomerId monsSessionId monsSite antiCsrfToken marketplaceSelection merchantId requestId __typename } }" })
      });
      if (res.status === 401 || res.status === 403) out.err = "GetUserContext not authorized (" + res.status + ") on this page; ids unavailable here (normal outside Opportunity Explorer pages; the DOM display name still identifies the account)";
      else if (!res.ok) out.err = "GetUserContext failed with HTTP " + res.status;
      else {
        var parsed = await res.json();
        if (parsed.errors && parsed.errors.length) out.err = "GraphQL error: " + String(parsed.errors[0].message || "").slice(0, 200);
        var u = (parsed.data || {}).userContext || {};
        out.partnerAccountId = u.partnerAccountId || null;
        out.merchantId = u.merchantId || null;
        out.marketplace = u.marketplaceSelection || null;
      }
    } catch (e) { out.err = "GetUserContext transport failed: " + String(e); }
  }
  var sels = ['[data-test="current-account"]', '.dropdown-account-switcher-header',
    '[class*="AccountSwitcher" i]', '[data-testid*="account-switcher" i]', '[id*="account-switcher" i]',
    '[class*="partner-switcher" i]', '#sc-mkt-picker-switcher-select', '[aria-label*="account" i][role="button"]'];
  for (var i = 0; i < sels.length; i++) {
    var el = document.querySelector(sels[i]);
    var t = el && (el.innerText || el.textContent || "").trim();
    if (t) { out.displayName = t.replace(/\\s+/g, " ").trim().slice(0, 80); break; }
  }
  return out;
})()`;

export async function readIdentity(session, { timeoutMs = 30000 } = {}) {
  return evaluate(session, IDENTITY_JS, timeoutMs);
}

export async function waitFor(session, expression, description, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      if (await evaluate(session, expression, 10000)) return;
    } catch (error) {
      if (!/context|navigation|target|session/i.test(error.message)) throw error;
    }
    await sleep(250);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

export async function trustedClick(session, expression, description) {
  const box = await evaluate(session, expression, 10000);
  if (!box || !Number.isFinite(box.x) || !Number.isFinite(box.y)) {
    throw new Error(`Could not find ${description}`);
  }
  for (const type of ["mousePressed", "mouseReleased"]) {
    await session.send("Input.dispatchMouseEvent", {
      type, x: box.x, y: box.y, button: "left", clickCount: 1,
    }, { timeoutMs: 10000 });
  }
}

export async function waitForAppPage(session, timeoutMs = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const ok = await evaluate(session,
      `document.readyState === "complete" && !!document.querySelector('meta[name="anti-csrftoken-a2z"]')`,
      10000).catch(() => false);
    if (ok) return;
    await sleep(500);
  }
  throw new Error("page never became ready after the account switch (readyState/meta tag). Is the session logged in?");
}

/*
 * Drive the full-page account picker to `profile.accountName` /
 * `profile.marketplaceLabel` (optionally expanding `profile.parentAccountName`
 * first), then navigate to `returnTo` and wait for an authenticated app page.
 * Fail-closed: any ambiguity (0 or >1 matches, challenge, logged out) throws
 * ACCOUNT_SWITCH_BLOCKED and changes nothing further.
 */
export async function switchAccount(session, origin, profile, { returnTo = "/home" } = {}) {
  await session.send("Page.enable", {}, { timeoutMs: 10000 });
  await session.send("Page.navigate", { url: accountPickerUrl(origin, returnTo) }, { timeoutMs: 15000 });
  await waitFor(session, `document.readyState === "complete"`, "Seller Central account picker");
  await waitFor(session, `document.querySelectorAll("button.full-page-account-switcher-account-details").length > 0
    || /signin|auth|login|mfa|captcha|\\/ap\\/cvf/.test(location.href)
    || !!document.querySelector('input[type="password"],input[autocomplete="one-time-code"],input[name="guess"]')`,
  "account picker or authentication challenge");
  const auth = await inspectAuthenticationState(session);
  if (auth !== "authenticated") throw new Error(`ACCOUNT_SWITCH_BLOCKED: Seller Central is ${auth}`);

  const account = JSON.stringify(profile.accountName);
  const marketplace = JSON.stringify(profile.marketplaceLabel);
  const accountBox = `(()=>{const norm=s=>(s||"").replace(/\\s*\\((aktuell|current)\\)\\s*$/i,"").trim();
    const matches=[...document.querySelectorAll("button.full-page-account-switcher-account-details")].filter(e=>norm(e.innerText)===${account});
    if(matches.length!==1)return {count:matches.length};const e=matches[0];e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();
    return{x:r.x+r.width/2,y:r.y+r.height/2,count:1,expanded:!!e.querySelector("[class*=expanded]")}})()`;
  let accountHit = await evaluate(session, accountBox, 10000);
  if (accountHit?.count === 0 && profile.parentAccountName) {
    const parent = JSON.stringify(profile.parentAccountName);
    const parentBox = `(()=>{const matches=[...document.querySelectorAll("button.full-page-account-switcher-account-details")]
      .filter(e=>(e.innerText||"").trim()===${parent});if(matches.length!==1)return {count:matches.length};const e=matches[0];
      e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2,count:1,expanded:!!e.querySelector("[class*=expanded]")}})()`;
    const parentHit = await evaluate(session, parentBox, 10000);
    if (parentHit?.count !== 1) throw new Error(`ACCOUNT_SWITCH_BLOCKED: parent account is unavailable or ambiguous (${profile.parentAccountName})`);
    await trustedClick(session, parentBox, `parent account ${profile.parentAccountName}`);
    await sleep(500);
    accountHit = await evaluate(session, accountBox, 10000);
  }
  if (accountHit?.count !== 1) throw new Error(`ACCOUNT_SWITCH_BLOCKED: account is unavailable or ambiguous (${profile.accountName})`);

  const marketplaceBox = `(()=>{const norm=s=>(s||"").replace(/\\s*\\((aktuell|current)\\)\\s*$/i,"").trim();
    const groups=[...document.querySelectorAll("div.full-page-account-switcher-account")];
    const groupsForAccount=groups.filter(g=>[...g.children].some(c=>c.matches?.("button.full-page-account-switcher-account-details")&&norm(c.innerText)===${account}));
    if(groupsForAccount.length!==1)return {count:groupsForAccount.length};
    const matches=[...groupsForAccount[0].querySelectorAll("button.full-page-account-switcher-account-details")].filter(e=>norm(e.innerText)===${marketplace});
    if(matches.length!==1)return {count:matches.length};const e=matches[0];e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();
    return{x:r.x+r.width/2,y:r.y+r.height/2,count:1,current:/\\((aktuell|current)\\)/i.test(e.innerText||"")}})()`;
  let marketplaceHit = await evaluate(session, marketplaceBox, 10000);
  if (marketplaceHit?.count === 0) {
    await trustedClick(session, accountBox, `account ${profile.accountName}`);
    await sleep(500);
    marketplaceHit = await evaluate(session, marketplaceBox, 10000);
  }
  if (marketplaceHit?.count !== 1) throw new Error(`ACCOUNT_SWITCH_BLOCKED: marketplace is unavailable or ambiguous (${profile.marketplaceLabel})`);
  if (!marketplaceHit.current) {
    await trustedClick(session, marketplaceBox, `marketplace ${profile.marketplaceLabel}`);
    await sleep(500);
    const labels = JSON.stringify(CONFIRM_BUTTON_LABELS);
    await trustedClick(session, `(()=>{const all=[];const walk=root=>{for(const e of root.querySelectorAll("*")){all.push(e);if(e.shadowRoot)walk(e.shadowRoot)}};walk(document);
      const labels=${labels};const matches=all.filter(e=>e.tagName==="BUTTON"&&labels.includes((e.textContent||"").trim())&&e.getBoundingClientRect().width>0);
      if(matches.length!==1)return null;const r=matches[0].getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`, "account confirmation");
    await waitFor(session, `!location.pathname.includes("account-switcher")`, "selected Seller Central account");
  }
  await session.send("Page.navigate", { url: `${normalizeOrigin(origin)}${returnTo}` }, { timeoutMs: 15000 });
  await waitForAppPage(session);
}

export function accountMatches(acct, expected) {
  if (!expected) return true;
  const norm = (s) => String(s || "").toLowerCase().replace(/\s+/g, " ").trim();
  const want = norm(expected);
  const cands = [acct.displayName, acct.partnerAccountId, acct.merchantId].map(norm).filter(Boolean);
  return cands.some((c) => c === want || c.includes(want) || want.includes(c));
}

/*
 * Probe one /json/list page entry with hard budgets and return a conclusive
 * three-state result. Failures are INDETERMINATE, never "signed out": a target
 * that cannot be probed says nothing about the session (conflating the two
 * produced the 13.08.2026 false "NOT signed in" verdict).
 * Returns { state, pageKind, authState, url, title, identity, reason, stale }.
 * `stale: true` marks results whose url could only come from the snapshot.
 */
export async function probeTab(page, opts = {}) {
  const { openTimeoutMs = 8000, factsTimeoutMs = 8000, identityTimeoutMs = 10000, deadlineMs = 20000 } = opts;
  let deadlineTimer;
  const deadline = new Promise((resolve) => {
    deadlineTimer = setTimeout(() => resolve({
      state: "indeterminate", pageKind: null, authState: null, identity: null, stale: true,
      url: page.url, title: page.title, reason: `probe exceeded its ${deadlineMs} ms deadline`,
    }), deadlineMs);
    deadlineTimer.unref?.();
  });
  const work = (async () => {
    let s;
    try {
      s = await Session.open(page.webSocketDebuggerUrl, { timeoutMs: openTimeoutMs });
    } catch (e) {
      return { state: "indeterminate", pageKind: null, authState: null, identity: null, stale: true, url: page.url, title: page.title, reason: `could not attach: ${e.message}` };
    }
    try {
      let facts;
      try {
        facts = await evaluate(s, PAGE_FACTS_JS, factsTimeoutMs);
      } catch (e) {
        return { state: "indeterminate", pageKind: null, authState: null, identity: null, stale: true, url: page.url, title: page.title, reason: `probe failed: ${e.message}` };
      }
      const { pageKind, authState } = classifyPage(facts);
      const state = authState === "authenticated" ? "signed-in"
        : authState === "logged_out" ? "signed-out"
        : authState === "human_challenge" ? "challenge"
        : "indeterminate";
      const out = {
        state, pageKind, authState, identity: null, stale: false,
        url: facts.url, title: facts.title,
        reason: state === "indeterminate" ? "page state is ambiguous (neither an app page, a sign-in page, nor the chooser)" : null,
      };
      if (state === "signed-in" && pageKind !== "chooser") {
        try { out.identity = await readIdentity(s, { timeoutMs: identityTimeoutMs }); }
        catch (e) { out.identity = { displayName: null, partnerAccountId: null, merchantId: null, marketplace: null, err: e.message }; }
      }
      return out;
    } finally { s.close(); }
  })();
  try {
    return await Promise.race([work, deadline]);
  } finally {
    clearTimeout(deadlineTimer);
  }
}

// Pure doctor verdict over probeTab results. Never claims "NOT signed in"
// unless every tab was conclusively probed as signed out.
export function doctorVerdict(tabs) {
  if (!tabs.length) {
    return { exitCode: 1, text: "Login: no Seller Central tab is open. Run tools/report-fetcher/launch-chrome-debug.sh --mode recovery, sign in, then return it to headless mode." };
  }
  const byState = (st) => tabs.filter((t) => t.state === st);
  const signedIn = byState("signed-in");
  if (signedIn.length) {
    const chooserOnly = signedIn.every((t) => t.pageKind === "chooser");
    return {
      exitCode: 0,
      text: chooserOnly
        ? "Login: OK, but the session sits on the account chooser with NO account selected. Pick one in the debug window, or pass --account with account_name/marketplace_label so the runner selects it."
        : "Login: OK. Session is active, ready to fetch.",
    };
  }
  if (byState("challenge").length) {
    return { exitCode: 1, text: "Login: BLOCKED by a human challenge (captcha/OTP). Run launch-chrome-debug.sh --mode recovery, complete it, then re-run doctor." };
  }
  const indeterminate = byState("indeterminate");
  if (indeterminate.length) {
    const reasons = [...new Set(indeterminate.map((t) => t.reason).filter(Boolean))].join("; ");
    return { exitCode: 2, text: `Login: INDETERMINATE. Could not conclusively probe ${indeterminate.length} of ${tabs.length} tab(s)${reasons ? ` (${reasons})` : ""}. Retry doctor; if it persists, restart the debug Chrome with launch-chrome-debug.sh.` };
  }
  return { exitCode: 1, text: "Login: NOT signed in on any open tab. Sign into Seller Central in the debug window (launch-chrome-debug.sh --mode recovery), then re-run doctor." };
}

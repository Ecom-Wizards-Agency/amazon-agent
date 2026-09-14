import { evaluate } from "../report-fetcher/cdp.mjs";
import { readIdentity } from "../report-fetcher/sc-account.mjs";
import { accountProfileMatches } from "../report-fetcher/account-selection.mjs";
import { resolveSession } from "./session.mjs";
import { scopeForOrigin } from "./context-scopes.mjs";
import { assertDeliveryPostcode } from "../report-fetcher/marketplace-postcode.mjs";

export async function verifyEvidenceIdentity(handle, expected, deps = {}) {
  await handle.session.assertTaskControl();
  const facts = await (deps.evaluate || evaluate)(handle.session, `({url:location.href,
    login:!!document.querySelector('input[type="password"]'),text:document.body.innerText.slice(0,18000)})`);
  const url = new URL(facts.url);
  if (facts.login || /sign-in|signin|login/.test(url.pathname)) throw new Error("BROWSER_LOGIN_REQUIRED: restore the task's selected session");
  if (/Robot Check|Enter the characters you see|Sorry, we just need to make sure you're not a robot/i.test(facts.text || "")) {
    throw new Error("BROWSER_CHALLENGE_REQUIRED: no verified evidence captured");
  }
  if (expected?.kind === "seller-central") {
    if (!scopeForOrigin(url.origin) || !expected.accountName || !expected.marketplace) {
      throw new Error("EVIDENCE_IDENTITY_REQUIRED: exact seller and marketplace");
    }
    const identity = await (deps.readIdentity || readIdentity)(handle.session);
    if (!accountProfileMatches(identity, expected)) throw new Error("EVIDENCE_IDENTITY_MISMATCH: seller or marketplace changed");
    return { kind: expected.kind, ...identity, accountName: expected.accountName,
      requestedMarketplace: expected.marketplace, url: facts.url };
  }
  if (expected?.kind === "datadive") {
    const niche = url.pathname.match(/^\/niche\/([^/]+)(?:\/|$)/)?.[1];
    if (url.protocol !== "https:" || !["2.datadive.tools", "app.datadive.tools"].includes(url.hostname) ||
        !expected.nicheId || niche !== expected.nicheId ||
        !expected.heroKeyword || !facts.text.toLowerCase().includes(expected.heroKeyword.toLowerCase())) {
      throw new Error("EVIDENCE_IDENTITY_MISMATCH: DataDive niche does not match the research input");
    }
    return { kind: expected.kind, nicheId: niche, heroKeyword: expected.heroKeyword, url: facts.url };
  }
  if (expected?.kind === "amazon-retail") {
    const markets = { "www.amazon.com": "US", "www.amazon.de": "DE", "www.amazon.co.uk": "UK",
      "www.amazon.ca": "CA", "www.amazon.com.mx": "MX", "www.amazon.com.au": "AU",
      "www.amazon.fr": "FR", "www.amazon.it": "IT", "www.amazon.es": "ES", "www.amazon.nl": "NL" };
    const marketplace = markets[url.hostname];
    const asin = url.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})(?:\/|$)/)?.[1];
    const query = url.pathname === "/s" ? url.searchParams.get("k") : null;
    if (url.protocol !== "https:" || !marketplace || marketplace !== expected.marketplace ||
        (expected.asin ? asin !== expected.asin : !expected.query || query !== expected.query)) {
      throw new Error("EVIDENCE_IDENTITY_MISMATCH: retail marketplace, ASIN or query");
    }
    await (deps.assertDeliveryPostcode || assertDeliveryPostcode)(handle.session, url.hostname.slice("www.amazon.".length));
    return { kind: expected.kind, marketplace, asin, query, url: facts.url };
  }
  throw new Error("EVIDENCE_IDENTITY_REQUIRED: seller-central, datadive or amazon-retail identity");
}

export async function captureTaskEvidence(handle, { expected, selector } = {}, deps = {}) {
  const verify = deps.verify || verifyEvidenceIdentity;
  const before = await verify(handle, expected, deps);
  let clip;
  if (selector) {
    clip = await (deps.evaluate || evaluate)(handle.session, `(() => {
      const matches=[...document.querySelectorAll(${JSON.stringify(selector)})].filter(e=>e.checkVisibility());
      if(matches.length!==1) throw new Error('EVIDENCE_SELECTOR_AMBIGUOUS_OR_MISSING');
      const r=matches[0].getBoundingClientRect();
      return {x:Math.max(0,r.left+scrollX),y:Math.max(0,r.top+scrollY),width:r.width,height:r.height,scale:1};
    })()`);
  }
  const shot = await handle.session.send("Page.captureScreenshot", {
    format: "png", fromSurface: true, captureBeyondViewport: Boolean(clip), ...(clip ? { clip } : {}),
  });
  const after = await verify(handle, expected, deps);
  if (JSON.stringify(before) !== JSON.stringify(after)) throw new Error("EVIDENCE_IDENTITY_CHANGED: discard capture");
  const binding = resolveSession(handle.port === 9223 ? "grimoire" : "operator");
  return { data: Buffer.from(shot.data, "base64"), evidence: {
    session: binding.name, port: handle.port, profile: binding.profile,
    task_id: handle.taskId, workflow: handle.workflow, slot: handle.slot,
    target_id: handle.targetId, verified_identity: after, captured_at: new Date().toISOString(),
  } };
}

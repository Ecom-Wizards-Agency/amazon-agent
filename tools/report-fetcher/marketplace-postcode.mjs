/**
 * Amazon retail pages need a local delivery postcode before they tell the truth.
 *
 * Without one, an automated session lands on Amazon's default ship-to (it renders as
 * "Kazakhstan" on the EU stores) and every listing comes back the same way: no price,
 * no Add to Cart, and "No disponible / Currently unavailable" on products that are in
 * stock and selling. Search results are reordered too, so the client's own ASINs drop
 * out of the top page. On 12.08.2026 this made an entire competitor set and a client's
 * EUR 14k-a-day hero listing look dead, and it would have shipped as audit evidence.
 *
 * The fix is per-marketplace, so it belongs here rather than in any one workflow. Use a
 * big-city postcode: coverage is best there, so it is the least likely to introduce a
 * genuine delivery restriction of its own.
 *
 * Amazon also drops the postcode when a NEW tab loads without a reload, which looks
 * exactly like the bug this fixes. `ensureDeliveryPostcode()` therefore verifies after
 * setting, and reloads and retries when the ship-to line does not read back.
 *
 *   import { ensureDeliveryPostcode } from "./marketplace-postcode.mjs";
 *   await ensureDeliveryPostcode(session, "es");   // -> { ok: true, shipTo: "Madrid 28001" }
 *
 * Setting a ship-to is a browsing preference on our own debug profile. It changes
 * nothing on any Amazon account, and it never touches cookies or storage directly.
 */

// Big-city postcode per marketplace, keyed by the amazon.<tld> suffix.
export const MARKETPLACE_POSTCODES = {
  "es": "28001",          // Madrid
  "de": "10115",          // Berlin
  "fr": "75001",          // Paris
  "it": "00184",          // Rome
  "nl": "1012",           // Amsterdam
  "se": "11120",          // Stockholm
  "pl": "00-001",         // Warsaw
  "com.be": "1000",       // Brussels
  "ie": "D01",            // Dublin
  "co.uk": "SW1A 1AA",    // London
  "com": "10001",         // New York
  "ca": "M5H 2N2",        // Toronto
  "com.mx": "01000",      // Mexico City
  "com.br": "01310-100",  // Sao Paulo
  "com.au": "2000",       // Sydney
  "co.jp": "100-0001",    // Tokyo
  "in": "110001",         // New Delhi
  "ae": "00000",          // Dubai
  "sa": "11564",          // Riyadh
  "com.tr": "34010",      // Istanbul
  "sg": "018956",         // Singapore
};

/** Postcode for a marketplace, given a tld ("es") or a URL/host. */
export function postcodeFor(marketplace) {
  const key = String(marketplace || "").trim().toLowerCase()
    .replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/^amazon\./, "").replace(/\/.*$/, "");
  return MARKETPLACE_POSTCODES[key] || null;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const evaluate = async (session, expression) =>
  (await session.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result?.value;

const SHIP_TO = `(() => { const e = document.querySelector("#glow-ingress-line2");
  return e ? e.innerText.trim().replace(/\\s+/g, " ") : null; })()`;

// The glow widget is a plain jQuery popover, so a scripted click plus input/change
// events is enough. Real mouse dispatch is not needed and is slower.
const APPLY = (postcode) => `(() => {
  const link = document.querySelector("#nav-global-location-popover-link, #glow-ingress-line2");
  if (!link) return "no-glow";
  link.click();
  return "opened";
})()`;

const FILL = (postcode) => `(() => {
  const i = document.querySelector("#GLUXZipUpdateInput");
  if (!i) return "no-input";
  i.focus(); i.value = ${JSON.stringify(String(postcode))};
  i.dispatchEvent(new Event("input", { bubbles: true }));
  i.dispatchEvent(new Event("change", { bubbles: true }));
  const b = document.querySelector("#GLUXZipUpdate input[type=submit], #GLUXZipUpdate .a-button-input, span#GLUXZipUpdate input");
  if (!b) return "no-apply";
  b.click(); return "applied";
})()`;

const CONFIRM = `(() => {
  const d = document.querySelector('.a-popover-footer #GLUXConfirmClose, button[name="glowDoneButton"]');
  if (d) { d.click(); return "closed"; }
  return "no-confirm";
})()`;

/** True when the ship-to line names the postcode we asked for. */
function shipToMatches(shipTo, postcode) {
  if (!shipTo) return false;
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, "");
  if (norm(shipTo).includes(norm(postcode))) return true;
  // amazon.co.uk masks the inward code: "SW1A 1AA" renders as "London SW1A 1" plus a
  // zero-width joiner, so the full postcode never reads back. Accept the outward code
  // plus the first inward digit when the postcode has a two-part UK shape.
  const uk = String(postcode).trim().match(/^([a-z]{1,2}\d[a-z\d]?)\s*(\d)[a-z]{2}$/i);
  if (uk) return norm(shipTo).includes(norm(uk[1] + uk[2]));
  return false;
}

/**
 * Set (or confirm) the delivery postcode on the page this session is attached to.
 * Verifies, and reloads once per attempt because Amazon drops the ship-to on a fresh
 * tab that has not been reloaded. Returns {ok, shipTo, postcode, attempts}.
 */
export async function ensureDeliveryPostcode(session, marketplace, { postcode, attempts = 3, settleMs = 3000 } = {}) {
  const zip = postcode || postcodeFor(marketplace);
  if (!zip) return { ok: false, reason: `no postcode configured for "${marketplace}"`, postcode: null };
  await session.send("Runtime.enable").catch(() => {});
  await session.send("Page.enable").catch(() => {});

  for (let attempt = 1; attempt <= attempts; attempt++) {
    let shipTo = await evaluate(session, SHIP_TO);
    if (shipToMatches(shipTo, zip)) return { ok: true, shipTo, postcode: zip, attempts: attempt };

    // A cookie banner sits over the glow widget on a first EU visit. Decline the
    // non-essential cookies where the banner offers it, which is also the privacy default.
    await evaluate(session, `(() => { const r = document.querySelector("#sp-cc-rejectall-link"); if (r) r.click(); })()`);
    await sleep(1500);
    await evaluate(session, APPLY(zip));
    await sleep(3000);
    await evaluate(session, FILL(zip));
    await sleep(3500);
    await evaluate(session, CONFIRM);
    await sleep(settleMs);

    shipTo = await evaluate(session, SHIP_TO);
    if (shipToMatches(shipTo, zip)) return { ok: true, shipTo, postcode: zip, attempts: attempt };

    // Not applied, or applied and then reverted. A reload is what makes it stick.
    await session.send("Page.reload", { ignoreCache: false }).catch(() => {});
    await sleep(settleMs + 2000);
    shipTo = await evaluate(session, SHIP_TO);
    if (shipToMatches(shipTo, zip)) return { ok: true, shipTo, postcode: zip, attempts: attempt };
  }
  return { ok: false, reason: "postcode did not stick", shipTo: await evaluate(session, SHIP_TO), postcode: zip, attempts };
}

/**
 * Guard for a tab that should already carry the postcode. Amazon reverts the ship-to
 * on a new tab that has not been reloaded, so call this after every navigation whose
 * result you are about to read or screenshot.
 */
export async function assertDeliveryPostcode(session, marketplace, { postcode } = {}) {
  const zip = postcode || postcodeFor(marketplace);
  const shipTo = await evaluate(session, SHIP_TO);
  if (shipToMatches(shipTo, zip)) return { ok: true, shipTo, postcode: zip };
  return ensureDeliveryPostcode(session, marketplace, { postcode: zip });
}

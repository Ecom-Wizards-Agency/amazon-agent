// Capture current live Amazon listing copy + image URLs via the debug Chrome (CDP).
// Read-only: navigates to each PDP, extracts title/bullets/description/images/price/brand.
// Usage: node tools/listing-capture/capture-cdp.mjs <ASIN[,ASIN...]> <out.json> [tld=com] [lang=en_US]
import fs from "node:fs";
import { assertChrome, createPage, closePage, evaluate } from "../report-fetcher/cdp.mjs";

const asins = (process.argv[2] || "").split(",").map((s) => s.trim()).filter(Boolean);
const out = process.argv[3];
const tld = process.argv[4] || "com";
const lang = process.argv[5] || "en_US";
if (!asins.length || !out) { console.error("need <ASINs> <out.json>"); process.exit(1); }

// Extractor runs in the page: polls up to ~18s for the title, then reads the PDP.
const EXTRACTOR = (asin) => `(async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 90; i++) { if (document.querySelector('#productTitle')) break; await sleep(200); }
  const txt = (s) => { const e = document.querySelector(s); return e ? e.textContent.trim().replace(/\\s+/g,' ') : ''; };
  const title = txt('#productTitle');
  let bullets = [];
  for (const sel of ['#feature-bullets ul', '#productFactsDesktopExpander > div:first-child ul']) {
    const ul = document.querySelector(sel);
    if (ul) { bullets = [...ul.querySelectorAll('li')].map(li => li.textContent.trim().replace(/\\s+/g,' ')).filter(t => t && !/^\\s*$/.test(t)); if (bullets.length) break; }
  }
  const desc = txt('#productDescription') || txt('#bookDescription_feature_div');
  const hasAplus = !!document.querySelector('#aplus, #aplus_feature_div, #dpx-aplus-product-description_feature_div');
  const mainImg = (() => { const e = document.querySelector('#landingImage, #imgTagWrapperId img'); return e ? (e.getAttribute('data-old-hires') || e.src) : ''; })();
  const gallery = [...document.querySelectorAll('#altImages img')].map(i => i.src).filter(Boolean);
  const price = txt('#corePriceDisplay_desktop_feature_div .a-price .a-offscreen') || txt('.a-price .a-offscreen');
  const brand = txt('#bylineInfo');
  const rating = txt('#acrPopover .a-size-base') || txt('#acrPopover');
  const reviews = txt('#acrCustomerReviewText');
  return { asin: '${asin}', resolvedAsin: (location.pathname.match(/\\/dp\\/([A-Z0-9]{10})/)||[])[1] || '${asin}',
    title, bullets, description: desc, aplusPresent: hasAplus, mainImage: mainImg, galleryImages: gallery,
    price, brand, rating, reviews, url: location.href, status: (title||bullets.length)?'ok':'empty' };
})()`;

await assertChrome();
const listings = [];
for (const asin of asins) {
  const url = `https://www.amazon.${tld}/dp/${asin}?language=${lang}&th=1&psc=1`;
  let page;
  try {
    page = await createPage(url);
    // The tab keeps navigating/redirecting for a moment after it appears, which
    // destroys the eval context. Retry until a fresh context returns the title.
    let r = null;
    for (let attempt = 0; attempt < 8; attempt++) {
      await new Promise((res) => setTimeout(res, 1500));
      try {
        r = await evaluate(page.session, EXTRACTOR(asin), 30000);
        if (r && r.status === "ok") break;
      } catch (e) {
        if (!/destroyed|context|timed out/i.test(e.message)) throw e;
      }
    }
    if (!r) r = { asin, status: "error", error: "no context after retries" };
    console.error(`  ${asin}: ${r.status} | "${(r.title||'').slice(0,60)}" | ${(r.bullets||[]).length} bullets | ${(r.galleryImages||[]).length} imgs${r.resolvedAsin&&r.resolvedAsin!==asin?` (-> ${r.resolvedAsin})`:''}`);
    listings.push(r);
  } catch (e) {
    console.error(`  ${asin}: ERROR ${e.message}`);
    listings.push({ asin, status: "error", error: e.message });
  } finally {
    if (page) await closePage(page.targetId);
  }
}
fs.mkdirSync(out.replace(/\/[^/]+$/, ""), { recursive: true });
fs.writeFileSync(out, JSON.stringify({ schemaVersion: "amazon-agent.listing-reference.v1", capturedAt: new Date().toISOString().slice(0,10), marketplace: tld, listings }, null, 2));
console.error(`\nwrote ${out} (${listings.length} listings)`);

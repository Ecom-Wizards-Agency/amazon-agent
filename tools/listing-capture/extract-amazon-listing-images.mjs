#!/usr/bin/env node
// Capture the LIVE image set of an Amazon PDP (main + secondary gallery, hi-res URLs),
// plus whether A+ content is present and how many modules it has.
//
// Why this exists: extract-amazon-listing-copy.js captures title/bullets only, so an
// image-concept review had no source of truth for what is actually live. Read-only.
//
// Usage:
//   node tools/listing-capture/extract-amazon-listing-images.mjs <ASIN> [--marketplace com] [--out <file.json>]
//
// Runs against the dedicated debug Chrome over CDP (port 9222), same profile as the
// report fetcher, so it uses the operator's existing session. It opens its own tab and
// closes it again.
import { ensureChrome, createPage, closePage, evaluate } from '../report-fetcher/cdp.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const args = process.argv.slice(2);
const asin = args.find(a => /^B0[A-Z0-9]{8}$/i.test(a));
const flag = (n, d) => { const i = args.indexOf(`--${n}`); return i >= 0 ? args[i + 1] : d; };
if (!asin) {
  console.error('usage: extract-amazon-listing-images.mjs <ASIN> [--marketplace com] [--out file.json]');
  process.exit(1);
}
const market = flag('marketplace', 'com');
const out = flag('out', null);
const url = `https://www.amazon.${market}/dp/${asin}?th=1&psc=1`;

// Read the page's own image-block data. colorImages is what the gallery renders from,
// so it carries the real ordered sequence including hiRes variants.
const EXPR = `(() => {
  const res = { asin: ${JSON.stringify(asin)}, url: location.href, title: null,
                images: [], aplus: { present: false, modules: 0, images: 0 },
                price: null, rating: null, reviewCount: null, videoCount: 0 };
  const t = document.querySelector('#productTitle'); if (t) res.title = t.textContent.trim();
  const pr = document.querySelector('.a-price .a-offscreen'); if (pr) res.price = pr.textContent.trim();
  const ra = document.querySelector('#acrPopover'); if (ra) res.rating = (ra.getAttribute('title') || '').trim();
  const rc = document.querySelector('#acrCustomerReviewText'); if (rc) res.reviewCount = rc.textContent.trim();

  // 1) preferred: the ImageBlock's own data
  let got = false;
  try {
    const m = Array.from(document.querySelectorAll('script'))
      .map(s => s.textContent || '')
      .find(x => x.includes('colorImages') && x.includes('initial'));
    if (m) {
      const j = m.slice(m.indexOf('colorImages'));
      const start = j.indexOf('[');
      let depth = 0, end = -1;
      for (let i = start; i < j.length; i++) {
        if (j[i] === '[') depth++;
        else if (j[i] === ']') { depth--; if (depth === 0) { end = i + 1; break; } }
      }
      if (end > start) {
        const arr = JSON.parse(j.slice(start, end).replace(/'/g, '"'));
        arr.forEach((im, i) => res.images.push({
          pos: i + 1, hiRes: im.hiRes || null, large: im.large || null,
          variant: im.variant || null
        }));
        got = arr.length > 0;
      }
    }
  } catch (e) { res.imageParseError = String(e); }

  // 2) fallback: the visible thumbnail rail, in DOM (display) order
  if (!got) {
    const seen = new Set();
    document.querySelectorAll('#altImages li.item img, #imageBlock img').forEach(img => {
      const s = img.getAttribute('src') || '';
      const base = s.replace(/\\._[^.]+_\\./, '.');
      if (base && !seen.has(base)) { seen.add(base); res.images.push({ pos: res.images.length + 1, large: base, variant: null }); }
    });
  }
  res.videoCount = document.querySelectorAll('#altImages .videoBlockIngress, #altImages li.videoThumbnail').length;

  const ap = document.querySelector('#aplus, #aplus_feature_div, #aplusBrandStory_feature_div');
  if (ap) {
    res.aplus.present = true;
    res.aplus.modules = ap.querySelectorAll('.aplus-module').length;
    res.aplus.images = ap.querySelectorAll('img').length;
  }
  return res;
})()`;

await ensureChrome();
// createPage returns an already-open Session, not a ws URL.
const { targetId, session: s } = await createPage(url);
try {
  await s.send('Runtime.enable', {});
  // let the image block hydrate
  await new Promise(r => setTimeout(r, 6000));
  const data = await evaluate(s, EXPR, 60000);
  if (!data || !data.title) {
    console.error('WARN: no product title found. A login wall or captcha may be showing. Check the tab.');
  }
  const json = JSON.stringify(data, null, 2);
  if (out) { mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, json); console.log(`wrote ${out}`); }
  console.log(`ASIN ${data.asin} · images ${data.images.length} · video thumbs ${data.videoCount} · A+ ${data.aplus.present ? `yes (${data.aplus.modules} modules, ${data.aplus.images} imgs)` : 'no'}`);
  console.log(`title: ${(data.title || '').slice(0, 90)}`);
  console.log(`price: ${data.price} · rating: ${data.rating} · reviews: ${data.reviewCount}`);
  if (!out) console.log(json);
} finally {
  try { s.close(); } catch (_) {}
  await closePage(targetId);
}

import fs from "node:fs";
import { ensureChrome, createPage, closePage, evaluate } from "../report-fetcher/cdp.mjs";
import { classifyPdp } from "./lib.mjs";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const LOCATION_TEXT = `(() => {
  const el = document.querySelector('#glow-ingress-line2, #nav-global-location-data-modal-action, #glow-ingress-block');
  return (el ? el.textContent : '').replace(/\\s+/g, ' ').trim();
})()`;

const OPEN_LOCATION = `(() => {
  const el = document.querySelector('#nav-global-location-popover-link, #nav-global-location-data-modal-action');
  if (!el) return { ok: false, reason: 'location control missing' };
  el.click();
  return { ok: true };
})()`;

const SET_LOCATION = (postalCode) => `(() => {
  const inputs = [...document.querySelectorAll('#GLUXZipUpdateInput, #GLUXZipUpdateInput_0, #GLUXZipUpdateInput_1, input[data-action="GLUXPostalInputAction"]')];
  if (!inputs.length) return { ok: false, reason: 'postal input missing' };
  const compact = ${JSON.stringify(postalCode)}.toUpperCase().replace(/[^A-Z0-9]/g, '');
  const values = inputs.length >= 2 ? [compact.slice(0, 3), compact.slice(3)] : [compact];
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  inputs.forEach((input, index) => {
    setter.call(input, values[index] || values[0]);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
  const button = document.querySelector('#GLUXZipUpdate input, input[aria-labelledby="GLUXZipUpdate-announce"], #GLUXZipUpdate');
  if (!button) return { ok: false, reason: 'postal apply button missing' };
  button.click();
  return { ok: true };
})()`;

const CLOSE_LOCATION = `(() => {
  const button = document.querySelector('#GLUXConfirmClose, input[aria-labelledby="GLUXConfirmClose-announce"]');
  if (button) button.click();
  return Boolean(button);
})()`;

const LOCATION_SUCCESS_TEXT = `(() => {
  const el = document.querySelector('#GLUXHiddenSuccessSelectedAddressPlaceholder, #GLUXZipConfirmationValue');
  return (el ? el.textContent : '').replace(/\\s+/g, ' ').trim();
})()`;

const PDP_EXTRACTOR = (requestedAsin) => `(async () => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  for (let i = 0; i < 50; i++) {
    const text = (document.body && document.body.innerText || '').slice(0, 5000);
    if (document.querySelector('#productTitle') || /Robot Check|characters you see|couldn't find that page/i.test(text)) break;
    await sleep(300);
  }
  const text = (selector) => {
    const el = document.querySelector(selector);
    return el ? (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim() : '';
  };
  const body = (document.body && document.body.innerText || '').slice(0, 12000);
  const blocked = /Robot Check|Enter the characters you see|Sorry, we just need to make sure you're not a robot/i.test(document.title + ' ' + body)
    || Boolean(document.querySelector('form[action*="validateCaptcha"], #captchacharacters'));
  const notFound = /Sorry! We couldn't find that page|Looking for something\?/i.test(document.title + ' ' + body)
    || Boolean(document.querySelector('#g img[alt*="Dog"], img[src*="error-dog"]'));
  const resolved = (location.pathname.match(/\\/(?:dp|gp\\/product)\\/([A-Z0-9]{10})/i) || [])[1] || '';
  const seller = text('#sellerProfileTriggerId')
    || text('#merchant-info a')
    || text('#tabular-buybox .tabular-buybox-text[tabindex="0"]');
  const buyboxRows = [...document.querySelectorAll('#tabular-buybox .tabular-buybox-text')]
    .map((el) => (el.textContent || '').replace(/\\s+/g, ' ').trim()).filter(Boolean);
  return {
    requestedAsin: ${JSON.stringify(requestedAsin)},
    resolvedAsin: resolved.toUpperCase(),
    title: text('#productTitle'),
    brand: text('#bylineInfo'),
    availability: text('#availability') || text('#outOfStock'),
    seller,
    shipsFrom: buyboxRows[0] || text('#fulfillerInfoFeature_feature_div'),
    price: text('#corePriceDisplay_desktop_feature_div .a-price .a-offscreen') || text('.a-price .a-offscreen'),
    rating: text('#acrPopover .a-size-base') || text('#acrPopover'),
    reviews: text('#acrCustomerReviewText'),
    mainImage: (() => { const el = document.querySelector('#landingImage, #imgTagWrapperId img'); return el ? (el.getAttribute('data-old-hires') || el.src || '') : ''; })(),
    url: location.href,
    pageTitle: document.title,
    blocked,
    notFound,
    reason: blocked ? 'Amazon robot or CAPTCHA page' : (notFound ? 'Amazon not-found page' : ''),
    capturedAt: new Date().toISOString(),
  };
})()`;

const SEARCH_EXTRACTOR = (query) => `(async () => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  for (let i = 0; i < 40; i++) {
    if (document.querySelector('[data-component-type="s-search-result"], #search') || /Robot Check/i.test(document.title)) break;
    await sleep(250);
  }
  const body = (document.body && document.body.innerText || '').slice(0, 6000);
  const blocked = /Robot Check|Enter the characters you see|make sure you're not a robot/i.test(document.title + ' ' + body)
    || Boolean(document.querySelector('form[action*="validateCaptcha"], #captchacharacters'));
  const cards = [...document.querySelectorAll('[data-component-type="s-search-result"][data-asin]')].map((card) => {
    const asin = (card.getAttribute('data-asin') || '').toUpperCase();
    const titleEl = card.querySelector('h2 span, h2 a span');
    const linkEl = card.querySelector('h2 a[href], a.a-link-normal.s-no-outline[href]');
    const priceEl = card.querySelector('.a-price .a-offscreen');
    const imageEl = card.querySelector('img.s-image');
    const cardText = (card.innerText || '').replace(/\\s+/g, ' ').trim();
    return {
      asin,
      title: titleEl ? (titleEl.textContent || '').replace(/\\s+/g, ' ').trim() : '',
      price: priceEl ? (priceEl.textContent || '').trim() : '',
      image: imageEl ? (imageEl.src || '') : '',
      url: linkEl ? new URL(linkEl.href, location.origin).href : '',
      sponsored: /Sponsored|Commandité/i.test(cardText),
      query: ${JSON.stringify(query)},
    };
  }).filter((card) => /^[A-Z0-9]{10}$/.test(card.asin));
  return { blocked, cards, url: location.href, pageTitle: document.title };
})()`;

async function freshPageEvaluation(url, expression, timeoutMs = 30000) {
  const page = await createPage(url);
  try {
    let lastError;
    for (let attempt = 0; attempt < 5; attempt++) {
      await sleep(attempt ? 1000 : 1800);
      try { return await evaluate(page.session, expression, timeoutMs); }
      catch (error) {
        lastError = error;
        if (!/destroyed|context|timed out|Cannot find context/i.test(error.message)) throw error;
      }
    }
    throw lastError || new Error("Page evaluation failed");
  } finally {
    await closePage(page.targetId);
  }
}

export async function browserDoctor() {
  const version = await ensureChrome();
  return { browser: version.Browser || "", protocolVersion: version["Protocol-Version"] || "", webSocket: Boolean(version.webSocketDebuggerUrl) };
}

export async function verifyDeliveryLocation(marketplace, settings, probeAsin = "") {
  await ensureChrome();
  const route = probeAsin ? `/dp/${probeAsin}` : "/";
  const url = `https://www.amazon.${marketplace}${route}?language=${encodeURIComponent(settings.language || "en_US")}`;
  const page = await createPage(url);
  try {
    await sleep(3500);
    let label = await evaluate(page.session, LOCATION_TEXT, 10000);
    const normalized = (value) => String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    const verified = () => settings.verifyTokens.some((token) => normalized(label).includes(normalized(token)));
    if (!verified()) {
      const opened = await evaluate(page.session, OPEN_LOCATION, 10000);
      if (!opened?.ok) return { ok: false, label, reason: opened?.reason || "location control failed" };
      let setResult = { ok: false, reason: "postal input missing" };
      for (let attempt = 0; attempt < 15 && !setResult.ok; attempt++) {
        await sleep(500);
        if (attempt === 7) await evaluate(page.session, OPEN_LOCATION, 10000);
        try { setResult = await evaluate(page.session, SET_LOCATION(settings.postalCode), 10000); }
        catch (error) {
          if (!/destroyed|context|closed/i.test(error.message)) throw error;
          setResult = { ok: true, navigated: true };
        }
      }
      if (!setResult?.ok) return { ok: false, label, reason: setResult?.reason || "location update failed" };
      await sleep(4000);
      for (let attempt = 0; attempt < 6; attempt++) {
        await sleep(1000);
        try {
          label = await evaluate(page.session, LOCATION_TEXT, 10000);
          if (verified()) break;
          const success = await evaluate(page.session, LOCATION_SUCCESS_TEXT, 10000);
          if (settings.verifyTokens.some((token) => normalized(success).includes(normalized(token)))) {
            await evaluate(page.session, CLOSE_LOCATION, 10000);
          }
        } catch (error) {
          if (!/destroyed|context|closed/i.test(error.message)) throw error;
        }
      }
      if (verified()) {
        try { await evaluate(page.session, CLOSE_LOCATION, 10000); } catch { /* modal may already be gone */ }
      }
    }
    return { ok: verified(), label, reason: verified() ? "" : `Expected one of: ${settings.verifyTokens.join(", ")}` };
  } catch (error) {
    return { ok: false, label: "", reason: error.message };
  } finally {
    await closePage(page.targetId);
  }
}

export async function capturePdp(marketplace, asin, language = "en_US") {
  await ensureChrome();
  const url = `https://www.amazon.${marketplace}/dp/${asin}?language=${encodeURIComponent(language)}&th=1&psc=1`;
  try {
    const raw = await freshPageEvaluation(url, PDP_EXTRACTOR(asin), 30000);
    return { marketplace, ...classifyPdp(raw, asin) };
  } catch (error) {
    return { marketplace, asin, resolvedAsin: asin, status: "error", reason: error.message, url, capturedAt: new Date().toISOString() };
  }
}

export async function searchAmazon(marketplace, query, pages = 1, language = "en_US") {
  await ensureChrome();
  const cards = [];
  for (let pageNumber = 1; pageNumber <= pages; pageNumber++) {
    const url = `https://www.amazon.${marketplace}/s?k=${encodeURIComponent(query)}&page=${pageNumber}&language=${encodeURIComponent(language)}`;
    try {
      const result = await freshPageEvaluation(url, SEARCH_EXTRACTOR(query), 30000);
      if (result?.blocked) return { status: "blocked", cards, reason: `Search blocked on page ${pageNumber}` };
      cards.push(...(result?.cards || []));
    } catch (error) {
      return { status: "error", cards, reason: error.message };
    }
  }
  return { status: "ok", cards };
}

export async function exactAsinSearch(marketplace, asin, language = "en_US") {
  const result = await searchAmazon(marketplace, asin, 1, language);
  return { ...result, found: result.cards.some((card) => card.asin === asin) };
}

export async function captureScreenshot(url, outputPath) {
  await ensureChrome();
  const page = await createPage(url);
  try {
    await sleep(3000);
    await page.session.send("Page.enable");
    const shot = await page.session.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    fs.writeFileSync(outputPath, Buffer.from(shot.data, "base64"));
    return outputPath;
  } finally {
    await closePage(page.targetId);
  }
}

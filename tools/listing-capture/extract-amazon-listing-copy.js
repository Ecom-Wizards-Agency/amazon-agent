/*
 * Browser-side Amazon listing-copy extractor.
 *
 * Deterministic replacement for a legacy browser workflow, without the
 * ChatGPT formatting steps. Captures
 * the title + bullet points + canonical link for the listing on the current
 * Amazon product page.
 *
 * The whole extractor is ONE self-contained function (helpers nested) so it can
 * be passed directly to a connected-browser evaluate call — no <script>
 * injection / eval / window assignment required.
 *
 * Execution paths (connected/internal browser only — never headless; Amazon
 * blocks bots; never inspect cookies/storage/credentials/tokens):
 *   A) Codex / Playwright:  await tab.playwright.evaluate(extractAmazonListingCopy, "<requestedAsin>")
 *   B) DevTools / injected:  window.amazonAgentExtractListingCopy("<requestedAsin>")
 *
 * Navigate in the LOCAL language first. For amazon.it use the locale path
 * https://www.amazon.it/-/it/dp/<ASIN> (plain /dp/ can render the EN UI);
 * verify the returned title/bullets are local-language, else retry the locale path.
 *
 * Returns: { asin, resolvedAsin, title, bullets[], link, capturedAt, status }.
 *  - asin        = the REQUESTED ASIN (what the builder keys on) when provided,
 *                  else the ASIN parsed from the (possibly redirected) URL.
 *  - resolvedAsin = the ASIN the page actually resolved to (variation parent),
 *                  so requested vs resolved is never silently lost.
 */

function extractAmazonListingCopy(requestedAsin) {
  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim()
  }

  function parseAsin() {
    const patterns = [/\/dp\/([A-Z0-9]{10})/i, /\/gp\/product\/([A-Z0-9]{10})/i, /\/product\/([A-Z0-9]{10})/i]
    for (const re of patterns) {
      const m = location.pathname.match(re) || location.href.match(re)
      if (m) return m[1].toUpperCase()
    }
    const el = document.querySelector("[data-asin]")
    const a = el && el.getAttribute("data-asin")
    return a && /^[A-Z0-9]{10}$/i.test(a) ? a.toUpperCase() : ""
  }

  function marketplaceTld() {
    const m = location.hostname.match(/amazon\.([a-z.]+)$/i)
    return m ? m[1] : "com"
  }

  function getTitle() {
    const el = document.querySelector("#productTitle")
    return cleanText(el && el.textContent)
  }

  // Bullets in the spec's order: primary #feature-bullets, then the
  // product-facts fallback (the selector test showed the primary is often empty).
  function getBullets() {
    const selectors = ["#feature-bullets ul", "#productFactsDesktopExpander > div:first-child ul"]
    for (const selector of selectors) {
      const ul = document.querySelector(selector)
      if (!ul) continue
      const items = Array.from(ul.querySelectorAll("li"))
        .map(function (li) { return cleanText(li.textContent) })
        .filter(function (t) { return t && !/^see more|^vedi|^mostra/i.test(t) })
      if (items.length) return items
    }
    return []
  }

  var resolvedAsin = parseAsin()
  var asin = String(requestedAsin || resolvedAsin || "").toUpperCase()
  var title = getTitle()
  var bullets = getBullets()
  var status = title || bullets.length ? "ok" : "empty"
  return {
    asin: asin,
    resolvedAsin: resolvedAsin,
    title: title,
    bullets: bullets,
    // Clean canonical link keyed on the REQUESTED asin (stable input for re-runs).
    link: asin ? "https://www.amazon." + marketplaceTld() + "/dp/" + asin : cleanText(location.href),
    capturedAt: new Date().toISOString(),
    status: status,
  }
}

// Injected-execution convenience (path B). Wrapped in try/catch so a read-only /
// non-extensible `window` (some Playwright evaluate contexts) does not throw —
// confirmed: without this, pasting the whole file into evaluate fails on the
// assignment. The string-evaluate path (A) below is the proven runner.
try {
  if (typeof window !== "undefined") {
    window.amazonAgentExtractListingCopy = extractAmazonListingCopy
  }
} catch (e) {
  /* window non-extensible — ignore; call extractAmazonListingCopy(...) directly */
}

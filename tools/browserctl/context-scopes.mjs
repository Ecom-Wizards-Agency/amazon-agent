/** Seller Central coordination groups. Selection is shared within each group. */
const REGIONS = new Map([
  ...["us", "ca", "mx"].map((code) => [code, "sc:na"]),
  ...["de", "fr", "it", "es", "nl", "se", "pl", "be", "ie", "uk", "gb"].map((code) => [code, "sc:eu"]),
  ["au", "sc:au"],
]);
const HOSTS = new Map(Object.entries({
  "sellercentral.amazon.com": "us", "sellercentral.amazon.ca": "ca",
  "sellercentral.amazon.com.mx": "mx", "sellercentral.amazon.de": "de",
  "sellercentral.amazon.fr": "fr", "sellercentral.amazon.it": "it",
  "sellercentral.amazon.es": "es", "sellercentral.amazon.nl": "nl",
  "sellercentral.amazon.se": "se", "sellercentral.amazon.pl": "pl",
  "sellercentral.amazon.com.be": "be", "sellercentral.amazon.ie": "ie",
  "sellercentral.amazon.co.uk": "uk", "sellercentral.amazon.com.au": "au",
  // These supported marketplaces have no independently authorized group yet.
  "sellercentral.amazon.com.br": "br", "sellercentral.amazon.com.tr": "tr",
  "sellercentral.amazon.co.jp": "jp", "sellercentral.amazon.sg": "sg",
  "sellercentral.amazon.in": "in", "sellercentral.amazon.ae": "ae",
  "sellercentral.amazon.sa": "sa", "sellercentral.amazon.eg": "eg",
  "sellercentral.amazon.co.za": "za",
}));

function invalid(message) {
  return Object.assign(new Error(`TASK_TAB_CONTEXT_INVALID: ${message}`), { code: "TASK_TAB_CONTEXT_INVALID" });
}
function mismatch(message) {
  return Object.assign(new Error(`TASK_TAB_CONTEXT_MISMATCH: ${message}`), { code: "TASK_TAB_CONTEXT_MISMATCH" });
}
function parseUrl(value) {
  if (typeof value !== "string" || !value.trim()) throw invalid("origin must be an absolute URL");
  try { return new URL(value); } catch { throw invalid("origin must be an absolute URL"); }
}

export function isRegionalScope(scope) {
  return scope === "sc:na" || scope === "sc:eu" || scope === "sc:au";
}

/** Return null for non-Seller-Central URLs, including authentication pages. */
export function scopeForOrigin(value) {
  const url = parseUrl(value);
  const marketplace = HOSTS.get(url.hostname);
  if (!marketplace) return null;
  if (url.protocol !== "https:" || url.port || url.username || url.password) {
    throw invalid("Seller Central origins must use HTTPS without credentials or a custom port");
  }
  return REGIONS.get(marketplace) || "global";
}

/** Resolve one operation's routing facts; unknown marketplace groups stay global. */
export function sellerCentralScope(descriptor = {}) {
  if (!descriptor || typeof descriptor !== "object" || Array.isArray(descriptor)
      || Object.keys(descriptor).some((key) => key !== "marketplace" && key !== "origin")) {
    throw invalid("sellerCentral must contain marketplace and/or origin");
  }
  let marketScope = null;
  let originScope = null;
  if (descriptor.marketplace != null) {
    if (typeof descriptor.marketplace !== "string" || !/^[a-z]{2}$/i.test(descriptor.marketplace.trim())) {
      throw invalid("marketplace must be a two-letter country code");
    }
    marketScope = REGIONS.get(descriptor.marketplace.trim().toLowerCase()) || "global";
  }
  if (descriptor.origin != null) {
    originScope = scopeForOrigin(descriptor.origin);
    if (!originScope) throw invalid("origin is not a supported Seller Central origin");
  }
  if (!marketScope && !originScope) throw invalid("sellerCentral requires marketplace and/or origin");
  if (isRegionalScope(marketScope) && isRegionalScope(originScope) && marketScope !== originScope) {
    throw mismatch(`marketplace requires ${marketScope}, but origin requires ${originScope}`);
  }
  if (marketScope === "global" || originScope === "global") return "global";
  return marketScope || originScope;
}

export function resolveContextScope({ exclusiveContext = false, sellerCentral } = {}) {
  if (sellerCentral !== undefined && !exclusiveContext) {
    throw invalid("Seller Central coordination requires exclusiveContext: true");
  }
  return exclusiveContext ? (sellerCentral === undefined ? "global" : sellerCentralScope(sellerCentral)) : null;
}

/** A global claim covers valid descriptors; a regional claim never expands itself. */
export function assertContextCovers(scope, descriptor) {
  const required = sellerCentralScope(descriptor);
  if (scope !== "global" && scope !== required) {
    throw mismatch(`held context ${scope || "none"} does not cover ${required}`);
  }
  return required;
}

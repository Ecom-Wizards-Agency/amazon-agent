const FAILURE_STATUSES = new Set(["blocked", "error"]);
const VERIFIED_STATUSES = new Set(["live", "unavailable", "removed", "redirected"]);
const LIFECYCLES = new Set(["candidate", "reported", "dismissed", "authorized"]);

export const STATE_SCHEMA = "amazon-agent.brand-surveillance-state.v1";
export const CONFIG_SCHEMA = "amazon-agent.brand-surveillance-config.v1";

export function normalizeAsin(value) {
  const asin = String(value || "").trim().toUpperCase();
  if (!/^[A-Z0-9]{10}$/.test(asin)) throw new Error(`Invalid ASIN: ${value}`);
  return asin;
}

export function normalizeMarketplace(value) {
  const raw = String(value || "").trim().toLowerCase().replace(/^amazon\./, "");
  if (!/^[a-z.]+$/.test(raw)) throw new Error(`Invalid Amazon marketplace: ${value}`);
  return raw;
}

export function entityKey(marketplace, asin) {
  return `${normalizeMarketplace(marketplace)}|${normalizeAsin(asin)}`;
}

export function parseAmazonTarget(value, fallbackMarketplace = "") {
  const input = String(value || "").trim();
  const urlMatch = input.match(/https?:\/\/(?:www\.)?amazon\.([a-z.]+)\/(?:[^?#]*?\/)?(?:dp|gp\/product)\/([A-Z0-9]{10})/i);
  if (urlMatch) {
    return { marketplace: normalizeMarketplace(urlMatch[1]), asin: normalizeAsin(urlMatch[2]) };
  }
  if (!fallbackMarketplace) throw new Error("A marketplace is required when adding a bare ASIN");
  return { marketplace: normalizeMarketplace(fallbackMarketplace), asin: normalizeAsin(input) };
}

function clean(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function normalizedWords(value) {
  const stop = new Set(["a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the", "to", "with"]);
  return clean(value).toLowerCase().replace(/[^a-z0-9]+/g, " ").split(" ")
    .filter((word) => word.length > 1 && !stop.has(word));
}

export function classifyPdp(raw, requestedAsin) {
  const asin = normalizeAsin(requestedAsin);
  const resolvedAsin = /^[A-Z0-9]{10}$/i.test(String(raw?.resolvedAsin || ""))
    ? String(raw.resolvedAsin).toUpperCase() : asin;
  const base = {
    asin,
    resolvedAsin,
    title: clean(raw?.title),
    brand: clean(raw?.brand),
    availability: clean(raw?.availability),
    seller: clean(raw?.seller),
    shipsFrom: clean(raw?.shipsFrom),
    price: clean(raw?.price),
    rating: clean(raw?.rating),
    reviews: clean(raw?.reviews),
    mainImage: clean(raw?.mainImage),
    url: clean(raw?.url),
    pageTitle: clean(raw?.pageTitle),
    capturedAt: clean(raw?.capturedAt) || new Date().toISOString(),
  };
  if (raw?.blocked) return { ...base, status: "blocked", reason: clean(raw.reason) || "Amazon robot or CAPTCHA page" };
  if (raw?.error) return { ...base, status: "error", reason: clean(raw.error) };
  if (raw?.notFound) return { ...base, status: "removed", reason: clean(raw.reason) || "Amazon not-found page" };
  if (!base.title) return { ...base, status: "error", reason: "PDP returned no product title" };
  if (resolvedAsin !== asin) return { ...base, status: "redirected" };
  const unavailable = /currently unavailable|temporarily out of stock|not available|indisponible|non disponible/i.test(base.availability);
  if (unavailable && !base.seller && !base.price) return { ...base, status: "unavailable" };
  return { ...base, status: "live" };
}

export function deriveSearchQueries(configuredQueries, snapshots, maxWords = 8) {
  const queries = new Set((configuredQueries || []).map(clean).filter(Boolean));
  for (const snapshot of snapshots || []) {
    if (!snapshot?.title || FAILURE_STATUSES.has(snapshot.status)) continue;
    const words = normalizedWords(snapshot.title).slice(0, maxWords);
    if (words.length >= 3) queries.add(words.join(" "));
  }
  return [...queries];
}

function similarity(a, b) {
  const left = new Set(normalizedWords(a));
  const right = new Set(normalizedWords(b));
  if (!left.size || !right.size) return 0;
  let overlap = 0;
  for (const word of left) if (right.has(word)) overlap += 1;
  return overlap / new Set([...left, ...right]).size;
}

export function findSuspectedCandidates(cards, { marketplace, brandTokens = [], trackedTitles = [], minimumSimilarity = 0.55 } = {}) {
  const found = new Map();
  for (const card of cards || []) {
    let asin;
    try { asin = normalizeAsin(card.asin); } catch { continue; }
    const title = clean(card.title);
    if (!title) continue;
    const lower = ` ${title.toLowerCase().replace(/[^a-z0-9]+/g, " ")} `;
    const brandMatch = brandTokens.some((token) => lower.includes(` ${String(token).toLowerCase()} `));
    const titleSimilarity = Math.max(0, ...trackedTitles.map((tracked) => similarity(title, tracked)));
    if (titleSimilarity < minimumSimilarity) continue;
    const key = entityKey(marketplace, asin);
    if (!found.has(key)) {
      found.set(key, {
        marketplace: normalizeMarketplace(marketplace), asin, title,
        price: clean(card.price), image: clean(card.image), url: clean(card.url),
        sponsored: Boolean(card.sponsored), query: clean(card.query),
        matchReason: brandMatch ? "brand-and-title" : "title-similarity",
        similarity: Number(titleSimilarity.toFixed(3)),
      });
    }
  }
  return [...found.values()];
}

export function validateConfig(config) {
  if (config?.schemaVersion !== CONFIG_SCHEMA) throw new Error(`Unsupported config schema: ${config?.schemaVersion}`);
  if (!Array.isArray(config.entities) || !config.entities.length) throw new Error("Config needs at least one tracked entity");
  for (const entity of config.entities) {
    normalizeMarketplace(entity.marketplace);
    normalizeAsin(entity.asin);
    if (!LIFECYCLES.has(entity.lifecycle)) throw new Error(`Invalid lifecycle for ${entity.asin}: ${entity.lifecycle}`);
  }
  for (const [marketplace, settings] of Object.entries(config.marketplaces || {})) {
    normalizeMarketplace(marketplace);
    if (!settings.postalCode || !Array.isArray(settings.verifyTokens) || !settings.verifyTokens.length) {
      throw new Error(`Marketplace ${marketplace} needs postalCode and verifyTokens`);
    }
  }
  return config;
}

function emptyState(now) {
  return {
    schemaVersion: STATE_SCHEMA,
    initializedAt: now,
    lastRunAt: null,
    lastSuccessfulRunAt: null,
    entities: {},
    candidates: {},
  };
}

function event(type, current, previous = null, extra = {}) {
  return {
    type,
    marketplace: current?.marketplace || previous?.marketplace || "",
    asin: current?.asin || previous?.asin || "",
    url: current?.url || previous?.url || "",
    before: previous,
    after: current,
    ...extra,
  };
}

export function applyRun(previousState, run, config) {
  const now = run.finishedAt || new Date().toISOString();
  const state = previousState?.schemaVersion === STATE_SCHEMA
    ? structuredClone(previousState) : emptyState(run.startedAt || now);
  const baseline = !state.lastSuccessfulRunAt;
  const events = [];
  const configured = new Map(config.entities.map((item) => [entityKey(item.marketplace, item.asin), item]));
  const snapshots = new Map((run.snapshots || []).map((item) => [entityKey(item.marketplace, item.asin), item]));

  for (const [key, settings] of configured) {
    if (state.candidates[key]) state.candidates[key].lifecycle = settings.lifecycle;
  }

  let missedRunGapHours = 0;
  if (state.lastRunAt) {
    missedRunGapHours = (new Date(run.startedAt).getTime() - new Date(state.lastRunAt).getTime()) / 3600000;
    if (!Number.isFinite(missedRunGapHours) || missedRunGapHours < 36) missedRunGapHours = 0;
  }

  for (const [key, settings] of configured) {
    const current = snapshots.get(key);
    const existing = state.entities[key] || {
      marketplace: normalizeMarketplace(settings.marketplace),
      asin: normalizeAsin(settings.asin),
      firstSeen: run.startedAt,
      lastSeen: null,
      lastVerified: null,
      lastAttempt: null,
    };
    existing.lifecycle = settings.lifecycle;
    if (!current) {
      state.entities[key] = existing;
      continue;
    }
    current.marketplace = normalizeMarketplace(settings.marketplace);
    current.asin = normalizeAsin(settings.asin);
    existing.lastAttempt = current;
    const previous = existing.lastVerified;
    if (!FAILURE_STATUSES.has(current.status) && VERIFIED_STATUSES.has(current.status)) {
      existing.lastVerified = current;
      existing.lastSeen = run.finishedAt;
      if (!baseline && previous) {
        if (current.status === "removed" && previous.status !== "removed") {
          events.push(event("takedown_confirmed", current, previous));
        } else if (previous.status === "removed" && current.status !== "removed") {
          events.push(event("reappeared", current, previous));
        }
        if (current.status === "redirected" && current.resolvedAsin !== previous.resolvedAsin) {
          events.push(event("redirect_changed", current, previous));
        }
        const sellerChanged = ["live", "redirected"].includes(current.status)
          && ["live", "redirected"].includes(previous.status)
          && current.seller && previous.seller && current.seller !== previous.seller;
        const fulfillerChanged = ["live", "redirected"].includes(current.status)
          && ["live", "redirected"].includes(previous.status)
          && current.shipsFrom && previous.shipsFrom && current.shipsFrom !== previous.shipsFrom;
        if (sellerChanged || fulfillerChanged) {
          events.push(event("seller_or_fulfiller_changed", current, previous));
        }
      }
    }
    state.entities[key] = existing;
  }

  for (const discovery of run.discoveries || []) {
    const key = entityKey(discovery.marketplace, discovery.asin);
    const configuredEntity = configured.get(key);
    if (configuredEntity?.lifecycle === "dismissed" || configuredEntity?.lifecycle === "authorized") continue;
    if (configuredEntity) continue;
    const existing = state.candidates[key];
    state.candidates[key] = {
      ...(existing || {}), ...discovery,
      lifecycle: existing?.lifecycle || "candidate",
      firstSeen: existing?.firstSeen || run.startedAt,
      lastSeen: run.finishedAt,
    };
    if (!baseline && !existing) events.push(event("new_suspected_asin", discovery));
  }

  for (const failure of run.failures || []) {
    events.push({ type: "run_failure", ...failure });
  }

  state.lastRunAt = run.finishedAt;
  if (!(run.failures || []).length) state.lastSuccessfulRunAt = run.finishedAt;
  return {
    state,
    events,
    baseline,
    missedRunGapHours: missedRunGapHours ? Number(missedRunGapHours.toFixed(1)) : 0,
    clean: events.length === 0,
  };
}

export function isFailureStatus(status) {
  return FAILURE_STATUSES.has(status);
}

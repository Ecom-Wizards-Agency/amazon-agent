#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const argv = process.argv.slice(2);
const opt = (name, fallback = null) => {
  const index = argv.indexOf(`--${name}`);
  return index >= 0 && argv[index + 1] ? argv[index + 1] : fallback;
};

export function normalizeSeed(value) {
  return String(value || "").toLowerCase().replace(/\s+/g, " ").trim();
}

export function buildManifest(input, now = new Date()) {
  const coverage = input.coverage || {};
  const seedMin = Number(coverage.seed_min ?? 8);
  const seedMax = Number(coverage.seed_max ?? 12);
  const nicheMin = Number(coverage.full_niche_min ?? 5);
  const nicheMax = Number(coverage.full_niche_max ?? 10);
  const cacheDays = Number(coverage.cache_max_age_days ?? 14);
  const branded = new Set((input.branded_terms || []).map(normalizeSeed));
  const seen = new Set();
  const seeds = [];
  for (const item of input.seeds || []) {
    const query = normalizeSeed(item.query || item);
    if (!query || seen.has(query)) continue;
    if ([...branded].some((term) => term && query.includes(term))) continue;
    seen.add(query);
    seeds.push({ query, category: item.category || "uncategorized", sources: item.sources || [] });
  }
  if (seeds.length < seedMin || seeds.length > seedMax) {
    throw new Error(`seed coverage must contain ${seedMin}-${seedMax} deduplicated non-branded seeds; found ${seeds.length}`);
  }
  const requiredCategories = ["head", "form", "mechanism", "use", "attribute"];
  const present = new Set(seeds.map((seed) => seed.category));
  const missingCategories = requiredCategories.filter((category) => !present.has(category));
  if (missingCategories.length) throw new Error(`seed categories missing: ${missingCategories.join(", ")}`);

  const relatedById = new Map();
  for (const niche of input.related_niches || []) {
    if (!niche.niche_id) continue;
    const existing = relatedById.get(niche.niche_id) || { ...niche, discovered_by: [] };
    existing.discovered_by = [...new Set([...(existing.discovered_by || []), ...(niche.discovered_by || [])])];
    relatedById.set(niche.niche_id, existing);
  }
  const related = [...relatedById.values()];
  const selected = related.filter((niche) => niche.relevant === true);
  if (selected.length > nicheMax) throw new Error(`selected relevant niches exceed maximum ${nicheMax}`);
  const limitation = selected.length < nicheMin
    ? `Only ${selected.length} relevant full niche packs qualified; all relevant niches must be downloaded.`
    : null;
  const nowMs = now.getTime();
  for (const niche of selected) {
    if (!niche.cached_at) {
      niche.cache_decision = "fetch";
      continue;
    }
    const ageDays = (nowMs - new Date(niche.cached_at).getTime()) / 86400000;
    niche.cache_age_days = Math.max(0, Math.floor(ageDays));
    niche.cache_decision = ageDays <= cacheDays && niche.full_pack_complete === true ? "reuse" : "refresh";
  }
  return {
    schema_version: 1,
    created_at: now.toISOString(),
    status: "planned",
    sources: input.sources || {},
    coverage: { seed_min: seedMin, seed_max: seedMax, full_niche_min: nicheMin, full_niche_max: nicheMax, cache_max_age_days: cacheDays },
    seeds,
    related_niches: related,
    selected_full_packs: selected,
    excluded_niches: related.filter((niche) => niche.relevant === false),
    limitation,
    supersedes: input.supersedes || [],
  };
}

if (argv[0] === "self-test") {
  const input = {
    branded_terms: ["acme"],
    seeds: [
      { query: "widget", category: "head" }, { query: "widget tool", category: "form" },
      { query: "rotary widget", category: "mechanism" }, { query: "widget for travel", category: "use" },
      { query: "steel widget", category: "attribute" }, { query: "small widget", category: "attribute" },
      { query: "manual widget", category: "mechanism" }, { query: "portable widget", category: "use" },
    ],
    related_niches: Array.from({ length: 5 }, (_, i) => ({ niche_id: `n${i}`, relevant: true, full_pack_complete: true, cached_at: "2026-08-01T00:00:00Z" })),
  };
  const out = buildManifest(input, new Date("2026-08-07T00:00:00Z"));
  if (out.seeds.length !== 8 || out.selected_full_packs.some((niche) => niche.cache_decision !== "reuse")) {
    throw new Error("build-scout-manifest self-test failed");
  }
  console.log("build-scout-manifest self-test: passed");
  process.exit(0);
}

const inputPath = opt("input");
const outputPath = opt("output");
if (!inputPath || !outputPath) {
  console.error("usage: build-scout-manifest.mjs --input scout-input.json --output coverage-manifest.json");
  console.error("       build-scout-manifest.mjs self-test");
  process.exit(1);
}
const manifest = buildManifest(JSON.parse(fs.readFileSync(inputPath, "utf8")));
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(manifest, null, 2) + "\n");
console.log(outputPath);

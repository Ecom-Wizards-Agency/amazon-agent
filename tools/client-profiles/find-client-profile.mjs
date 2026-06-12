#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const repoRoot = process.cwd();
const cachePath = path.join(repoRoot, "_local", "client-profiles", "profiles.json");
const query = process.argv.slice(2).join(" ").trim().toLowerCase();

if (!query) {
  console.error("Usage: node tools/client-profiles/find-client-profile.mjs <brand-or-profile>");
  process.exit(2);
}

if (!fs.existsSync(cachePath)) {
  console.error(`No local client profile cache found at ${cachePath}`);
  console.error("Check Notion Amazon Agent Ops Profiles, then generate the local cache.");
  process.exit(1);
}

const cache = JSON.parse(fs.readFileSync(cachePath, "utf8"));
const profiles = Array.isArray(cache.profiles) ? cache.profiles : [];

const matches = profiles.filter((profile) => {
  const haystack = [
    profile.profile_name,
    profile.local_cache_key,
    profile.marketplace,
    profile.seller_central_name,
    profile.amazon_ads_ppc_name,
    profile.main_stakeholders,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return haystack.includes(query);
});

if (matches.length === 0) {
  console.error(`No local profile matched "${query}". Check Notion before acting.`);
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      source: cache.source,
      synced_at: cache.synced_at,
      matches,
    },
    null,
    2,
  ),
);

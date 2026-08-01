#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..", "..");
const pointerPath = path.join(repoRoot, "_local", "team-vault-path.txt");
const profileFilename = "Amazon Ops.md";
const forbiddenKeyPattern = /(password|passphrase|token|secret|cookie|login.?email|sellerboard.?email)/i;
const emailPattern = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;

function expandHome(value) {
  if (value === "~") return os.homedir();
  if (value.startsWith(`~${path.sep}`)) return path.join(os.homedir(), value.slice(2));
  return value;
}

function resolveTeamVault() {
  const configured = process.env.AMAZON_AGENT_TEAM_VAULT?.trim();
  if (configured) return path.resolve(repoRoot, expandHome(configured));

  if (fs.existsSync(pointerPath)) {
    const pointer = fs
      .readFileSync(pointerPath, "utf8")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .find((line) => line && !line.startsWith("#"));
    if (pointer) return path.resolve(repoRoot, expandHome(pointer));
  }

  throw new Error(
    "Team vault is not configured. Set AMAZON_AGENT_TEAM_VAULT or add its path to _local/team-vault-path.txt.",
  );
}

function findProfileFiles(vaultPath) {
  const clientsDir = path.join(vaultPath, "Clients");
  if (!fs.existsSync(clientsDir) || !fs.statSync(clientsDir).isDirectory()) {
    throw new Error(`Team vault has no Clients directory: ${clientsDir}`);
  }

  return fs
    .readdirSync(clientsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(clientsDir, entry.name, profileFilename))
    .filter((filePath) => fs.existsSync(filePath))
    .sort((a, b) => a.localeCompare(b));
}

function extractJson(filePath) {
  const markdown = fs.readFileSync(filePath, "utf8");
  const blocks = [...markdown.matchAll(/```json\s*\n([\s\S]*?)```/g)];
  if (blocks.length !== 1) {
    throw new Error(`Expected exactly one fenced JSON block, found ${blocks.length}`);
  }
  return JSON.parse(blocks[0][1]);
}

function findSensitiveContent(value, location = "$", findings = []) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => findSensitiveContent(item, `${location}[${index}]`, findings));
    return findings;
  }
  if (value && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      if (forbiddenKeyPattern.test(key)) findings.push(`${location}.${key} uses a forbidden sensitive field name`);
      findSensitiveContent(child, `${location}.${key}`, findings);
    }
    return findings;
  }
  if (typeof value === "string" && emailPattern.test(value)) {
    findings.push(`${location} contains an email address`);
  }
  return findings;
}

function withDerivedPlanning(profile) {
  const output = structuredClone(profile);
  const reshipment = output.reshipment;
  if (!reshipment || reshipment.enabled !== true) return output;

  const components = [
    reshipment.target_stock_days,
    reshipment.lead_time_days,
    reshipment.amazon_booking_buffer_days,
  ];
  if (components.every((value) => typeof value === "number" && Number.isFinite(value))) {
    reshipment.effective_coverage_days = components.reduce((sum, value) => sum + value, 0);
  }
  return output;
}

function loadProfiles() {
  const vaultPath = resolveTeamVault();
  const files = findProfileFiles(vaultPath);
  const errors = [];
  const warnings = [];
  const profiles = [];
  const seenProfileKeys = new Map();

  for (const filePath of files) {
    const sourceFile = path.relative(vaultPath, filePath);
    let document;
    try {
      document = extractJson(filePath);
    } catch (error) {
      errors.push(`${sourceFile}: ${error.message}`);
      continue;
    }

    if (document.schema_version !== 1) errors.push(`${sourceFile}: schema_version must be 1`);
    if (typeof document.client_slug !== "string" || !document.client_slug.trim()) {
      errors.push(`${sourceFile}: client_slug is required`);
    }
    if (!Array.isArray(document.profiles) || document.profiles.length === 0) {
      errors.push(`${sourceFile}: profiles must be a non-empty array`);
      continue;
    }

    for (const finding of findSensitiveContent(document)) errors.push(`${sourceFile}: ${finding}`);

    for (const profile of document.profiles) {
      if (!profile || typeof profile !== "object" || Array.isArray(profile)) {
        errors.push(`${sourceFile}: every profiles entry must be an object`);
        continue;
      }
      const key = profile.profile_key;
      if (typeof key !== "string" || !key.trim()) {
        errors.push(`${sourceFile}: every profile requires profile_key`);
        continue;
      }
      if (seenProfileKeys.has(key)) {
        errors.push(`${sourceFile}: duplicate profile_key ${key}; first seen in ${seenProfileKeys.get(key)}`);
      } else {
        seenProfileKeys.set(key, sourceFile);
      }
      for (const required of ["profile_name", "status", "marketplace"]) {
        if (typeof profile[required] !== "string" || !profile[required].trim()) {
          errors.push(`${sourceFile}: ${key} requires ${required}`);
        }
      }
      if (Object.hasOwn(profile.reshipment ?? {}, "effective_coverage_days")) {
        errors.push(`${sourceFile}: ${key} must not store derived effective_coverage_days`);
      }
      if (profile.reshipment?.enabled === true) {
        for (const field of ["target_stock_days", "lead_time_days", "amazon_booking_buffer_days"]) {
          if (typeof profile.reshipment[field] !== "number" || !Number.isFinite(profile.reshipment[field])) {
            warnings.push(`${sourceFile}: ${key} cannot derive coverage because ${field} is not numeric`);
          }
        }
      }
      profiles.push({
        ...withDerivedPlanning(profile),
        client_slug: document.client_slug,
        source_file: sourceFile,
      });
    }
  }

  if (files.length === 0) warnings.push("No Amazon Ops.md files were found under Clients/");
  return { vaultPath, files, profiles, errors, warnings };
}

function searchableText(profile) {
  return [
    profile.client_slug,
    profile.profile_key,
    profile.profile_name,
    ...(Array.isArray(profile.aliases) ? profile.aliases : []),
    profile.marketplace,
    profile.seller_central_name,
    profile.amazon_ads_ppc_name,
    profile.main_stakeholders,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

let loaded;
try {
  loaded = loadProfiles();
} catch (error) {
  console.error(error.message);
  process.exit(1);
}

if (process.argv[2] === "--validate") {
  const result = {
    source: "team-vault",
    profile_files: loaded.files.length,
    profiles: loaded.profiles.length,
    errors: loaded.errors,
    warnings: loaded.warnings,
  };
  console.log(JSON.stringify(result, null, 2));
  process.exit(loaded.errors.length === 0 ? 0 : 1);
}

const query = process.argv.slice(2).join(" ").trim().toLowerCase();
if (!query) {
  console.error("Usage: node tools/client-profiles/find-client-profile.mjs <brand-or-profile>");
  console.error("       node tools/client-profiles/find-client-profile.mjs --validate");
  process.exit(2);
}
if (loaded.errors.length > 0) {
  console.error("Shared client profiles failed validation:");
  loaded.errors.forEach((error) => console.error(`- ${error}`));
  process.exit(1);
}

const matches = loaded.profiles.filter((profile) => searchableText(profile).includes(query));
if (matches.length === 0) {
  console.error(`No shared team-vault profile matched "${query}".`);
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      source: "team-vault",
      matches,
      warnings: loaded.warnings,
    },
    null,
    2,
  ),
);

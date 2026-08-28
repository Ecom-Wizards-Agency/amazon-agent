#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import {
  CONFIG_SCHEMA, STATE_SCHEMA, applyRun, deriveSearchQueries, entityKey,
  findSuspectedCandidates, isFailureStatus, normalizeAsin, normalizeMarketplace,
  parseAmazonTarget, validateConfig,
} from "./lib.mjs";
import {
  browserDoctor, capturePdp, captureScreenshot, exactAsinSearch,
  searchAmazon, verifyDeliveryLocation,
} from "./browser.mjs";

const DEFAULT_RUNTIME = path.join(os.homedir(), ".codex", "automations", "tmrw-amazon-product-tracker");
const DEFAULT_CONFIG = path.join(DEFAULT_RUNTIME, "config.json");

function parseCli() {
  const positional = [];
  const options = {};
  const args = process.argv.slice(2);
  for (let index = 0; index < args.length; index++) {
    const value = args[index];
    if (value === "--config" || value === "--marketplace") {
      if (!args[index + 1]) throw new Error(`${value} needs a value`);
      options[value.slice(2)] = args[++index];
    } else {
      positional.push(value);
    }
  }
  return { positional, options };
}

function runtimePaths(configPath, config = {}) {
  const root = path.resolve(config.runtimeDir || path.dirname(configPath));
  return {
    root,
    state: path.join(root, "state.json"),
    history: path.join(root, "history.jsonl"),
    evidence: path.join(root, "evidence"),
    lock: path.join(root, "run.lock"),
  };
}

function atomicJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const temporary = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  fs.renameSync(temporary, file);
}

function loadJson(file, fallback = null) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); }
  catch (error) {
    if (error.code === "ENOENT") return fallback;
    throw error;
  }
}

function defaultConfig() {
  return {
    schemaVersion: CONFIG_SCHEMA,
    name: "TMRW Amazon suspected-product tracker",
    timezone: "Asia/Qostanay",
    brandTokens: ["tmrw"],
    discovery: { queries: ["TMRW"], pages: 3, minimumSimilarity: 0.55, titleQueryWords: 8 },
    marketplaces: {
      ca: { postalCode: "M5V 3L9", verifyTokens: ["M5V", "TORONTO"], language: "en_CA" },
      com: { postalCode: "10001", verifyTokens: ["10001", "NEW YORK"], language: "en_US" },
    },
    entities: [
      { marketplace: "ca", asin: "B0HDBBPG9S", lifecycle: "reported", label: "Initial suspected TMRW listing" },
      { marketplace: "com", asin: "B0HDH2KNFY", lifecycle: "reported", label: "Initial suspected TMRW listing" },
    ],
  };
}

function readConfig(configPath) {
  const config = loadJson(configPath);
  if (!config) throw new Error(`Config not found: ${configPath}. Run init first.`);
  return validateConfig(config);
}

function acquireLock(lockPath) {
  fs.mkdirSync(path.dirname(lockPath), { recursive: true, mode: 0o700 });
  try {
    const fd = fs.openSync(lockPath, "wx", 0o600);
    fs.writeFileSync(fd, `${JSON.stringify({ pid: process.pid, startedAt: new Date().toISOString() })}\n`);
    fs.closeSync(fd);
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    const detail = fs.readFileSync(lockPath, "utf8").trim();
    throw new Error(`Monitor lock exists at ${lockPath}${detail ? `: ${detail}` : ""}`);
  }
  let released = false;
  return () => {
    if (released) return;
    released = true;
    try { fs.unlinkSync(lockPath); } catch (error) { if (error.code !== "ENOENT") throw error; }
  };
}

async function confirmedPdp(marketplace, asin, settings) {
  const first = await capturePdp(marketplace, asin, settings.language);
  if (first.status !== "removed") return first;
  const second = await capturePdp(marketplace, asin, settings.language);
  if (second.status !== "removed") {
    return { ...second, status: "error", reason: `Removal unconfirmed: first=${first.status}, second=${second.status}` };
  }
  const search = await exactAsinSearch(marketplace, asin, settings.language);
  if (search.status !== "ok") {
    return { ...second, status: search.status, reason: `Removal unconfirmed: exact-ASIN search ${search.reason || search.status}` };
  }
  if (search.found) {
    return { ...second, status: "error", reason: "Removal unconfirmed: exact-ASIN search still returned the listing" };
  }
  return { ...second, confirmation: { pdpChecks: 2, exactAsinSearchAbsent: true } };
}

async function writeEvidence(paths, report) {
  if (!report.events.length) return "";
  const stamp = report.run.finishedAt.replace(/[:.]/g, "-");
  const directory = path.join(paths.evidence, stamp.slice(0, 10), stamp);
  fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
  const screenshotErrors = [];
  const screenshotted = new Set();
  for (const item of report.events) {
    if (!item.url || screenshotted.has(item.url)) continue;
    screenshotted.add(item.url);
    const name = `${item.marketplace || "amazon"}-${item.asin || "event"}-${item.type}.png`.replace(/[^a-zA-Z0-9_.-]/g, "_");
    try { await captureScreenshot(item.url, path.join(directory, name)); }
    catch (error) { screenshotErrors.push({ url: item.url, error: error.message }); }
  }
  const summary = path.join(directory, "events.json");
  atomicJson(summary, { ...report, screenshotErrors });
  return summary;
}

async function runMonitor(configPath) {
  const config = readConfig(configPath);
  const paths = runtimePaths(configPath, config);
  const release = acquireLock(paths.lock);
  const onSignal = () => { release(); process.exit(130); };
  process.once("SIGINT", onSignal);
  process.once("SIGTERM", onSignal);
  try {
    const previousState = loadJson(paths.state, null);
    if (previousState && previousState.schemaVersion !== STATE_SCHEMA) {
      throw new Error(`Unsupported state schema: ${previousState.schemaVersion}`);
    }
    const run = {
      startedAt: new Date().toISOString(),
      finishedAt: null,
      locations: {},
      snapshots: [],
      discoveries: [],
      failures: [],
    };

    await browserDoctor();
    for (const [marketplace, settings] of Object.entries(config.marketplaces)) {
      const entities = config.entities.filter((item) => normalizeMarketplace(item.marketplace) === marketplace
        && !["dismissed", "authorized"].includes(item.lifecycle));
      const location = await verifyDeliveryLocation(marketplace, settings, entities[0]?.asin || "");
      run.locations[marketplace] = location;
      if (!location.ok) {
        run.failures.push({ scope: `marketplace:${marketplace}`, reason: `Delivery location not verified: ${location.label || location.reason}` });
        for (const entity of entities) {
          run.snapshots.push({ marketplace, asin: entity.asin, status: "error", reason: "Delivery location not verified", capturedAt: new Date().toISOString() });
        }
        continue;
      }

      const marketplaceSnapshots = [];
      for (const entity of entities) {
        const snapshot = await confirmedPdp(marketplace, normalizeAsin(entity.asin), settings);
        marketplaceSnapshots.push(snapshot);
        run.snapshots.push(snapshot);
        if (isFailureStatus(snapshot.status)) {
          run.failures.push({ scope: `${marketplace}:${entity.asin}`, reason: snapshot.reason || snapshot.status, url: snapshot.url || "" });
        }
      }

      const queries = deriveSearchQueries(
        config.discovery?.queries || [], marketplaceSnapshots,
        config.discovery?.titleQueryWords || 8,
      );
      const cards = [];
      for (const query of queries) {
        const search = await searchAmazon(marketplace, query, config.discovery?.pages || 3, settings.language);
        cards.push(...search.cards);
        if (search.status !== "ok") {
          run.failures.push({ scope: `search:${marketplace}:${query}`, reason: search.reason || search.status });
        }
      }
      const trackedTitles = marketplaceSnapshots.map((item) => item.title).filter(Boolean);
      run.discoveries.push(...findSuspectedCandidates(cards, {
        marketplace,
        brandTokens: config.brandTokens || [],
        trackedTitles,
        minimumSimilarity: config.discovery?.minimumSimilarity || 0.55,
      }));
    }

    run.finishedAt = new Date().toISOString();
    const applied = applyRun(previousState, run, config);
    const report = { schemaVersion: "amazon-agent.brand-surveillance-run.v1", run, ...applied };
    report.evidencePath = await writeEvidence(paths, report);
    for (const item of report.events) if (report.evidencePath) item.evidencePath = report.evidencePath;
    atomicJson(paths.state, report.state);
    fs.appendFileSync(paths.history, `${JSON.stringify({ ...report, state: undefined })}\n`, { mode: 0o600 });
    return report;
  } finally {
    process.removeListener("SIGINT", onSignal);
    process.removeListener("SIGTERM", onSignal);
    release();
  }
}

async function init(configPath) {
  if (fs.existsSync(configPath)) return { ok: true, created: false, configPath };
  atomicJson(configPath, defaultConfig());
  const paths = runtimePaths(configPath);
  fs.mkdirSync(paths.evidence, { recursive: true, mode: 0o700 });
  return { ok: true, created: true, configPath };
}

async function doctor(configPath) {
  const config = readConfig(configPath);
  const paths = runtimePaths(configPath, config);
  fs.mkdirSync(paths.root, { recursive: true, mode: 0o700 });
  fs.accessSync(paths.root, fs.constants.R_OK | fs.constants.W_OK);
  const browser = await browserDoctor();
  return { ok: true, configPath, runtime: paths.root, lockPresent: fs.existsSync(paths.lock), browser, entities: config.entities.length };
}

function publicRunReport(report) {
  return {
    schemaVersion: report.schemaVersion,
    baseline: report.baseline,
    clean: report.clean,
    missedRunGapHours: report.missedRunGapHours,
    evidencePath: report.evidencePath,
    events: report.events,
    run: {
      startedAt: report.run.startedAt,
      finishedAt: report.run.finishedAt,
      locations: report.run.locations,
      snapshots: report.run.snapshots,
      failures: report.run.failures,
      discoveryCount: report.run.discoveries.length,
    },
  };
}

function updateEntity(configPath, target, lifecycle, fallbackMarketplace = "") {
  const config = readConfig(configPath);
  const parsed = parseAmazonTarget(target, fallbackMarketplace);
  const key = entityKey(parsed.marketplace, parsed.asin);
  const existing = config.entities.find((item) => entityKey(item.marketplace, item.asin) === key);
  if (existing) existing.lifecycle = lifecycle;
  else config.entities.push({ ...parsed, lifecycle, label: "Added through monitor CLI" });
  atomicJson(configPath, config);
  return { ok: true, ...parsed, lifecycle, updated: Boolean(existing) };
}

async function main() {
  const cli = parseCli();
  const configPath = path.resolve(cli.options.config || DEFAULT_CONFIG);
  const args = cli.positional;
  const command = args[0] || "run";
  let result;
  if (command === "init") result = await init(configPath);
  else if (command === "doctor") result = await doctor(configPath);
  else if (command === "run") result = publicRunReport(await runMonitor(configPath));
  else if (command === "add") result = updateEntity(configPath, args[1], args[2] || "candidate", cli.options.marketplace || "");
  else if (command === "set-status") {
    const marketplace = normalizeMarketplace(args[1]);
    const asin = normalizeAsin(args[2]);
    const lifecycle = args[3];
    if (!new Set(["candidate", "reported", "dismissed", "authorized"]).has(lifecycle)) throw new Error(`Invalid lifecycle: ${lifecycle}`);
    result = updateEntity(configPath, asin, lifecycle, marketplace);
  } else {
    throw new Error("Usage: monitor.mjs init|doctor|run|add <url|asin> [lifecycle] [--marketplace com]|set-status <marketplace> <asin> <lifecycle> [--config path]");
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (command === "run" && result.run.failures.length) process.exitCode = 2;
}

main().catch((error) => {
  process.stdout.write(`${JSON.stringify({ ok: false, fatal: true, error: error.message, stack: error.stack }, null, 2)}\n`);
  process.exitCode = 2;
});

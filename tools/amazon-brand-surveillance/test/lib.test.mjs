import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  CONFIG_SCHEMA, STATE_SCHEMA, applyRun, classifyPdp, findSuspectedCandidates,
  parseAmazonTarget,
} from "../lib.mjs";

const fixtureRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures");
const fixture = (name) => JSON.parse(fs.readFileSync(path.join(fixtureRoot, name), "utf8"));
const asin = "B0HDH2KNFY";
const config = {
  schemaVersion: CONFIG_SCHEMA,
  marketplaces: { com: { postalCode: "10001", verifyTokens: ["10001"] } },
  entities: [{ marketplace: "com", asin, lifecycle: "reported" }],
};

test("parses Amazon URLs and bare ASINs", () => {
  assert.deepEqual(parseAmazonTarget("https://www.amazon.ca/dp/B0HDBBPG9S?th=1"), { marketplace: "ca", asin: "B0HDBBPG9S" });
  assert.deepEqual(parseAmazonTarget(asin, "com"), { marketplace: "com", asin });
});

test("classifies live, unavailable, removed, blocked, and redirected fixtures", () => {
  assert.equal(classifyPdp(fixture("live.json"), asin).status, "live");
  assert.equal(classifyPdp(fixture("unavailable.json"), asin).status, "unavailable");
  assert.equal(classifyPdp(fixture("removed.json"), asin).status, "removed");
  assert.equal(classifyPdp(fixture("blocked.json"), asin).status, "blocked");
  assert.equal(classifyPdp(fixture("redirected.json"), asin).status, "redirected");
});

test("discovery deduplicates matching organic and sponsored result cards", () => {
  const candidates = findSuspectedCandidates(fixture("search-results.json"), {
    marketplace: "com", brandTokens: ["tmrw"], trackedTitles: ["TMRW Example Product"], minimumSimilarity: 0.55,
  });
  assert.deepEqual(candidates.map((item) => item.asin), ["B0HDH2KNFY", "B0BBBBBBBB"]);
  assert.equal(candidates[1].sponsored, true);
  assert.equal(candidates.some((item) => item.asin === "B0DDDDDDDD"), false);
});

test("first run is a quiet baseline and second identical run stays clean", () => {
  const snapshot = { marketplace: "com", ...classifyPdp(fixture("live.json"), asin) };
  const firstRun = { startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z", snapshots: [snapshot], discoveries: [], failures: [] };
  const first = applyRun(null, firstRun, config);
  assert.equal(first.baseline, true);
  assert.equal(first.events.length, 0);
  assert.equal(first.state.schemaVersion, STATE_SCHEMA);
  const secondRun = { ...firstRun, startedAt: "2026-08-11T01:00:00Z", finishedAt: "2026-08-11T01:01:00Z" };
  const second = applyRun(first.state, secondRun, config);
  assert.equal(second.baseline, false);
  assert.equal(second.clean, true);
});

test("a failed first run does not consume the successful baseline", () => {
  const failed = applyRun(null, {
    startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z",
    snapshots: [], discoveries: [], failures: [{ scope: "marketplace:com", reason: "location" }],
  }, config);
  assert.equal(failed.baseline, true);
  assert.equal(failed.state.lastSuccessfulRunAt, null);
  const live = { marketplace: "com", ...classifyPdp(fixture("live.json"), asin) };
  const recovered = applyRun(failed.state, {
    startedAt: "2026-08-11T01:00:00Z", finishedAt: "2026-08-11T01:01:00Z",
    snapshots: [live], discoveries: [{ marketplace: "com", asin: "B0BBBBBBBB", title: "TMRW Copy" }], failures: [],
  }, config);
  assert.equal(recovered.baseline, true);
  assert.equal(recovered.events.length, 0);
});

test("confirmed removal and later reappearance emit high-signal events", () => {
  const live = { marketplace: "com", ...classifyPdp(fixture("live.json"), asin) };
  const baseline = applyRun(null, { startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z", snapshots: [live], discoveries: [], failures: [] }, config);
  const removed = { marketplace: "com", ...classifyPdp(fixture("removed.json"), asin), confirmation: { pdpChecks: 2, exactAsinSearchAbsent: true } };
  const takedown = applyRun(baseline.state, { startedAt: "2026-08-11T01:00:00Z", finishedAt: "2026-08-11T01:01:00Z", snapshots: [removed], discoveries: [], failures: [] }, config);
  assert.equal(takedown.events[0].type, "takedown_confirmed");
  const reappeared = applyRun(takedown.state, { startedAt: "2026-08-12T01:00:00Z", finishedAt: "2026-08-12T01:01:00Z", snapshots: [live], discoveries: [], failures: [] }, config);
  assert.equal(reappeared.events[0].type, "reappeared");
});

test("blocked capture never replaces the last verified state", () => {
  const live = { marketplace: "com", ...classifyPdp(fixture("live.json"), asin) };
  const baseline = applyRun(null, { startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z", snapshots: [live], discoveries: [], failures: [] }, config);
  const blocked = { marketplace: "com", ...classifyPdp(fixture("blocked.json"), asin) };
  const result = applyRun(baseline.state, {
    startedAt: "2026-08-11T01:00:00Z", finishedAt: "2026-08-11T01:01:00Z",
    snapshots: [blocked], discoveries: [], failures: [{ scope: `com:${asin}`, reason: blocked.reason }],
  }, config);
  assert.equal(result.state.entities[`com|${asin}`].lastVerified.status, "live");
  assert.equal(result.events[0].type, "run_failure");
});

test("dismissed and authorized ASINs do not enter the candidate queue", () => {
  const suppressed = {
    ...config,
    entities: [
      ...config.entities,
      { marketplace: "com", asin: "B0BBBBBBBB", lifecycle: "dismissed" },
      { marketplace: "com", asin: "B0CCCCCCCC", lifecycle: "authorized" },
    ],
  };
  const run = {
    startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z", snapshots: [], failures: [],
    discoveries: [
      { marketplace: "com", asin: "B0BBBBBBBB", title: "TMRW Copy" },
      { marketplace: "com", asin: "B0CCCCCCCC", title: "TMRW Authorized" },
    ],
  };
  const result = applyRun(null, run, suppressed);
  assert.deepEqual(Object.keys(result.state.candidates), []);
});

test("an existing candidate adopts a later dismissed lifecycle", () => {
  const discovery = { marketplace: "com", asin: "B0BBBBBBBB", title: "TMRW Copy" };
  const first = applyRun(null, {
    startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z",
    snapshots: [], failures: [], discoveries: [discovery],
  }, config);
  const dismissed = {
    ...config,
    entities: [...config.entities, { marketplace: "com", asin: "B0BBBBBBBB", lifecycle: "dismissed" }],
  };
  const second = applyRun(first.state, {
    startedAt: "2026-08-11T01:00:00Z", finishedAt: "2026-08-11T01:01:00Z",
    snapshots: [], failures: [], discoveries: [discovery],
  }, dismissed);
  assert.equal(second.state.candidates["com|B0BBBBBBBB"].lifecycle, "dismissed");
  assert.equal(second.events.length, 0);
});

test("featured seller change emits one high-signal event", () => {
  const live = { marketplace: "com", ...classifyPdp(fixture("live.json"), asin) };
  const baseline = applyRun(null, { startedAt: "2026-08-10T01:00:00Z", finishedAt: "2026-08-10T01:01:00Z", snapshots: [live], discoveries: [], failures: [] }, config);
  const changed = { ...live, seller: "Different Seller", capturedAt: "2026-08-11T01:00:00Z" };
  const result = applyRun(baseline.state, { startedAt: "2026-08-11T01:00:00Z", finishedAt: "2026-08-11T01:01:00Z", snapshots: [changed], discoveries: [], failures: [] }, config);
  assert.equal(result.events.length, 1);
  assert.equal(result.events[0].type, "seller_or_fulfiller_changed");
});

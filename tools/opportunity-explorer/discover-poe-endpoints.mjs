/*
 * POE endpoint discovery logger — Phase 0 of the Opportunity Explorer downloader
 * rebuild (see references/poe-endpoints.md for the resulting contract).
 *
 * Attaches (read-only) to the operator's ALREADY logged-in Seller Central tab via
 * the Chrome debug port and streams the page's own network traffic while the
 * operator/agent clicks through one niche's tabs. Same-origin JSON/CSV exchanges
 * are appended as NDJSON records, one file per UI-tab label, so the internal API
 * behind each POE tab can be documented before coding fetch-poe.js.
 *
 * SAFETY
 *   Observes traffic the page itself generates in the operator's session; never
 *   sends requests, never logs in, never reads cookies, local/session storage, or
 *   tokens. Request headers are WHITELISTED (content-type, accept, csrf meta value)
 *   — cookie/authorization headers are never written. Output goes to client
 *   downloads folders (gitignored); the committed deliverable is the sanitized
 *   references/poe-endpoints.md, written by hand from these captures.
 *
 * USAGE
 *   tools/report-fetcher/launch-chrome-debug.sh     # then log into Seller Central
 *   node tools/opportunity-explorer/discover-poe-endpoints.mjs \
 *     --out "downloads/<client>/opportunity-data/poe-endpoint-capture-<date>" \
 *     [--evidence "evidence/<client>/opportunity-data"] [--all-hosts] [--tab <n>]
 *
 *   Interactive commands (stdin) while clicking through the UI:
 *     label <name>   tag subsequent records with this UI tab (e.g. label cri-positive)
 *     shot <name>    save a PNG screenshot of the attached tab to --evidence
 *     note <text>    append a free-text note record to the current label file
 *     tabs           re-list candidate Seller Central tabs
 *     quit           detach and exit
 */

import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { assertChrome, listPages, Session } from "../report-fetcher/cdp.mjs";

const BODY_CAP = 4096; // bytes of response body kept per record

function arg(name, dflt) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
}
const flag = (name) => process.argv.includes(`--${name}`);

const OUT_DIR = arg("out", `downloads/discovery/poe-endpoint-capture-${new Date().toISOString().slice(0, 10)}`);
const EVIDENCE_DIR = arg("evidence", OUT_DIR);
const ALL_HOSTS = flag("all-hosts");

// Only headers that document the API contract. Never cookie/authorization.
const HEADER_WHITELIST = new Set([
  "content-type", "accept", "anti-csrftoken-a2z", "x-amz-target", "x-api-csrf-token",
]);

function pickHeaders(headers = {}) {
  const out = {};
  for (const [k, v] of Object.entries(headers)) {
    if (HEADER_WHITELIST.has(k.toLowerCase())) out[k.toLowerCase()] = v;
  }
  return out;
}

function interesting(url, mimeType, resourceType) {
  if (!/sellercentral\.amazon\./.test(url) && !ALL_HOSTS) return false;
  if (/\.(js|css|png|jpe?g|gif|svg|woff2?|ttf|ico|map)(\?|$)/.test(url)) return false;
  if (resourceType && !["XHR", "Fetch", "Document", "Other"].includes(resourceType)) return false;
  const mt = (mimeType || "").toLowerCase();
  return mt.includes("json") || mt.includes("csv") || mt.includes("graphql") ||
         mt.includes("text/plain") || mt === "" || resourceType === "XHR" || resourceType === "Fetch";
}

async function pickTab() {
  const pages = await listPages();
  const sc = pages.filter((p) => /sellercentral\.amazon\./.test(p.url));
  if (!sc.length) {
    console.error("No Seller Central tab found. Open Seller Central (ideally the Opportunity Explorer) and retry.");
    console.error("Open tabs:"); pages.forEach((p, i) => console.error(`  [${i}] ${p.url.slice(0, 110)}`));
    process.exit(1);
  }
  sc.sort((a, b) => Number(/opportunity-explorer/.test(b.url)) - Number(/opportunity-explorer/.test(a.url)));
  const idx = arg("tab", null);
  const chosen = idx !== null ? sc[Number(idx)] : sc[0];
  console.log("Candidate Seller Central tabs:");
  sc.forEach((p, i) => console.log(`  [${i}]${p === chosen ? " <== attached" : ""} ${p.url.slice(0, 110)}`));
  return chosen;
}

async function main() {
  await assertChrome();
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });

  const tab = await pickTab();
  const session = await Session.open(tab.webSocketDebuggerUrl);
  await session.send("Network.enable", { maxTotalBufferSize: 100 * 1024 * 1024, maxResourceBufferSize: 20 * 1024 * 1024 });
  await session.send("Page.enable");

  let label = "unlabeled";
  const reqs = new Map(); // requestId -> partial record
  const streams = new Map(); // label -> write stream

  function out(rec) {
    if (!streams.has(rec.label)) {
      streams.set(rec.label, fs.createWriteStream(path.join(OUT_DIR, `${rec.label}.ndjson`), { flags: "a" }));
    }
    streams.get(rec.label).write(JSON.stringify(rec) + "\n");
  }

  session.subscribe("Network.requestWillBeSent", (p) => {
    const r = p.request || {};
    if (!/sellercentral\.amazon\./.test(r.url) && !ALL_HOSTS) return;
    reqs.set(p.requestId, {
      ts: new Date().toISOString(), label,
      method: r.method, url: r.url,
      resourceType: p.type || "",
      requestHeaders: pickHeaders(r.headers),
      postData: r.postData || null,
      hasPostData: !!r.hasPostData,
    });
  });

  session.subscribe("Network.responseReceived", (p) => {
    const rec = reqs.get(p.requestId);
    if (!rec) return;
    rec.status = p.response?.status;
    rec.mimeType = p.response?.mimeType || "";
    rec.responseHeaders = pickHeaders(p.response?.headers || {});
  });

  session.subscribe("Network.loadingFinished", async (p) => {
    const rec = reqs.get(p.requestId);
    reqs.delete(p.requestId);
    if (!rec || !interesting(rec.url, rec.mimeType, rec.resourceType)) return;
    if (rec.hasPostData && !rec.postData) {
      try { rec.postData = (await session.send("Network.getRequestPostData", { requestId: p.requestId })).postData; }
      catch (_) { /* body evicted — keep the record anyway */ }
    }
    try {
      const b = await session.send("Network.getResponseBody", { requestId: p.requestId });
      const text = b.base64Encoded ? Buffer.from(b.body, "base64").toString("utf8") : b.body;
      rec.responseBodyBytes = Buffer.byteLength(text);
      rec.responseBodyFirst4KB = text.slice(0, BODY_CAP);
    } catch (_) {
      rec.responseBodyBytes = null;
      rec.responseBodyFirst4KB = null; // body evicted or non-retrievable (e.g. download)
    }
    out(rec);
    console.log(`  [${rec.label}] ${rec.method} ${rec.status} ${rec.mimeType.padEnd(24).slice(0, 24)} ${rec.url.slice(0, 100)}`);
  });

  // Downloads (native CSV export button) surface here even when no fetch is visible.
  session.subscribe("Page.downloadWillBegin", (p) => {
    out({ ts: new Date().toISOString(), label, event: "downloadWillBegin", url: p.url, suggestedFilename: p.suggestedFilename });
    console.log(`  [${label}] DOWNLOAD ${p.suggestedFilename || ""} ${String(p.url).slice(0, 100)}`);
  });

  console.log(`\nLogging same-origin JSON/CSV traffic to ${OUT_DIR}/<label>.ndjson`);
  console.log(`Commands: label <name> | shot <name> | note <text> | tabs | quit\n`);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, prompt: "poe> " });
  rl.prompt();
  rl.on("line", async (line) => {
    const [cmd, ...rest] = line.trim().split(/\s+/);
    const restStr = rest.join(" ");
    try {
      if (cmd === "quit" || cmd === "q") { rl.close(); return; }
      else if (cmd === "label" && restStr) { label = restStr.toLowerCase().replace(/[^a-z0-9_-]+/g, "-"); console.log(`label = ${label}`); }
      else if (cmd === "shot" && restStr) {
        const shot = await session.send("Page.captureScreenshot", { format: "png" });
        const file = path.join(EVIDENCE_DIR, `${new Date().toISOString().slice(0, 10)}_poe_${restStr}.png`);
        fs.writeFileSync(file, Buffer.from(shot.data, "base64"));
        console.log(`saved ${file}`);
      }
      else if (cmd === "note" && restStr) { out({ ts: new Date().toISOString(), label, event: "note", text: restStr }); console.log("noted"); }
      else if (cmd === "tabs") { (await listPages()).forEach((p, i) => console.log(`  [${i}] ${p.url.slice(0, 110)}`)); }
      else if (cmd) console.log("commands: label <name> | shot <name> | note <text> | tabs | quit");
    } catch (e) { console.error("command failed:", e.message); }
    rl.prompt();
  });
  rl.on("close", () => {
    for (const s of streams.values()) s.end();
    session.close();
    console.log(`\nDone. Captures in ${OUT_DIR}`);
    process.exit(0);
  });
}

main().catch((e) => { console.error(e.message); process.exit(1); });

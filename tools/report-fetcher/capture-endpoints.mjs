#!/usr/bin/env node
/*
 * Endpoint capture — log the network calls Seller Central makes, to discover the
 * internal APIs behind a report/page (e.g. FBA Inventory / Restock, which the
 * fetcher doesn't cover yet). Read-only: it only OBSERVES traffic via CDP and can
 * NAVIGATE to view pages; it never submits forms or clicks generate/download.
 *
 *   node tools/report-fetcher/capture-endpoints.mjs [--seconds 180] \
 *        [--out output/_capture/inventory.json] [--filter <regex>] \
 *        [--navigate "https://sellercentral.amazon.com/...,https://..."]
 *
 * Attaches to all current Seller Central tabs (and new ones). With --navigate it
 * opens a tab and walks the given view URLs, capturing each page's data XHRs.
 * Every XHR/fetch/POST to a sellercentral host is logged: method, URL, request
 * body, status, mimeType.
 *
 * Prereq: the debug Chrome (launch-chrome-debug.sh), signed in.
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { assertChrome, listPages, createPage, closePage, Session } from "./cdp.mjs";

function arg(name, def) { const i = process.argv.indexOf("--" + name); return i > 0 ? process.argv[i + 1] : def; }
const SECONDS = Number(arg("seconds", "180"));
const OUT = arg("out", "output/_capture/endpoints.json");
const FILTER = arg("filter", "");
const NAV = (arg("navigate", "") || "").split(",").map((s) => s.trim()).filter(Boolean);
const rx = FILTER ? new RegExp(FILTER, "i") : null;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const seen = new Map();
const attached = new Set();
const distinct = new Set();
const wantUrl = (u) => /sellercentral\.amazon\./.test(u) && (!rx || rx.test(u));

const ALL_TYPES = process.argv.includes("--all-types");
const downloads = [];

async function attach(page) {
  if (attached.has(page.id)) return;
  attached.add(page.id);
  let s;
  try { s = await Session.open(page.webSocketDebuggerUrl); } catch { attached.delete(page.id); return; }
  await s.send("Network.enable", { maxPostDataSize: 65536 });
  await s.send("Page.enable").catch(() => {});
  await s.send("Page.setDownloadBehavior", { behavior: "default" }).catch(() => {});
  // A file download fires downloadWillBegin with the real URL — the reliable way to
  // catch report downloads (they aren't plain XHRs).
  s.subscribe("Page.downloadWillBegin", (p) => {
    if (!p || !p.url) return;
    downloads.push({ url: p.url, suggestedFilename: p.suggestedFilename });
    console.log(`  DOWNLOAD ${p.suggestedFilename || ""}\n    ${p.url}`);
  });
  s.subscribe("Network.requestWillBeSent", (p) => {
    const t = p.type || "", m = (p.request && p.request.method) || "";
    if (!ALL_TYPES && !(t === "XHR" || t === "Fetch" || m === "POST")) return;
    if (!wantUrl(p.request.url)) return;
    seen.set(p.requestId, { type: t, method: m, url: p.request.url, postData: p.request.postData || null });
  });
  s.subscribe("Network.responseReceived", (p) => {
    const rec = seen.get(p.requestId);
    if (!rec) return;
    rec.status = p.response && p.response.status;
    rec.mimeType = p.response && p.response.mimeType;
    const key = rec.method + " " + rec.url.split("?")[0];
    if (!distinct.has(key)) { distinct.add(key); console.log(`  ${rec.status || "?"} ${key}  [${rec.mimeType || ""}]`); }
  });
}

async function main() {
  await assertChrome();
  console.log(`Capturing Seller Central endpoints${FILTER ? " (filter " + FILTER + ")" : ""} for up to ${SECONDS}s.\n`);
  let done = false;
  const rescan = setInterval(async () => {
    for (const p of await listPages()) if (/sellercentral\.amazon\./.test(p.url || "")) await attach(p);
  }, 1500);

  if (NAV.length) {
    const { targetId, session } = await createPage(NAV[0]);
    await session.send("Page.enable");
    for (const u of NAV) {
      console.log("navigate →", u);
      try { await session.send("Page.navigate", { url: u }); } catch (e) { console.log("  (navigate failed:", e.message + ")"); }
      await sleep(14000);   // let the page fire its data XHRs
    }
    session.close(); await closePage(targetId);
  } else {
    await sleep(SECONDS * 1000);
  }
  clearInterval(rescan);

  const records = [...seen.values()].filter((r) => r.status !== undefined);
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify({ requests: records, downloads }, null, 1));
  console.log(`\nDone — ${records.length} request(s), ${distinct.size} distinct endpoint(s), ${downloads.length} download(s) → ${OUT}`);
}

main().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });

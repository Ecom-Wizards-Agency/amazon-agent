#!/usr/bin/env node
/* Capture viewport or element screenshots from the dedicated CDP Chrome.

Input JSON: { output_dir, account, marketplace, captures: [{ id, url_contains,
title_contains, selector, finding, caption, section, source_kind, priority }] }
The script never navigates or changes account state. It captures only already-open tabs.
*/
import fs from "node:fs/promises";
import path from "node:path";
import { ensureChrome, listPages, Session, evaluate } from "../report-fetcher/cdp.mjs";

const specPath = process.argv[2];
if (!specPath) throw new Error("usage: capture_audit_evidence.mjs <spec.json>");
const spec = JSON.parse(await fs.readFile(specPath, "utf8"));
await ensureChrome();
await fs.mkdir(spec.output_dir, { recursive: true });
const pages = await listPages();
const candidates = [];

for (const item of spec.captures || []) {
  const page = pages.find((p) =>
    (!item.url_contains || String(p.url).includes(item.url_contains)) &&
    (!item.title_contains || String(p.title).includes(item.title_contains)));
  if (!page) continue;
  const session = await Session.open(page.webSocketDebuggerUrl);
  try {
    await session.send("Page.enable");
    let clip;
    if (item.selector) {
      clip = await evaluate(session, `(() => {
        const el = document.querySelector(${JSON.stringify(item.selector)});
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x: Math.max(0, r.left + scrollX), y: Math.max(0, r.top + scrollY),
                width: Math.max(1, r.width), height: Math.max(1, r.height), scale: 1};
      })()`);
      if (!clip) continue;
    }
    const shot = await session.send("Page.captureScreenshot", {
      format: "png", fromSurface: true, captureBeyondViewport: Boolean(clip), ...(clip ? { clip } : {}),
    });
    const out = path.join(spec.output_dir, `${item.id}.png`);
    await fs.writeFile(out, Buffer.from(shot.data, "base64"));
    candidates.push({ ...item, path: out, account: spec.account,
      marketplace: spec.marketplace, source_url: page.url,
      captured_at: new Date().toISOString(), viewport_only: true });
  } finally {
    session.close();
  }
}

const manifest = path.join(spec.output_dir, "evidence_candidates.json");
await fs.writeFile(manifest, JSON.stringify({ candidates }, null, 2) + "\n");
console.log(manifest);

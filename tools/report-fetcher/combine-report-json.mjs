#!/usr/bin/env node
/* Combine compatible report-fetcher raw JSON documents and render one CSV. */
import { readFileSync, writeFileSync } from "node:fs";
import { format } from "./format-seller-reports.mjs";

function fail(message) {
  console.error("ERROR: " + message);
  process.exit(1);
}

const args = process.argv.slice(2);
const outAt = args.indexOf("--out");
if (outAt < 0 || !args[outAt + 1]) {
  fail("usage: node combine-report-json.mjs <raw1.json> <raw2.json> ... --out <combined.csv>");
}
const inputs = args.slice(0, outAt);
const outPath = args[outAt + 1];
if (!inputs.length) fail("at least one input JSON is required");

const docs = inputs.map((path) => JSON.parse(readFileSync(path, "utf8")));
const first = docs[0];
for (const doc of docs) {
  if (doc.error) fail("input carries a fetch error: " + doc.error);
  if (doc.report !== first.report) fail("report types differ");
  if ((doc.marketplace || "") !== (first.marketplace || "")) fail("marketplaces differ");
  if ((doc.sourceView || "") !== (first.sourceView || "")) fail("source views differ");
  if ((doc.proxyAsin || "") !== (first.proxyAsin || "")) fail("proxy ASINs differ");
}

const combined = {
  ...first,
  capturedAt: new Date().toISOString(),
  combinedFrom: inputs,
  columns: docs.find((doc) => (doc.columns || []).length)?.columns || first.columns || [],
  batches: docs.flatMap((doc) => doc.batches || []),
};
writeFileSync(outPath, format(combined));
const rows = combined.batches.reduce((n, batch) => n + (batch.rows || []).length, 0);
console.log(`OK: ${outPath} (${rows} rows from ${inputs.length} source files)`);

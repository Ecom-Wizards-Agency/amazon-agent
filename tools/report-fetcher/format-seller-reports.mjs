#!/usr/bin/env node
/*
 * Convert fetch-seller-reports.js output JSON -> the exact CSV the audit builders
 * read. Deterministic, local, no network.
 *
 *   node format-seller-reports.mjs <input.json> <out.csv>
 *   node format-seller-reports.mjs --self-test
 *
 * SQP  -> the 12 headers build_sqp_workbook.py reads via csv.DictReader.
 * Business -> the "Detail Page Sales and Traffic by Child ASIN" headers
 *             analyze_audit.py:parse_business_report reads (with its fallbacks).
 *
 * Column mapping is by SEMANTIC keyword match against each source column's id/label,
 * so it survives Amazon's exact column-id spellings. If a required target column is
 * unmatched the tool exits non-zero and lists the source columns it saw — a one-line
 * mapping tweak, never a silent wrong file.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const SQP_HEADERS = [
  "Reporting Date", "Search Query", "ASIN", "Search Query Volume",
  "Impressions: Total Count", "Impressions: ASIN Count",
  "Clicks: Total Count", "Clicks: ASIN Count",
  "Cart Adds: Total Count", "Cart Adds: ASIN Count",
  "Purchases: Total Count", "Purchases: ASIN Count",
];

// Business Report headers analyze_audit.py recognizes (primary spellings).
const BR_HEADERS = [
  "(Parent) ASIN", "(Child) ASIN", "Title", "SKU", "Sessions - Total",
  "Session Percentage - Total", "Page Views - Total", "Featured Offer (Buy Box) Percentage",
  "Units Ordered", "Unit Session Percentage", "Ordered Product Sales", "Total Order Items",
];

// keyword tests (lowercased) against a source column's id+label, most specific first
const SQP_MATCH = [
  ["Search Query Volume", (s) => /search.?query.?volume|\bsv\b|volume/.test(s) && !/rank/.test(s)],
  ["Search Query", (s) => /search.?query|search.?term/.test(s) && !/volume|rank|score/.test(s)],
  ["ASIN", (s) => /\basin\b/.test(s) && !/count|share/.test(s)],
  ["Impressions: ASIN Count", (s) => /impression/.test(s) && /asin/.test(s)],
  ["Impressions: Total Count", (s) => /impression/.test(s) && /total/.test(s)],
  ["Clicks: ASIN Count", (s) => /click/.test(s) && /asin/.test(s)],
  ["Clicks: Total Count", (s) => /click/.test(s) && /total/.test(s)],
  ["Cart Adds: ASIN Count", (s) => /cart.?add/.test(s) && /asin/.test(s)],
  ["Cart Adds: Total Count", (s) => /cart.?add/.test(s) && /total/.test(s)],
  ["Purchases: ASIN Count", (s) => /purchase/.test(s) && /asin/.test(s)],
  ["Purchases: Total Count", (s) => /purchase/.test(s) && /total/.test(s)],
];

const BR_MATCH = [
  ["(Parent) ASIN", (s) => /parent/.test(s) && /asin|item/.test(s)],
  ["(Child) ASIN", (s) => /child/.test(s) && /asin|item/.test(s)],
  ["SKU", (s) => /\bsku\b/.test(s)],
  ["Title", (s) => /title/.test(s)],
  ["Sessions - Total", (s) => /session/.test(s) && /total/.test(s) && !/percent/.test(s)],
  ["Session Percentage - Total", (s) => /session/.test(s) && /percent/.test(s) && /total/.test(s)],
  ["Page Views - Total", (s) => /page.?view/.test(s) && /total/.test(s) && !/percent/.test(s)],
  ["Featured Offer (Buy Box) Percentage", (s) => /buy.?box|featured.?offer/.test(s)],
  ["Units Ordered", (s) => /unit/.test(s) && /order/.test(s) && !/session|percent|item/.test(s)],
  ["Unit Session Percentage", (s) => /unit.?session.?percent/.test(s)],
  ["Ordered Product Sales", (s) => /order.*product.*sales|ordered.?product.?sales/.test(s)],
  ["Total Order Items", (s) => /order.?item/.test(s)],
];

// Exact source-column-id -> target-header maps (verified against Amazon's report
// API). Applied before the semantic fallback so mapping is deterministic.
const SQP_EXACT = {
  "qp-asin-query": "Search Query",
  "qp-asin-query-volume": "Search Query Volume",
  "qp-asin-impressions": "Impressions: Total Count",
  "qp-asin-count-impressions": "Impressions: ASIN Count",
  "qp-asin-clicks": "Clicks: Total Count",
  "qp-asin-count-clicks": "Clicks: ASIN Count",
  "qp-asin-cart-adds": "Cart Adds: Total Count",
  "qp-asin-count-cart-adds": "Cart Adds: ASIN Count",
  "qp-asin-purchases": "Purchases: Total Count",
  "qp-asin-count-purchases": "Purchases: ASIN Count",
  "asin": "ASIN",
};
const BR_EXACT = {
  "SC_MA_ParentASIN_25990": "(Parent) ASIN",
  "SC_MA_ChildASIN_25991": "(Child) ASIN",
  "sc_mat-ss_colDef_title": "Title",
  "SC_MA_SKU_25959": "SKU",
  "SC_MA_Sessions_Total": "Sessions - Total",
  "SC_MA_SessionPercentage_Total": "Session Percentage - Total",
  "SC_MA_PageViews_Total": "Page Views - Total",
  "SC_MA_BuyBoxPercentage_25956": "Featured Offer (Buy Box) Percentage",
  "SC_MA_UnitsOrdered_40590": "Units Ordered",
  "SC_MA_UnitSessionPercentage_25957": "Unit Session Percentage",
  "SC_MA_OrderedProductSales_40591": "Ordered Product Sales",
  "SC_MA_TotalOrderItems_1": "Total Order Items",
};

// ASIN + Reporting Date come from the batch (Amazon returns neither as a column).
const REQUIRED_SQP = new Set(SQP_HEADERS.filter((h) => h !== "Reporting Date" && h !== "ASIN"));
const REQUIRED_BR = new Set(["(Child) ASIN", "Ordered Product Sales", "Units Ordered",
  "Sessions - Total", "Unit Session Percentage", "Featured Offer (Buy Box) Percentage"]);

function colId(col) {
  if (typeof col === "string") return col;
  // translationKey is the id Business-Report rows are keyed by (SC_MA_*).
  return col.id || col.columnId || col.translationKey || col.key || col.name || "";
}

// The text we keyword-match against. Prefer a human label — the raw ids carry a
// view prefix ("qp-asin-…") whose "asin" would match every column; strip it when
// no label exists.
function colHaystack(col) {
  if (typeof col !== "string") {
    const label = col.label || col.displayName || col.title;
    if (label) return String(label).toLowerCase();
  }
  return String(colId(col)).toLowerCase().replace(/^(qp-(asin|brand|scp)-|sc_ma_|tst-)/, "");
}

function colKey(col) {
  if (typeof col === "string") return col;
  return [col.id, col.columnId, col.key, col.name, col.label, col.displayName]
    .filter(Boolean).join(" ");
}

function buildMap(columns, rules, exact) {
  // { targetHeader: sourceColumnId } — exact id map first, semantic fallback second.
  const map = {};
  const ids = columns.map(colId);
  if (exact) {
    for (const id of ids) if (exact[id]) map[exact[id]] = id;
  }
  const hay = columns.map(colHaystack);
  for (const [target, test] of rules) {
    if (map[target]) continue;
    for (let i = 0; i < hay.length; i++) {
      if (test(hay[i])) { map[target] = ids[i]; break; }
    }
  }
  return map;
}

function num(v) {
  if (v === null || v === undefined) return "";
  if (typeof v === "number") return String(v);
  const s = String(v).replace(/[,%$€£]/g, "").trim();
  return s === "" || s === "-" || s === "—" ? "" : (isNaN(Number(s)) ? String(v) : s);
}

function csvCell(v) {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function toCsv(headers, rows) {
  const lines = [headers.map(csvCell).join(",")];
  for (const r of rows) lines.push(headers.map((h) => csvCell(r[h] ?? "")).join(","));
  return lines.join("\n") + "\n";
}

// Rows may arrive keyed by column id with no separate columns array (SQP). Fall
// back to the union of row keys so the id maps still resolve.
function columnsFrom(doc) {
  const cols = doc.columns || [];
  if (cols.length) return cols;
  const seen = new Set();
  for (const b of doc.batches || []) for (const r of b.rows || []) for (const k in r) seen.add(k);
  return [...seen];
}

function formatSqp(doc) {
  const cols = columnsFrom(doc);
  const map = buildMap(cols, SQP_MATCH, SQP_EXACT);
  const missing = [...REQUIRED_SQP].filter((h) => !map[h]);
  if (missing.length) {
    fail("SQP: could not map required columns " + JSON.stringify(missing) +
      "\n  source columns seen: " + cols.map(colKey).join(" | "));
  }
  const out = [];
  for (const batch of doc.batches || []) {
    for (const row of batch.rows || []) {
      const rec = { "Reporting Date": batch.reportingDate || "" };
      for (const h of SQP_HEADERS) {
        if (h === "Reporting Date") continue;
        const src = map[h];
        const raw = src ? row[src] : "";
        rec[h] = (h === "Search Query" || h === "ASIN") ? (raw ?? "") : num(raw);
      }
      if (!rec["ASIN"]) rec["ASIN"] = batch.asin || "";
      out.push(rec);
    }
  }
  return toCsv(SQP_HEADERS, out);
}

function formatBusiness(doc) {
  const cols = columnsFrom(doc);
  const map = buildMap(cols, BR_MATCH, BR_EXACT);
  const missing = [...REQUIRED_BR].filter((h) => !map[h]);
  if (missing.length) {
    fail("Business: could not map required columns " + JSON.stringify(missing) +
      "\n  source columns seen: " + cols.map(colKey).join(" | "));
  }
  const rows = (doc.batches && doc.batches[0] && doc.batches[0].rows) || [];
  const out = rows.map((row) => {
    const rec = {};
    for (const h of BR_HEADERS) {
      const src = map[h];
      const raw = src ? row[src] : "";
      const textCol = /ASIN|Title|SKU/.test(h);
      rec[h] = textCol ? (raw ?? "") : num(raw);
    }
    return rec;
  });
  return toCsv(BR_HEADERS, out);
}

export function format(doc) {
  if (doc.error) fail("input JSON carries an error from the fetch: " + doc.error);
  if (doc.report === "sqp") return formatSqp(doc);
  if (doc.report === "business") return formatBusiness(doc);
  fail('unknown report type: ' + JSON.stringify(doc.report));
}

function fail(msg) { console.error("ERROR: " + msg); process.exit(1); }

// ---------------------------------------------------------------- self-test
function selfTest() {
  const sqp = {
    report: "sqp", marketplace: "US",
    columns: [
      { id: "qp-asin-search-query", label: "Search Query" },
      { id: "qp-asin-search-query-volume", label: "Search Query Volume" },
      { id: "qp-asin-asin", label: "ASIN" },
      { id: "qp-asin-impressions-total-count", label: "Impressions: Total Count" },
      { id: "qp-asin-impressions-asin-count", label: "Impressions: ASIN Count" },
      { id: "qp-asin-clicks-total-count", label: "Clicks: Total Count" },
      { id: "qp-asin-clicks-asin-count", label: "Clicks: ASIN Count" },
      { id: "qp-asin-cart-adds-total-count", label: "Cart Adds: Total Count" },
      { id: "qp-asin-cart-adds-asin-count", label: "Cart Adds: ASIN Count" },
      { id: "qp-asin-purchases-total-count", label: "Purchases: Total Count" },
      { id: "qp-asin-purchases-asin-count", label: "Purchases: ASIN Count" },
    ],
    batches: [{
      asin: "B0TEST00001", reportingDate: "2026-06-28",
      rows: [{
        "qp-asin-search-query": "manuka balm", "qp-asin-search-query-volume": "1,234",
        "qp-asin-asin": "B0TEST00001",
        "qp-asin-impressions-total-count": "10000", "qp-asin-impressions-asin-count": "800",
        "qp-asin-clicks-total-count": "500", "qp-asin-clicks-asin-count": "40",
        "qp-asin-cart-adds-total-count": "60", "qp-asin-cart-adds-asin-count": "5",
        "qp-asin-purchases-total-count": "30", "qp-asin-purchases-asin-count": "3",
      }],
    }],
  };
  const br = {
    report: "business",
    columns: [
      { id: "SC_MA_ParentASIN_25990", label: "(Parent) ASIN" },
      { id: "SC_MA_ChildASIN_25991", label: "(Child) ASIN" },
      { id: "SC_MA_Title_00001", label: "Title" },
      { id: "SC_MA_SKU_25959", label: "SKU" },
      { id: "SC_MA_SessionsTotal_00010", label: "Sessions - Total" },
      { id: "SC_MA_SessionPctTotal_00011", label: "Session Percentage - Total" },
      { id: "SC_MA_PageViewsTotal_00012", label: "Page Views - Total" },
      { id: "SC_MA_BuyBoxPct_00013", label: "Featured Offer (Buy Box) Percentage" },
      { id: "SC_MA_UnitsOrdered_00014", label: "Units Ordered" },
      { id: "SC_MA_UnitSessionPct_00015", label: "Unit Session Percentage" },
      { id: "SC_MA_OrderedProductSales_40591", label: "Ordered Product Sales" },
      { id: "SC_MA_TotalOrderItems_00016", label: "Total Order Items" },
    ],
    batches: [{
      rows: [[
        "B0PARENT001", "B0TEST00001", "Test Manuka Balm 55g", "SKU-1",
        "1,200", "48.0%", "1,500", "92.0%", "80", "6.67%", "$1,999.00", "78",
      ]],
    }],
  };
  // remap br rows: array-form is zipped by _rfNormalizeRow in the browser; here we
  // emulate that the fetcher already normalized to objects.
  const brObj = { ...br, batches: [{ rows: [Object.fromEntries(br.columns.map((c, i) => [c.id, br.batches[0].rows[0][i]]))] }] };

  const sqpCsv = formatSqp(sqp);
  const brCsv = formatBusiness(brObj);

  const sqpHeader = sqpCsv.split("\n")[0];
  const expectSqp = SQP_HEADERS.join(",");
  assert(sqpHeader === expectSqp, "SQP header mismatch:\n  got:  " + sqpHeader + "\n  want: " + expectSqp);
  const sqpRow = sqpCsv.split("\n")[1];
  assert(sqpRow === "2026-06-28,manuka balm,B0TEST00001,1234,10000,800,500,40,60,5,30,3", "SQP row mismatch: " + sqpRow);

  const brHeader = brCsv.split("\n")[0];
  assert(brHeader === BR_HEADERS.join(","), "BR header mismatch: " + brHeader);
  const brRow = brCsv.split("\n")[1];
  assert(/B0TEST00001/.test(brRow) && /1999.00/.test(brRow) && /Test Manuka Balm 55g/.test(brRow),
    "BR row mismatch: " + brRow);

  console.log("self-test OK — SQP 12/12 headers + row parity; Business headers + row parity");
}

function assert(cond, msg) { if (!cond) fail("self-test: " + msg); }

// ---------------------------------------------------------------- main
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args[0] === "--self-test") {
    selfTest();
  } else if (args.length === 2) {
    const doc = JSON.parse(readFileSync(args[0], "utf8"));
    const csv = format(doc);
    writeFileSync(args[1], csv);
    const n = csv.split("\n").filter((l) => l.trim()).length - 1;
    console.log(`wrote ${args[1]} (${n} rows, ${doc.report})`);
  } else {
    console.error("usage: node format-seller-reports.mjs <input.json> <out.csv>\n   or: node format-seller-reports.mjs --self-test");
    process.exit(2);
  }
}

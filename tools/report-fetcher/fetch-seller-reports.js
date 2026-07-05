/*
 * Browser-side Seller Central report fetcher — Business Reports + Search Query
 * Performance (SQP). Original code; no third-party source is reused.
 *
 * HOW IT WORKS
 *   Runs inside the operator's ALREADY logged-in sellercentral.amazon.* tab via a
 *   connected/internal-browser `evaluate` call. Because it runs in the page origin,
 *   the report POSTs are same-origin: the browser attaches the login cookies, Origin
 *   and Referer automatically. The only extra header the Brand-Analytics API needs is
 *   `anti-csrftoken-a2z`, which we read from the page's OWN <meta> tag (the value the
 *   page itself uses for its own requests). We never read cookies, localStorage,
 *   sessionStorage, passwords, bearer/refresh tokens, or any credential; we never log
 *   in. Report JSON is returned to the caller and never sent anywhere else.
 *
 * SAFETY
 *   Connected/internal browser only — never headless (Amazon blocks bots). Read-only:
 *   these endpoints only READ reports. ~5 s spacing between requests (mirrors real
 *   usage). If there is no active session (network error / 403 / missing token) the
 *   function returns an { error } object and changes nothing — the agent then stops
 *   and asks the operator to open/refresh the Brand Analytics tab.
 *
 * EXECUTION PATHS (same as extract-amazon-listing-copy.js)
 *   A) Codex / Playwright — pass the source as a string that defines + calls the fn:
 *        await tab.playwright.evaluate(`(function(){\n${src}\nreturn fetchSqp(${json});\n})()`)
 *   B) DevTools / injected — window.amazonAgentFetchSqp(params) /
 *        window.amazonAgentFetchBusinessReport(params)
 *
 * Returns (both):
 *   { schemaVersion:"amazon-agent.seller-report.v1", report, marketplace, capturedAt,
 *     columns:[...], batches:[{asin?, reportingRange?, reportingDate?, rows:[...]}], error? }
 *   Rows are normalized to flat { columnId: value } objects regardless of the raw
 *   array-vs-object shape, so the local formatter maps columns → CSV deterministically.
 */

function _rfSleep(ms) {
  return new Promise(function (r) { setTimeout(r, ms); });
}

// ~5 s with jitter, so a multi-request pull reads like a person clicking around.
function _rfPace() {
  return _rfSleep(4750 + Math.floor(Math.random() * 500));
}

function _rfCsrfToken() {
  var el = document.querySelector('meta[name="anti-csrftoken-a2z"]');
  return el ? el.getAttribute("content") : "";
}

// Normalize one report row to { columnId: value }. Handles object rows
// (keyed by column id) and positional array rows (zipped with columnIds).
function _rfNormalizeRow(row, columnIds) {
  if (Array.isArray(row)) {
    var out = {};
    for (var i = 0; i < columnIds.length; i++) out[columnIds[i]] = row[i];
    return out;
  }
  if (row && typeof row === "object") {
    // some responses wrap the value as {value:...} / {displayValue:...}
    var flat = {};
    for (var k in row) {
      if (!Object.prototype.hasOwnProperty.call(row, k)) continue;
      var v = row[k];
      if (v && typeof v === "object" && ("value" in v || "displayValue" in v)) {
        flat[k] = "value" in v ? v.value : v.displayValue;
      } else {
        flat[k] = v;
      }
    }
    return flat;
  }
  return {};
}

function _rfColumnIds(section) {
  var cols = (section && (section.columns || section.headers)) || [];
  return cols.map(function (c) {
    if (typeof c === "string") return c;
    // translationKey is the id Business-Report rows are keyed/aligned by (SC_MA_*).
    return c.id || c.columnId || c.translationKey || c.key || c.name || "";
  });
}

// Resolve fetch from whatever global the evaluate context exposes. Some
// connected-browser evaluate worlds don't bind a bare `fetch` identifier.
function _rfFetch() {
  var g = (typeof globalThis !== "undefined" && globalThis) ||
          (typeof self !== "undefined" && self) ||
          (typeof window !== "undefined" && window) || null;
  var f = g && g.fetch;
  return typeof f === "function" ? f.bind(g) : null;
}

// XHR transport — present in every real page/isolated context; the fallback
// when the eval world doesn't expose fetch. Returns {status, text}.
function _rfXhrPost(url, headers, body) {
  return new Promise(function (resolve, reject) {
    var X = (typeof XMLHttpRequest !== "undefined") ? XMLHttpRequest :
            (typeof globalThis !== "undefined" && globalThis.XMLHttpRequest) || null;
    if (!X) { reject(new Error("no fetch and no XMLHttpRequest in this context")); return; }
    var xhr = new X();
    xhr.open("POST", url, true);
    xhr.withCredentials = true;               // same-origin session cookies
    for (var k in headers) if (Object.prototype.hasOwnProperty.call(headers, k)) xhr.setRequestHeader(k, headers[k]);
    xhr.onload = function () { resolve({ status: xhr.status, text: xhr.responseText }); };
    xhr.onerror = function () { reject(new Error("XHR network error")); };
    xhr.send(body);
  });
}

async function _rfPost(url, payload, useCsrf) {
  var headers = { "Content-Type": "application/json", "Accept": "application/json" };
  if (useCsrf) {
    var t = _rfCsrfToken();
    if (!t) return { __error: "missing anti-csrftoken-a2z meta tag — open the Brand Analytics dashboard tab and retry" };
    headers["anti-csrftoken-a2z"] = t;
  }
  var body = JSON.stringify(payload);
  var status, text;
  var f = _rfFetch();
  try {
    if (f) {
      var res = await f(url, { method: "POST", credentials: "include", headers: headers, body: body });
      status = res.status;
      text = await res.text();
    } else {
      var xr = await _rfXhrPost(url, headers, body);   // fetch unavailable in this eval world
      status = xr.status; text = xr.text;
    }
  } catch (e) {
    return { __error: "request transport failed (no active session, or evaluate context blocks network): " + String(e) };
  }
  if (status === 401 || status === 403) {
    return { __error: "not authorized (" + status + ") — session logged out or wrong account/marketplace" };
  }
  if (status < 200 || status >= 300) return { __error: "request failed with HTTP " + status };
  try { return { data: JSON.parse(text) }; }
  catch (e) { return { __error: "response was not JSON — likely a login redirect" }; }
}

// Brand-Analytics range filters for a reporting range + period-END date (YYYY-MM-DD).
// Verified identical for SQP / SCP / TST. Weekly = one filter; monthly/quarterly add a
// year companion. Returns an array to spread into filterSelections.
function _rfRangeFilters(range, periodEnd) {
  var yyyy = String(periodEnd).slice(0, 4);
  if (range === "monthly") {
    return [{ id: "monthly-year", value: yyyy, valueType: null },
            { id: yyyy + "-month", value: periodEnd, valueType: "monthly" }];
  }
  if (range === "quarterly") {
    return [{ id: "quarterly-year", value: yyyy, valueType: null },
            { id: yyyy + "-quarter", value: periodEnd, valueType: "quarterly" }];
  }
  return [{ id: "weekly-week", value: periodEnd, valueType: "weekly" }];
}

// Generic Brand-Analytics dashboard fetch (SQP/SCP/TST share the shape): loop each
// period, page to ceil(totalItems/100), collect reportsV2[0].rows. `extraFilters`
// are prepended (asin/brand/etc). Returns { columns, batches:[{reportingDate, rows}] }.
async function _rfDashboardFetch(url, range, mp, periodEndDates, reportId, viewId, sortByColumnId, ascending, extraFilters) {
  var out = { columns: [], batches: [] };
  var first = true;
  for (var pi = 0; pi < periodEndDates.length; pi++) {
    var periodEnd = periodEndDates[pi];
    var rows = [];
    var page = 1;
    while (true) {
      if (!first) await _rfPace();
      first = false;
      var payload = {
        filterSelections: (extraFilters || []).concat(
          [{ id: "reporting-range", value: range, valueType: null }],
          _rfRangeFilters(range, periodEnd)),
        reportId: reportId,
        reportOperations: [{ ascending: ascending, pageNumber: page, pageSize: 100,
          reportId: reportId, reportType: "TABLE", sortByColumnId: sortByColumnId }],
        selectedCountries: [mp],
        viewId: viewId
      };
      var r = await _rfPost(url, payload, true);
      if (r.__error) { out.error = r.__error; return out; }
      var section = (((r.data || {}).data || {}).reportsV2 || [])[0] || (r.data.reportsV2 || [])[0] || {};
      var colIds = _rfColumnIds(section);
      if (colIds.length && !out.columns.length) out.columns = section.columns || section.headers || colIds;
      var raw = section.rows || [];
      for (var i = 0; i < raw.length; i++) rows.push(_rfNormalizeRow(raw[i], colIds));
      var total = section.totalItems || section.totalRows || null;
      if (raw.length < 100 || (total !== null && page * 100 >= total)) break;
      page += 1;
    }
    out.batches.push({ reportingRange: range, reportingDate: periodEnd, rows: rows });
  }
  return out;
}

// ---------------------------------------------------------------- SQP
// params: { asins:[...], marketplace:"us", reportingRange:"weekly"|"monthly"|"quarterly",
//           periodEndDates:["YYYY-MM-DD", ...] }  (dates are period-END, LA time)
// Payload verified against Amazon's report API (reconciled to the manual UI export).
async function fetchSqp(params) {
  var base = location.origin;
  var url = base + "/api/brand-analytics/v1/dashboard/query-performance/reports";
  var range = (params.reportingRange || "weekly").toLowerCase();
  var mp = (params.marketplace || "us").toLowerCase();       // lowercase country code
  var out = {
    schemaVersion: "amazon-agent.seller-report.v1", report: "sqp",
    marketplace: mp, reportingRange: range,
    capturedAt: new Date().toISOString(), columns: [], batches: []
  };
  // one single-ASIN pass per ASIN → uncapped SV (better than Amazon's multi-ASIN grid)
  for (var ai = 0; ai < params.asins.length; ai++) {
    var asin = params.asins[ai];
    var res = await _rfDashboardFetch(url, range, mp, params.periodEndDates,
      "query-performance-asin-report-table", "query-performance-asin-view",
      "qp-asin-query-rank", true, [{ id: "asin", value: asin, valueType: "ASIN" }]);
    if (res.error) { out.error = res.error; return out; }
    if (!out.columns.length) out.columns = res.columns;
    for (var bi = 0; bi < res.batches.length; bi++) {
      out.batches.push({ asin: asin, reportingRange: range,
        reportingDate: res.batches[bi].reportingDate, rows: res.batches[bi].rows });
    }
  }
  return out;
}

// ---------------------------------------------------------------- SCP (Brand Catalog Performance)
// params: { marketplace:"us", reportingRange, periodEndDates:[...], asins?:[...], brand?:"<brand id>" }
async function fetchScp(params) {
  var base = location.origin;
  var url = base + "/api/brand-analytics/v1/dashboard/brand-catalog-performance/reports";
  var range = (params.reportingRange || "weekly").toLowerCase();
  var mp = (params.marketplace || "us").toLowerCase();
  var extra = [];
  if (params.brand) extra.push({ id: "brand", value: params.brand, valueType: null });
  if (params.asins && params.asins.length) extra.push({ id: "asins", value: params.asins.join(","), valueType: "ASIN" });
  var res = await _rfDashboardFetch(url, range, mp, params.periodEndDates,
    "brand-catalog-performance-report-table", "brand-catalog-performance-default-view",
    "impressions-count", false, extra);
  return Object.assign({ schemaVersion: "amazon-agent.seller-report.v1", report: "scp",
    marketplace: mp, reportingRange: range, capturedAt: new Date().toISOString() }, res);
}

// ---------------------------------------------------------------- TST (Top Search Terms)
// params: { marketplace:"us", reportingRange, periodEndDates:[...], asins?:[...], brand?, searchTerm? }
async function fetchTst(params) {
  var base = location.origin;
  var url = base + "/api/brand-analytics/v1/dashboard/top-search-terms/reports";
  var range = (params.reportingRange || "weekly").toLowerCase();
  var mp = (params.marketplace || "us").toLowerCase();
  var extra = [];
  if (params.asins && params.asins.length) extra.push({ id: "asins", value: params.asins.join(","), valueType: "ASIN" });
  if (params.brand) extra.push({ id: "brand-freeform", value: params.brand, valueType: "BRAND" });
  if (params.searchTerm) extra.push({ id: "search-term-freeform", value: params.searchTerm, valueType: "SEARCH_TERM" });
  var res = await _rfDashboardFetch(url, range, mp, params.periodEndDates,
    "top-search-terms-report-table", "top-search-terms-default-view",
    "st-search-frequency", true, extra);
  return Object.assign({ schemaVersion: "amazon-agent.seller-report.v1", report: "tst",
    marketplace: mp, reportingRange: range, capturedAt: new Date().toISOString() }, res);
}

// ------------------------------------------------------- Business Reports
// params: { legacyReportId, asins?, startDate:"YYYY-MM-DD", endDate:"YYYY-MM-DD",
//           granularity:"DAY"|"WEEK"|"MONTH" }
// legacyReportId: "102:DetailSalesTrafficByChildItem" (child ASIN — default),
//   "102:DetailSalesTrafficByParentItem", "102:DetailSalesTrafficBySKU",
//   "102:SalesTrafficTimeSeries" (by date).
async function fetchBusinessReport(params) {
  var base = location.origin;
  var url = base + "/business-reports/api";
  // `columns` needs a sub-selection (it is an object type); `rows` is a scalar
  // (positional arrays). Query + input verified against Amazon's API.
  var query = "query reportDataQuery($input:GetReportDataInput){getReportData(input:$input){" +
    "granularity hadPrevious hasNext size startDate endDate page " +
    "columns{label valueFormat isGraphable translationKey isDefaultSortAscending " +
    "isDefaultGraphed isDefaultSelected isDefaultSortColumn __typename} rows __typename}}";
  var out = {
    schemaVersion: "amazon-agent.seller-report.v1", report: "business",
    legacyReportId: params.legacyReportId || "102:DetailSalesTrafficByChildItem",
    capturedAt: new Date().toISOString(), columns: [], batches: [{ rows: [] }]
  };
  var page = 0, first = true;   // Business Reports page counter is 0-indexed
  while (true) {
    if (!first) await _rfPace();
    first = false;
    var input = {
      asins: params.asins || [],
      startDate: params.startDate, endDate: params.endDate,
      legacyReportId: params.legacyReportId || "102:DetailSalesTrafficByChildItem",
      page: page
    };
    // Same-origin: Origin/Referer are set by the browser; no CSRF header needed here.
    var r = await _rfPost(url, { operationName: "reportDataQuery", query: query, variables: { input: input } }, false);
    if (r.__error) { out.error = r.__error; return out; }
    var section = ((r.data || {}).data || {}).getReportData || {};
    var colIds = _rfColumnIds(section);
    if (colIds.length && !out.columns.length) out.columns = section.columns || colIds;
    var raw = section.rows || [];
    for (var i = 0; i < raw.length; i++) out.batches[0].rows.push(_rfNormalizeRow(raw[i], colIds));
    if (!section.hasNext) break;
    page += 1;
  }
  return out;
}

try {
  window.amazonAgentFetchSqp = fetchSqp;
  window.amazonAgentFetchBusinessReport = fetchBusinessReport;
  window.amazonAgentFetchScp = fetchScp;
  window.amazonAgentFetchTst = fetchTst;
} catch (e) { /* non-extensible window in some evaluate contexts — path A is used instead */ }

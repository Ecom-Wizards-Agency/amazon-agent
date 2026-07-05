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

// ---------------------------------------------------------------- SQP
// params: { asins:[...], marketplace:"us", reportingRange:"weekly"|"monthly",
//           periodEndDates:["YYYY-MM-DD", ...] }  (dates are period-END Saturday, LA time)
// Payload verified against Amazon's report API (reconciled to the manual UI export).
async function fetchSqp(params) {
  var base = location.origin;
  var url = base + "/api/brand-analytics/v1/dashboard/query-performance/reports";
  var range = (params.reportingRange || "weekly").toLowerCase();
  var mp = (params.marketplace || "us").toLowerCase();       // lowercase country code
  var rangeIdByRange = { weekly: "weekly-week", monthly: "monthly-month", quarterly: "quarterly-quarter" };
  var out = {
    schemaVersion: "amazon-agent.seller-report.v1", report: "sqp",
    marketplace: mp, reportingRange: range,
    capturedAt: new Date().toISOString(), columns: [], batches: []
  };
  var first = true;
  for (var ai = 0; ai < params.asins.length; ai++) {
    var asin = params.asins[ai];
    for (var pi = 0; pi < params.periodEndDates.length; pi++) {
      var periodEnd = params.periodEndDates[pi];
      var rows = [];
      var page = 1;
      while (true) {
        if (!first) await _rfPace();
        first = false;
        var payload = {
          filterSelections: [
            { id: "asin", value: asin, valueType: "ASIN" },
            { id: "reporting-range", value: range, valueType: null },
            { id: rangeIdByRange[range], value: periodEnd, valueType: range }
          ],
          reportId: "query-performance-asin-report-table",
          reportOperations: [{
            ascending: true, pageNumber: page, pageSize: 100,
            reportId: "query-performance-asin-report-table", reportType: "TABLE",
            sortByColumnId: "qp-asin-query-rank"
          }],
          selectedCountries: [mp],
          viewId: "query-performance-asin-view"
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
      out.batches.push({ asin: asin, reportingRange: range, reportingDate: periodEnd, rows: rows });
    }
  }
  return out;
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
} catch (e) { /* non-extensible window in some evaluate contexts — path A is used instead */ }

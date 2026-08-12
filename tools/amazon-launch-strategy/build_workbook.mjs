import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [modelPath, outputPath, previewDir] = process.argv.slice(2);
if (!modelPath || !outputPath || !previewDir) {
  throw new Error("Usage: node build_workbook.mjs <model.json> <output.xlsx> <preview-dir>");
}

const model = JSON.parse(await fs.readFile(modelPath, "utf8"));
const config = model.generated_from;
const commercial = model.commercial;
if (!commercial) throw new Error("The executive workbook requires commercial_targets in the launch config.");

const currency = config.client.currency;
const money0 = currency === "USD" ? "$#,##0" : `${currency} #,##0`;
const money2 = currency === "USD" ? "$#,##0.00" : `${currency} #,##0.00`;
const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const logoData = await fs.readFile(path.join(repoRoot, "tools/amazon-ad-audit/brand/logo_black.png"));
const logoDataUrl = `data:image/png;base64,${logoData.toString("base64")}`;

const COLORS = {
  obsidian: "#0F1318", slate: "#1E242C", coral: "#FD4807", cloud: "#F5F6F8",
  hairline: "#E3E7ED", white: "#FFFFFF", ink: "#1E242C", mist: "#9AA5B4",
  green: "#0B6E4F", amber: "#A15C00",
};

function colName(index) {
  let n = index + 1;
  let result = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    result = String.fromCharCode(65 + rem) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

function usedRangeAddress(rows, cols) {
  return `A1:${colName(cols - 1)}${rows}`;
}

function applyGlobal(sheet) {
  sheet.showGridLines = false;
  sheet.getRange("A1:Z200").format.font = { name: "Aptos", size: 10, color: COLORS.ink };
}

function addBrandHeader(sheet, title, subtitle, lastCol) {
  sheet.mergeCells("A1:B2");
  sheet.mergeCells(`C1:${lastCol}1`);
  sheet.mergeCells(`C2:${lastCol}2`);
  sheet.getRange(`A1:${lastCol}2`).format = {
    fill: COLORS.white,
    borders: { bottom: { style: "medium", color: COLORS.coral } },
    verticalAlignment: "center",
  };
  sheet.getRange(`C1:${lastCol}1`).values = [[title]];
  sheet.getRange(`C1:${lastCol}1`).format = { font: { name: "Aptos Display", size: 20, bold: true, color: COLORS.obsidian } };
  sheet.getRange(`C2:${lastCol}2`).values = [[subtitle]];
  sheet.getRange(`C2:${lastCol}2`).format = { font: { name: "Aptos", size: 9, color: COLORS.mist } };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeightPx = 30;
  sheet.getRange(`A2:${lastCol}2`).format.rowHeightPx = 24;
  sheet.images.add({ dataUrl: logoDataUrl, anchor: { from: { row: 0, col: 0 }, extent: { widthPx: 145, heightPx: 34 } } });
}

function setWidths(sheet, widths) {
  widths.forEach((width, index) => { sheet.getRangeByIndexes(0, index, 1, 1).format.columnWidthPx = width; });
}

function styleTable(sheet, headerRow, lastRow, lastCol) {
  sheet.getRange(`A${headerRow}:${lastCol}${headerRow}`).format = {
    fill: COLORS.obsidian,
    font: { name: "Aptos", size: 9, bold: true, color: COLORS.white },
    wrapText: true,
    verticalAlignment: "center",
    borders: { bottom: { style: "medium", color: COLORS.coral } },
    rowHeightPx: 30,
  };
  if (lastRow <= headerRow) return;
  sheet.getRange(`A${headerRow + 1}:${lastCol}${lastRow}`).format = {
    verticalAlignment: "center",
    wrapText: true,
    borders: { insideHorizontal: { style: "thin", color: COLORS.hairline } },
  };
  for (let row = headerRow + 2; row <= lastRow; row += 2) sheet.getRange(`A${row}:${lastCol}${row}`).format.fill = COLORS.cloud;
}

function sectionBar(sheet, range, label) {
  sheet.mergeCells(range);
  sheet.getRange(range).values = [[label]];
  sheet.getRange(range).format = { fill: COLORS.slate, font: { bold: true, color: COLORS.white }, rowHeightPx: 24 };
}

const workbook = Workbook.create();
const exec = workbook.worksheets.add("Executive Summary");
const inputs = workbook.worksheets.add("Inputs & Sources");
const forecast = workbook.worksheets.add("13-Week Forecast");
const ppc = workbook.worksheets.add("PPC Plan");
const pricing = workbook.worksheets.add("Pricing & Margin");
const stock = workbook.worksheets.add("Stock & Reviews");
for (const sheet of [exec, inputs, forecast, ppc, pricing, stock]) applyGlobal(sheet);

// Executive Summary
addBrandHeader(exec, `${config.client.brand} | 90-Day Amazon Launch Strategy`, `${config.client.account} | ${config.client.marketplace} | ${config.client.launch_timing_label} | ${model.validation.status}`, "H");
exec.mergeCells("A4:H4");
exec.getRange("A4:H4").values = [["OBJECTIVE: Exit Month 1 at $300/day, reach $1,000/day by the end of Month 2, maintain $1,000/day in Month 3, and unlock $2,000/day only through the stretch gates."]];
exec.getRange("A4:H4").format = { fill: "#FFF4E5", font: { bold: true, color: COLORS.amber }, wrapText: true, rowHeightPx: 38 };
exec.getRange("A6:H6").values = [["Path", "13-week sales", "Forecast units", "Customer stock", "Vine units", "Total stock", "Month 3 objective", "Status"]];
const execRows = commercial.summaries.map((item) => [item.path, item.target_revenue, item.forecast_units, item.customer_sale_inventory_required, item.vine_units, item.total_inventory_required, item.month_3_objective, "Operating target"]);
exec.getRangeByIndexes(6, 0, execRows.length, 8).values = execRows;
styleTable(exec, 6, 6 + execRows.length, "H");
exec.getRange("B7:B9").format.numberFormat = money0;
exec.getRange("C7:F9").format.numberFormat = "#,##0";
sectionBar(exec, "A11:H11", "90-day milestones");
exec.getRange("A12:E12").values = [["Period", "Run-rate path", "Target sales", "Planned PPC", "Available ceiling"]];
const committedMonths = commercial.monthly.filter((item) => item.path_id === "committed");
const milestoneRows = committedMonths.map((item) => [item.month, `$${Math.round(item.start_daily_revenue).toLocaleString()}/day to $${Math.round(item.exit_daily_revenue).toLocaleString()}/day`, item.target_revenue, item.planned_ppc, item.ppc_ceiling]);
milestoneRows.push(["Month 3 stretch", "$1,000/day to $2,000/day", 52500, commercial.ppc_plan.month_3_stretch.planned_spend, commercial.ppc_plan.month_3_stretch.spend_ceiling]);
exec.getRangeByIndexes(11, 0, milestoneRows.length + 1, 5).values = [["Period", "Run-rate path", "Target sales", "Planned PPC", "Available ceiling"], ...milestoneRows];
styleTable(exec, 12, 12 + milestoneRows.length, "E");
exec.getRange(`C13:E${12 + milestoneRows.length}`).format.numberFormat = money0;
exec.mergeCells("A19:H19");
exec.getRange("A19:H19").values = [["Scaling rule: ceilings are available funding, not forced spend. Release the next step only when relevance, conversion, margin visibility, and stock coverage support it."]];
exec.getRange("A19:H19").format = { fill: COLORS.cloud, font: { bold: true }, wrapText: true, rowHeightPx: 42 };
setWidths(exec, [145, 130, 115, 110, 90, 100, 190, 130]);
exec.freezePanes.freezeRows(6);

// Inputs & Sources
addBrandHeader(inputs, "Inputs & Sources", "Confirmed facts, editable targets, and open confirmations", "H");
const inputHeaders = ["Group", "Field", "Scope", "Value", "Status", "Source", "Locator", "Notes"];
inputs.getRange("A5:H5").values = [inputHeaders];
const inputRows = [];
const milestones = commercial.daily_revenue_milestones;
for (const [field, value] of Object.entries(milestones)) inputRows.push(["Commercial target", field, "Amazon US", value, "Approved objective", "Executive plan", "", "Daily Amazon sales revenue"]);
inputRows.push(["Inventory", "Stock safety buffer", "Launch offers", commercial.stock_safety_buffer_pct, "Approved assumption", "Executive plan", "", "Added above forecast customer sales"]);
for (const item of committedMonths) inputRows.push(["Product mix", item.month, "Starter / Refill", `${Math.round(item.product_mix["starter-kit"] * 100)}% / ${Math.round(item.product_mix["refill-pouch"] * 100)}%`, "Approved assumption", "Executive plan", "", "Editable"]);
for (const [planId, plan] of Object.entries(commercial.ppc_plan)) inputRows.push(["PPC", plan.label, "Amazon US", `${plan.planned_spend} planned / ${plan.spend_ceiling} ceiling`, "Approved objective", "Executive plan", "", "Ceiling is available funding, not forced spend"]);
inputRows.push(["Baseline", "Current revenue", config.client.marketplace, config.baseline.current_revenue ?? "", config.baseline.current_revenue === null ? "Open" : "Confirmed", "Client actuals", "", ""]);
inputRows.push(["Baseline", "Orders by product", config.client.marketplace, config.baseline.orders_by_product ? JSON.stringify(config.baseline.orders_by_product) : "", config.baseline.orders_by_product ? "Confirmed" : "Open", "Client actuals", "", ""]);
for (const [field, label] of [["current_meta_spend", "Current Meta spend"], ["current_google_spend", "Current Google spend"], ["branded_search_contribution", "Branded-search contribution"], ["planned_launch_support", "Planned launch support"]]) inputRows.push(["External", label, "Amazon US", config.external_channels[field] ?? "", config.external_channels[field] === null ? "Open" : "Confirmed", "External-channel input", "", "Halo remains zero until evidence is supplied"]);
for (const product of config.products.filter((item) => item.phase === "launch")) {
  const econ = product.unit_economics;
  const inv = product.inventory;
  inputRows.push(["Pricing", "Launch price", product.name, product.launch_price, "Confirmed", "Approved offer", "", ""]);
  for (const [field, label] of [["landed_cogs", "Landed COGS"], ["amazon_fees", "Amazon fees"], ["other_variable_costs", "Other variable costs"], ["discount_floor", "Discount floor"]]) inputRows.push(["Economics", label, product.name, econ[field] ?? "", econ[field] === null ? "Open" : "Confirmed", "Finance input", "", ""]);
  inputRows.push(["Inventory", "Opening stock", product.name, inv.opening_stock ?? "", inv.opening_stock === null ? "Open" : "Confirmed", "Seller Central / 3PL", "", ""]);
  inputRows.push(["Inventory", "Inbound stock", product.name, inv.inbound ? JSON.stringify(inv.inbound) : "", inv.inbound === null ? "Open" : "Confirmed", "Seller Central / 3PL", "", ""]);
  inputRows.push(["Inventory", "MOQ and lead times", product.name, inv.moq ?? "", inv.moq === null ? "Open" : "Confirmed", "Supply plan", "", JSON.stringify(inv.lead_times)]);
  inputRows.push(["Reviews", "Vine eligibility", product.name, product.reviews.vine_eligible ?? "", product.reviews.vine_eligible === null ? "Open" : "Confirmed", "Amazon Vine", "https://sell.amazon.com/programs/vine", "Confirmed units are added above customer stock"]);
}
for (const source of config.sources) inputRows.push(["Source", source.name, config.client.brand, source.freshness ?? "", source.status, source.type, source.locator, source.notes ?? ""]);
inputs.getRangeByIndexes(5, 0, inputRows.length, 8).values = inputRows;
styleTable(inputs, 5, 5 + inputRows.length, "H");
inputs.getRange(`E6:E${5 + inputRows.length}`).conditionalFormats.addCustom(`=$E6="Open"`, { fill: "#FFF4E5", font: { color: COLORS.amber, bold: true } });
setWidths(inputs, [115, 160, 150, 150, 105, 150, 300, 260]);
inputs.freezePanes.freezeRows(5);

// 13-Week Forecast
addBrandHeader(forecast, "13-Week Forecast", "Commercial target paths by week and launch configuration", "J");
const forecastHeaders = ["Path", "Week", "Month", "Product", "Mix", "Price", "Target revenue", "Forecast units", "External halo", "Inventory note"];
forecast.getRange("A5:J5").values = [forecastHeaders];
const forecastRows = commercial.weekly.map((row) => [row.path, row.week, row.month, row.product, row.mix, row.effective_price, "", row.forecast_units, row.external_halo_units, "Stock position open until actual inventory is confirmed"]);
forecast.getRangeByIndexes(5, 0, forecastRows.length, 10).values = forecastRows;
for (let index = 0; index < forecastRows.length; index += 1) {
  const row = index + 6;
  forecast.getRange(`G${row}`).formulas = [[`=F${row}*H${row}`]];
}
const forecastLast = 5 + forecastRows.length;
styleTable(forecast, 5, forecastLast, "J");
forecast.getRange(`E6:E${forecastLast}`).format.numberFormat = "0%";
forecast.getRange(`F6:G${forecastLast}`).format.numberFormat = money2;
forecast.getRange(`H6:I${forecastLast}`).format.numberFormat = "#,##0.0";
setWidths(forecast, [120, 60, 80, 190, 70, 90, 110, 105, 100, 280]);
forecast.freezePanes.freezeRows(5);

// PPC Plan
addBrandHeader(ppc, "PPC Plan", "Planned spend, available ceilings, campaign purpose, and approved targeting direction", "J");
const ppcHeaders = ["Period", "Planned spend", "Ceiling", "Planning CPC", "Planning CVR", "Spend-supported ad units", "Target units", "Required non-ad units", "External halo", "Control"];
ppc.getRange("A5:J5").values = [ppcHeaders];
const ppcRows = [
  commercial.monthly.find((item) => item.path_id === "committed" && item.month_id === "month_1"),
  commercial.monthly.find((item) => item.path_id === "committed" && item.month_id === "month_2"),
  commercial.monthly.find((item) => item.path_id === "committed" && item.month_id === "month_3"),
  commercial.monthly.find((item) => item.path_id === "stretch" && item.month_id === "month_3"),
].map((item) => [item.path_id === "stretch" ? "Month 3 stretch" : `${item.month}${item.month_id === "month_3" ? " committed" : ""}`, item.planned_ppc, item.ppc_ceiling, commercial.ppc_plan[item.month_id === "month_3" ? (item.path_id === "stretch" ? "month_3_stretch" : "month_3_committed") : item.month_id].planning_cpc, commercial.ppc_plan[item.month_id === "month_3" ? (item.path_id === "stretch" ? "month_3_stretch" : "month_3_committed") : item.month_id].planning_cvr, item.spend_supported_ad_units ?? "", item.required_units, item.required_non_ad_units ?? "", 0, "Ceiling is not forced spend"]);
ppc.getRangeByIndexes(5, 0, ppcRows.length, 10).values = ppcRows;
styleTable(ppc, 5, 5 + ppcRows.length, "J");
ppc.getRange("B6:D9").format.numberFormat = money2;
ppc.getRange("E6:E9").format.numberFormat = "0.0%";
ppc.getRange("F6:I9").format.numberFormat = "#,##0.0";
sectionBar(ppc, "A12:J12", "Campaign-purpose allocation");
ppc.getRange("A13:F13").values = [["Period", "Core non-brand", "Discovery", "Competitor KW", "Competitor PT", "Brand defense"]];
const allocRows = Object.values(commercial.ppc_plan).map((plan) => [plan.label, plan.campaign_allocation.high_intent_non_branded, plan.campaign_allocation.discovery, plan.campaign_allocation.competitor_keywords, plan.campaign_allocation.competitor_product_targeting, plan.campaign_allocation.branded_defense]);
ppc.getRangeByIndexes(13, 0, allocRows.length, 6).values = allocRows;
styleTable(ppc, 13, 13 + allocRows.length, "F");
ppc.getRange("B14:F17").format.numberFormat = "0%";
sectionBar(ppc, "A20:J20", "Approved keyword direction");
const keywordRows = [
  ["Core", commercial.keywords.core.join(", ")],
  ["Discovery", commercial.keywords.discovery.join(", ")],
  ["Competitors", commercial.keywords.competitors.join(", ")],
  ["Controlled test", `${commercial.keywords.controlled_tests.join(", ")}. ${commercial.keywords.controlled_test_guardrail}`],
];
for (let row = 21; row <= 24; row += 1) ppc.mergeCells(`B${row}:J${row}`);
ppc.getRange("A21:B24").values = keywordRows;
ppc.getRange("A21:A24").format.font = { bold: true, color: COLORS.slate };
ppc.getRange("A21:J24").format.wrapText = true;
ppc.getRange("A21:J24").format.rowHeightPx = 38;
setWidths(ppc, [145, 120, 110, 105, 95, 130, 105, 130, 95, 220]);
ppc.freezePanes.freezeRows(5);

// Pricing & Margin
addBrandHeader(pricing, "Pricing & Margin", "Confirmed prices. Unknown economics remain open and break-even ACOS is not fabricated.", "I");
pricing.getRange("A5:I5").values = [["Offer", "Phase", "List price", "Launch price", "Discount", "Landed COGS", "Amazon fees", "Pre-ad contribution", "Break-even ACOS"]];
const pricingRows = model.pricing_summary.map((item) => {
  const product = config.products.find((candidate) => candidate.id === item.product_id);
  return [item.product, item.phase, item.list_price ?? "", item.launch_price ?? "", item.discount_pct ?? "", product.unit_economics?.landed_cogs ?? "", product.unit_economics?.amazon_fees ?? "", item.contribution_per_unit_before_ads ?? "", item.break_even_acos ?? ""];
});
pricing.getRangeByIndexes(5, 0, pricingRows.length, 9).values = pricingRows;
styleTable(pricing, 5, 5 + pricingRows.length, "I");
pricing.getRange(`C6:D${5 + pricingRows.length}`).format.numberFormat = money2;
pricing.getRange(`E6:E${5 + pricingRows.length}`).format.numberFormat = "0.0%";
pricing.getRange(`F6:H${5 + pricingRows.length}`).format.numberFormat = money2;
pricing.getRange(`I6:I${5 + pricingRows.length}`).format.numberFormat = "0.0%";
pricing.mergeCells(`A${8 + pricingRows.length}:I${8 + pricingRows.length}`);
pricing.getRange(`A${8 + pricingRows.length}:I${8 + pricingRows.length}`).values = [["Pricing rule: keep the confirmed $104.99 Starter Kit and $99.99 Refill Pouch prices until landed COGS, Amazon fees, contribution margin, and discount floor are confirmed."]];
pricing.getRange(`A${8 + pricingRows.length}:I${8 + pricingRows.length}`).format = { fill: COLORS.cloud, font: { bold: true }, wrapText: true, rowHeightPx: 45 };
setWidths(pricing, [185, 100, 110, 110, 90, 110, 110, 140, 125]);
pricing.freezePanes.freezeRows(5);

// Stock & Reviews
addBrandHeader(stock, "Stock & Reviews", "Customer-sale requirement, 20% buffer, Vine allocation, and policy controls", "J");
stock.getRange("A5:J5").values = [["Path", "Offer", "Forecast sales", "Customer stock", "Vine units", "Total required", "Opening stock", "Inbound", "Lead time", "Coverage status"]];
const launchProducts = Object.fromEntries(config.products.filter((item) => item.phase === "launch").map((item) => [item.id, item]));
const stockRows = [];
for (const summary of commercial.summaries) {
  for (const [productId, units] of Object.entries(summary.product_units)) {
    const product = launchProducts[productId];
    stockRows.push([summary.path, product.name, units, summary.customer_stock_by_product[productId], product.reviews.vine_units, summary.total_stock_by_product[productId], product.inventory.opening_stock ?? "", product.inventory.inbound ? JSON.stringify(product.inventory.inbound) : "", Object.values(product.inventory.lead_times).every((value) => value !== null) ? Object.values(product.inventory.lead_times).reduce((sum, value) => sum + value, 0) : "", "Open until actual stock and inbound are confirmed"]);
  }
}
stock.getRangeByIndexes(5, 0, stockRows.length, 10).values = stockRows;
styleTable(stock, 5, 5 + stockRows.length, "J");
stock.getRange(`C6:I${5 + stockRows.length}`).format.numberFormat = "#,##0";
sectionBar(stock, "A14:J14", "Review policy controls");
stock.getRange("A15:F15").values = [["Review path", "Enabled", "Policy status", "Limit", "Deduplication", "Notes"]];
const helium = config.reviews.helium10_follow_up;
const reviewRows = [
  ["Amazon Vine", config.reviews.vine.enabled ? "Yes" : "Conditional", "Eligibility open", "Approved allocation", "N/A", "Add confirmed units above customer-sale stock"],
  ["Request a Review", config.reviews.request_a_review.enabled ? "Yes" : "No", "Allowed", "One standard request", "Required", "Amazon standard flow"],
  ["Helium 10 Follow-Up", helium.enabled ? "Yes" : "No", model.review_policy.status, helium.max_requests_per_order, helium.deduplicate_with_seller_central ? "Yes" : "Required", "Amazon standard template only"],
  ["Incentives, gating, or disguised compensation", "No", "PROHIBITED", "N/A", "N/A", "Validation fails if configured"],
];
stock.getRange("A16:F19").values = reviewRows;
styleTable(stock, 15, 19, "F");
stock.mergeCells("A22:J22");
stock.getRange("A22:J22").values = [["External halo is zero until explicit evidence or an editable assumption is provided. Vine eligibility, actual inventory, inbound stock, MOQ, and lead times remain open."]];
stock.getRange("A22:J22").format = { fill: COLORS.cloud, font: { bold: true }, wrapText: true, rowHeightPx: 42 };
setWidths(stock, [115, 185, 105, 110, 90, 105, 100, 130, 105, 245]);
stock.freezePanes.freezeRows(5);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const formulaErrors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "launch strategy formula error scan", maxChars: 10000 });
const renderTargets = [
  ["Executive Summary", usedRangeAddress(19, 8), "executive-summary", 0.9],
  ["Inputs & Sources", usedRangeAddress(5 + inputRows.length, 8), "inputs-sources", 0.7],
  ["13-Week Forecast", usedRangeAddress(forecastLast, 10), "13-week-forecast", 0.7],
  ["PPC Plan", usedRangeAddress(24, 10), "ppc-plan", 0.8],
  ["Pricing & Margin", usedRangeAddress(8 + pricingRows.length, 9), "pricing-margin", 0.9],
  ["Stock & Reviews", usedRangeAddress(22, 10), "stock-reviews", 0.8],
];
const rendered = [];
for (const [sheetName, range, stem, scale] of renderTargets) {
  const preview = await workbook.render({ sheetName, range, scale, format: "png" });
  const destination = path.join(previewDir, `${stem}.png`);
  await fs.writeFile(destination, new Uint8Array(await preview.arrayBuffer()));
  rendered.push({ sheetName, range, destination });
}
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
const inspect = await workbook.inspect({ kind: "workbook,sheet", include: "id,name", maxChars: 10000 });
await fs.writeFile(path.join(previewDir, "workbook-inspect.ndjson"), inspect.ndjson, "utf8");
await fs.writeFile(path.join(previewDir, "formula-errors.ndjson"), formulaErrors.ndjson, "utf8");
await fs.writeFile(path.join(previewDir, "render-manifest.json"), JSON.stringify(rendered, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ outputPath, previewDir, rendered, formulaErrors: formulaErrors.ndjson }, null, 2));

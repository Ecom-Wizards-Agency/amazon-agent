// Send to Amazon adapter: saved case-pack templates, own-carrier SPD and thermal
// labels. Selectors come from the attended STA workflow captured in September
// 2026. New UI variants fail closed; this adapter requires a scoped live canary.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const MARKETS = { US: ["https://sellercentral.amazon.com", "United States"],
  AU: ["https://sellercentral.amazon.com.au", "Australia"],
  AUS: ["https://sellercentral.amazon.com.au", "Australia"],
  CA: ["https://sellercentral.amazon.ca", "Canada"],
  UK: ["https://sellercentral.amazon.co.uk", "United Kingdom"],
  GB: ["https://sellercentral.amazon.co.uk", "United Kingdom"] };
const sha256 = value => createHash("sha256").update(value).digest("hex");
const now = () => new Date().toISOString();
const norm = value => String(value || "").replace(/\s+/g, " ").trim().toLowerCase();
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const positive = n => Number.isFinite(n) && n > 0;
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);

export function validateShipment(envelope) {
  const plan = envelope?.plan, shipment = plan?.body?.shipment, limits = plan?.body?.limits;
  assert(envelope?.schema_version === 1 && plan?.schema_version === 1 && plan.operation === "shipment.create", "invalid shipment envelope");
  assert(/^[a-f0-9]{64}$/.test(envelope.plan_hash || ""), "plan hash is required");
  assert(shipment && limits && plan.account?.seller_id && plan.account?.marketplace_id && plan.account?.seller_central_name,
    "shipment and stable seller/marketplace identity are required");
  assert(MARKETS[plan.account.marketplace], "this marketplace's STA UI has no canary-supported adapter");
  const missing = ["ship_date", "ship_mode", "carrier_mode", "packing_templates", "label_format"]
    .filter(key => shipment[key] == null || shipment[key] === "");
  assert(!missing.length, `required_inputs: ${missing.join(", ")}`);
  assert(shipment.ship_mode === "SPD" && shipment.carrier_mode === "non_partnered",
    "only own-carrier small-parcel delivery is supported by the observed STA adapter");
  assert(shipment.label_format === "thermal_4x6", "only thermal_4x6 labels are supported");
  assert(/^\d{4}-\d{2}-\d{2}$/.test(shipment.ship_date) && Number.isFinite(Date.parse(shipment.ship_date)) &&
    new Date(shipment.ship_date).toISOString().slice(0,10) === shipment.ship_date, "ship_date must be an ISO calendar date");
  assert(equal(limits.account, plan.account) && shipment.currency === limits.currency && limits.carriers?.includes(shipment.carrier), "shipment exceeds account/carrier/currency authority");
  assert(Number.isFinite(limits.max_cost) && limits.max_cost >= 0 && Number.isFinite(shipment.estimated_cost) && shipment.estimated_cost >= 0 && shipment.estimated_cost <= limits.max_cost, "invalid or excessive shipment cost");
  assert(shipment.shipment_reference && ["address_line1", "city", "postal_code", "country"].every(key => shipment.ship_from?.[key]), "shipment reference and complete ship-from address required");
  const quantities = {}, packing = {}, cartonIds = new Set();
  assert(Array.isArray(shipment.lines) && shipment.lines.length, "shipment lines required");
  for (const line of shipment.lines) {
    assert(line.sku && !Object.hasOwn(quantities, line.sku) && Number.isInteger(line.quantity) && line.quantity > 0, "invalid or duplicate shipment line");
    quantities[line.sku] = line.quantity;
  }
  assert(equal(Object.keys(quantities).sort(), [...plan.targets].sort()), "shipment target mismatch");
  assert(Object.values(quantities).reduce((a, b) => a + b, 0) <= limits.max_units, "shipment exceeds unit limit");
  assert(Array.isArray(shipment.cartons) && shipment.cartons.length, "cartons required");
  for (const carton of shipment.cartons) {
    assert(carton.id && !cartonIds.has(carton.id), "duplicate carton ID");
    cartonIds.add(carton.id);
    const skus = Object.keys(carton.contents || {});
    assert(skus.length === 1 && Object.hasOwn(quantities, skus[0]), "mixed-SKU cartons require a separately validated packing adapter");
    const sku = skus[0], qty = carton.contents[sku], template = shipment.packing_templates[sku];
    assert(template?.name && Number.isInteger(template.units_per_box) && template.units_per_box === qty && qty > 0, `packing template quantities do not match ${sku}`);
    assert(positive(carton.weight) && carton.weight === template.weight && carton.weight_unit === template.weight_unit &&
      ["kg", "lb"].includes(carton.weight_unit) && Array.isArray(carton.dimensions) && carton.dimensions.length === 3 && carton.dimensions.every(positive) &&
      equal(carton.dimensions, template.dimensions) && carton.dimension_unit === template.dimension_unit && ["cm", "in"].includes(carton.dimension_unit), `packing template dimensions/weight do not match ${sku}`);
    packing[sku] ||= { boxes: 0, units: 0, template };
    packing[sku].boxes++; packing[sku].units += qty;
  }
  for (const [sku, qty] of Object.entries(quantities)) assert(packing[sku]?.units === qty, `carton coverage differs for ${sku}`);
  return { plan, shipment, limits, quantities, packing };
}

export function validateQuote(quote, context) {
  const { shipment, limits } = context;
  assert(quote && quote.carrier === shipment.carrier && quote.ship_date === shipment.ship_date &&
    quote.ship_mode === shipment.ship_mode && quote.carrier_mode === shipment.carrier_mode, "final shipping terms differ from request");
  assert(quote.currency === shipment.currency && Number.isFinite(quote.actual_cost) && quote.actual_cost >= 0 && quote.actual_cost <= limits.max_cost, "final shipping cost/currency is unknown or exceeds saved limit");
  assert(quote.boxes === shipment.cartons.length && quote.units === Object.values(context.quantities).reduce((a, b) => a + b, 0), "final shipment counts differ");
  assert(Array.isArray(quote.destinations) && quote.destinations.length && new Set(quote.destinations).size === quote.destinations.length, "destinations are missing or ambiguous");
  if (shipment.allowed_destinations) assert(quote.destinations.every(id => shipment.allowed_destinations.includes(id)), "destination is outside requested placement scope");
  if (shipment.placement) assert(quote.placement === shipment.placement, "placement differs from request");
  return quote;
}

export function writeReceipt(filename, value, { exclusive = false } = {}) {
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  if (exclusive) {
    const fd = fs.openSync(filename, "wx", 0o600);
    try { fs.writeFileSync(fd, JSON.stringify(value)); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  } else {
    const tmp = filename + `.tmp-${process.pid}`;
    const fd = fs.openSync(tmp, "wx", 0o600);
    try { fs.writeFileSync(fd, JSON.stringify(value)); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    fs.renameSync(tmp, filename);
  }
  const dir = fs.openSync(path.dirname(filename), "r");
  try { fs.fsyncSync(dir); } finally { fs.closeSync(dir); }
}

export async function executeShipment(envelope, ui, save) {
  const context = validateShipment(envelope);
  let record = { schema_version: 1, plan_hash: envelope.plan_hash, status: "blocked", phase: "preflight", updated_at: now() };
  const persist = changes => { record = { ...record, ...changes, updated_at: now() }; save(record); return record; };
  let committed = false;
  const commit = async (phase, action) => {
    await ui.assertIdentity();
    persist({ status: "uncertain", phase, reason: "submission_attempt_started" });
    committed = true;
    return action();
  };
  try {
    await ui.open(context);
    await ui.assertIdentity();
    const workflowId = await commit("creating_workflow", () => ui.createWorkflow());
    assert(/^wf[a-zA-Z0-9-]+$/.test(workflowId), "workflow ID was not captured");
    persist({ workflow_id: workflowId, submission_id: workflowId, phase: "preparing_content" });
    await ui.prepareContent(context, workflowId);
    await ui.verifyContent(context, workflowId);
    await commit("confirming_content", () => ui.confirmContent());
    const quote = validateQuote(await ui.prepareShipping(context), context);
    persist({ phase: "shipping_prepared", quote });
    await ui.assertIdentity();
    const final = validateQuote(await ui.readQuote(context), context);
    assert(equal(final, quote), "shipping terms changed after preparation");
    await commit("confirming_shipping", () => ui.confirmShipping());
    const confirmed = await ui.readConfirmed(context, workflowId);
    assert(confirmed.workflow_id === workflowId && confirmed.shipment_ids?.length &&
      confirmed.shipment_ids.every(id => /^FBA[A-Z0-9]+$/.test(id)) && new Set(confirmed.shipment_ids).size === confirmed.shipment_ids.length,
      "confirmed shipment IDs are missing or inconsistent");
    persist({ status: "processing", phase: "downloading_labels", submission_ids: confirmed.shipment_ids, reason: "awaiting_label_verification" });
    await ui.assertIdentity();
    const labels = await ui.downloadLabels(context, confirmed);
    assert(labels.length === context.shipment.cartons.length &&
      equal(labels.map(item => item.carton_id).sort(), context.shipment.cartons.map(item => item.id).sort()) &&
      labels.every(item => confirmed.shipment_ids.includes(item.shipment_id)), "label carton coverage differs from request");
    const evidence = { account: context.plan.account, plan_hash: envelope.plan_hash,
      source_id: confirmed.url, observed_at: now(), processing_status: "complete",
      submission_id: workflowId, submission_ids: confirmed.shipment_ids,
      shipment_reference: context.shipment.shipment_reference, carrier: quote.carrier,
      currency: quote.currency, actual_cost: quote.actual_cost, quantities: context.quantities,
      labels, workflow_id: workflowId, shipping_quote: quote };
    return persist({ status: "processing", phase: "evidence_ready", reason: "independent_reconciliation_required", evidence });
  } catch (error) {
    return persist({ status: committed ? "uncertain" : "blocked", reason: String(error.message || error), phase: record.phase });
  } finally { await ui.close().catch(() => {}); }
}

export class StaBrowser {
  constructor(envelope) { this.envelope = envelope; this.directory = path.dirname(envelope.receipt_path); }
  async open(context) {
    this.context = context;
    [this.origin, this.marketplaceLabel] = MARKETS[context.plan.account.marketplace];
    const cdp = await import("../report-fetcher/cdp.mjs");
    const account = await import("../report-fetcher/sc-account.mjs");
    const tasks = await import("../browserctl/task-tabs.mjs");
    this.evaluate = cdp.evaluate; this.readIdentity = account.readIdentity;
    this.clickAt = account.trustedClick; this.release = tasks.releaseTaskPage;
    this.page = await tasks.acquireTaskPage({ port: Number(process.env.CDP_PORT || 9222),
      taskId: `amazon-operation:${context.plan.operation_id}`, slot: "primary", workflow: "amazon-logistics",
      initialUrl: this.origin + "/home", exclusiveContext: true, allowOperatorActivity: true });
    this.session = this.page.session;
    await account.switchAccount(this.session, this.origin, { accountName: context.plan.account.seller_central_name,
      marketplaceLabel: this.marketplaceLabel }, { returnTo: "/fba/sendtoamazon" });
    // Verify PDF tooling before creating anything externally.
    for (const command of ["pdfinfo", "pdftotext"]) execFileSync(command, ["-v"], { stdio: "pipe" });
  }
  ev(expression) { return this.evaluate(this.session, expression, 20000); }
  async wait(fn, label, attempts = 60) {
    for (let i = 0; i < attempts; i++) { const result = await fn(); if (result) return result; await new Promise(r => setTimeout(r, 1000)); }
    throw new Error(`timed out waiting for ${label}; reconcile before retrying`);
  }
  async assertIdentity() {
    const identity = await this.readIdentity(this.session);
    const account = this.context.plan.account;
    assert(identity?.merchantId === account.seller_id && identity?.marketplace === account.marketplace_id,
      "live stable seller/marketplace identity is unavailable or mismatched");
    const url = await this.ev("location.href");
    assert(new URL(url).origin === this.origin, "Seller Central origin changed");
  }
  async click(selector, label) {
    await this.clickAt(this.session, `(() => { const nodes = [...document.querySelectorAll(${JSON.stringify(selector)})]
      .filter(e => e.getBoundingClientRect().width > 0 && !e.hasAttribute('disabled'));
      if (nodes.length !== 1) return null; const e=nodes[0]; e.scrollIntoView({block:'center'});
      const r=e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}; })()`, label);
  }
  async createWorkflow() {
    const previous = await this.ev('new URL(location.href).searchParams.get("wf")');
    await this.click('[data-testid="start-new-link"]', "Start new workflow");
    await this.wait(() => this.ev('!!document.querySelector(\'[data-testid="start-new-button"]\')'), "new workflow confirmation");
    await this.click('[data-testid="start-new-button"]', "Confirm new workflow");
    return this.wait(async () => { const id = await this.ev('new URL(location.href).searchParams.get("wf")');
      return id && id !== previous ? id : null; }, "new workflow ID");
  }
  row(sku) {
    return `(() => { const links=[...document.querySelectorAll('[data-testid="sku-central-link"]')]
      .filter(a => new URL(a.getAttribute('href'),location.origin).searchParams.get('mSku') === ${JSON.stringify(sku)});
      return links.length === 1 ? links[0].closest('[data-testid="sku-row-information-details"]') : null; })()`;
  }
  async setField(selector, value, root = "document") {
    const result = await this.ev(`(() => { const root=${root}; if(!root)return false;
      const hosts=[...root.querySelectorAll(${JSON.stringify(selector)})]; if(hosts.length!==1)return false;
      let input=hosts[0]; for(let i=0;i<4&&!input.matches('input');i++)input=input.shadowRoot?.querySelector('input,kat-input')||input.querySelector('input');
      if(!input||input.disabled)return false; input.focus();
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(String(value))});
      input.dispatchEvent(new Event('input',{bubbles:true,composed:true})); input.dispatchEvent(new Event('change',{bubbles:true,composed:true})); input.blur();
      return input.value===${JSON.stringify(String(value))}; })()`);
    assert(result, `required input unavailable or ambiguous: ${selector}`);
  }
  async prepareContent(context, workflowId) {
    await this.wait(() => this.ev('!!document.querySelector(\'[data-testid="step1-continue"]\')'), "content step");
    const agl = await this.ev(`(() => { const hosts=[...document.querySelectorAll('kat-checkbox')].filter(e=>
      /Amazon Global Logistics/i.test([e.getAttribute('label'),e.getAttribute('aria-label'),e.innerText].join(' ')));
      if(hosts.length>1)return -1; if(!hosts.length)return 0; const e=hosts[0];
      if(e.hasAttribute('checked')||e.shadowRoot?.querySelector('input')?.checked)e.click();return 1; })()`);
    assert(agl >= 0, "Amazon Global Logistics control is ambiguous");
    for (const [sku, packing] of Object.entries(context.packing)) {
      let row = await this.ev(`!!(${this.row(sku)})`);
      if (!row) {
        await this.setField('input[type="search"],kat-input[type="search"]', sku);
        await this.wait(() => this.ev(`!!(${this.row(sku)})`), `requested SKU ${sku}`);
      }
      const text = await this.ev(`(${this.row(sku)})?.innerText || ''`);
      assert(norm(text).includes(norm(packing.template.name)), `selected saved packing template differs for ${sku}`);
      const unitsPerBox = text.match(/Units per box:\s*([\d,]+)/i)?.[1]?.replaceAll(",", "");
      assert(Number(unitsPerBox) === packing.template.units_per_box, `saved packing units differ for ${sku}`);
      // The plan's saved template must agree with the current Amazon template,
      // including physical dimensions. Missing collapsed details need a canary
      // selector update, not an assumption that the saved name implies the specs.
      const dimensions = text.match(/(?:Dimensions|Box dimensions)\s*:?\s*([\d.]+)\s*[x×]\s*([\d.]+)\s*[x×]\s*([\d.]+)\s*(cm|in)\b/i);
      const weight = text.match(/(?:Weight|Box weight)\s*:?\s*([\d.]+)\s*(kg|lb)\b/i);
      assert(dimensions && equal(dimensions.slice(1,4).map(Number),packing.template.dimensions) &&
        dimensions[4].toLowerCase()===packing.template.dimension_unit && weight &&
        Number(weight[1])===packing.template.weight && weight[2].toLowerCase()===packing.template.weight_unit,
        `live packing-template dimensions/weight are unavailable or differ for ${sku}`);
      await this.setField('[data-testid="sku-readiness-number-of-boxes-input"]', packing.boxes, this.row(sku));
      const hasExpiry = await this.ev(`!!(${this.row(sku)})?.querySelector('[data-testid="skureadiness-date-picker"]')`);
      if (hasExpiry) {
        assert(packing.template.expiration_date, `required_inputs: packing_templates.${sku}.expiration_date`);
        await this.setField('[data-testid="skureadiness-date-picker"]', packing.template.expiration_date, this.row(sku));
      }
      await this.assertIdentity();
      const committed = await this.ev(`(() => { const row=${this.row(sku)}; const host=row?.querySelector('[data-testid="skureadiness-confirm-button"]');
        const button=host?.shadowRoot?.querySelector('button')||host;
        if(!host||host.hasAttribute('disabled')||button.disabled)return false;button.click();return true; })()`);
      assert(committed, `Ready to send is unavailable for ${sku}`);
      await this.wait(() => this.ev(`(() => {const text=(${this.row(sku)})?.innerText||'';
        const boxes=text.match(/Boxes:\\s*([\\d,]+)/)?.[1]?.replaceAll(',','');
        const units=text.match(/Units:\\s*([\\d,]+)/)?.[1]?.replaceAll(',','');
        return Number(boxes)===${packing.boxes}&&Number(units)===${packing.units};})()`), `committed quantity for ${sku}`);
    }
  }
  async verifyContent(context, workflowId) {
    const checkpoint = await this.ev(`(() => { const text=(document.body.innerText||'').replace(/\\s+/g,' ');
      const agl=[...document.querySelectorAll('kat-checkbox')].filter(e=>/Amazon Global Logistics/i.test([e.getAttribute('label'),e.innerText].join(' ')));
      const address=[...document.querySelectorAll('[data-testid*="ship-from"]')].map(e=>(e.innerText||'').replace(/\\s+/g,' ')).filter(Boolean);
      return {workflow_id:new URL(location.href).searchParams.get('wf'),text,address,
        agl:agl.some(e=>e.hasAttribute('checked')||e.shadowRoot?.querySelector('input')?.checked)};})()`);
    assert(checkpoint.workflow_id === workflowId && !checkpoint.agl, "workflow/own-carrier freight mismatch");
    const address = context.shipment.ship_from;
    const countryLabel = {US:"United States",AU:"Australia",CA:"Canada",GB:"United Kingdom",UK:"United Kingdom"}[address.country] || address.country;
    assert(checkpoint.address.some(text => [address.address_line1, address.city, address.postal_code, countryLabel].every(part => norm(text).includes(norm(part)))), "ship-from address does not match the request");
    const ready = checkpoint.text.match(/SKUs ready to send:\s*(\d+)\s*\(([\d,]+) units\)/i);
    assert(ready && Number(ready[1]) === Object.keys(context.quantities).length && Number(ready[2].replaceAll(",", "")) === Object.values(context.quantities).reduce((a,b)=>a+b,0), "ready SKU/unit totals differ from plan");
  }
  confirmContent() { return this.click('[data-testid="step1-continue"]', "Confirm shipment contents"); }
  async choose(selector, label) {
    await this.click(selector, "shipping choice");
    await this.clickAt(this.session, `(() => { const host=document.querySelector(${JSON.stringify(selector)});
      const roots=[host?.shadowRoot,document].filter(Boolean); const matches=[];
      for(const root of roots)for(const e of root.querySelectorAll('[role="option"],kat-option,option'))
        if((e.innerText||e.textContent||e.getAttribute('label')||'').trim()===${JSON.stringify(label)}&&e.getBoundingClientRect().width>0)matches.push(e);
      if(matches.length!==1)return null; const r=matches[0].getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`, label);
  }
  async selectLabelFormat(container) {
    await this.clickAt(this.session, `(() => {const root=${container};const e=root?.querySelector('[data-testid="print-label-dropdown"]');
      if(!e)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`, "thermal label format dropdown");
    await this.clickAt(this.session, `(() => {const root=${container};const host=root?.querySelector('[data-testid="print-label-dropdown"]');
      const roots=[host?.shadowRoot,document].filter(Boolean);const matches=[];
      for(const scope of roots)for(const e of scope.querySelectorAll('[role="option"],kat-option,option'))
        if((e.getAttribute('value')||e.getAttribute('data-value'))==='PackageLabel_Thermal_NonPCP'&&e.getBoundingClientRect().width>0)matches.push(e);
      if(matches.length!==1)return null;const r=matches[0].getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`, "Thermal non-partnered box labels");
  }
  async prepareShipping(context) {
    await this.wait(() => this.ev('!!document.querySelector(\'[data-testid="nonpcp-carrier-tile"]\')'), "shipping choices");
    const selected = await this.ev(`(() => {const e=document.querySelector('[data-testid="nonpcp-carrier-tile"]')?.closest('[data-testid="carrier-tile"]');if(!e)return false;e.click();return true;})()`);
    assert(selected, "non-partnered carrier choice is missing");
    await this.choose('[data-testid="non-pcp-carrier-choices"]', context.shipment.carrier);
    await this.setField('[data-testid="kat-ship-date-picker"]', context.shipment.ship_date_ui || context.shipment.ship_date);
    return this.wait(async () => { const quote=await this.readQuote(context); return quote.actual_cost == null ? null : quote; }, "shipping quote");
  }
  async readQuote(context) {
    const state = await this.ev(`(() => { const text=(document.body.innerText||'').replace(/\\s+/g,' ');
      const carrier=document.querySelector('[data-testid="non-pcp-carrier-choices"]');
      const date=document.querySelector('[data-testid="kat-ship-date-picker"]');
      const tile=document.querySelector('[data-testid="nonpcp-carrier-tile"]')?.closest('[data-testid="carrier-tile"]');
      return {text,carrier:carrier?.value||carrier?.getAttribute('value'),carrier_text:(carrier?.shadowRoot?.textContent||carrier?.innerText||'').trim(),
        date:date?.value||date?.getAttribute('value'),non_partnered:!!tile?.classList.contains('selected')};})()`);
    const carrier = context.shipment.carrier;
    assert(norm(state.carrier) === norm(carrier) || norm(state.carrier_text) === norm(carrier), "selected carrier readback differs");
    assert(state.non_partnered && /Small parcel delivery/i.test(state.text), "own-carrier SPD is not selected");
    assert(state.date === context.shipment.ship_date || state.date === context.shipment.ship_date_ui, "ship date readback differs");
    const costs = [...state.text.matchAll(/Total estimated(?: shipping)? (?:charges|fees|cost)\s*:?\s*(USD|AUD|CAD|GBP)\s*\$?\s*([\d,]+(?:\.\d{2})?)/gi)];
    const totalBoxes = state.text.match(/Total boxes\s*:?\s*([\d,]+)/i);
    const totalUnits = state.text.match(/Total units\s*:?\s*([\d,]+)/i);
    const boxes = totalBoxes || state.text.match(/Boxes\s*:?\s*([\d,]+)/i);
    const units = totalUnits || state.text.match(/Units\s*:?\s*([\d,]+)/i);
    const destinations = [...new Set([...state.text.matchAll(/(?:Ship to|Destination|Fulfillment cent(?:er|re))\s*:?\s*([A-Z]{3}\d)\b/g)].map(m=>m[1]))].sort();
    return {carrier,ship_date:context.shipment.ship_date,ship_mode:"SPD",carrier_mode:"non_partnered",
      actual_cost:costs.length===1?Number(costs[0][2].replaceAll(",","")):null,
      currency:costs.length===1?costs[0][1].toUpperCase():null,
      boxes:boxes?Number(boxes[1].replaceAll(",","")):null,units:units?Number(units[1].replaceAll(",","")):null,
      destinations,placement:context.shipment.placement&&state.text.includes(context.shipment.placement)?context.shipment.placement:null};
  }
  confirmShipping() { return this.click('[data-testid="confirm-spd-shipping"]', "Confirm shipping"); }
  async readConfirmed(context, workflowId) {
    return this.wait(async () => {
      const state = await this.ev(`(() => {const text=document.body.innerText||'';
        return {url:location.href,workflow_id:new URL(location.href).searchParams.get('wf'),
          shipment_ids:[...new Set([...text.matchAll(/\\bFBA[A-Z0-9]{8,}(?![A-Z0-9])/g)].map(m=>m[0].replace(/U\\d{6}$/,'')))],
          labels:document.querySelectorAll('[data-testid="print-box-labels-button"]').length};})()`);
      return state.workflow_id===workflowId&&state.shipment_ids.length&&state.labels?state:null;
    }, "created shipments and labels", 180);
  }
  async downloadLabels(context, confirmed) {
    const downloads = path.join(this.directory, "shipment-labels"); fs.mkdirSync(downloads, { recursive: true });
    await this.session.send("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: downloads, eventsEnabled: true }, { timeoutMs: 10000 });
    const outputs = [];
    for (const id of confirmed.shipment_ids) {
      await this.assertIdentity();
      // Anchor both controls to the exact shipment ID, never dropdown proximity.
      const container = `(() => { const buttons=[...document.querySelectorAll('[data-testid="print-box-labels-button"]')];
        const matches=[];for(const button of buttons){let e=button.parentElement;while(e&&e!==document.body){
          const ids=[...new Set([...(e.innerText||'').matchAll(/\\bFBA[A-Z0-9]{8,}/g)].map(m=>m[0]))];
          if(ids.length===1&&ids[0]===${JSON.stringify(id)}&&e.querySelectorAll('[data-testid="print-box-labels-button"]').length===1){matches.push(e);break;}e=e.parentElement;}}
        return matches.length===1?matches[0]:null;})()`;
      let format = await this.ev(`(() => {const root=${container};const select=root?.querySelector('[data-testid="print-label-dropdown"]');
        if(!select)return null;return select.value||select.getAttribute('value');})()`);
      if (format !== "PackageLabel_Thermal_NonPCP") {
        await this.selectLabelFormat(container);
        format = await this.ev(`(() => {const root=${container};const select=root?.querySelector('[data-testid="print-label-dropdown"]');return select?.value||select?.getAttribute('value');})()`);
      }
      assert(format === "PackageLabel_Thermal_NonPCP", "requested thermal label format is not selected; do not print another format");
      const before = new Set(fs.readdirSync(downloads));
      await this.clickAt(this.session, `(() => {const root=${container};const e=root?.querySelector('[data-testid="print-box-labels-button"]');
        if(!e||e.hasAttribute('disabled'))return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`, `labels for ${id}`);
      const file = await this.wait(() => {
        const fresh=fs.readdirSync(downloads).filter(name=>!before.has(name));
        if(fresh.some(name=>name.endsWith('.crdownload')))return null;
        const pdfs=fresh.filter(name=>name.toLowerCase().endsWith('.pdf'));
        assert(pdfs.length<=1,"ambiguous label downloads");return pdfs.length===1?path.join(downloads,pdfs[0]):null;
      }, `completed label PDF for ${id}`);
      outputs.push({ shipment_id:id,path:file,sha256:sha256(fs.readFileSync(file)) });
    }
    return verifyLabelPdfs(outputs, context.shipment.cartons);
  }
  async close() { if(this.page)await this.release(this.page,{outcome:"inspection"}); }
}

export function labelPages(text, shipmentId) {
  return text.split("\f").filter(page=>page.trim()).map((page,index) => {
    const ids=[...new Set([...page.matchAll(/\b(FBA[A-Z0-9]+U\d{6})\b/g)].map(m=>m[1]))];
    assert(ids.length===1&&ids[0].startsWith(shipmentId+"U"), "PDF label shipment identity mismatch");
    const sku=page.match(/Single SKU\s+([^\r\n]+)/i)?.[1]?.trim();
    const qty=Number(page.match(/\bQty\s+([\d,]+)/i)?.[1]?.replaceAll(",",""));
    assert(sku&&Number.isInteger(qty)&&qty>0,"PDF label SKU/quantity is missing");
    const destination=page.match(/SHIP TO:[\s\S]{0,300}?\b([A-Z]{3}\d)\b/)?.[1] || null;
    return {amazon_carton_id:ids[0],sku,quantity:qty,page:index+1,destination};
  });
}

export function verifyLabelPdfs(outputs, cartons) {
  const unused=[...cartons], labels=[], seen=new Set();
  for(const output of outputs){
    assert(fs.readFileSync(output.path).subarray(0,5).toString()==="%PDF-","label download is not a PDF");
    const info=execFileSync("pdfinfo",[output.path],{encoding:"utf8"});
    const pages=Number(info.match(/^Pages:\s*(\d+)/m)?.[1]);
    assert(Number.isInteger(pages)&&pages>0,"label PDF page count is missing");
    const sizes=execFileSync("pdfinfo",["-f","1","-l",String(pages),output.path],{encoding:"utf8"});
    const dimensions=[...sizes.matchAll(/(?:Page\s+\d+\s+size|Page size):\s*([\d.]+) x ([\d.]+) pts/g)];
    assert(dimensions.length===pages&&dimensions.every(m=>Math.abs(Math.min(+m[1],+m[2])-288)<3&&Math.abs(Math.max(+m[1],+m[2])-432)<3),"label stock is not thermal 4x6 on every page");
    const text=execFileSync("pdftotext",[output.path,"-"],{encoding:"utf8"});
    const records=labelPages(text,output.shipment_id);
    assert(records.length===pages,"PDF label page count does not match carton records");
    for(const record of records){
      assert(!seen.has(record.amazon_carton_id),"duplicate Amazon carton label");seen.add(record.amazon_carton_id);
      const index=unused.findIndex(carton=>equal(carton.contents,{[record.sku]:record.quantity}));
      assert(index>=0,"label SKU/quantity is outside the requested carton packing plan");
      const [carton]=unused.splice(index,1);
      labels.push({...output,...record,carton_id:carton.id});
    }
  }
  assert(!unused.length,"label PDFs do not cover all requested cartons");
  return labels;
}

export async function main(argv=process.argv.slice(2)) {
  assert(argv.length===2&&argv[0]==="--request","usage: node shipments.mjs --request FILE");
  const requestPath=path.resolve(argv[1]), envelope=JSON.parse(fs.readFileSync(requestPath,"utf8"));
  const receipt=path.resolve(envelope.receipt_path);
  assert(path.dirname(receipt)===path.dirname(requestPath),"receipt must remain beside the operation request");
  const hash=execFileSync("python3",["-c","import hashlib,json,sys; p=json.load(open(sys.argv[1]))['plan']; print(hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest())",requestPath],{encoding:"utf8"}).trim();
  assert(hash===envelope.plan_hash,"operation plan hash mismatch");
  validateShipment(envelope);
  for(const artifact of envelope.plan.artifacts||[])assert(sha256(fs.readFileSync(artifact.path))===artifact.sha256,"prepared artifact changed");
  if(fs.existsSync(receipt)){
    const previous=JSON.parse(fs.readFileSync(receipt,"utf8"));assert(previous.plan_hash===hash,"receipt belongs to another plan");
    return {...previous,reason:previous.reason||"existing_submission_requires_reconciliation"};
  }
  writeReceipt(receipt,{schema_version:1,plan_hash:hash,status:"uncertain",phase:"reserved",updated_at:now()},{exclusive:true});
  return executeShipment(envelope,new StaBrowser(envelope),record=>writeReceipt(receipt,record));
}

if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  console.log = (...values) => console.error(...values);
  let result;
  try{result=await main();}catch(error){
    let planHash=null;try{planHash=JSON.parse(fs.readFileSync(process.argv[3],"utf8")).plan_hash;}catch{}
    result={schema_version:1,plan_hash:planHash,status:"blocked",reason:String(error.message||error)};
  }
  process.stdout.write(JSON.stringify(result)+"\n");
}

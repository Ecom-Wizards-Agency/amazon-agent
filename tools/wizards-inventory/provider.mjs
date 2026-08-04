#!/usr/bin/env node
import { mkdirSync, readFileSync, readdirSync, unlinkSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { aggregateAwd, aggregateFba, classifyAuthPage, combineInventory, parseCsv } from "./lib.mjs";
import { assertAuthPolicy, loadViewOnlyLogin } from "./auth.mjs";

let assertChrome, closePage, createPage, evaluate, listPages, Session;

const HERE = dirname(fileURLToPath(import.meta.url));
const AMAZON_AGENT = resolve(HERE, "../..");
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

function authenticationError(status) {
  const error = new Error(`Seller Central authentication state: ${status}`);
  error.authStatus = status;
  return error;
}

async function inspectAuthState(session, allowedOrigins = []) {
  const page = await evaluate(session, `(()=>({
    url:location.href,
    origin:location.origin,
    body:(document.body?.innerText||"").slice(0,1600),
    hasPassword:!!document.querySelector('input[type="password"],input[name="password"]'),
    hasOtp:!!document.querySelector('input[name="otpCode"],input[name="code"],input[autocomplete="one-time-code"]'),
    hasCaptcha:!!document.querySelector('input[name="guess"],img[src*="captcha"],form[action*="validateCaptcha"]'),
    hasRecovery:!!document.querySelector('form[action*="password"],a[href*="account-recovery"]'),
    hasApproval:!!document.querySelector('[data-a-name*="approval"],form[action*="cvf"]'),
    hasInventoryMarker:!!document.querySelector('meta[name="anti-csrftoken-a2z"]'),
    hasAccountPicker:document.querySelectorAll('button.full-page-account-switcher-account-details').length>0
  }))()`);
  const status = classifyAuthPage(page);
  if (["password_required", "totp_required"].includes(status)
      && allowedOrigins.length && !allowedOrigins.includes(page.origin)) {
    return "human_challenge";
  }
  return status;
}

const FBA_QUERY = `query WizardsInventory($pagination: PaginationInput) {
  listingsV2(pagination: $pagination, usecase: MANAGE_INVENTORY_VIEW,
    multiSelectFilters: [{key: "FULFILLMENT", values: ["AllChannels"]}],
    sortRequest: {key: CREATE_DATE, order: DESCENDING}) {
    listings {
      coreListingFields { asin sku fnSku fulfillmentChannel }
      availability {
        coreListingFields { fulfillmentChannel }
        reserved { fcTransfer customerOrder fcProcessing }
        buyableInTransit quantity unfulfillable inbound onHandQuantity
        researching { shortTerm midTerm longTerm }
      }
    }
    count
    configContext { merchantId marketplaceId }
  }
}`;

function args(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const value = argv[i + 1];
    if (value && !value.startsWith("--")) { out[key] = value; i++; }
    else out[key] = true;
  }
  return out;
}

function isoDate(date) { return date.toISOString().slice(0, 10); }
function reportDate(date) { return isoDate(date).replaceAll("-", "/"); }
function locationForPicker() {
  const returnTo = "/myinventory/inventory";
  return `https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace?returnTo=${encodeURIComponent(returnTo)}`;
}

async function waitFor(session, expression, description, attempts = 80) {
  for (let i = 0; i < attempts; i++) {
    if (await evaluate(session, expression)) return;
    await sleep(250);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

async function trustedClick(session, expression, description) {
  const box = await evaluate(session, expression);
  if (!box || !Number.isFinite(box.x) || !Number.isFinite(box.y)) {
    throw new Error(`Could not find ${description}`);
  }
  for (const type of ["mousePressed", "mouseReleased"]) {
    await session.send("Input.dispatchMouseEvent", {
      type, x: box.x, y: box.y, button: "left", clickCount: 1,
    });
  }
}

async function replaceInput(session, selector, value, description) {
  const expression = `(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;
    e.scrollIntoView({block:"center"});e.focus();const r=e.getBoundingClientRect();
    return{x:r.x+r.width/2,y:r.y+r.height/2}})()`;
  const box = await evaluate(session, expression);
  if (!box) throw new Error(`Could not find ${description}`);
  await trustedClick(session, expression, description);
  await session.send("Input.dispatchKeyEvent", {
    type: "keyDown", key: "a", code: "KeyA", modifiers: 4,
  });
  await session.send("Input.dispatchKeyEvent", {
    type: "keyUp", key: "a", code: "KeyA", modifiers: 4,
  });
  await session.send("Input.insertText", { text: value });
}

async function submitAuthForm(session) {
  await trustedClick(session, `(()=>{const e=document.querySelector('button[type="submit"],input[type="submit"],#signInSubmit,#continue');
    if(!e)return null;e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();
    return{x:r.x+r.width/2,y:r.y+r.height/2}})()`, "authentication submit button");
  await sleep(1200);
}

async function tryServiceAccountLogin(session, config) {
  if (!assertAuthPolicy(config)) return await inspectAuthState(
    session, config.inventory_questions?.allowed_auth_origins || []);
  const allowed = config.inventory_questions?.allowed_auth_origins || [];
  let login;
  for (let step = 0; step < 5; step++) {
    const state = await inspectAuthState(session, allowed);
    if (state === "authenticated" || state === "human_challenge") return state;
    const origin = await evaluate(session, "location.origin");
    if (!allowed.includes(origin)) return "human_challenge";
    if (!login) login = loadViewOnlyLogin(config);
    const hasEmail = await evaluate(session,
      `!!document.querySelector('input[type="email"],input[name="email"],#ap_email,#ap_email_login')`);
    if (hasEmail) {
      await replaceInput(session,
        'input[type="email"],input[name="email"],#ap_email,#ap_email_login',
        login.username, "Amazon login email");
      await submitAuthForm(session);
      continue;
    }
    if (state === "password_required") {
      await replaceInput(session, 'input[type="password"],input[name="password"]',
        login.password, "Amazon login password");
      await submitAuthForm(session);
      continue;
    }
    if (state === "totp_required") {
      const otpLogin = loadViewOnlyLogin(config, { includeOtp: true });
      await replaceInput(session,
        'input[name="otpCode"],input[name="code"],input[autocomplete="one-time-code"]',
        otpLogin.otp, "Amazon one-time password");
      await submitAuthForm(session);
      continue;
    }
    return state;
  }
  return await inspectAuthState(session, allowed);
}

async function selectAccount(session, profile, config) {
  const allowedOrigins = config.inventory_questions?.allowed_auth_origins || [];
  await waitFor(session, `document.readyState === "complete"`, "account picker");
  await waitFor(session, `document.querySelectorAll("button.full-page-account-switcher-account-details").length > 0
    || /signin|auth|mfa|captcha|\/ap\/cvf/.test(location.href)
    || !!document.querySelector('input[type="password"],input[autocomplete="one-time-code"],input[name="guess"]')`,
    "account picker or authentication state", 120);
  let authState = await inspectAuthState(session, allowedOrigins);
  if (authState !== "authenticated" && config.authentication?.enabled) {
    authState = await tryServiceAccountLogin(session, config);
    if (authState === "authenticated") {
      await session.send("Page.enable");
      await session.send("Page.navigate", { url: locationForPicker() });
      await waitFor(session, `document.readyState === "complete"`, "account picker after login", 120);
    }
  }
  if (authState !== "authenticated") throw authenticationError(authState);
  const account = JSON.stringify(profile.account_name);
  const marketplace = JSON.stringify(profile.marketplace_label);
  const accountBox = `(()=>{const norm=s=>(s||"").replace(/\\s*\\((aktuell|current)\\)\\s*$/i,"").trim();
    const e=[...document.querySelectorAll("button.full-page-account-switcher-account-details")]
      .find(e=>norm(e.innerText)===${account}); if(!e)return null;
    e.scrollIntoView({block:"center"}); const r=e.getBoundingClientRect();
    return {x:r.x+r.width/2,y:r.y+r.height/2,expanded:!!e.querySelector("[class*=expanded]")}})()`;
  let accountHit;
  for (let i = 0; i < 20 && !accountHit; i++) {
    accountHit = await evaluate(session, accountBox);
    if (!accountHit) await sleep(250);
  }
  // Agency access is hierarchical. A fresh picker initially renders only the
  // agency parent; expand it before looking for the client account.
  if (!accountHit && profile.parent_account_name) {
    const parent = JSON.stringify(profile.parent_account_name);
    const parentBox = `(()=>{const e=[...document.querySelectorAll("button.full-page-account-switcher-account-details")]
      .find(e=>(e.innerText||"").trim()===${parent});if(!e)return null;
      e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2,expanded:!!e.querySelector("[class*=expanded]")}})()`;
    const parentHit = await evaluate(session, parentBox);
    if (!parentHit) throw new Error(`Could not find agency account ${profile.parent_account_name}`);
    if (!parentHit.expanded) await trustedClick(session, parentBox, `agency account ${profile.parent_account_name}`);
    for (let i = 0; i < 20 && !accountHit; i++) {
      accountHit = await evaluate(session, accountBox);
      if (!accountHit) await sleep(250);
    }
  }
  if (!accountHit) throw new Error(`Account ${profile.account_name} is not available`);
  const marketplaceBox = `(()=>{const norm=s=>(s||"").replace(/\\s*\\((aktuell|current)\\)\\s*$/i,"").trim();
    const groups=[...document.querySelectorAll("div.full-page-account-switcher-account")];
    const g=groups.find(x=>[...x.children].some(c=>c.matches?.("button.full-page-account-switcher-account-details")&&norm(c.innerText)===${account}));
    const e=g&&[...g.querySelectorAll("button.full-page-account-switcher-account-details")]
      .find(b=>norm(b.innerText)===${marketplace}); if(!e)return null;
    e.scrollIntoView({block:"center"}); const r=e.getBoundingClientRect();
    return {x:r.x+r.width/2,y:r.y+r.height/2,current:/\\((aktuell|current)\\)/i.test(e.innerText||"")}})()`;
  let marketplaceHit;
  for (let i = 0; i < 20 && !marketplaceHit; i++) {
    marketplaceHit = await evaluate(session, marketplaceBox);
    if (!marketplaceHit) await sleep(250);
  }
  if (!marketplaceHit) {
    await trustedClick(session, accountBox, `account ${profile.account_name}`);
    for (let i = 0; i < 20 && !marketplaceHit; i++) {
      marketplaceHit = await evaluate(session, marketplaceBox);
      if (!marketplaceHit) await sleep(250);
    }
  }
  if (!marketplaceHit) throw new Error(`Could not find marketplace ${profile.marketplace_label}`);
  if (marketplaceHit.current) {
    await session.send("Page.enable");
    await session.send("Page.navigate", { url: "https://sellercentral.amazon.com/amazonsell/manage-products?ref=myi&pageSize=100&pageIndex=0" });
    await waitFor(session, `location.pathname.includes("/amazonsell/manage-products")`, "current account inventory page", 120);
    await waitFor(session, `!!document.querySelector("meta[name=anti-csrftoken-a2z]")`, "inventory application", 120);
    return;
  }
  await trustedClick(session, marketplaceBox, `marketplace ${profile.marketplace_label}`);
  await sleep(500);
  await trustedClick(session, `(()=>{const all=[];const walk=root=>{for(const e of root.querySelectorAll("*")){all.push(e);if(e.shadowRoot)walk(e.shadowRoot)}};walk(document);
    const labels=${JSON.stringify(profile.confirm_labels || ["Select account", "Konto auswählen"])};
    const e=all.find(e=>e.tagName==="BUTTON"&&labels.includes((e.textContent||"").trim())&&e.getBoundingClientRect().width>0);
    if(!e)return null;const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`, "account confirmation");
  await waitFor(session, `!location.pathname.includes("account-switcher")`, "selected Seller Central account", 120);
  await waitFor(session, `!!document.querySelector("meta[name=anti-csrftoken-a2z]")`, "inventory application", 120);
}

async function fetchFba(session, profile) {
  const listings = [];
  let total = 1;
  for (let from = 0; from < total; from += 100) {
    const payload = { operationName: "WizardsInventory", variables: { pagination: { from, size: 100 } }, query: FBA_QUERY };
    const page = await evaluate(session, `(async()=>{const token=document.querySelector("meta[name=anti-csrftoken-a2z]")?.content;
      if(!token)throw new Error("anti-CSRF marker missing");
      const r=await fetch("/myinventory/gql",{method:"POST",credentials:"include",headers:{"content-type":"application/json","anti-csrftoken-a2z":token},body:${JSON.stringify(JSON.stringify(payload))}});
      if(!r.ok)throw new Error("FBA GraphQL HTTP "+r.status);return await r.json()})()`);
    if (page.errors?.length) throw new Error(`FBA GraphQL: ${page.errors.map((e) => e.message).join("; ")}`);
    const root = page.data?.listingsV2;
    if (!root) throw new Error("FBA GraphQL response shape changed");
    if (root.configContext?.merchantId !== profile.seller_id
      || root.configContext?.marketplaceId !== profile.marketplace_id) {
      throw new Error(`ACCOUNT_MISMATCH: expected ${profile.seller_id}/${profile.marketplace_id}, got ${root.configContext?.merchantId}/${root.configContext?.marketplaceId}`);
    }
    total = Number(root.count || 0);
    listings.push(...(root.listings || []));
  }
  return aggregateFba(listings);
}

async function fetchAwd(session, profile) {
  const end = new Date();
  end.setUTCDate(end.getUTCDate() - 2);
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - 31);
  const params = new URLSearchParams({
    domainIdentifier: "inventory_awdInventory_2024_01_31",
    queryName: "awdLedgerSummary",
    reportFileFormat: "CSV",
    reportStartDate: reportDate(start),
    reportEndDate: reportDate(end),
    xdaysBeforeUntilToday: "-1",
    startDateTimeOffset: "0",
    endDateTimeOffset: "0",
    specialDateOptions: "",
    language: "",
    disableTimezone: "true",
  });
  params.append("filters", JSON.stringify({ filterKey: "aggregatedByTimePeriod", value: "DAY" }));
  params.append("filters", JSON.stringify({ filterKey: "aggregateByLocation", value: "COUNTRY" }));
  const desiredStart = reportDate(start);
  const desiredEnd = reportDate(end);
  const history = await evaluate(session, `(async()=>{const r=await fetch("/reportcentral/api/v2/getDownloadHistoryRecords?queryName=awdLedgerSummary&queryName=awdLedgerDetail&domainIdentifier=inventory_awdInventory_2024_01_31",{credentials:"include"});
    if(!r.ok)return [];return await r.json()})()`);
  let submitted = (Array.isArray(history) ? history : []).find((record) =>
    record.queryName === "awdLedgerSummary"
    && String(record.queryStartDateTime || "").startsWith(desiredStart)
    && String(record.queryEndDateTime || "").startsWith(desiredEnd)
  );
  if (!submitted) {
    submitted = await evaluate(session, `(async()=>{const r=await fetch("/reportcentral/api/v2/submitDownloadReport?${params}",{method:"POST",credentials:"include"});
      if(!r.ok)throw new Error("AWD submit HTTP "+r.status);return await r.json()})()`);
  }
  if (!submitted?.queryId) throw new Error("AWD report did not return a query id");
  const statusPayload = [{
    queryId: submitted.queryId,
    domainIdentifier: "inventory_awdInventory_2024_01_31",
    queryName: "awdLedgerSummary",
    reportType: "AWD_INVENTORY_LEDGER_REPORT",
  }];
  let status = submitted.processingStatus === "DONE" ? [{
    queryId: submitted.queryId, status: "DONE", dataDocumentId: submitted.dataDocumentId,
  }] : undefined;
  for (let i = 0; i < 40; i++) {
    if (status?.[0]?.status === "DONE") break;
    status = await evaluate(session, `(async()=>{const r=await fetch("/reportcentral/api/v2/getDownloadReportStatus",{method:"POST",credentials:"include",headers:{"content-type":"application/json"},body:${JSON.stringify(JSON.stringify(statusPayload))}});return await r.json()})()`);
    if (!["IN_PROGRESS", "IN_QUEUE", "PENDING", undefined].includes(status?.[0]?.status)) break;
    await sleep(1500);
  }
  const record = status?.[0];
  if (record?.status === "NO_DATA_AVAILABLE") return aggregateAwd([]);
  if (record?.status !== "DONE" || !record.dataDocumentId) {
    throw new Error(`AWD report status ${record?.status || "unknown"}`);
  }
  const brokerPath = `/reportcentral/api/v2/downloadFile?domainIdentifier=inventory_awdInventory_2024_01_31&queryName=awdLedgerSummary&documentId=${encodeURIComponent(record.dataDocumentId)}`;
  const signedUrl = await evaluate(session, `(async()=>{const r=await fetch(${JSON.stringify(brokerPath)},{credentials:"include"});if(!r.ok)throw new Error("AWD download broker HTTP "+r.status);return await r.text()})()`);
  if (!/^https:\/\//.test(signedUrl)) throw new Error("AWD download broker returned an invalid URL");
  const response = await fetch(signedUrl);
  if (!response.ok) throw new Error(`AWD document HTTP ${response.status}`);
  const rows = parseCsv(await response.text());
  const awd = aggregateAwd(rows);
  awd.report_start = isoDate(start);
  awd.report_end = isoDate(end);
  awd.data_delay_hours = 24;
  return awd;
}

function retainAudits(directory, days) {
  const cutoff = Date.now() - days * 86400_000;
  for (const name of readdirSync(directory)) {
    const match = /^(\d{4}-\d{2}-\d{2})/.exec(name);
    if (match && new Date(`${match[1]}T00:00:00Z`).getTime() < cutoff) unlinkSync(join(directory, name));
  }
}

function writeAudit(directory, result) {
  mkdirSync(directory, { recursive: true });
  const stamp = result.checked_at.replaceAll(":", "-");
  writeFileSync(join(directory, `${stamp}.json`), JSON.stringify(result, null, 2));
  retainAudits(directory, 14);
}

async function main() {
  const options = args(process.argv.slice(2));
  if (!options.config || !options.profile) throw new Error("usage: provider.mjs --config <wizards config.json> --profile <key> [--audit-dir <dir>]");
  const config = JSON.parse(readFileSync(resolve(options.config), "utf8"));
  const inventory = config.inventory_questions || {};
  const profile = inventory.profiles?.[options.profile];
  if (!profile) throw new Error(`Unknown inventory profile ${options.profile}`);
  if (inventory.auto_reauth && !config.authentication?.enabled) {
    throw new Error("AUTO_REAUTH_NOT_CONFIGURED: enable the scoped service-account configuration first");
  }
  if (config.authentication?.enabled) assertAuthPolicy(config);
  process.env.CDP_PORT = String(inventory.cdp_port || 9223);
  process.env.CDP_PROFILE = (inventory.cdp_profile || "~/.amazon-agent/wizards-ai-chrome").replace(/^~/, process.env.HOME);
  ({ assertChrome, closePage, createPage, evaluate, listPages, Session }
    = await import("../report-fetcher/cdp.mjs"));
  try { await assertChrome(); }
  catch {
    const launcher = join(AMAZON_AGENT, "tools/report-fetcher/launch-chrome-debug.sh");
    const browserMode = inventory.browser_mode || "headed";
    const launched = spawnSync(launcher, ["--mode", browserMode], {
      env: { ...process.env, CDP_START_URL: "https://sellercentral.amazon.com" }, encoding: "utf8",
    });
    if (launched.status !== 0) throw new Error(`Could not launch dedicated Chrome: ${launched.stderr || launched.stdout}`);
    await assertChrome();
  }

  const picker = locationForPicker();
  const started = Date.now();
  // Reuse the dedicated bot tab when it is already on Manage Products. Seller
  // Central carries delegated-account selection in tab context; opening a new
  // target can intentionally return to the account picker even though the
  // dedicated tab is selected. The GraphQL seller/marketplace assertion below
  // is the hard safety check before any numbers are accepted.
  const existing = (await listPages()).find((page) =>
    page.url.startsWith("https://sellercentral.amazon.com/amazonsell/manage-products"));
  const created = existing ? null : await createPage(picker);
  const targetId = created?.targetId || null;
  const session = created?.session || await Session.open(existing.webSocketDebuggerUrl);
  const auditDir = resolve(options["audit-dir"] || join(AMAZON_AGENT, "output/wizards-inventory/audit"));
  let result;
  try {
    if (created) await selectAccount(session, profile, config);
    else await waitFor(session, `!!document.querySelector("meta[name=anti-csrftoken-a2z]")`, "inventory application", 120);
    const fba = await fetchFba(session, profile);
    let awd;
    const warnings = [];
    try { awd = await fetchAwd(session, profile); }
    catch (error) {
      awd = null;
      warnings.push(`AWD unavailable: ${error.message}`);
    }
    if (awd && Math.abs(fba.awd_buyable_in_transit_signal - awd.stored) > 0) {
      warnings.push(`Current AWD signal is ${fba.awd_buyable_in_transit_signal.toLocaleString("en-US")} versus ${awd.stored.toLocaleString("en-US")} in the delayed ledger`);
    }
    result = {
      schema_version: 1,
      request_id: `${profile.key}-${Date.now()}`,
      profile: profile.key,
      account: profile.account_name,
      marketplace: profile.marketplace,
      seller_id: profile.seller_id,
      checked_at: new Date().toISOString(),
      duration_ms: Date.now() - started,
      status: awd ? "complete" : "partial",
      source: { fba: "Seller Central Manage Products GraphQL", awd: awd ? "Seller Central AWD Inventory Ledger" : null },
      fba,
      awd,
      totals: awd ? combineInventory(fba, awd) : null,
      warnings,
      double_count_rule: "AWD ending balance is counted once. AWD departed units and FBA inbound are movement buckets and are not added to stored inventory.",
    };
  } catch (error) {
    if (!error.authStatus) {
      try {
        const authState = await inspectAuthState(session, inventory.allowed_auth_origins || []);
        if (authState !== "authenticated") throw authenticationError(authState);
        if (/HTTP (401|403)|anti-CSRF marker missing/i.test(error.message)) {
          throw authenticationError("login_required");
        }
      } catch (authCheckError) {
        if (authCheckError.authStatus) throw authCheckError;
      }
    }
    if (error.authStatus) throw error;
    try {
      await session.send("Page.enable");
      const shot = await session.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
      mkdirSync(auditDir, { recursive: true });
      const stamp = new Date().toISOString().replaceAll(":", "-");
      writeFileSync(join(auditDir, `${stamp}-failure.png`), shot.data, "base64");
      retainAudits(auditDir, 14);
    } catch {}
    throw error;
  } finally {
    session.close();
    if (targetId) await closePage(targetId);
  }
  writeAudit(auditDir, result);
  process.stdout.write(JSON.stringify(result));
}

main().catch((error) => {
  const status = error.authStatus || "error";
  const result = {
    schema_version: 1,
    checked_at: new Date().toISOString(),
    status,
    error: status === "error" ? error.message : "Seller Central authentication requires recovery",
  };
  try {
    const options = args(process.argv.slice(2));
    const directory = resolve(options["audit-dir"] || join(AMAZON_AGENT, "output/wizards-inventory/audit"));
    writeAudit(directory, result);
  } catch {}
  process.stdout.write(JSON.stringify(result));
  process.exitCode = 2;
});

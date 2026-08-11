export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else quoted = false;
      } else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ",") { row.push(field); field = ""; }
    else if (char === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (char !== "\r") field += char;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  if (!rows.length) return [];
  const headers = rows[0];
  return rows.slice(1).filter((r) => r.some(Boolean)).map((r) =>
    Object.fromEntries(headers.map((header, index) => [header, r[index] ?? ""])));
}

const qty = (value) => Number.isFinite(Number(value)) ? Number(value) : 0;

export function nullableQty(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const normalized = String(value).replaceAll(",", "").match(/-?\d+(?:\.\d+)?/);
  if (!normalized) return null;
  const number = Number(normalized[0]);
  return Number.isFinite(number) ? number : null;
}

const first = (...values) => values.find((value) => value !== undefined && value !== null && value !== "");

export function assertAccountIdentity(profile, identity) {
  const expectedSeller = profile?.seller_id;
  const expectedMarketplace = profile?.marketplace_id;
  const actualSeller = identity?.merchantId;
  const actualMarketplace = identity?.marketplaceId;
  if ((expectedSeller && actualSeller !== expectedSeller)
      || (expectedMarketplace && actualMarketplace !== expectedMarketplace)) {
    throw new Error(`ACCOUNT_MISMATCH: expected ${expectedSeller || "selected account"}/${expectedMarketplace}, got ${actualSeller}/${actualMarketplace}`);
  }
  return true;
}

export function selectOnlyRequested(options = {}) {
  return options["select-only"] === true;
}

function normalizeContent(raw = {}) {
  return {
    seller_sku: String(first(raw.seller_sku, raw.sellerSku, raw.sku, raw["Seller SKU"], "")).trim(),
    expected: nullableQty(first(raw.expected, raw.expected_units, raw.expectedUnits, raw["Expected units"])),
    shipped: nullableQty(first(raw.shipped, raw.shipped_units, raw.shippedUnits, raw["Shipped units"])),
    received: nullableQty(first(raw.received, raw.received_units, raw.receivedUnits, raw["Received units"])),
  };
}

export function normalizeShipment(raw = {}) {
  const contents = (raw.contents || raw.items || raw.products || []).map(normalizeContent);
  const sumKnown = (field) => {
    const values = contents.map((item) => item[field]);
    return values.length && values.every((value) => value !== null)
      ? values.reduce((total, value) => total + value, 0) : null;
  };
  return {
    shipment_id: String(first(raw.shipment_id, raw.shipmentId, raw.id, "")).trim() || null,
    shipment_name: String(first(raw.shipment_name, raw.shipmentName, raw.name, "")).trim() || null,
    status: String(first(raw.status, raw.shipment_status, raw.shipmentStatus, "")).trim() || null,
    last_updated: String(first(raw.last_updated, raw.lastUpdated, raw.updated_at, raw.updatedAt, "")).trim() || null,
    url: raw.url || null,
    quantities: {
      expected: nullableQty(first(raw.quantities?.expected, raw.expected, raw.expected_units, sumKnown("expected"))),
      shipped: nullableQty(first(raw.quantities?.shipped, raw.shipped, raw.shipped_units, sumKnown("shipped"))),
      received: nullableQty(first(raw.quantities?.received, raw.received, raw.received_units, sumKnown("received"))),
    },
    contents,
  };
}

export function shipmentVerdict(quantities = {}) {
  const expected = nullableQty(quantities.expected);
  const received = nullableQty(quantities.received);
  if (expected === null || received === null) return "unknown";
  if (received === 0) return "not-booked-in";
  if (received < expected) return "partially-booked-in";
  return "fully-booked-in";
}

export function filterShipmentContents(rawShipments, requestedSkus) {
  const wanted = new Set((requestedSkus || []).map((sku) => String(sku).trim().toUpperCase()));
  const matches = [];
  for (const raw of rawShipments || []) {
    const shipment = normalizeShipment(raw);
    const contents = shipment.contents.filter((item) => wanted.has(item.seller_sku.toUpperCase()));
    if (!contents.length) continue;
    const sumKnown = (field) => contents.every((item) => item[field] !== null)
      ? contents.reduce((total, item) => total + item[field], 0) : null;
    shipment.contents = contents;
    shipment.quantities = {
      expected: sumKnown("expected"),
      shipped: sumKnown("shipped"),
      received: sumKnown("received"),
    };
    shipment.verdict = shipmentVerdict(shipment.quantities);
    matches.push(shipment);
  }
  let verdict = "unknown";
  if (matches.length && matches.every((item) => item.verdict !== "unknown")) {
    const states = new Set(matches.map((item) => item.verdict));
    verdict = states.size === 1 ? matches[0].verdict : "partially-booked-in";
  }
  return { requested_skus: [...wanted], matches, verdict };
}

export function aggregateFba(listings) {
  const out = {
    listings: 0,
    available: 0,
    reserved: { fc_transfer: 0, customer_order: 0, fc_processing: 0, total: 0 },
    inbound: 0,
    unfulfillable: 0,
    researching: 0,
    stored: 0,
    on_hand_reported: 0,
    awd_buyable_in_transit_signal: 0,
  };
  for (const listing of listings) {
    const availability = listing.availability || {};
    const channel = listing.coreListingFields?.fulfillmentChannel
      || availability.coreListingFields?.fulfillmentChannel;
    if (channel !== "AFN") continue;
    out.listings++;
    out.available += qty(availability.quantity);
    out.reserved.fc_transfer += qty(availability.reserved?.fcTransfer);
    out.reserved.customer_order += qty(availability.reserved?.customerOrder);
    out.reserved.fc_processing += qty(availability.reserved?.fcProcessing);
    out.inbound += qty(availability.inbound);
    out.unfulfillable += qty(availability.unfulfillable);
    out.researching += qty(availability.researching?.shortTerm)
      + qty(availability.researching?.midTerm)
      + qty(availability.researching?.longTerm);
    out.on_hand_reported += qty(availability.onHandQuantity);
    out.awd_buyable_in_transit_signal += qty(availability.buyableInTransit);
  }
  out.reserved.total = out.reserved.fc_transfer + out.reserved.customer_order
    + out.reserved.fc_processing;
  // Amazon's `quantity` is the available FBA quantity. Reserved, unfulfillable,
  // and researching units are separate physical buckets. Inbound is not stored.
  out.stored = out.available + out.reserved.total + out.unfulfillable + out.researching;
  return out;
}

export function summarizeFbaBySku(listings, requestedSkus) {
  const wanted = new Set((requestedSkus || []).map((sku) => String(sku).trim().toUpperCase()));
  return (listings || []).filter((listing) => {
    const sku = String(listing.coreListingFields?.sku || "").trim().toUpperCase();
    return wanted.has(sku);
  }).map((listing) => {
    const totals = aggregateFba([listing]);
    const channel = listing.coreListingFields?.fulfillmentChannel
      || listing.availability?.coreListingFields?.fulfillmentChannel || null;
    return {
      seller_sku: listing.coreListingFields?.sku || null,
      asin: listing.coreListingFields?.asin || null,
      // Whether an FBA offer exists at all, which the quantities cannot tell
      // you: an out-of-stock FBA child and an FBM-only child both aggregate to
      // zero. Reshipment planning needs that difference. The first wants
      // restocking; the second must never be sent to FBA, and on 11.08.2026 a
      // plan built without it proposed 5,603 and 5,296 units of two AlphaInfuse
      // children that hold no FBA offer at all.
      fulfillment_channel: channel,
      fba_offer: channel === "AFN",
      available: totals.available,
      reserved: totals.reserved.total,
      inbound: totals.inbound,
      unfulfillable: totals.unfulfillable,
      stored: totals.stored,
    };
  });
}

export function aggregateAwd(rows) {
  if (!rows.length) return {
    as_of: null, rows: 0, ending_cartons: 0, stored: 0, available: 0,
    reserved: null, inbound: 0, outbound: 0, lost: 0, found: 0,
  };
  const dates = rows.map((row) => row.Date).filter(Boolean).sort();
  const asOf = dates.at(-1) || null;
  const latest = rows.filter((row) => row.Date === asOf);
  const units = (row, column) => qty(row[column]) * qty(row["Package Quantity"]);
  const sum = (column) => latest.reduce((total, row) => total + units(row, column), 0);
  const stored = sum("Ending Warehouse Balance (cartons)");
  return {
    as_of: asOf,
    rows: latest.length,
    ending_cartons: latest.reduce((total, row) =>
      total + qty(row["Ending Warehouse Balance (cartons)"]), 0),
    stored,
    available: stored,
    // The AWD ledger has no reserved bucket. Departed units are no longer in
    // the ending balance and must not be added to FBA inbound or the total.
    reserved: null,
    inbound: sum("Received (cartons)"),
    outbound: sum("Departed (cartons)"),
    lost: sum("Lost (cartons)"),
    found: sum("Found (cartons)"),
  };
}

export function combineInventory(fba, awd) {
  return {
    stored: fba.stored + awd.stored,
    available_network: fba.available + awd.available,
    fba_stored: fba.stored,
    fba_available: fba.available,
    awd_stored: awd.stored,
    reserved_fba: fba.reserved.total,
    inbound_fba: fba.inbound,
    unfulfillable_fba: fba.unfulfillable,
  };
}

export function classifyAuthPage(page) {
  const url = String(page?.url || "").toLowerCase();
  const body = String(page?.body || "").toLowerCase();
  if (page?.hasCaptcha || /captcha|enter the characters you see/.test(body)) {
    return "human_challenge";
  }
  if (page?.hasRecovery || page?.hasApproval
      || /account recovery|password assistance|approve the notification|verify your identity/.test(body)) {
    return "human_challenge";
  }
  if (page?.hasOtp || /\/ap\/mfa|one[- ]time password|authentication code/.test(url + body)) {
    return "totp_required";
  }
  if (page?.hasPassword || /\/ap\/signin|signin|auth/.test(url)) {
    return "password_required";
  }
  if (page?.hasInventoryMarker || page?.hasAccountPicker) return "authenticated";
  return "login_required";
}

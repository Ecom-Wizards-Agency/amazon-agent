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

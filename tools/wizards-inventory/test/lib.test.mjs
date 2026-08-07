import test from "node:test";
import assert from "node:assert/strict";
import {
  aggregateAwd, aggregateFba, assertAccountIdentity, classifyAuthPage,
  combineInventory, filterShipmentContents, normalizeShipment, parseCsv,
  selectOnlyRequested, shipmentVerdict, summarizeFbaBySku,
} from "../lib.mjs";

test("FBA buckets are aggregated without counting inbound as stored", () => {
  const fba = aggregateFba([{ coreListingFields: { fulfillmentChannel: "AFN" }, availability: {
    quantity: 100, reserved: { fcTransfer: 5, customerOrder: 7, fcProcessing: 8 },
    inbound: 30, unfulfillable: 2, researching: { shortTerm: 1, midTerm: 2, longTerm: 0 },
    onHandQuantity: 105, buyableInTransit: 200,
  } }]);
  assert.equal(fba.available, 100);
  assert.equal(fba.reserved.total, 20);
  assert.equal(fba.stored, 125);
  assert.equal(fba.inbound, 30);
});

test("AWD uses only the latest date and converts cartons to units", () => {
  const rows = parseCsv('Date,Package Quantity,Ending Warehouse Balance (cartons),Received (cartons),Departed (cartons),Lost (cartons),Found (cartons)\n2026-07-30,10,2,0,0,0,0\n2026-07-31,10,3,1,2,0,0\n2026-07-31,5,4,0,1,0,1\n');
  const awd = aggregateAwd(rows);
  assert.equal(awd.as_of, "2026-07-31");
  assert.equal(awd.stored, 50);
  assert.equal(awd.inbound, 10);
  assert.equal(awd.outbound, 25);
  assert.equal(awd.found, 5);
});

test("network totals do not add movement buckets", () => {
  const totals = combineInventory({ stored: 125, available: 100, reserved: { total: 20 }, inbound: 30, unfulfillable: 2 }, { stored: 50, available: 50 });
  assert.deepEqual(totals, {
    stored: 175, available_network: 150, fba_stored: 125, fba_available: 100,
    awd_stored: 50, reserved_fba: 20, inbound_fba: 30, unfulfillable_fba: 2,
  });
});

test("authentication pages are classified without exposing their contents", () => {
  assert.equal(classifyAuthPage({ url: "https://www.amazon.com/ap/signin", hasPassword: true }), "password_required");
  assert.equal(classifyAuthPage({ url: "https://www.amazon.com/ap/mfa", hasOtp: true }), "totp_required");
  assert.equal(classifyAuthPage({ url: "https://www.amazon.com/ap/cvf", hasApproval: true }), "human_challenge");
  assert.equal(classifyAuthPage({ url: "https://sellercentral.amazon.com/account-switcher", hasAccountPicker: true }), "authenticated");
  assert.equal(classifyAuthPage({ url: "https://sellercentral.amazon.com/amazonsell/manage-products", hasInventoryMarker: true }), "authenticated");
});

test("shipment fields are normalized from Seller Central-shaped aliases", () => {
  const shipment = normalizeShipment({
    shipmentId: "FBA123", shipmentName: "ShineFoam inbound", shipmentStatus: "Receiving",
    lastUpdated: "05.08.2026", items: [{
      sellerSku: "SK-TWF001", expectedUnits: "1,000", shippedUnits: "1,000", receivedUnits: "250",
    }],
  });
  assert.equal(shipment.shipment_id, "FBA123");
  assert.equal(shipment.status, "Receiving");
  assert.deepEqual(shipment.quantities, { expected: 1000, shipped: 1000, received: 250 });
});

test("shipment filtering keeps only requested SKUs", () => {
  const filtered = filterShipmentContents([{ shipment_id: "FBA123", contents: [
    { seller_sku: "SK-TWF001", expected: 100, shipped: 100, received: 100 },
    { seller_sku: "OTHER", expected: 50, shipped: 50, received: 0 },
  ] }], ["SK-TWF001", "SK-TWF-002"]);
  assert.equal(filtered.matches.length, 1);
  assert.deepEqual(filtered.matches[0].contents.map((item) => item.seller_sku), ["SK-TWF001"]);
  assert.deepEqual(filtered.requested_skus, ["SK-TWF001", "SK-TWF-002"]);
});

test("booked-in classification distinguishes zero, partial, and full receipt", () => {
  assert.equal(shipmentVerdict({ expected: 100, received: 0 }), "not-booked-in");
  assert.equal(shipmentVerdict({ expected: 100, received: 25 }), "partially-booked-in");
  assert.equal(shipmentVerdict({ expected: 100, received: 100 }), "fully-booked-in");
});

test("missing shipment quantities remain unknown", () => {
  assert.equal(shipmentVerdict({ expected: 100 }), "unknown");
  const filtered = filterShipmentContents([{ shipment_id: "FBA123", contents: [
    { seller_sku: "SK-TWF001", expected: 100, received: null },
  ] }], ["SK-TWF001"]);
  assert.equal(filtered.verdict, "unknown");
});

test("account identity rejects the wrong marketplace or seller", () => {
  assert.equal(assertAccountIdentity(
    { seller_id: "SELLER", marketplace_id: "US" },
    { merchantId: "SELLER", marketplaceId: "US" }), true);
  assert.throws(() => assertAccountIdentity(
    { seller_id: "SELLER", marketplace_id: "US" },
    { merchantId: "OTHER", marketplaceId: "US" }), /ACCOUNT_MISMATCH/);
  assert.throws(() => assertAccountIdentity(
    { marketplace_id: "US" }, { merchantId: "SELLER", marketplaceId: "DE" }), /ACCOUNT_MISMATCH/);
});

test("select-only mode stays opt-in and bypass-compatible", () => {
  assert.equal(selectOnlyRequested({ "select-only": true }), true);
  assert.equal(selectOnlyRequested({ "select-only": "true" }), false);
  assert.equal(selectOnlyRequested({}), false);
});

test("configured SKU stock is returned without unrelated listings", () => {
  const listings = [
    { coreListingFields: { sku: "SK-TWF001", asin: "B001", fulfillmentChannel: "AFN" }, availability: { quantity: 10, inbound: 5 } },
    { coreListingFields: { sku: "OTHER", asin: "B002", fulfillmentChannel: "AFN" }, availability: { quantity: 99 } },
  ];
  assert.deepEqual(summarizeFbaBySku(listings, ["SK-TWF001"]), [{
    seller_sku: "SK-TWF001", asin: "B001", available: 10, reserved: 0,
    inbound: 5, unfulfillable: 0, stored: 10,
  }]);
});

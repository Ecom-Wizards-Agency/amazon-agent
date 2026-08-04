import test from "node:test";
import assert from "node:assert/strict";
import { aggregateAwd, aggregateFba, classifyAuthPage, combineInventory, parseCsv } from "../lib.mjs";

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

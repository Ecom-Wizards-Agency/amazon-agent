import assert from "node:assert/strict";
import test from "node:test";
import { assertPriceExpectations, normalizePriceRows, parseMoney } from "../price-lib.mjs";

test("parses US and decimal-comma prices", () => {
  assert.deepEqual(parseMoney("$25.95"), { amount: 25.95, currency: "USD" });
  assert.deepEqual(parseMoney("€ 25,95"), { amount: 25.95, currency: "EUR" });
});

test("normalizes one exact ASIN row and uses an active lower sale price", () => {
  const result = normalizePriceRows([{
    text: "B0C2DCC73B SKU-NHT Price $29.99 Sale price $25.95",
    headers: ["ASIN", "Your price", "Sale price"],
    cells: ["B0C2DCC73B", "$29.99", "$25.95"], sku: "SKU-NHT",
  }], "B0C2DCC73B");
  assert.equal(result.configured_price, 29.99);
  assert.equal(result.sale_price, 25.95);
  assert.equal(result.effective_price, 25.95);
});

test("refuses conflicting prices for the same ASIN", () => {
  assert.throws(() => normalizePriceRows([
    { text: "B0C2DCC73B Price $29.99", headers: ["Price"], cells: ["$29.99"] },
    { text: "B0C2DCC73B Price $25.95", headers: ["Price"], cells: ["$25.95"] },
  ], "B0C2DCC73B"), /conflicting/);
});

test("requires and verifies all expected identities", () => {
  assert.throws(() => assertPriceExpectations({}, {}, {}), /require/);
  assert.doesNotThrow(() => assertPriceExpectations(
    { "expect-account": "Swissklip", "expect-seller-id": "SELLER", "expect-marketplace-id": "MARKET" },
    { account_name: "Swissklip" }, { merchantId: "SELLER", marketplaceId: "MARKET" },
  ));
});

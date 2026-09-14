import assert from "node:assert/strict";
import test from "node:test";
import { identityFieldsConsistent } from "../sc-account.mjs";

const baseline = { merchantId: "MERCHANT", partnerAccountId: "PARTNER", displayName: "Example Seller" };

test("missing display name is accepted when the merchant ID matches", () => {
  for (const displayName of [null, "", undefined, "   "]) {
    assert.deepEqual(identityFieldsConsistent(baseline, { ...baseline, displayName }), { ok: true, field: null });
  }
});

test("different display name fails even when the merchant ID matches", () => {
  assert.deepEqual(identityFieldsConsistent(baseline, { ...baseline, displayName: "Other Seller" }),
    { ok: false, field: "displayName" });
});

test("no readable strong ID fails on the first unverifiable baseline field", () => {
  assert.deepEqual(identityFieldsConsistent(baseline, { displayName: null }),
    { ok: false, field: "merchantId" });
  assert.deepEqual(identityFieldsConsistent({ displayName: baseline.displayName }, { displayName: null }),
    { ok: false, field: "displayName" });
});

test("different merchant ID fails even when the partner ID matches", () => {
  assert.deepEqual(identityFieldsConsistent(baseline, { ...baseline, merchantId: "OTHER" }),
    { ok: false, field: "merchantId" });
});

test("matching partner ID permits missing merchant ID and display name", () => {
  assert.deepEqual(identityFieldsConsistent(baseline, { partnerAccountId: baseline.partnerAccountId }),
    { ok: true, field: null });
});

test("an unmatched live strong ID cannot excuse missing baseline fields", () => {
  assert.deepEqual(identityFieldsConsistent({ displayName: baseline.displayName }, { merchantId: "MERCHANT" }),
    { ok: false, field: "displayName" });
});

test("different partner ID fails even when the merchant ID matches", () => {
  assert.deepEqual(identityFieldsConsistent(baseline, { ...baseline, partnerAccountId: "OTHER" }),
    { ok: false, field: "partnerAccountId" });
});

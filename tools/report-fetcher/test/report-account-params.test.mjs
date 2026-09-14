import assert from "node:assert/strict";
import test from "node:test";

import { reportAccountParams } from "../sc-account.mjs";

const liveMerchantId = "amzn1.merchant.d.ADIJQSDVTSU23LVH2UELFXMNJK2Q";
const forcedMerchantId = "amzn1.merchant.d.OTHER";
const liveUrl = `https://sellercentral.amazon.com/home?mons_sel_dir_mcid=${liveMerchantId}&mons_sel_dir_paid=LIVE-PARTNER&mons_sel_mkid=ATVPDKIKX0DER&unrelated=value`;

test("bare Seller ID is not injected and live seller navigation params are kept", () => {
  const params = reportAccountParams(liveUrl, "AWRIFF79JWP4T");
  assert.ok(params instanceof URLSearchParams);
  assert.deepEqual([...params], [
    ["mons_sel_dir_mcid", liveMerchantId],
    ["mons_sel_dir_paid", "LIVE-PARTNER"],
  ]);
});

test("directed merchant ID is injected with a case-insensitive prefix match", () => {
  for (const forced of [forcedMerchantId, "AMZN1.MERCHANT.D.OTHER"]) {
    assert.deepEqual([...reportAccountParams("https://sellercentral.amazon.com/home", forced)], [
      ["mons_sel_dir_mcid", forced],
    ]);
  }
});

test("no live params and a bare Seller ID yields empty params", () => {
  for (const url of ["https://sellercentral.amazon.com/home", "", undefined]) {
    assert.equal(reportAccountParams(url, "AWRIFF79JWP4T").toString(), "");
  }
});

test("existing live merchant ID is replaced only by a forced directed merchant ID", () => {
  for (const forced of [undefined, "", "AWRIFF79JWP4T", "amzn1.merchant.o.OTHER", "prefix.amzn1.merchant.d.OTHER", forcedMerchantId]) {
    assert.deepEqual([...reportAccountParams(liveUrl, forced)], [
      ["mons_sel_dir_mcid", forced === forcedMerchantId ? forcedMerchantId : liveMerchantId],
      ["mons_sel_dir_paid", "LIVE-PARTNER"],
    ]);
  }
});

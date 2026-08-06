const SYMBOLS = { "$": "USD", "€": "EUR", "£": "GBP", "A$": "AUD" };

export function parseMoney(value) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  const match = text.match(/(A\$|[$€£])\s*([\d,.]+)/);
  if (!match) return null;
  let numeric = match[2];
  if (numeric.includes(",") && numeric.includes(".")) numeric = numeric.replaceAll(",", "");
  else if (numeric.includes(",") && /,\d{2}$/.test(numeric)) numeric = numeric.replace(",", ".");
  else numeric = numeric.replaceAll(",", "");
  const amount = Number(numeric);
  return Number.isFinite(amount) ? { amount, currency: SYMBOLS[match[1]] } : null;
}

function labeledMoney(text, labels) {
  for (const label of labels) {
    const pattern = new RegExp(`${label}\\s*[:\\-]?\\s*((?:A\\$|[$€£])\\s*[\\d,.]+)`, "i");
    const parsed = parseMoney(String(text || "").match(pattern)?.[1]);
    if (parsed) return parsed;
  }
  return null;
}

export function normalizePriceRows(rows, asin) {
  const exact = (rows || []).filter((row) => String(row.text || "").toUpperCase().includes(asin));
  const normalized = exact.map((row) => {
    const headers = row.headers || [];
    const cells = row.cells || [];
    const byHeader = (labels) => {
      const index = headers.findIndex((header) => labels.some((label) =>
        String(header).toLowerCase().includes(label)));
      return index >= 0 ? parseMoney(cells[index]) : null;
    };
    const configured = byHeader(["your price", "standard price", "price"])
      || labeledMoney(row.text, ["Your price", "Standard price", "Price"]);
    const sale = byHeader(["sale price"]) || labeledMoney(row.text, ["Sale price"]);
    if (!configured) return null;
    return {
      configured_price: configured.amount,
      sale_price: sale?.amount ?? null,
      effective_price: sale && sale.amount < configured.amount ? sale.amount : configured.amount,
      currency: configured.currency,
      seller_sku: row.sku || null,
    };
  }).filter(Boolean);
  if (!normalized.length) throw new Error(`No exact configured price was readable for ASIN ${asin}`);
  const signatures = new Set(normalized.map((item) =>
    `${item.currency}:${item.configured_price}:${item.sale_price ?? ""}`));
  if (signatures.size !== 1) throw new Error(`ASIN ${asin} has multiple conflicting configured prices`);
  return { asin, ...normalized[0],
    seller_skus: [...new Set(normalized.map((item) => item.seller_sku).filter(Boolean))] };
}

export function assertPriceExpectations(options, profile, identity) {
  const expected = { account: options["expect-account"], seller: options["expect-seller-id"],
    marketplace: options["expect-marketplace-id"] };
  if (!expected.account || !expected.seller || !expected.marketplace) {
    throw new Error("Price checks require --expect-account, --expect-seller-id, and --expect-marketplace-id");
  }
  if (profile.account_name !== expected.account || identity?.merchantId !== expected.seller
      || identity?.marketplaceId !== expected.marketplace) {
    const error = new Error("Price check account, seller, or marketplace identity mismatch");
    error.operationStatus = "identity_mismatch";
    throw error;
  }
}

export function marketplaceDomain(marketplace) {
  return ({ US: "www.amazon.com", UK: "www.amazon.co.uk", DE: "www.amazon.de",
    FR: "www.amazon.fr", IT: "www.amazon.it", ES: "www.amazon.es", NL: "www.amazon.nl",
    SE: "www.amazon.se", AUS: "www.amazon.com.au" })[marketplace] || null;
}

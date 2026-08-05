import test from "node:test";
import assert from "node:assert/strict";
import {
  assertAuthPolicy, authenticationFormStep, parseItemReference, parseLoginItem,
} from "../auth.mjs";

function config() {
  return {
    authentication: {
      enabled: true,
      mode: "onepassword_service_account",
      scope: "view-only-amazon-login",
      keychain_service: "test", keychain_account: "test",
      item_reference: "op://test/item",
    },
    browser_routing: {
      read: { cdp_port: 9223, required_account_access: "view-only", allow_fallback: false },
    },
    inventory_questions: {
      cdp_port: 9223,
      allowed_auth_origins: ["https://sellercentral.amazon.com", "https://www.amazon.com"],
    },
  };
}

test("service-account auth is restricted to the view-only port", () => {
  assert.equal(assertAuthPolicy(config()), true);
  const unsafe = config();
  unsafe.inventory_questions.cdp_port = 9222;
  assert.throws(() => assertAuthPolicy(unsafe), /restricted to view-only port 9223/);
});

test("login item parsing returns only username and password", () => {
  assert.deepEqual(parseLoginItem({ fields: [
    { id: "username", value: "viewer@example.test" },
    { id: "password", value: "secret" },
    { label: "notesPlain", value: "ignored" },
  ] }), { username: "viewer@example.test", password: "secret" });
});

test("item references split into explicit vault and item arguments", () => {
  assert.deepEqual(
    parseItemReference("op://Wizards AI Automation/Amazon - Wizards AI"),
    { vault: "Wizards AI Automation", item: "Amazon - Wizards AI" },
  );
});

test("combined Seller Central form submits both credentials before email-only", () => {
  assert.equal(authenticationFormStep({ email: true, password: true, otp: false }, "password_required"), "credentials");
  assert.equal(authenticationFormStep({ email: true, password: false, otp: false }, "password_required"), "email");
  assert.equal(authenticationFormStep({ email: false, password: false, otp: true }, "totp_required"), "otp");
});

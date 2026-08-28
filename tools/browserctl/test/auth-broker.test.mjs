import assert from "node:assert/strict";
import test from "node:test";
import { classifyAuthenticationPage, publicAuthenticationStatus } from "../auth-broker.mjs";

const base = {
  origin: "https://example.test", path: "/", email: false, password: false,
  otp: false, captcha: false, recovery: false, approval: false, invalid: false,
  rateLimited: false, amazonApp: false,
};

test("Amazon adapter distinguishes app, password, OTP, and human challenge states", () => {
  assert.equal(classifyAuthenticationPage("amazon", { ...base, amazonApp: true }).status, "authenticated");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, password: true }).status, "password_required");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, otp: true }).status, "totp_required");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, captcha: true }).status, "human_challenge");
});

test("FlatFilePro adapter treats login as unauthenticated and app routes as authenticated", () => {
  assert.equal(classifyAuthenticationPage("flatfilepro", {
    ...base, origin: "https://app.flatfile.pro", path: "/login", email: true,
  }).status, "login_required");
  assert.equal(classifyAuthenticationPage("flatfilepro", {
    ...base, origin: "https://app.flatfile.pro", path: "/imports",
  }).status, "authenticated");
});

test("invalid credentials and rate limiting stop rather than retry", () => {
  assert.equal(classifyAuthenticationPage("flatfilepro", { ...base, invalid: true }).status, "authentication_failed");
  assert.equal(classifyAuthenticationPage("amazon", { ...base, rateLimited: true }).status, "human_challenge");
});

test("public authentication statuses cannot include secret values", () => {
  const result = publicAuthenticationStatus({
    status: "authenticated", route: { id: "flatfilepro", adapter: "flatfilepro" },
    port: 9222, targetId: "target", origin: "https://app.flatfile.pro/login?token=secret",
    username: "user@example.test", password: "password-secret", otp: "123456",
  });
  const serialized = JSON.stringify(result);
  assert.deepEqual(Object.keys(result).sort(),
    ["adapter", "origin", "port", "route_id", "status", "targetId"].sort());
  assert.equal(result.origin, "https://app.flatfile.pro");
  assert.equal(/user@example|password-secret|123456|token=/.test(serialized), false);
});

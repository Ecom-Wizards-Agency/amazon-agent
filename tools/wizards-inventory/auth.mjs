import { spawnSync } from "node:child_process";
import { join } from "node:path";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: "utf8", timeout: 30000, maxBuffer: 2_000_000, ...options,
  });
  if (result.error || result.status !== 0) {
    throw new Error(`${command} credential helper unavailable`);
  }
  return result.stdout.trim();
}

export function assertAuthPolicy(config) {
  const auth = config.authentication || {};
  const read = config.browser_routing?.read || {};
  const inventory = config.inventory_questions || {};
  if (!auth.enabled) return false;
  if (auth.mode !== "onepassword_service_account"
      || auth.scope !== "view-only-amazon-login") {
    throw new Error("AUTH_POLICY_REFUSED: unsupported 1Password scope");
  }
  if (Number(read.cdp_port) !== 9223 || Number(inventory.cdp_port) !== 9223
      || read.required_account_access !== "view-only" || read.allow_fallback !== false) {
    throw new Error("AUTH_POLICY_REFUSED: automated login is restricted to view-only port 9223");
  }
  if (!auth.keychain_service || !auth.keychain_account || !auth.item_reference) {
    throw new Error("AUTH_POLICY_REFUSED: incomplete service-account configuration");
  }
  const approvedOrigins = new Set([
    "https://sellercentral.amazon.com", "https://www.amazon.com",
    "https://sellercentral.amazon.de", "https://www.amazon.de",
    "https://sellercentral.amazon.com.au", "https://www.amazon.com.au",
  ]);
  const configuredOrigins = inventory.allowed_auth_origins || [];
  if (!configuredOrigins.length || configuredOrigins.some((origin) => !approvedOrigins.has(origin))) {
    throw new Error("AUTH_POLICY_REFUSED: authentication origins must be approved Amazon domains");
  }
  return true;
}

function fieldValue(document, names) {
  const wanted = new Set(names.map((name) => name.toLowerCase()));
  const field = (document.fields || []).find((item) =>
    wanted.has(String(item.id || "").toLowerCase())
    || wanted.has(String(item.label || "").toLowerCase()));
  return typeof field?.value === "string" ? field.value : "";
}

export function parseLoginItem(document) {
  const username = fieldValue(document, ["username", "email"]);
  const password = fieldValue(document, ["password"]);
  if (!username || !password) throw new Error("1Password item lacks username or password");
  return { username, password };
}

export function parseItemReference(reference) {
  if (typeof reference !== "string" || !reference.startsWith("op://")) {
    throw new Error("1Password item reference must start with op://");
  }
  const location = reference.slice(5);
  const separator = location.indexOf("/");
  if (separator < 1 || separator === location.length - 1) {
    throw new Error("1Password item reference must contain vault and item names");
  }
  return { vault: location.slice(0, separator), item: location.slice(separator + 1) };
}

export function loadViewOnlyLogin(config, { includeOtp = false } = {}) {
  if (!assertAuthPolicy(config)) return null;
  const auth = config.authentication;
  const helper = join(process.env.HOME, ".amazon-agent", "bin", "wizards-keychain");
  const token = run(helper, [
    "get", auth.keychain_service, auth.keychain_account,
  ]);
  const env = { ...process.env, OP_SERVICE_ACCOUNT_TOKEN: token };
  const location = parseItemReference(auth.item_reference);
  const itemArguments = ["item", "get", location.item, "--vault", location.vault];
  const raw = run("op", [...itemArguments, "--format", "json"], { env });
  const login = parseLoginItem(JSON.parse(raw));
  if (includeOtp) {
    login.otp = run("op", [...itemArguments, "--otp"], { env });
  }
  return login;
}

export function authenticationFormStep(fields, state) {
  if (fields?.password) return "credentials";
  if (fields?.email) return "email";
  if (fields?.otp || state === "totp_required") return "otp";
  return "none";
}

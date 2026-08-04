import { spawnSync } from "node:child_process";

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

export function loadViewOnlyLogin(config, { includeOtp = false } = {}) {
  if (!assertAuthPolicy(config)) return null;
  const auth = config.authentication;
  const token = run("security", [
    "find-generic-password", "-s", auth.keychain_service,
    "-a", auth.keychain_account, "-w",
  ]);
  const env = { ...process.env, OP_SERVICE_ACCOUNT_TOKEN: token };
  const raw = run("op", ["item", "get", auth.item_reference, "--format", "json"], { env });
  const login = parseLoginItem(JSON.parse(raw));
  if (includeOtp) {
    login.otp = run("op", ["item", "get", auth.item_reference, "--otp"], { env });
  }
  return login;
}

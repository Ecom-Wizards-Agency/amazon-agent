// One session binding per process. Call before importing any CDP client.
import { realpathSync } from "node:fs";
import { resolve } from "node:path";
import { homedir } from "node:os";
import { loadBrowserPolicy, policyForPort } from "./policy.mjs";

const canonical = (p) => {
  p = resolve(String(p).replace(/^~(?=\/|$)/, homedir()));
  try { return realpathSync(p); } catch { return p; }
};

// Grimoire's units set WIZARDS_AI_MODE=1. They stay on grimoire and never reach
// the attended operator browser, whichever flag or variable selects it.
export function wizardsAiMode(env = process.env) {
  return /^(1|true|yes|on)$/i.test(String(env.WIZARDS_AI_MODE || "").trim());
}

const REFUSED = "BROWSER_SESSION_REFUSED: WIZARDS_AI_MODE runs only on grimoire (CDP 9223); "
  + "operator (CDP 9222) is the attended browser";

// CDP_PORT names a managed session by number, so "09222" is still the operator port.
const managedSession = (port) => ({ 9222: "operator", 9223: "grimoire" })[Number(String(port ?? "").trim())];

export function sessionForPort(port, env = process.env) {
  const name = Number(port) === 9223 ? "grimoire" : "operator";
  if (name !== "grimoire" && wizardsAiMode(env)) throw new Error(REFUSED);
  return name;
}

export function resolveSession(name = "grimoire", policy = loadBrowserPolicy()) {
  const port = { grimoire: 9223, operator: 9222 }[name];
  if (!port) throw new Error(`BROWSER_SESSION_UNKNOWN: ${name}`);
  const profile = policyForPort(port, policy).profile;
  if (canonical(profile) === canonical(policyForPort(port === 9223 ? 9222 : 9223, policy).profile)) {
    throw new Error("BROWSER_SESSION_PROFILE_CONFLICT: operator and grimoire must have separate profiles");
  }
  return Object.freeze({ name, host: "127.0.0.1", port, profile });
}

export function sessionEnvironment(name, env = process.env, policy = loadBrowserPolicy()) {
  // Order: --session, AMAZON_BROWSER_SESSION, CDP_PORT, then the machine policy's
  // attended default. WIZARDS_AI_MODE defaults to grimoire and refuses operator.
  const portSession = managedSession(env.CDP_PORT);
  if (wizardsAiMode(env) && [name, env.AMAZON_BROWSER_SESSION, portSession].includes("operator")) {
    throw new Error(REFUSED);
  }
  const binding = resolveSession(name || env.AMAZON_BROWSER_SESSION || portSession
    || (wizardsAiMode(env) ? "grimoire" : sessionForPort(policy.routing.default_cdp_port, env)), policy);
  for (const [key, expected] of Object.entries({ AMAZON_BROWSER_SESSION: binding.name,
    CDP_HOST: binding.host, CDP_PORT: String(binding.port), CDP_PROFILE: binding.profile })) {
    if (!env[key]) continue;
    const equal = key === "CDP_PROFILE" ? canonical(env[key]) === canonical(expected)
      : key === "CDP_HOST" ? [expected, "localhost"].includes(env[key]) : env[key] === expected;
    if (!equal) throw new Error(`BROWSER_SESSION_CONFLICT: ${key} disagrees with ${binding.name}`);
  }
  return { AMAZON_BROWSER_SESSION: binding.name, CDP_HOST: binding.host,
    CDP_PORT: String(binding.port), CDP_PROFILE: binding.profile };
}

export function bindProcessSession() {
  // Isolated CDP fixtures use ephemeral ports, never a managed session name.
  if (!process.env.AMAZON_BROWSER_SESSION && process.env.CDP_PORT &&
      !managedSession(process.env.CDP_PORT)) return;
  Object.assign(process.env, sessionEnvironment(undefined));
}

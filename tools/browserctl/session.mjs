// One session binding per process. Call before importing any CDP client.
import { realpathSync } from "node:fs";
import { resolve } from "node:path";
import { homedir } from "node:os";
import { loadBrowserPolicy, policyForPort } from "./policy.mjs";

const canonical = (p) => {
  p = resolve(String(p).replace(/^~(?=\/|$)/, homedir()));
  try { return realpathSync(p); } catch { return p; }
};

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
  const binding = resolveSession(name || env.AMAZON_BROWSER_SESSION ||
    (env.CDP_PORT === "9222" ? "operator" : "grimoire"), policy);
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
      !["9222", "9223"].includes(process.env.CDP_PORT)) return;
  Object.assign(process.env, sessionEnvironment(undefined));
}

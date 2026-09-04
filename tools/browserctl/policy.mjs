import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";

export const RUNTIME_ROOT = resolve(
  process.env.AMAZON_BROWSER_RUNTIME_DIR || `${homedir()}/.amazon-agent/browser-runtime`,
);
export const POLICY_PATH = resolve(
  process.env.AMAZON_BROWSER_POLICY || `${RUNTIME_ROOT}/policy.json`,
);

const DEFAULT_ANCHORS = [
  {
    key: "US",
    url: "https://sellercentral.amazon.com/home",
    accepted_paths: ["/home", "/amazonsell/business"],
    auth_origins: ["https://www.amazon.com"],
  },
  {
    key: "DE",
    url: "https://sellercentral.amazon.de/home",
    accepted_paths: ["/home", "/amazonsell/business"],
    auth_origins: ["https://www.amazon.de"],
  },
  {
    key: "AUS",
    url: "https://sellercentral.amazon.com.au/home",
    accepted_paths: ["/home", "/amazonsell/business"],
    auth_origins: ["https://www.amazon.com.au"],
  },
];

function expandHome(value) {
  if (typeof value !== "string") return value;
  return value.replace(/^~(?=\/|$)/, homedir());
}

function defaultPort(port) {
  if (Number(port) === 9223) {
    return {
      mode: "headless",
      profile: `${homedir()}/.amazon-agent/wizards-ai-chrome`,
      start_url: DEFAULT_ANCHORS[0].url,
      anchors: DEFAULT_ANCHORS,
    };
  }
  return {
    mode: "headless",
    profile: `${homedir()}/.amazon-agent/chrome-debug`,
    start_url: DEFAULT_ANCHORS[0].url,
    anchors: DEFAULT_ANCHORS,
  };
}

function validateAnchor(anchor) {
  if (!anchor || typeof anchor.key !== "string" || typeof anchor.url !== "string") {
    throw new Error("BROWSER_POLICY_INVALID: every anchor needs key and url");
  }
  const url = new URL(anchor.url);
  if (url.protocol !== "https:") {
    throw new Error(`BROWSER_POLICY_INVALID: anchor ${anchor.key} must use HTTPS`);
  }
  return {
    key: anchor.key.toUpperCase(),
    url: url.href,
    accepted_paths: [...new Set((anchor.accepted_paths || [url.pathname]).map(String))],
    auth_origins: [...new Set((anchor.auth_origins || []).map((origin) => new URL(origin).origin))],
  };
}

function validatePort(port, input = {}) {
  const base = defaultPort(port);
  const mode = input.mode || base.mode;
  if (!new Set(["headed", "headless", "recovery"]).has(mode)) {
    throw new Error(`BROWSER_POLICY_INVALID: unsupported mode ${mode} on port ${port}`);
  }
  const windowClass = input.window_class || null;
  if (windowClass && !/^[A-Za-z0-9._-]+$/.test(windowClass)) {
    throw new Error(`BROWSER_POLICY_INVALID: unsafe window_class on port ${port}`);
  }
  const anchors = (input.anchors || base.anchors).map(validateAnchor);
  if (new Set(anchors.map((anchor) => anchor.key)).size !== anchors.length) {
    throw new Error(`BROWSER_POLICY_INVALID: duplicate anchor key on port ${port}`);
  }
  return {
    mode,
    profile: expandHome(input.profile || base.profile),
    chrome_bin: expandHome(input.chrome_bin || "") || null,
    window_class: windowClass,
    start_url: String(input.start_url || base.start_url),
    anchors,
  };
}

function positiveDuration(value, fallback, name) {
  const duration = Number(value ?? fallback);
  if (!Number.isFinite(duration) || duration <= 0) {
    throw new Error(`BROWSER_POLICY_INVALID: ${name} must be a positive duration`);
  }
  return duration;
}

export function loadBrowserPolicy(path = POLICY_PATH) {
  let raw = {};
  if (existsSync(path)) raw = JSON.parse(readFileSync(path, "utf8"));
  if (raw.schema_version != null && Number(raw.schema_version) !== 1) {
    throw new Error(`BROWSER_POLICY_INVALID: unsupported schema_version ${raw.schema_version}`);
  }
  const configuredPorts = raw.ports || {};
  const ports = {};
  for (const port of new Set(["9222", "9223", ...Object.keys(configuredPorts)])) {
    ports[port] = validatePort(port, configuredPorts[port]);
  }
  const cleanupMode = raw.cleanup?.mode || "audit";
  if (!new Set(["audit", "active"]).has(cleanupMode)) {
    throw new Error(`BROWSER_POLICY_INVALID: cleanup.mode must be audit or active`);
  }
  const adoptUnregisteredTabs = raw.cleanup?.adopt_unregistered_tabs ?? false;
  if (typeof adoptUnregisteredTabs !== "boolean") {
    throw new Error("BROWSER_POLICY_INVALID: cleanup.adopt_unregistered_tabs must be boolean");
  }
  const defaultPort = Number(raw.routing?.default_cdp_port ?? 9222);
  const wizardsPort = Number(raw.routing?.wizards_ai_cdp_port ?? 9223);
  const inAppPriority = raw.routing?.in_app_browser_priority || "explicit-only";
  const allowSilentFallback = raw.routing?.allow_silent_in_app_fallback ?? false;
  if (defaultPort !== 9222 || wizardsPort !== 9223
      || inAppPriority !== "explicit-only" || allowSilentFallback !== false) {
    throw new Error(
      "BROWSER_POLICY_INVALID: browser routing must default to CDP 9222, reserve 9223 for Wizards AI, and disable silent in-app fallback",
    );
  }
  return {
    schema_version: 1,
    path,
    cleanup: {
      mode: cleanupMode,
      adopt_unregistered_tabs: adoptUnregisteredTabs,
      background_grace_ms: positiveDuration(raw.cleanup?.background_grace_ms, 10 * 60 * 1000, "background_grace_ms"),
      interactive_idle_ms: positiveDuration(raw.cleanup?.interactive_idle_ms, 2 * 60 * 60 * 1000, "interactive_idle_ms"),
      heartbeat_interval_ms: positiveDuration(raw.cleanup?.heartbeat_interval_ms, 30 * 1000, "heartbeat_interval_ms"),
      heartbeat_stale_ms: positiveDuration(raw.cleanup?.heartbeat_stale_ms, 90 * 1000, "heartbeat_stale_ms"),
      auth_retry_cooldown_ms: positiveDuration(raw.cleanup?.auth_retry_cooldown_ms, 5 * 60 * 1000, "auth_retry_cooldown_ms"),
    },
    routing: {
      default_cdp_port: defaultPort,
      wizards_ai_cdp_port: wizardsPort,
      in_app_browser_priority: inAppPriority,
      allow_silent_in_app_fallback: false,
    },
    ports,
  };
}

export function policyForPort(port, policy = loadBrowserPolicy()) {
  const key = String(Number(port));
  if (!policy.ports[key]) throw new Error(`BROWSER_POLICY_INVALID: port ${port} is not configured`);
  return policy.ports[key];
}

export function anchorMatchesUrl(anchor, rawUrl) {
  let actual;
  let wanted;
  try {
    actual = new URL(rawUrl);
    wanted = new URL(anchor.url);
  } catch {
    return false;
  }
  if (actual.origin === wanted.origin) {
    return anchor.accepted_paths.some((path) => actual.pathname.replace(/\/$/, "") === path.replace(/\/$/, ""));
  }
  if (!anchor.auth_origins.includes(actual.origin)) return false;
  return /signin|auth|mfa|captcha|\/ap\/cvf|account-recovery/i.test(actual.pathname + actual.search);
}

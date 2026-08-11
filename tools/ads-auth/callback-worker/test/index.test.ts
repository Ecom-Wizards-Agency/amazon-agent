import { env, exports } from "cloudflare:workers";
import { describe, expect, it } from "vitest";

const START_URL = "https://auth.ecomwizards.agency/amazon/start";
const CALLBACK_URL = "https://auth.ecomwizards.agency/amazon/callback";
const NONCE_COOKIE = "__Host-ew_ads_oauth_nonce";

type StartResult = {
  state: string;
  cookie: string;
};

async function start(): Promise<StartResult> {
  const result = await exports.default.fetch(
    new Request(START_URL, { redirect: "manual" }),
  );
  expect(result.status).toBe(302);
  const location = new URL(result.headers.get("Location") ?? "");
  const state = location.searchParams.get("state");
  const setCookie = result.headers.get("Set-Cookie");
  expect(state).toBeTruthy();
  expect(setCookie).toBeTruthy();
  return {
    state: state ?? "",
    cookie: (setCookie ?? "").split(";", 1)[0] ?? "",
  };
}

function assertSecurityHeaders(result: Response): void {
  expect(result.headers.get("Cache-Control")).toBe("no-store, max-age=0");
  expect(result.headers.get("Content-Security-Policy")).toContain(
    "default-src 'none'",
  );
  expect(result.headers.get("Content-Security-Policy")).not.toContain(
    "'unsafe-inline'",
  );
  expect(result.headers.get("Referrer-Policy")).toBe("no-referrer");
  expect(result.headers.get("X-Content-Type-Options")).toBe("nosniff");
  expect(result.headers.get("X-Frame-Options")).toBe("DENY");
}

async function assertStyleAllowedByCsp(
  result: Response,
  body: string,
): Promise<void> {
  const style = body.match(/<style>([^<]+)<\/style>/u)?.[1];
  expect(style).toBeTruthy();
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(style ?? ""),
  );
  const hash = btoa(String.fromCharCode(...new Uint8Array(digest)));
  expect(result.headers.get("Content-Security-Policy")).toContain(
    `'sha256-${hash}'`,
  );
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

async function signedState(
  nonce: string,
  issuedAt: number,
  expiresAt: number,
): Promise<string> {
  const encoded = base64Url(new TextEncoder().encode(JSON.stringify({
    v: 1,
    iat: issuedAt,
    exp: expiresAt,
    nonce,
  })));
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(env.STATE_SIGNING_KEY),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(encoded),
  );
  return `${encoded}.${base64Url(new Uint8Array(signature))}`;
}

describe("Amazon Ads OAuth callback Worker", () => {
  it("serves a no-store health response with security headers", async () => {
    const result = await exports.default.fetch(
      new Request("https://auth.ecomwizards.agency/health"),
    );
    expect(result.status).toBe(200);
    await expect(result.json()).resolves.toEqual({ status: "ok" });
    assertSecurityHeaders(result);
  });

  it("starts authorization with the exact Amazon parameters and secure cookie", async () => {
    const result = await exports.default.fetch(
      new Request(START_URL, { redirect: "manual" }),
    );
    const location = new URL(result.headers.get("Location") ?? "");
    expect(location.origin + location.pathname).toBe(
      "https://na.account.amazon.com/ap/oa",
    );
    expect(location.searchParams.get("client_id")).toBe(
      "amzn1.application-oa2-client.6c760c65ad124a44bae67ac27e5669ae",
    );
    expect(location.searchParams.get("scope")).toBe(
      "advertising::campaign_management",
    );
    expect(location.searchParams.get("response_type")).toBe("code");
    expect(location.searchParams.get("redirect_uri")).toBe(
      CALLBACK_URL,
    );
    expect(location.searchParams.get("state")).toBeTruthy();
    const cookie = result.headers.get("Set-Cookie") ?? "";
    expect(cookie).toContain(`${NONCE_COOKIE}=`);
    expect(cookie).toContain("Max-Age=900");
    expect(cookie).toContain("HttpOnly");
    expect(cookie).toContain("Secure");
    expect(cookie).toContain("SameSite=Lax");
    assertSecurityHeaders(result);
  });

  it("accepts a valid browser-bound state and escapes the authorization code", async () => {
    const { state, cookie } = await start();
    const code = '<script>alert("x")</script>&secret';
    const url = new URL(CALLBACK_URL);
    url.searchParams.set("state", state);
    url.searchParams.set("code", code);
    const result = await exports.default.fetch(
      new Request(url, { headers: { Cookie: cookie } }),
    );
    const body = await result.text();
    expect(result.status).toBe(200);
    expect(body).not.toContain(code);
    expect(body).toContain("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;&amp;secret");
    expect(result.headers.get("Set-Cookie")).toContain("Max-Age=0");
    assertSecurityHeaders(result);
    await assertStyleAllowedByCsp(result, body);
  });

  it("rejects a missing state", async () => {
    const result = await exports.default.fetch(
      new Request(`${CALLBACK_URL}?code=test`),
    );
    expect(result.status).toBe(400);
    expect(await result.text()).toContain("could not be verified");
    expect(result.headers.get("Set-Cookie")).toContain("Max-Age=0");
  });

  it("rejects a tampered state", async () => {
    const { state, cookie } = await start();
    const tampered = `${state.slice(0, -1)}${state.endsWith("A") ? "B" : "A"}`;
    const url = new URL(CALLBACK_URL);
    url.searchParams.set("state", tampered);
    url.searchParams.set("code", "test");
    const result = await exports.default.fetch(
      new Request(url, { headers: { Cookie: cookie } }),
    );
    expect(result.status).toBe(400);
  });

  it("rejects a state opened with a different browser nonce", async () => {
    const { state } = await start();
    const url = new URL(CALLBACK_URL);
    url.searchParams.set("state", state);
    url.searchParams.set("code", "test");
    const result = await exports.default.fetch(new Request(url, {
      headers: { Cookie: `${NONCE_COOKIE}=wrong-browser-nonce` },
    }));
    expect(result.status).toBe(400);
  });

  it("rejects an expired state", async () => {
    const nonce = "A".repeat(43);
    const now = Math.floor(Date.now() / 1000);
    const state = await signedState(nonce, now - 901, now - 1);
    const url = new URL(CALLBACK_URL);
    url.searchParams.set("state", state);
    url.searchParams.set("code", "test");
    const result = await exports.default.fetch(new Request(url, {
      headers: { Cookie: `${NONCE_COOKIE}=${nonce}` },
    }));
    expect(result.status).toBe(400);
  });

  it("handles Amazon denial without exposing an authorization code", async () => {
    const { state, cookie } = await start();
    const url = new URL(CALLBACK_URL);
    url.searchParams.set("state", state);
    url.searchParams.set("error", "access_denied");
    url.searchParams.set("error_description", "The user denied access <test>.");
    const result = await exports.default.fetch(
      new Request(url, { headers: { Cookie: cookie } }),
    );
    const body = await result.text();
    expect(result.status).toBe(200);
    expect(body).toContain("The user denied access &lt;test&gt;.");
    expect(body).toContain("No token was created or stored");
    expect(result.headers.get("Set-Cookie")).toContain("Max-Age=0");
  });

  it("rejects a verified response with no code", async () => {
    const { state, cookie } = await start();
    const url = new URL(CALLBACK_URL);
    url.searchParams.set("state", state);
    const result = await exports.default.fetch(
      new Request(url, { headers: { Cookie: cookie } }),
    );
    expect(result.status).toBe(400);
    expect(await result.text()).toContain("Authorization code is missing");
  });

  it("rejects unsupported methods", async () => {
    const result = await exports.default.fetch(
      new Request(START_URL, { method: "POST" }),
    );
    expect(result.status).toBe(405);
    expect(result.headers.get("Allow")).toBe("GET");
    assertSecurityHeaders(result);
  });

  it("returns a secure 404 for unknown routes", async () => {
    const result = await exports.default.fetch(
      new Request("https://auth.ecomwizards.agency/nope"),
    );
    expect(result.status).toBe(404);
    assertSecurityHeaders(result);
  });
});

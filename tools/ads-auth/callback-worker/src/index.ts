const STATE_VERSION = 1;
const STATE_TTL_SECONDS = 15 * 60;
const NONCE_BYTES = 32;
const NONCE_COOKIE = "__Host-ew_ads_oauth_nonce";
const PAGE_STYLE =
  ":root{color-scheme:light;font-family:system-ui,sans-serif}" +
  "body{margin:0;background:#f6f7f9;color:#17212b}" +
  "main{max-width:720px;margin:10vh auto;padding:32px;background:white;" +
  "border:1px solid #dce1e7;border-radius:14px;box-shadow:0 12px 34px #17212b14}" +
  "h1{margin-top:0;font-size:1.65rem}p{line-height:1.55}" +
  "code,input{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}" +
  "input{width:100%;box-sizing:border-box;padding:12px;border:1px solid #aeb8c4;" +
  "border-radius:8px;font-size:.95rem}.note{color:#4b5b6b;font-size:.93rem}";

const textEncoder = new TextEncoder();

type OAuthState = {
  v: number;
  iat: number;
  exp: number;
  nonce: string;
};

const SECURITY_HEADERS: Readonly<Record<string, string>> = {
  "Cache-Control": "no-store, max-age=0",
  Pragma: "no-cache",
  Expires: "0",
  "Content-Security-Policy":
    "default-src 'none'; " +
    "style-src 'sha256-mr+to6UuO++Cf1aphhKH7CE2XRBhGJgLYRImIHUHDNI='; " +
    "base-uri 'none'; " +
    "form-action 'none'; frame-ancestors 'none'",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Permissions-Policy":
    "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
};

function response(
  body: BodyInit | null,
  init: ResponseInit = {},
  additionalHeaders: HeadersInit = {},
): Response {
  const headers = new Headers(SECURITY_HEADERS);
  new Headers(additionalHeaders).forEach((value, name) => {
    headers.set(name, value);
  });
  return new Response(body, { ...init, headers });
}

function htmlResponse(
  title: string,
  heading: string,
  message: string,
  status = 200,
  additionalHeaders: HeadersInit = {},
): Response {
  const safeTitle = escapeHtml(title);
  const safeHeading = escapeHtml(heading);
  const body = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${safeTitle}</title>
  <style>${PAGE_STYLE}</style>
</head>
<body>
  <main>
    <h1>${safeHeading}</h1>
    ${message}
  </main>
</body>
</html>`;
  const headers = new Headers(additionalHeaders);
  headers.set("Content-Type", "text/html; charset=utf-8");
  return response(body, { status }, headers);
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    };
    return entities[character] ?? character;
  });
}

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function base64UrlToBytes(value: string): Uint8Array<ArrayBuffer> | null {
  if (!/^[A-Za-z0-9_-]+$/u.test(value)) return null;
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  try {
    const binary = atob(value.replaceAll("-", "+").replaceAll("_", "/") + padding);
    return Uint8Array.from(binary, (character) => character.charCodeAt(0));
  } catch {
    return null;
  }
}

function randomNonce(): string {
  const bytes = new Uint8Array(NONCE_BYTES);
  crypto.getRandomValues(bytes);
  return bytesToBase64Url(bytes);
}

async function signingKey(secret: string): Promise<CryptoKey> {
  if (textEncoder.encode(secret).byteLength < 32) {
    throw new Error("STATE_SIGNING_KEY must contain at least 32 bytes");
  }
  return crypto.subtle.importKey(
    "raw",
    textEncoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

async function createState(secret: string, nonce: string): Promise<string> {
  const issuedAt = Math.floor(Date.now() / 1000);
  const payload: OAuthState = {
    v: STATE_VERSION,
    iat: issuedAt,
    exp: issuedAt + STATE_TTL_SECONDS,
    nonce,
  };
  const encodedPayload = bytesToBase64Url(
    textEncoder.encode(JSON.stringify(payload)),
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    await signingKey(secret),
    textEncoder.encode(encodedPayload),
  );
  return `${encodedPayload}.${bytesToBase64Url(new Uint8Array(signature))}`;
}

async function verifyState(
  secret: string,
  state: string | null,
  cookieNonce: string | null,
): Promise<boolean> {
  if (!state || !cookieNonce || state.length > 1024) return false;
  const parts = state.split(".");
  if (parts.length !== 2) return false;
  const [encodedPayload, encodedSignature] = parts;
  if (!encodedPayload || !encodedSignature) return false;

  const signature = base64UrlToBytes(encodedSignature);
  const payloadBytes = base64UrlToBytes(encodedPayload);
  if (!signature || !payloadBytes) return false;

  const key = await signingKey(secret);
  const signatureIsValid = await crypto.subtle.verify(
    "HMAC",
    key,
    signature,
    textEncoder.encode(encodedPayload),
  );
  if (!signatureIsValid) return false;

  let payload: unknown;
  try {
    payload = JSON.parse(new TextDecoder().decode(payloadBytes));
  } catch {
    return false;
  }
  if (!isOAuthState(payload)) return false;

  const now = Math.floor(Date.now() / 1000);
  if (payload.exp < now || payload.iat > now + 30) return false;
  if (payload.exp - payload.iat !== STATE_TTL_SECONDS) return false;

  const stateNonceSignature = await crypto.subtle.sign(
    "HMAC",
    key,
    textEncoder.encode(payload.nonce),
  );
  return crypto.subtle.verify(
    "HMAC",
    key,
    stateNonceSignature,
    textEncoder.encode(cookieNonce),
  );
}

function isOAuthState(value: unknown): value is OAuthState {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    candidate.v === STATE_VERSION &&
    Number.isInteger(candidate.iat) &&
    Number.isInteger(candidate.exp) &&
    typeof candidate.nonce === "string" &&
    candidate.nonce.length === 43
  );
}

function cookieValue(request: Request, name: string): string | null {
  const cookieHeader = request.headers.get("Cookie");
  if (!cookieHeader) return null;
  for (const segment of cookieHeader.split(";")) {
    const [cookieName, ...valueParts] = segment.trim().split("=");
    if (cookieName === name) return valueParts.join("=");
  }
  return null;
}

function nonceCookie(nonce: string): string {
  return `${NONCE_COOKIE}=${nonce}; Path=/; Max-Age=${STATE_TTL_SECONDS}; ` +
    "HttpOnly; Secure; SameSite=Lax";
}

function clearedNonceCookie(): string {
  return `${NONCE_COOKIE}=; Path=/; Max-Age=0; ` +
    "Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax";
}

async function startAuthorization(env: Env): Promise<Response> {
  const nonce = randomNonce();
  const state = await createState(env.STATE_SIGNING_KEY, nonce);
  const authorizeUrl = new URL(env.AMAZON_AUTHORIZE_URL);
  authorizeUrl.search = new URLSearchParams({
    client_id: env.CLIENT_ID,
    scope: env.OAUTH_SCOPE,
    response_type: "code",
    redirect_uri: env.REDIRECT_URI,
    state,
  }).toString();
  return response(null, { status: 302 }, {
    Location: authorizeUrl.toString(),
    "Set-Cookie": nonceCookie(nonce),
  });
}

async function handleCallback(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const validState = await verifyState(
    env.STATE_SIGNING_KEY,
    url.searchParams.get("state"),
    cookieValue(request, NONCE_COOKIE),
  );
  const clearCookie = { "Set-Cookie": clearedNonceCookie() };
  if (!validState) {
    return htmlResponse(
      "Invalid Amazon authorization response",
      "Authorization could not be verified",
      "<p>The security state was missing, expired, altered, or opened in a different browser session. Start again from <code>/amazon/start</code>.</p>",
      400,
      clearCookie,
    );
  }

  const amazonError = url.searchParams.get("error");
  if (amazonError) {
    const description = url.searchParams.get("error_description") ??
      "Amazon did not grant access.";
    return htmlResponse(
      "Amazon authorization not granted",
      "Authorization was not granted",
      `<p>${escapeHtml(description)}</p><p class="note">No token was created or stored. You can close this page.</p>`,
      200,
      clearCookie,
    );
  }

  const code = url.searchParams.get("code");
  if (!code) {
    return htmlResponse(
      "Missing Amazon authorization code",
      "Authorization code is missing",
      "<p>Amazon returned a verified response without an authorization code. Start again from <code>/amazon/start</code>.</p>",
      400,
      clearCookie,
    );
  }

  const safeCode = escapeHtml(code);
  return htmlResponse(
    "Amazon authorization code ready",
    "Amazon authorization received",
    `<p>Copy this short-lived code now:</p>
    <input type="text" readonly value="${safeCode}" aria-label="Authorization code">
    <p>In a local terminal, run <code>python3 tools/ads-auth/exchange_token.py auth</code> and paste the code when prompted.</p>
    <p class="note">Exchange it within five minutes, then close this page. The code and tokens are not stored by this callback.</p>`,
    200,
    clearCookie,
  );
}

async function route(request: Request, env: Env): Promise<Response> {
  if (request.method !== "GET") {
    return response("Method Not Allowed\n", { status: 405 }, {
      Allow: "GET",
      "Content-Type": "text/plain; charset=utf-8",
    });
  }

  const { pathname } = new URL(request.url);
  if (pathname === "/health") {
    return response(JSON.stringify({ status: "ok" }), { status: 200 }, {
      "Content-Type": "application/json; charset=utf-8",
    });
  }
  if (pathname === "/amazon/start") return startAuthorization(env);
  if (pathname === "/amazon/callback") return handleCallback(request, env);
  return response("Not Found\n", { status: 404 }, {
    "Content-Type": "text/plain; charset=utf-8",
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      return await route(request, env);
    } catch {
      return response("Internal Server Error\n", { status: 500 }, {
        "Content-Type": "text/plain; charset=utf-8",
      });
    }
  },
} satisfies ExportedHandler<Env>;

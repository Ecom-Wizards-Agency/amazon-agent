#!/usr/bin/env python3
"""SP-API OAuth helper: exchange an authorization redirect URL for a refresh
token, store it locally, and smoke-test the grant.

Usage (run these yourself in a terminal; tokens never leave _local/):

  python3 tools/spapi-auth/exchange_token.py auth
      Prompts for the full redirect URL you landed on after the Seller
      Central consent screen (contains spapi_oauth_code=...). Exchanges the
      code and saves the refresh token to _local/spapi/tokens.json keyed by
      selling_partner_id. The code expires ~5 minutes after consent, so run
      this right away.

  python3 tools/spapi-auth/exchange_token.py test <selling_partner_id>
      Uses the stored refresh token to call GET /sellers/v1/marketplaceParticipations
      (tries NA, then EU, then FE) and prints the marketplaces the grant covers.

Setup: _local/spapi/config.json must exist with the app client credentials
from Developer Central > your app > View:

  {"client_id": "amzn1.application-oa2-client....", "client_secret": "..."}
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_DIR = ROOT / "_local" / "spapi"
CONFIG_PATH = LOCAL_DIR / "config.json"
TOKENS_PATH = LOCAL_DIR / "tokens.json"

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
SPAPI_HOSTS = {
    "na": "https://sellingpartnerapi-na.amazon.com",
    "eu": "https://sellingpartnerapi-eu.amazon.com",
    "fe": "https://sellingpartnerapi-fe.amazon.com",
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        die(f"missing {CONFIG_PATH}. Create it with client_id + client_secret "
            "from Developer Central (View credentials on the app client).")
    cfg = json.loads(CONFIG_PATH.read_text())
    for key in ("client_id", "client_secret"):
        if not cfg.get(key):
            die(f"{CONFIG_PATH} is missing '{key}'")
    return cfg


def lwa_request(payload: dict) -> dict:
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(LWA_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        die(f"LWA token endpoint returned {e.code}: {body}")


def mask(value: str) -> str:
    return value[:6] + "..." + value[-4:] if len(value) > 12 else "***"


def cmd_auth() -> None:
    cfg = load_config()
    url = input("Paste the full redirect URL from the address bar: ").strip()
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    code = (query.get("spapi_oauth_code") or [None])[0]
    seller_id = (query.get("selling_partner_id") or [None])[0]
    if not code:
        die("no spapi_oauth_code found in that URL. Make sure you copied the "
            "final URL after clicking Confirm on the consent screen.")
    result = lwa_request({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    })
    refresh_token = result.get("refresh_token")
    if not refresh_token:
        die(f"no refresh_token in LWA response: {json.dumps(result)[:200]}")
    tokens = json.loads(TOKENS_PATH.read_text()) if TOKENS_PATH.exists() else {}
    tokens[seller_id or "unknown"] = {"refresh_token": refresh_token}
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(json.dumps(tokens, indent=2) + "\n")
    print(f"OK: refresh token {mask(refresh_token)} saved for "
          f"selling_partner_id={seller_id} -> {TOKENS_PATH}")
    print(f"Next: python3 {Path(__file__).relative_to(ROOT)} test {seller_id}")


def cmd_test(seller_id: str) -> None:
    cfg = load_config()
    if not TOKENS_PATH.exists():
        die(f"no {TOKENS_PATH}; run the auth step first")
    tokens = json.loads(TOKENS_PATH.read_text())
    entry = tokens.get(seller_id) or die(f"no token stored for '{seller_id}'. "
                                         f"Known: {', '.join(tokens)}")
    access = lwa_request({
        "grant_type": "refresh_token",
        "refresh_token": entry["refresh_token"],
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }).get("access_token") or die("no access_token in LWA response")
    for region, host in SPAPI_HOSTS.items():
        req = urllib.request.Request(f"{host}/sellers/v1/marketplaceParticipations")
        req.add_header("x-amz-access-token", access)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"{region.upper()}: HTTP {e.code}")
            continue
        rows = payload.get("payload", [])
        names = [p.get("marketplace", {}).get("countryCode", "?") for p in rows]
        print(f"{region.upper()}: {len(rows)} marketplaces: {', '.join(names) or '-'}")
    print("Done. Any region listing marketplaces means the grant is LIVE.")


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "auth":
        cmd_auth()
    elif len(sys.argv) >= 3 and sys.argv[1] == "test":
        cmd_test(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()

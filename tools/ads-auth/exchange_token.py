#!/usr/bin/env python3
"""Amazon Ads API OAuth helper: turn the one-time consent redirect into a
refresh token, store it in _local/ads-monitor/config.json, and smoke-test
the grant by listing advertiser profiles in all three regions.

Usage (run these yourself in a terminal; tokens never leave _local/):

  python3 tools/ads-auth/exchange_token.py url
      Prints the consent URL to open in the browser. Sign in with the main
      agency login (the one that manages all client ad accounts) and click
      Allow. You land on the redirect URL with ?code=... in the address bar.

  python3 tools/ads-auth/exchange_token.py auth
      Prompts for that full redirect URL, exchanges the code for a refresh
      token, and merges it into _local/ads-monitor/config.json under "lwa"
      (existing keys in the file are preserved). The code expires within
      minutes of consent, so run this right away.

  python3 tools/ads-auth/exchange_token.py test
      Uses the stored refresh token to call GET /v2/profiles on the NA, EU,
      and FE hosts and prints every advertiser profile the grant covers
      (profile ID, country, account name). Copy the profile IDs you need
      into config.accounts[].

Setup: _local/ads-monitor/config.json needs the LWA app credentials first
(developer.amazon.com > Login with Amazon > security profile "Ecom Wizards
Ads Tool" > Web Settings):

  "lwa": {"client_id": "amzn1.application-oa2-client....",
          "client_secret": "...",
          "redirect_uri": "https://ecomwizards.com/amazon/callback"}

The redirect_uri must also be listed as an Allowed Return URL in that same
Web Settings screen, or Amazon rejects the consent page.

Prerequisite that is easy to miss: API approval alone does not give the LWA
app advertising scopes. The "Assign API access" step at
https://advertising.amazon.com/developer/overview links the approval to the
security profile. Until that is done, the consent page fails with "This LWA
app doesn't have access to the Amazon Ads API scopes" and the profile shows
only profile/profile:name scopes. Assign it while signed in as the SAME
Amazon user account that requested API access; a mismatch can only be undone
by ads-api-onboarding@amazon.com.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "_local" / "ads-monitor" / "config.json"

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
CONSENT_URL = "https://www.amazon.com/ap/oa"
SCOPE = "advertising::campaign_management"
ADS_HOSTS = {
    "na": "https://advertising-api.amazon.com",
    "eu": "https://advertising-api-eu.amazon.com",
    "fe": "https://advertising-api-fe.amazon.com",
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        die(f"missing {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def lwa_block(cfg: dict, *required: str) -> dict:
    lwa = cfg.get("lwa") or {}
    for key in required:
        if not lwa.get(key):
            die(f"config.json 'lwa' block is missing '{key}'. See the setup "
                "note in this script's docstring.")
    return lwa


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


def cmd_url() -> None:
    lwa = lwa_block(load_config(), "client_id", "redirect_uri")
    params = urllib.parse.urlencode({
        "client_id": lwa["client_id"],
        "scope": SCOPE,
        "response_type": "code",
        "redirect_uri": lwa["redirect_uri"],
    })
    print("Open this in the browser, signed in as the main agency login:\n")
    print(f"{CONSENT_URL}?{params}")
    print("\nAfter clicking Allow, copy the full URL you land on and run:")
    print(f"  python3 {Path(__file__).relative_to(ROOT)} auth")


def cmd_auth() -> None:
    cfg = load_config()
    lwa = lwa_block(cfg, "client_id", "client_secret", "redirect_uri")
    url = input("Paste the full redirect URL from the address bar: ").strip()
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    code = (query.get("code") or [None])[0]
    if not code:
        die("no code= found in that URL. Make sure you copied the final URL "
            "after clicking Allow on the consent screen.")
    result = lwa_request({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": lwa["client_id"],
        "client_secret": lwa["client_secret"],
        "redirect_uri": lwa["redirect_uri"],
    })
    refresh_token = result.get("refresh_token")
    if not refresh_token:
        die(f"no refresh_token in LWA response: {json.dumps(result)[:200]}")
    cfg.setdefault("lwa", {})["refresh_token"] = refresh_token
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"OK: refresh token {mask(refresh_token)} merged into {CONFIG_PATH}")
    print(f"Next: python3 {Path(__file__).relative_to(ROOT)} test")


def cmd_test() -> None:
    lwa = lwa_block(load_config(), "client_id", "client_secret", "refresh_token")
    access = lwa_request({
        "grant_type": "refresh_token",
        "refresh_token": lwa["refresh_token"],
        "client_id": lwa["client_id"],
        "client_secret": lwa["client_secret"],
    }).get("access_token") or die("no access_token in LWA response")
    total = 0
    for region, host in ADS_HOSTS.items():
        req = urllib.request.Request(f"{host}/v2/profiles")
        req.add_header("Authorization", f"Bearer {access}")
        req.add_header("Amazon-Ads-ClientId", lwa["client_id"])
        req.add_header("Amazon-Advertising-API-ClientId", lwa["client_id"])
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                profiles = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"{region.upper()}: HTTP {e.code} {e.read().decode(errors='replace')[:200]}")
            continue
        print(f"{region.upper()}: {len(profiles)} profiles")
        for p in profiles:
            info = p.get("accountInfo", {})
            print(f"  {p.get('profileId')}  {p.get('countryCode', '?')}  "
                  f"{info.get('type', '?')}  {info.get('name', '?')}")
        total += len(profiles)
    print(f"Done. {total} profiles total. Any profile listed means the grant "
          "is LIVE; copy the IDs you need into config.accounts[].")


def main() -> None:
    cmds = {"url": cmd_url, "auth": cmd_auth, "test": cmd_test}
    if len(sys.argv) >= 2 and sys.argv[1] in cmds:
        cmds[sys.argv[1]]()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()

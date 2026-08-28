#!/usr/bin/env python3
"""Amazon Ads API OAuth helper: turn the one-time consent redirect into a
refresh token, store it in _local/ads-monitor/config.json, and smoke-test
the grant by listing advertiser profiles in all three regions.

Usage (run these yourself in a terminal; tokens never leave _local/):

  python3 tools/ads-auth/exchange_token.py configure
      Securely prompts for the LWA client secret without echoing it and stores
      it in the ignored local configuration. The public client ID and exact
      redirect URI are filled automatically.

  python3 tools/ads-auth/exchange_token.py url
      Prints the secure Ecom Wizards start URL. Open it while signed in as
      amazon@ecomwizards.agency and click Allow.

  python3 tools/ads-auth/exchange_token.py auth
      Prompts without echo for either the displayed authorization code or the
      full callback URL. It exchanges the code immediately, merges the refresh
      token into _local/ads-monitor/config.json, and tests all three regions.

  python3 tools/ads-auth/exchange_token.py test
      Uses the stored refresh token to call GET /v2/profiles on the NA, EU,
      and FE hosts and prints every advertiser profile the grant covers
      (profile ID, country, account name). Copy the profile IDs you need
      into config.accounts[].

Setup: run the configure command and enter the LWA client secret locally. Do
not paste it into chat. The resulting ignored config block is:

  "lwa": {"client_id": "amzn1.application-oa2-client.6c760...",
          "client_secret": "...",
          "redirect_uri": "https://auth.ecomwizards.agency/amazon/callback"}

The redirect_uri must also be listed as an Allowed Return URL in that same
Web Settings screen, or Amazon rejects the consent page.

Prerequisite that is easy to miss: API approval alone does not give the LWA
app advertising scopes. The "Assign API access" step at
https://advertising.amazon.com/developer/overview links the approval to the
security profile. Until that is done, the consent page fails with "This LWA
app doesn't have access to the Amazon Ads API scopes" and the profile shows
only profile/profile:name scopes. Assign it while signed in as the same Amazon
user account that requested API access. If Amazon says another person initiated
onboarding, follow the Jira service-desk instruction shown on that page.
"""

import getpass
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "_local" / "ads-monitor" / "config.json"

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
START_URL = "https://auth.ecomwizards.agency/amazon/start"
CLIENT_ID = "amzn1.application-oa2-client.6c760c65ad124a44bae67ac27e5669ae"
REDIRECT_URI = "https://auth.ecomwizards.agency/amazon/callback"
ADS_HOSTS = {
    "na": "https://advertising-api.amazon.com",
    "eu": "https://advertising-api-eu.amazon.com",
    "fe": "https://advertising-api-fe.amazon.com",
}


def die(msg: str) -> NoReturn:
    print(f"ERROR: {msg}")
    sys.exit(1)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        die(f"missing {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def write_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=CONFIG_PATH.parent, prefix="config.", suffix=".tmp",
            delete=False
        ) as temp:
            json.dump(cfg, temp, indent=2)
            temp.write("\n")
            temp_path = Path(temp.name)
        temp_path.chmod(0o600)
        os.replace(temp_path, CONFIG_PATH)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


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
        try:
            error_body = json.loads(body)
        except json.JSONDecodeError:
            error_body = {}
        error = error_body.get("error", "request_failed")
        description = error_body.get(
            "error_description", "No safe error details returned"
        )
        die(f"LWA token endpoint returned {e.code}: {error}: {description}")


def mask(value: str) -> str:
    return value[:6] + "..." + value[-4:] if len(value) > 12 else "***"


def validate_public_config(lwa: dict) -> None:
    if lwa.get("client_id") not in (None, CLIENT_ID):
        die("config.json contains a different LWA client_id")
    if lwa.get("redirect_uri") not in (None, REDIRECT_URI):
        die("config.json contains a different redirect_uri")


def cmd_configure() -> None:
    cfg = load_config()
    lwa = cfg.setdefault("lwa", {})
    validate_public_config(lwa)
    client_secret = getpass.getpass("Enter the LWA client secret (input hidden): ").strip()
    if not client_secret:
        die("client secret cannot be empty")
    lwa.update({
        "client_id": CLIENT_ID,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
    })
    write_config(cfg)
    print(f"OK: LWA configuration stored locally in {CONFIG_PATH} with mode 600")
    print(f"Next: python3 {Path(__file__).relative_to(ROOT)} url")


def cmd_url() -> None:
    print("Only continue if Amazon's developer overview lists the Ads API scope.")
    print("Open this in the browser, signed in as amazon@ecomwizards.agency:\n")
    print(START_URL)
    print("\nAfter clicking Allow, copy the displayed code and run immediately:")
    print(f"  python3 {Path(__file__).relative_to(ROOT)} auth")


def authorization_code(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme and parsed.netloc:
        query = urllib.parse.parse_qs(parsed.query)
        if query.get("error"):
            description = (query.get("error_description") or query["error"])[0]
            die(f"Amazon did not grant access: {description}")
        code = (query.get("code") or [""])[0].strip()
        if not code:
            die("no code= found in that callback URL")
        return code
    code = value.strip()
    if not code:
        die("authorization code cannot be empty")
    return code


def cmd_auth() -> None:
    cfg = load_config()
    lwa = lwa_block(cfg, "client_secret")
    validate_public_config(lwa)
    value = getpass.getpass(
        "Paste the authorization code or full callback URL (input hidden): "
    ).strip()
    code = authorization_code(value)
    result = lwa_request({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": lwa["client_secret"],
        "redirect_uri": REDIRECT_URI,
    })
    refresh_token = result.get("refresh_token")
    if not refresh_token:
        safe_keys = ", ".join(sorted(result.keys()))
        die(f"no refresh_token in LWA response (returned keys: {safe_keys})")
    cfg.setdefault("lwa", {}).update({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "refresh_token": refresh_token,
    })
    write_config(cfg)
    print(f"OK: refresh token {mask(refresh_token)} merged into {CONFIG_PATH}")
    print("Testing advertiser profiles in NA, EU, and FE now.")
    test_profiles(cfg)


def test_profiles(cfg: dict) -> None:
    lwa = lwa_block(cfg, "client_id", "client_secret", "refresh_token")
    validate_public_config(lwa)
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
        req.add_header("Amazon-Advertising-API-ClientId", lwa["client_id"])
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                profiles = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            e.read()
            print(f"{region.upper()}: HTTP {e.code} request_failed")
            continue
        print(f"{region.upper()}: {len(profiles)} profiles")
        for p in profiles:
            info = p.get("accountInfo", {})
            print(f"  {p.get('profileId')}  {p.get('countryCode', '?')}  "
                  f"{info.get('type', '?')}  {info.get('name', '?')}")
        total += len(profiles)
    print(f"Done. {total} profiles total. Any profile listed means the grant "
          "is LIVE; copy the IDs you need into config.accounts[].")


def cmd_test() -> None:
    test_profiles(load_config())


def main() -> None:
    cmds = {
        "configure": cmd_configure,
        "url": cmd_url,
        "auth": cmd_auth,
        "test": cmd_test,
    }
    if len(sys.argv) >= 2 and sys.argv[1] in cmds:
        cmds[sys.argv[1]]()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()

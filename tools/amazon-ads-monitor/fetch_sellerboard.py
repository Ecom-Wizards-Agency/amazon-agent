#!/usr/bin/env python3
"""fetch_sellerboard.py -- save one brand's Sellerboard feed CSV locally.

Reads the brand's private feed URL from the gitignored manifest
`_local/ads-monitor/sellerboard-feeds.json`, sends one GET from this
machine and saves the CSV under
`_local/ads-monitor/inbox/<slug>/fetched/<slug>_dashboardtotals_<date>.csv`
(mode 0600). The feed URL carries an access token, so it goes to nobody
but the feed's own host: never to Firecrawl, Monid, a browser or any other
third-party fetcher.

Standard library only. The URL, its query and the token are never printed,
including inside exception text: failures report the exception class and
HTTP status only.

Manifest shape (the same one wizards-ai's weekly reporter reads):

    {"feeds": {"<slug>": "<url>" | {"url": "<url>", "allowed_hosts": [...]}},
     "allowed_hosts": [...]}

An empty `url` means the feed is not configured. Requests go over https
only, to the configured URL's own host plus any hostnames listed in the
optional `allowed_hosts` (per feed or top level). A redirect is followed
only inside that set.

Fetched files sit in a `fetched/` subfolder because wizards-ai's weekly
reporter treats every top-level `inbox/<slug>/*.csv` as weekly input.

    python3 tools/amazon-ads-monitor/fetch_sellerboard.py --account acme

Exit codes: 0 saved, 1 manifest missing or unreadable, 2 usage error,
3 blank feed (nothing saved), 4 fetch failed, 5 refused (not https, or a
host outside the allowed set), 6 feed not configured (no network call).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "_local" / "ads-monitor" / "sellerboard-feeds.json"
DEFAULT_INBOX = REPO_ROOT / "_local" / "ads-monitor" / "inbox"
FETCHED_SUBDIR = "fetched"
MAX_BYTES = 25 * 1024 * 1024
TIMEOUT_SECONDS = 90
USER_AGENT = "EcomWizards-AdsMonitor/1.0"
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

EXIT_SAVED = 0
EXIT_MANIFEST = 1
EXIT_BLANK = 3
EXIT_FETCH_FAILED = 4
EXIT_REFUSED = 5
EXIT_NOT_CONFIGURED = 6

# Extra urllib handlers for the offline selftest (a fake HTTPS handler).
# Empty in normal use.
_EXTRA_HANDLERS: tuple = ()


class HostRefused(Exception):
    """A request or redirect target outside the allowed https hosts.

    Carries no message so the URL can never leak through it."""


class _HostLockedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: frozenset):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not url_allowed(newurl, self.allowed_hosts):
            fp.close()
            raise HostRefused()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _hostname(url: str):
    try:
        return urllib.parse.urlsplit(url).hostname
    except ValueError:
        return None


def url_allowed(url: str, allowed_hosts: frozenset) -> bool:
    try:
        scheme = urllib.parse.urlsplit(url).scheme.lower()
    except ValueError:
        return False
    host = _hostname(url)
    return scheme == "https" and bool(host) and host in allowed_hosts


def _host_list(value) -> list:
    if not isinstance(value, list):
        return []
    return [item.strip().lower() for item in value if isinstance(item, str) and item.strip()]


def load_feed(manifest_path: Path, slug: str):
    """Return (url, extra_hosts) for the slug; url is "" when not configured.

    Raises ValueError (no message) when the manifest is unreadable."""
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError() from None
    if not isinstance(payload, dict):
        raise ValueError()
    feeds = payload.get("feeds")
    extra = []
    if isinstance(feeds, dict):
        extra = _host_list(payload.get("allowed_hosts"))
    else:
        feeds = payload
    raw = feeds.get(slug)
    if isinstance(raw, str):
        return raw.strip(), extra
    if isinstance(raw, dict):
        url = raw.get("url")
        url = url.strip() if isinstance(url, str) else ""
        return url, extra + _host_list(raw.get("allowed_hosts"))
    return "", extra


def _open(url: str, allowed_hosts: frozenset):
    opener = urllib.request.build_opener(_HostLockedRedirect(allowed_hosts), *_EXTRA_HANDLERS)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return opener.open(request, timeout=TIMEOUT_SECONDS)


def fetch(url: str, allowed_hosts: frozenset) -> bytes:
    with _open(url, allowed_hosts) as response:
        if not url_allowed(response.geturl(), allowed_hosts):
            raise HostRefused()
        return response.read(MAX_BYTES + 1)


def _save(inbox: Path, slug: str, date: str, content: bytes) -> Path:
    directory = inbox / slug / FETCHED_SUBDIR
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / f"{slug}_dashboardtotals_{date}.csv"
    partial = directory / f".{target.name}.partial"
    if partial.exists():
        partial.unlink()
    fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.chmod(partial, 0o600)
        os.replace(partial, target)
    except BaseException:
        if partial.exists():
            partial.unlink()
        raise
    return target


def _failure_label(error: BaseException) -> str:
    code = getattr(error, "code", None)
    label = type(error).__name__
    if isinstance(code, int):
        label += f" HTTP {code}"
    return label


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Save one brand's Sellerboard feed CSV into the local inbox. "
                    "Never prints the feed URL or token.")
    parser.add_argument("--account", required=True, help="brand slug as keyed in the manifest")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                        help="feed manifest (default: _local/ads-monitor/sellerboard-feeds.json)")
    parser.add_argument("--inbox", default=str(DEFAULT_INBOX),
                        help="inbox root (default: _local/ads-monitor/inbox)")
    parser.add_argument("--date", default=dt.date.today().isoformat(),
                        help="date for the saved filename, YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)

    slug = args.account
    if not SLUG_RE.match(slug):
        parser.error("--account must be a plain slug (letters, digits, '.', '_' or '-')")
    try:
        date = dt.date.fromisoformat(args.date).isoformat()
    except ValueError:
        parser.error("--date must be YYYY-MM-DD")

    try:
        url, extra_hosts = load_feed(Path(args.manifest), slug)
    except ValueError:
        print(f"{slug}: feed manifest missing or unreadable", file=sys.stderr)
        return EXIT_MANIFEST
    if not url:
        print(f"{slug}: Sellerboard feed is not configured", file=sys.stderr)
        return EXIT_NOT_CONFIGURED

    own_host = _hostname(url)
    allowed = frozenset(([own_host] if own_host else []) + extra_hosts)
    if not url_allowed(url, allowed):
        print(f"{slug}: refused (the feed URL must be https with a hostname)", file=sys.stderr)
        return EXIT_REFUSED

    try:
        content = fetch(url, allowed)
    except HostRefused:
        print(f"{slug}: refused (redirect to a host outside the allowed set)", file=sys.stderr)
        return EXIT_REFUSED
    except Exception as error:  # noqa: BLE001 -- report the class only, never the text
        print(f"{slug}: fetch failed ({_failure_label(error)})", file=sys.stderr)
        return EXIT_FETCH_FAILED

    if len(content) > MAX_BYTES:
        print(f"{slug}: fetch failed (response larger than 25 MiB)", file=sys.stderr)
        return EXIT_FETCH_FAILED
    if not content.strip():
        print(f"{slug}: blank feed, nothing saved")
        return EXIT_BLANK
    if content.lstrip()[:1] == b"<":
        print(f"{slug}: fetch failed (response is HTML, not CSV)", file=sys.stderr)
        return EXIT_FETCH_FAILED

    try:
        target = _save(Path(args.inbox), slug, date, content)
    except OSError as error:
        print(f"{slug}: could not save the CSV ({_failure_label(error)})", file=sys.stderr)
        return EXIT_FETCH_FAILED
    print(f"{slug}: saved {target} ({len(content)} bytes)")
    return EXIT_SAVED


if __name__ == "__main__":
    sys.exit(main())

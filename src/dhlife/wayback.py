"""Wayback Machine (CDX API) and live-HTTP helpers shared by every command.

Semantics used for the paper (do not change lightly, see ``get_wayback_info``):
all snapshots are requested without ``collapse`` and with ``matchType=exact``;
snapshots with a 4xx/5xx status are dropped in Python, everything else (2xx *and*
3xx) counts towards first/last seen.
"""

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import requests

CDX_API_URL = "https://web.archive.org/cdx/search/cdx"
MAX_RETRIES = 5
BACKOFF_FACTOR = 2
RATE_LIMIT_DELAY = 0.3  # baseline pause between rows; 429 handling + backoff provide safety
REQUEST_TIMEOUT = 60  # Wayback CDX can be very slow, avoid unnecessary retries

# Descriptive User-Agent per Internet Archive automation guidelines.
USER_AGENT = "VitaMorteDHArchiveChecker/1.0 (+research; contact: project-team)"

CDX_TIMESTAMP = "%Y%m%d%H%M%S"

# Outcomes of get_wayback_info()
OK = "OK"  # snapshots found, dates returned
EMPTY = "EMPTY"  # request succeeded, Wayback genuinely has no usable snapshot
FETCH_FAILED = "FETCH_FAILED"  # request failed: dates are UNKNOWN, not absent

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})

log = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"^(http(s)?://|www\.)[^\s]+$")


@dataclass
class Snapshot:
    timestamp: str  # CDX "YYYYmmddHHMMSS"
    original: str
    status: str

    @property
    def datetime(self) -> datetime:
        return datetime.strptime(self.timestamp, CDX_TIMESTAMP)

    @property
    def link(self) -> str:
        return f"https://web.archive.org/web/{self.timestamp}/{self.original}"


def is_valid_url(url: Optional[str]) -> bool:
    """True if ``url`` looks like an http(s) or www-based URL."""
    return bool(url) and bool(_URL_PATTERN.match(url))


def normalize_url(url: str) -> str:
    """Add an ``http://`` scheme if the URL starts with ``www.`` or has none."""
    if url.startswith("www."):
        return "http://" + url
    if not urlparse(url).scheme:
        return "http://" + url
    return url


def check_live_status(url: str) -> Optional[int]:
    """Current HTTP status of ``url`` (after redirects), or None if the request failed."""
    try:
        return SESSION.get(url, timeout=REQUEST_TIMEOUT).status_code
    except requests.RequestException as e:
        log.warning("Status check failed for %s: %s", url, e)
        return None


def _cdx(params: dict) -> Optional[list]:
    """Query the CDX API with retries. Returns the JSON rows (header stripped) or None on failure."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.debug("[CDX attempt %d] %s", attempt, params)
            resp = SESSION.get(CDX_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after else BACKOFF_FACTOR ** (attempt - 1)
                except ValueError:
                    wait = BACKOFF_FACTOR ** (attempt - 1)
                log.warning("429 for %s, waiting %ss", params["url"], wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data[1:]  # data[0] is the header row
        except requests.RequestException as e:
            log.warning("CDX request failed (attempt %d) for %s: %s", attempt, params["url"], e)
            if attempt == MAX_RETRIES:
                break
            time.sleep(BACKOFF_FACTOR ** (attempt - 1))
        except ValueError as e:
            log.error("Invalid CDX JSON for %s: %s", params["url"], e)
            return None
    log.error("CDX lookup exhausted all retries for %s", params["url"])
    return None


def list_snapshots(url: str, only_200: bool = False, limit: Optional[int] = None,
                   reverse: bool = False) -> Optional[list[Snapshot]]:
    """All CDX records for exactly ``url`` (None if the lookup failed)."""
    params = {"url": url, "output": "json", "fl": "timestamp,original,statuscode", "matchType": "exact"}
    if only_200:
        params["filter"] = "statuscode:200"
    if limit:
        params["limit"] = str(limit)
    if reverse:
        params["sort"] = "reverse"
    rows = _cdx(params)
    if rows is None:
        return None
    return [Snapshot(*row[:3]) for row in rows]


def last_snapshot(url: str, only_200: bool = False) -> Optional[Snapshot]:
    snapshots = list_snapshots(url, only_200=only_200, limit=1, reverse=True)
    return snapshots[0] if snapshots else None


def get_wayback_info(url: str) -> tuple[Optional[datetime], Optional[datetime], Optional[str], str]:
    """First seen, last seen, last snapshot link and outcome (OK / EMPTY / FETCH_FAILED).

    Considers every snapshot except those with a 4xx/5xx status code (3xx redirects
    are kept). This is the definition of url_first_seen / url_last_seen in the dataset.
    """
    snapshots = list_snapshots(url)
    if snapshots is None:
        return None, None, None, FETCH_FAILED
    valid = []
    for s in snapshots:
        try:
            code = int(s.status)
        except ValueError:  # e.g. "-" for revisit records
            continue
        if not 400 <= code < 600:
            valid.append(s)
    if not valid:
        log.info("No usable snapshots for %s", url)
        return None, None, None, EMPTY
    valid.sort(key=lambda s: s.timestamp)
    first, last = valid[0], valid[-1]
    return first.datetime, last.datetime, last.link, OK

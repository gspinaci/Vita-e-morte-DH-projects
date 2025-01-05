#!/usr/bin/env python3

import requests
import time
import re
from urllib.parse import urlparse
from datetime import datetime

CDX_API_URL = "https://web.archive.org/cdx/search/cdx"
MAX_RETRIES = 8
BACKOFF_FACTOR = 4

def is_valid_url(url: str) -> bool:
    """Checks if the given string is a syntactically valid URL (http(s) or www)."""
    pattern = re.compile(r'^(http(s)?://|www\.)[^\s]+$')
    return bool(pattern.match(url))

def normalize_url(url: str) -> str:
    """Ensure the URL has a scheme (http://) if missing, or if it starts with 'www.'."""
    if url.startswith("www."):
        return "http://" + url
    parsed = urlparse(url)
    if not parsed.scheme:
        return "http://" + url
    return url

def check_live_status(url: str) -> int or None:
    """
    Makes a live GET request to the provided URL.
    Returns the status code or None if the request fails.
    """
    try:
        resp = requests.get(url, timeout=10)
        return resp.status_code
    except requests.RequestException:
        return None

def get_wayback_snapshots(url: str):
    """
    Returns a list of (timestamp, original_url, statuscode) for status=200 snapshots
    from the Wayback Machine, sorted by timestamp ascending.
    Also returns first_seen_dt, last_seen_dt as datetime objects (or None if none found).
    """
    params = {
        'url': url,
        'output': 'json',
        'fl': 'timestamp,original,statuscode',
        'filter': 'statuscode:200',
        'limit': '5000',
        # 'matchType': 'prefix',  # Uncomment if needed for domain variants
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(CDX_API_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # data[0] should be headers ["timestamp","original","statuscode"]
            # data[1:] are the actual rows
            if len(data) < 2:
                return [], None, None  # no snapshots

            rows = data[1:]
            if not rows:
                return [], None, None

            # row = [timestamp, original, statuscode]
            # Convert each row's timestamp to a proper string
            # We only have 200-coded snapshots here due to 'filter=statuscode:200'
            snapshots = [(row[0], row[1], row[2]) for row in rows]
            # Sort by timestamp ascending
            snapshots.sort(key=lambda r: r[0])

            first_ts = snapshots[0][0]
            last_ts = snapshots[-1][0]

            first_dt = datetime.strptime(first_ts, "%Y%m%d%H%M%S")
            last_dt = datetime.strptime(last_ts, "%Y%m%d%H%M%S")

            return snapshots, first_dt, last_dt

        except requests.RequestException:
            # Exponential backoff
            if attempt == MAX_RETRIES:
                return [], None, None
            time.sleep(BACKOFF_FACTOR ** (attempt - 1))
        except ValueError:
            # JSON decode error or invalid data
            return [], None, None

def main():
    # Ask for the URL from the user
    input_url = input("Enter a URL: ").strip()

    # Basic validity check
    if not is_valid_url(input_url):
        print("The input is not a valid URL format (must start with http://, https://, or www.).")
        return

    # Normalize (ensure scheme)
    normalized_url = normalize_url(input_url)

    # 1) Check the live status code
    status_code = check_live_status(normalized_url)
    if status_code is None:
        print(f"Could not retrieve the live status code for: {normalized_url}")
    else:
        print(f"Live status code for {normalized_url}: {status_code}")

    # 2) Query Wayback Machine for snapshots
    snapshots, first_seen_dt, last_seen_dt = get_wayback_snapshots(normalized_url)
    total_snapshots = len(snapshots)

    if total_snapshots == 0:
        print("No HTTP 200 snapshots found in the Wayback Machine for this URL.")
        return

    # 3) Print all snapshots (timestamps, original, statuscode)
    print("\nList of Wayback Machine Snapshots (HTTP 200 only):")
    for ts, original, code in snapshots:
        # Convert timestamp (YYYYmmddHHMMSS) to a friendlier format
        dt_str = datetime.strptime(ts, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        print(f"- {dt_str} | {original} | statuscode={code}")

    # 4) Print total, first seen, last seen
    print(f"\nTotal snapshots (HTTP 200): {total_snapshots}")

    first_str = first_seen_dt.strftime("%Y-%m-%d %H:%M:%S") if first_seen_dt else "N/A"
    last_str = last_seen_dt.strftime("%Y-%m-%d %H:%M:%S") if last_seen_dt else "N/A"
    print(f"First seen: {first_str}")
    print(f"Last seen:  {last_str}")

if __name__ == "__main__":
    main()

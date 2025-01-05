#!/usr/bin/env python3

import sys
import requests
from datetime import datetime
from urllib.parse import urlparse
from colorama import init, Fore, Style

init(autoreset=True)
green = Fore.GREEN
blue = Fore.BLUE
reset = Style.RESET_ALL

CDX_API_URL = "https://web.archive.org/cdx/search/cdx"

def normalize_url(url: str) -> str:
    """Ensure the URL has http:// scheme if missing, or if it only has 'www.'."""
    if url.startswith("www."):
        return "http://" + url
    parsed = urlparse(url)
    if not parsed.scheme:
        return "http://" + url
    return url

def get_last_snapshot(url: str, filter_200: bool = False):
    """
    Fetch the *most recent* snapshot from the CDX API.
    If filter_200=True, only return snapshots with statuscode=200.
    Returns a tuple: (timestamp_str, original_url, status_code) or None if none found.
    """
    # We ask the CDX API for just 1 record, sorted in descending order (most recent).
    params = {
        "url": url,
        "output": "json",
        "fl": "timestamp,original,statuscode",
        "limit": "1",
        "sort": "reverse"
    }
    if filter_200:
        params["filter"] = "statuscode:200"
    
    try:
        resp = requests.get(CDX_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None

    # data[0] = header row -> ["timestamp","original","statuscode"]
    # data[1:] = actual rows
    if len(data) < 2:
        return None
    
    row = data[1][0:3]  # [timestamp, original, statuscode]
    # Example row: ["20230102123456", "http://example.com/", "302"]
    timestamp_str = row[0]
    original_url = row[1]
    code = row[2]
    return timestamp_str, original_url, code

def format_wayback_url(timestamp_str, original_url):
    """Return a full clickable Wayback Machine URL."""
    return f"https://web.archive.org/web/{timestamp_str}/{original_url}"

def main():
    # Get the URL either from sys.argv[1] or ask the user
    if len(sys.argv) > 1:
        input_url = sys.argv[1].strip()
    else:
        input_url = input("Enter a URL: ").strip()

    if not input_url:
        print("No URL entered.")
        sys.exit(1)

    normalized_url = normalize_url(input_url)

    # 1) Last snapshot *regardless* of code
    snapshot_any = get_last_snapshot(normalized_url, filter_200=False)
    # 2) Last snapshot *with* code=200
    snapshot_200 = get_last_snapshot(normalized_url, filter_200=True)

    print(f"\nChecking most recent snapshots for: {normalized_url}\n")

    # Print 1) last snapshot ANY code
    if snapshot_any:
        ts_any, orig_any, code_any = snapshot_any
        dt_any = datetime.strptime(ts_any, "%Y%m%d%H%M%S")
        wb_url_any = format_wayback_url(ts_any, orig_any)
        print(f"Most recent snapshot (ANY code):")
        print(
            f"  Date: {green}{dt_any.strftime('%Y-%m-%d %H:%M:%S')}{reset}"
            f" | Code: {code_any}"
            f" | Link: {blue}{wb_url_any}{reset}"
        )
    else:
        print(f"Most recent snapshot (ANY code): None found.")

    print()

    # Print 2) last snapshot code=200
    if snapshot_200:
        ts_200, orig_200, code_200 = snapshot_200
        dt_200 = datetime.strptime(ts_200, "%Y%m%d%H%M%S")
        wb_url_200 = format_wayback_url(ts_200, orig_200)
        print(f"Most recent snapshot (code=200 only):")
        print(
            f"  Date: {green}{dt_200.strftime('%Y-%m-%d %H:%M:%S')}{reset}"
            f" | Code: {code_200}"
            f" | Link: {blue}{wb_url_200}{reset}"
        )
    else:
        print(f"Most recent snapshot (code=200 only): None found.")

if __name__ == "__main__":
    main()

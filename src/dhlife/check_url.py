"""Inspect the Wayback Machine history of a single URL.

    python -m dhlife check-url https://example.org           # live status + summary
    python -m dhlife check-url https://example.org --list    # also list every HTTP 200 snapshot

Prints the live status, first/last seen as computed for the dataset (4xx/5xx excluded),
and the most recent snapshot with any status vs. with status 200, which is the quickest
way to spot a site that is archived but has been returning redirects or error pages.
"""

import argparse
import sys

from dhlife import wayback
from dhlife.schema import DATE_FORMAT


def _fmt(snapshot):
    if snapshot is None:
        return "none found"
    return f"{snapshot.datetime:{DATE_FORMAT}} | status {snapshot.status} | {snapshot.link}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("--list", action="store_true", help="list every HTTP 200 snapshot")
    args = parser.parse_args(argv)

    if not wayback.is_valid_url(args.url):
        sys.exit("Not a valid URL (must start with http://, https:// or www.)")
    url = wayback.normalize_url(args.url)

    status = wayback.check_live_status(url)
    print(f"URL:               {url}")
    print(f"Live status:       {status if status is not None else 'unreachable'}")

    first, last, link, outcome = wayback.get_wayback_info(url)
    if outcome == wayback.FETCH_FAILED:
        sys.exit("Wayback CDX lookup failed (see warnings above); try again later.")
    print(f"First seen:        {first:{DATE_FORMAT}}" if first else "First seen:        -")
    print(f"Last seen:         {last:{DATE_FORMAT}}" if last else "Last seen:         -")
    print(f"Last snapshot (any status): {_fmt(wayback.last_snapshot(url))}")
    print(f"Last snapshot (status 200): {_fmt(wayback.last_snapshot(url, only_200=True))}")

    if args.list:
        snapshots = wayback.list_snapshots(url, only_200=True) or []
        print(f"\n{len(snapshots)} snapshots with status 200:")
        for s in snapshots:
            print(f"  {s.datetime:{DATE_FORMAT}} | {s.original}")


if __name__ == "__main__":
    main()

"""Enrich the project list with Wayback Machine history and the live HTTP status.

For each of ``project_url`` and ``url_showcase`` four columns are (re)computed:
first seen, last seen, live status code, link to the last snapshot
(see ``dhlife.schema.ARCHIVE_COLUMNS``).

    python -m dhlife archive-check                       # curated -> processed (~30 min)
    python -m dhlife archive-check --output data/processed/projects_archive_2027.csv

If a Wayback lookup fails (network error, repeated 429s) the values from
``--previous`` are kept instead of being blanked.
"""

import argparse
import logging
import sys
import time
from datetime import datetime

import pandas as pd

from dhlife import paths, wayback
from dhlife.schema import (
    ARCHIVED_URL_COLUMNS, CURATED_COLUMNS, DATE_FORMAT, NO_STATUS_CODE, NOT_PROVIDED,
    archive_columns, read_projects, write_projects,
)

log = logging.getLogger(__name__)


def process_url(url, prev: dict) -> list[str]:
    """[first_seen, last_seen, status_code, last_snapshot] for one URL."""
    url = (url or "").strip() if isinstance(url, str) else ""
    if not wayback.is_valid_url(url):
        return [NOT_PROVIDED, NOT_PROVIDED, NOT_PROVIDED, ""]

    url = wayback.normalize_url(url)
    status = wayback.check_live_status(url)
    live_reachable = status is not None
    status = str(status) if live_reachable else NO_STATUS_CODE

    first, last, snapshot, outcome = wayback.get_wayback_info(url)
    if outcome == wayback.FETCH_FAILED:
        # Dates are UNKNOWN, not absent: keep what we had rather than blanking it.
        log.warning("Wayback fetch failed for %s; keeping previous values %s", url, prev)
        if not live_reachable and prev.get("status"):
            # Wayback unreachable too: our own network was probably down.
            status = prev["status"]
        return [prev.get("first", ""), prev.get("last", ""), status, prev.get("snapshot", "")]

    return [
        first.strftime(DATE_FORMAT) if first else "",
        last.strftime(DATE_FORMAT) if last else "",
        status,
        snapshot or "",
    ]


def _previous_values(previous: pd.DataFrame | None, i: int, prefix: str) -> dict:
    if previous is None or i >= len(previous):
        return {}
    cols = archive_columns(prefix)
    row = previous.iloc[i]
    vals = [row.get(c) for c in cols]
    vals = ["" if pd.isna(v) else str(v) for v in vals]
    return dict(zip(["first", "last", "status", "snapshot"], vals))


def run(input_path, output_path, previous_path=None):
    projects = read_projects(input_path)[CURATED_COLUMNS]
    previous = None
    if previous_path and previous_path.exists():
        previous = read_projects(previous_path)
        if len(previous) != len(projects) or not previous["title"].equals(projects["title"]):
            # Rows are matched by position; refuse to mix up projects.
            log.warning("--previous rows do not match --input; ignoring it")
            previous = None

    results = {c: [] for p in ARCHIVED_URL_COLUMNS.values() for c in archive_columns(p)}
    start, total = time.time(), len(projects)
    for i, row in enumerate(projects.itertuples(index=False)):
        for url_col, prefix in ARCHIVED_URL_COLUMNS.items():
            values = process_url(getattr(row, url_col), _previous_values(previous, i, prefix))
            for col, val in zip(archive_columns(prefix), values):
                results[col].append(val)
        time.sleep(wayback.RATE_LIMIT_DELAY)
        done = i + 1
        remaining = (time.time() - start) / done * (total - done)
        sys.stderr.write(f"\r[{'#' * (40 * done // total):<40}] {done}/{total}  ~{remaining / 60:.1f} min left")
    sys.stderr.write("\n")

    out = pd.concat([projects, pd.DataFrame(results)], axis=1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_projects(out, output_path)
    log.info("Wrote %s (%d rows) in %.0fs", output_path, len(out), time.time() - start)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=paths.Path, default=paths.PROJECTS)
    parser.add_argument("--output", type=paths.Path, default=paths.PROJECTS_ARCHIVE)
    parser.add_argument("--previous", type=paths.Path, default=paths.PROJECTS_ARCHIVE,
                        help="earlier run whose values are kept when a lookup fails (default: --output)")
    args = parser.parse_args(argv)

    paths.LOGS.mkdir(exist_ok=True)
    logfile = paths.LOGS / f"archive_check_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.getLogger("urllib3").setLevel(logging.INFO)
    print(f"Logging to {logfile}", file=sys.stderr)
    run(args.input, args.output, args.previous)


if __name__ == "__main__":
    main()

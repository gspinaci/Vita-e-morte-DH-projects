"""Shared analysis logic behind ``stats`` and ``charts`` (ported from the old make_chart notebook).

Definitions used in the paper:

* *functioning*: manual flag ``functioning_website`` — the ground truth for active/ended.
  The archive status code is noisy and never used to classify projects.
* *migrated*: ``new_website_url`` is set; the project lives on at another address and
  is counted as available, not as discontinued.
* *unavailable in year Y*: not functioning, not migrated, last seen (after manual
  corrections) in year Y.

``taxonomy`` maps these flags onto the taxonomy of the paper (§4.3).
"""

import numpy as np
import pandas as pd

from dhlife import paths
from dhlife.schema import read_projects

CURRENT_YEAR = 2026  # year of the check: excluded from yearly counts (partial year)
GROWTH_BASELINE_YEAR = 2003  # a year with no events, added so the series has no gap


def load(path=paths.PROJECTS_ARCHIVE) -> pd.DataFrame:
    return read_projects(path)


def migrated(df: pd.DataFrame) -> pd.Series:
    return df["new_website_url"].notna()


def apply_last_seen_corrections(df: pd.DataFrame, corrections_path=paths.LAST_SEEN_CORRECTIONS):
    """Override ``url_last_seen`` with manually verified dates (matched on project_url).

    Returns the corrected copy and the corrections that matched no project.
    """
    df = df.copy()
    corrections = pd.read_csv(corrections_path, dtype=str).dropna(subset=["correct_last_seen", "project_url"])
    unmatched = []
    for row in corrections.itertuples():
        mask = df["project_url"] == row.project_url
        if mask.any():
            df.loc[mask, "url_last_seen"] = row.correct_last_seen
        else:
            unmatched.append(row)
    df.attrs["corrections_applied"] = len(corrections) - len(unmatched)
    return df, pd.DataFrame(unmatched).drop(columns="Index", errors="ignore")


def add_years(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ("url_first_seen", "url_last_seen"):
        # NOTPROVIDED / blanks become NaT
        df[col + "_dt"] = pd.to_datetime(df[col], format="ISO8601", errors="coerce")
    df["year_first_seen"] = df["url_first_seen_dt"].dt.year
    df["year_last_seen"] = df["url_last_seen_dt"].dt.year
    return df


def yearly_counts(df: pd.DataFrame) -> pd.DataFrame:
    """New (first seen) and Unavailable (last seen, discontinued) projects per year.

    ``df`` must have gone through ``add_years`` (and normally the corrections).
    """
    new = df.loc[df["year_first_seen"] != CURRENT_YEAR, "year_first_seen"].value_counts()
    ended = df[
        df["url_last_seen_dt"].notna()
        & (df["functioning_website"] == False)  # noqa: E712 - NaN must not match
        & ~migrated(df)
        & (df["year_last_seen"] != CURRENT_YEAR)
    ]["year_last_seen"].value_counts()
    years = sorted(set(new.index) | set(ended.index))
    return pd.DataFrame({
        "year": [int(y) for y in years],
        "new": [int(new.get(y, 0)) for y in years],
        "unavailable": [int(ended.get(y, 0)) for y in years],
    })


def growth_table(yearly: pd.DataFrame) -> pd.DataFrame:
    """Cumulative available projects and normalised (arc) growth rate per year."""
    t = yearly[yearly["year"] != CURRENT_YEAR]
    if GROWTH_BASELINE_YEAR not in set(t["year"]):
        t = pd.concat([t, pd.DataFrame({"year": [GROWTH_BASELINE_YEAR], "new": [0], "unavailable": [0]})])
    t = t.sort_values("year").reset_index(drop=True)
    t["net_diff"] = t["new"] - t["unavailable"]
    t["total_projects"] = t["net_diff"].cumsum()
    prev, curr = t["total_projects"].shift(1), t["total_projects"]
    arc_growth = (curr - prev) / ((curr + prev) / 2) * 100
    t["normalized_growth_rate"] = arc_growth * curr / 100
    t.loc[0, "normalized_growth_rate"] = None
    return t


def discontinued(df: pd.DataFrame) -> pd.DataFrame:
    """Projects with a URL that is no longer reachable and that did not migrate."""
    return df[(df["website_not_found"] == False) & (df["functioning_website"] == False) & ~migrated(df)]  # noqa: E712


def taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    """Project Status, Accessibility and Data Preservation (paper §4.3) from the manual flags.

    * ``project_status``: ``never_published`` (no project URL), ``migrated`` (Transformed ›
      Migrated: ``new_website_url`` set), ``active`` (functioning) or ``ended``.
    * ``accessibility`` at ``project_url``: ``fully_accessible``, ``partially_accessible``
      or ``inaccessible``; empty for never-published projects.
    * ``data_preservation``: ``unknown`` (not assessed).

    Categories the flags cannot tell apart (dormant, archived, restricted, planned vs.
    unplanned ending, the other kinds of transformation) are not assigned.
    """
    has_url = df["project_url"].notna()
    functioning = df["functioning_website"] == True  # noqa: E712
    partial = df["partially_unaccessible_website"] == True  # noqa: E712
    status = np.select([~has_url, migrated(df), functioning], ["never_published", "migrated", "active"], "ended")
    accessibility = np.select(
        [~has_url, functioning & ~partial, functioning & partial],
        ["", "fully_accessible", "partially_accessible"], "inaccessible")
    return pd.DataFrame({
        "project_status": status,
        "accessibility": pd.Series(accessibility, index=df.index).replace("", pd.NA),
        "data_preservation": "unknown",
    }, index=df.index)


def lifespans(df: pd.DataFrame) -> pd.DataFrame:
    """Lifespan of discontinued projects, both as the paper computes it (difference of
    years) and in days. ``df`` must have gone through ``add_years``."""
    d = discontinued(df).copy()
    d["lifespan_years_by_year"] = d["year_last_seen"] - d["year_first_seen"]
    d["lifespan_days"] = (d["url_last_seen_dt"] - d["url_first_seen_dt"]).dt.days
    return d


def macro_status(code) -> str:
    s = "" if pd.isna(code) else str(code).strip()
    if s in ("", "NOSTATUSCODE"):
        return "none"
    if s == "NOTPROVIDED":
        return "NOTPROVIDED"
    try:
        c = int(float(s))
    except ValueError:
        return f"other:{s}"
    return f"{c // 100}xx" if 200 <= c < 600 else f"other:{s}"


def status_discrepancies(df: pd.DataFrame) -> pd.DataFrame:
    """Rows where the live status code disagrees with the manual functioning flag."""
    d = df.assign(macro_status=df["url_status_code"].map(macro_status))
    false_negative = d[(d["functioning_website"] == True)  # noqa: E712
                       & d["macro_status"].isin(["4xx", "5xx", "none", "NOTPROVIDED"])]
    false_positive = d[(d["functioning_website"] == False) & (d["macro_status"] == "2xx")]  # noqa: E712
    cols = ["title", "project_url", "functioning_website", "url_status_code", "macro_status"]
    return pd.concat([
        false_negative[cols].assign(discrepancy="false_negative: functioning but status 4xx/5xx/none"),
        false_positive[cols].assign(discrepancy="false_positive: not functioning but status 2xx"),
    ], ignore_index=True)


UNAVAILABILITY_FLAGS = {
    "website_not_found": "not found",
    "non_functioning_website": "not functioning",
    "not_redirected_website": "not redirected",
}


def unavailable_projects(raw: pd.DataFrame, corrected: pd.DataFrame) -> pd.DataFrame:
    """One row per project with any unavailability flag, with the last-seen date used."""
    flags = pd.DataFrame({label: raw[col] == True for col, label in UNAVAILABILITY_FLAGS.items()})  # noqa: E712
    mask = flags.any(axis=1)
    out = pd.DataFrame({
        "title": raw["title"],
        "project_url": raw["project_url"],
        "unavailability": flags.apply(lambda r: "; ".join(k for k, v in r.items() if v), axis=1),
        "migrated_to": raw["new_website_url"],
        "provenance": raw["provenance"],
        "first_seen": corrected["url_first_seen_dt"],
        "wayback_last_seen": pd.to_datetime(raw["url_last_seen"], format="ISO8601", errors="coerce"),
        "last_seen_used": corrected["url_last_seen_dt"],
    })[mask]
    out["last_seen_corrected"] = out["last_seen_used"] != out["wayback_last_seen"]
    out.loc[out["last_seen_used"].isna(), "last_seen_corrected"] = False
    out["lifespan_days"] = (out["last_seen_used"] - out["first_seen"]).dt.days
    out["lifespan_years"] = (out["lifespan_days"] / 365.25).round(2)
    return out.reset_index(drop=True)

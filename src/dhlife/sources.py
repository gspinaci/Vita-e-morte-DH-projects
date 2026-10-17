"""Turn the frozen Google Sheet snapshot into clean, English, one-table-per-file source CSVs.

The working spreadsheet (see ``data/sources/README.md``) is frozen: it is snapshotted
once as ``data/sources/raw/working_sheet_snapshot_<date>.xlsx`` and never read at analysis time.
This module only keeps the *source* tabs (where candidate projects came from); the many
superseded "Lista finale" tabs are left in the raw snapshot for provenance.

The ``dead_projects`` tab was extracted once to ``data/curated/last_seen_manual_corrections.csv``,
which is now edited by hand and deliberately not rewritten here.

    python -m dhlife sources                 # rebuild CSVs from the committed snapshot
    python -m dhlife sources --download      # take a fresh snapshot first
"""

import argparse
import datetime as dt
import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import requests

from dhlife import paths

SHEET_ID = "1G3WiRMoopP8Y2FlVJfwCRqZVLilw-aMQRBxF_SoMF20"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

TRUE_VALUES = {"true", "sì", "si", "yes", "y"}
FALSE_VALUES = {"false", "no", "n"}

# Informal internal remarks in the sheet's notes, reworded for the public CSVs
# (the raw snapshot is left as it is).
NOTE_REWORDING = {
    "Coming soon LOL": "Coming soon",
    "non si capisce un cazzo": "di difficile comprensione",
}

log = logging.getLogger(__name__)


@dataclass
class Tab:
    """How to turn one spreadsheet tab into one CSV."""

    sheet: str
    output: str
    columns: dict[str, str]  # sheet header -> output column (only these are kept)
    keys: list[str]  # a row is kept if at least one of these is non-empty
    booleans: list[str] = field(default_factory=list)


TABS = [
    Tab(
        "DH Awards",
        "dh_awards_all_nominees.csv",
        {"Year": "year", "Category": "category", "Title": "title", "URL": "url"},
        keys=["title", "url"],
    ),
    Tab(
        "DH Awards (Italians)",
        "dh_awards_italian_nominees.csv",
        {
            "Year": "year",
            "Category": "category",
            "Title": "title",
            "URL": "url",
            "Ancora esistente?": "still_exists",
            "Digital Publication?": "digital_publication",
            "NOTE": "notes",
            "FIRST APPEARANCE (archive)": "first_appearance_archive",
            "LAST APPEARANCE (archive)": "last_appearance_archive",
            "IP history": "ip_history",
        },
        keys=["title", "url"],
        booleans=["still_exists", "digital_publication"],
    ),
    Tab(
        "Proceedings AIUCD",
        "aiucd_proceedings_projects.csv",
        {
            "Title": "title",
            "Article Title": "article_title",
            "Project URL": "project_url",
            "Project URL resolving": "project_url_resolves",
            "sito vetrina URL": "url_showcase",
            "Landing page resolving": "url_showcase_resolves",
            "Antichamber URL": "url_landing_page",
            "Antichamber resolving": "url_landing_page_resolves",
            "NOTE": "notes",
        },
        keys=["title", "article_title", "project_url"],
        booleans=["project_url_resolves", "url_showcase_resolves", "url_landing_page_resolves"],
    ),
    Tab(
        "IRCDL",
        "ircdl_proceedings_articles.csv",
        {
            "Year": "year",
            "IRCDL program": "program_url",
            "Authors": "authors",
            "Article title": "article_title",
            "Project URL": "project_url",
            "Still exhisting?": "project_url_exists",
            "Sito vetrina URL": "url_showcase",
            "Still exhisting? 2": "url_showcase_exists",
            "Note": "notes",
        },
        keys=["article_title", "project_url"],
        booleans=["project_url_exists", "url_showcase_exists"],
    ),
    Tab(
        "KNOT aggregator",
        "knot_all_homepages.csv",
        {"s": "knot_uri", "o": "homepage"},  # SPARQL: ?s foaf:homepage ?o
        keys=["knot_uri"],
    ),
    Tab(
        "KNOT finale",
        "knot_selected_projects.csv",
        {"Titolo": "knot_uri", "URL progetto": "project_url"},
        keys=["knot_uri", "project_url"],
    ),
    Tab(
        "Centri DH",
        "italian_dh_centres.csv",
        {"Categoria": "category", "Nome": "name", "Luogo": "location", "URL": "urls"},
        keys=["name", "urls"],
    ),
    Tab(
        "dh italian projects",
        "italian_dh_centres_projects.csv",
        {
            "categoria": "category",
            "institution": "institution",
            "location": "location",
            "project_name": "project_name",
            "Vero URL progetto": "project_url",
            "SITO VETRINA": "url_showcase",
            "what is it?": "description",
            "Ancora esistente?": "still_exists",
        },
        keys=["institution", "project_name", "project_url"],
        booleans=["still_exists"],
    ),
]


def to_bool(value):
    if pd.isna(value):
        return value
    v = str(value).strip().lower()
    if v in TRUE_VALUES:
        return "TRUE"
    if v in FALSE_VALUES:
        return "FALSE"
    return value


def clean(raw: pd.DataFrame, tab: Tab) -> pd.DataFrame:
    raw = raw.rename(columns=lambda c: str(c).replace("\xa0", " ").strip())
    df = raw[list(tab.columns)].rename(columns=tab.columns)
    df = df.apply(lambda s: s.str.strip()).replace("", pd.NA)
    df = df[df[tab.keys].notna().any(axis=1)]
    for col in tab.booleans:
        df[col] = df[col].map(to_bool)
    if "notes" in df:
        for informal, neutral in NOTE_REWORDING.items():
            df["notes"] = df["notes"].str.replace(informal, neutral, regex=False)
    if "urls" in df:  # several URLs per cell, normalise the separator
        df["urls"] = df["urls"].str.replace(r"\s*;\s*", "; ", regex=True)
    return df.reset_index(drop=True)


def download(target_dir: Path) -> Path:
    target = target_dir / f"working_sheet_snapshot_{dt.date.today().isoformat()}.xlsx"
    resp = requests.get(EXPORT_URL, timeout=120)
    resp.raise_for_status()
    target.write_bytes(resp.content)
    log.info("Downloaded sheet snapshot to %s", target)
    return target


def build(snapshot: Path) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # openpyxl: "Unknown extension is not supported"
        book = pd.read_excel(snapshot, sheet_name=[t.sheet for t in TABS], dtype=str)
    for tab in TABS:
        df = clean(book[tab.sheet], tab)
        paths.SOURCES.mkdir(parents=True, exist_ok=True)
        df.to_csv(paths.SOURCES / tab.output, index=False)
        log.info("%-24s -> %s (%d rows)", tab.sheet, paths.SOURCES / tab.output, len(df))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", type=Path, default=paths.SHEET_SNAPSHOT, help="xlsx snapshot to read")
    parser.add_argument("--download", action="store_true", help="download a fresh snapshot and use it")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    snapshot = download(paths.SOURCES_RAW) if args.download else args.snapshot
    build(snapshot)


if __name__ == "__main__":
    main()

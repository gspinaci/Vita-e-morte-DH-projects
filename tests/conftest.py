import pandas as pd
import pytest

from dhlife.schema import ARCHIVE_COLUMNS, CURATED_COLUMNS


def make_projects(rows):
    """DataFrame with every release column; ``rows`` only list the columns a test cares about."""
    df = pd.DataFrame(rows)
    for col in CURATED_COLUMNS + ARCHIVE_COLUMNS:
        if col not in df:
            df[col] = pd.NA
    return df[CURATED_COLUMNS + ARCHIVE_COLUMNS]


@pytest.fixture
def projects():
    """Four projects: alive, migrated, discontinued, without URL."""
    return make_projects([
        {"title": "Alive", "project_url": "https://alive.it", "functioning_website": True,
         "website_not_found": False, "non_functioning_website": False,
         "partially_unaccessible_website": False, "provenance": "KNOT",
         "url_first_seen": "2010-01-01 00:00:00", "url_last_seen": "2026-05-01 00:00:00",
         "url_status_code": "200"},
        {"title": "Migrated", "project_url": "https://old.it", "functioning_website": False,
         "website_not_found": False, "non_functioning_website": True, "not_redirected_website": True,
         "new_website_url": "https://new.it", "provenance": "AIUCD",
         "url_first_seen": "2012-03-01 00:00:00", "url_last_seen": "2020-06-01 00:00:00",
         "url_status_code": "NOSTATUSCODE"},
        {"title": "Dead", "project_url": "https://dead.it", "functioning_website": False,
         "website_not_found": False, "non_functioning_website": True, "provenance": "IRCDL",
         "url_first_seen": "2008-01-01 00:00:00", "url_last_seen": "2018-01-01 00:00:00",
         "url_status_code": "200"},
        {"title": "No URL", "functioning_website": False, "website_not_found": True,
         "provenance": "DH Awards", "url_first_seen": "NOTPROVIDED", "url_last_seen": "NOTPROVIDED",
         "url_status_code": "NOTPROVIDED"},
    ])

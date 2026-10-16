"""Crawl the websites of Italian DH centres for links that look like projects.

    python -m dhlife crawl            # data/sources/dh_centers.csv -> data/sources/dh_center_projects_crawled.csv

A link is kept when its text or URL contains one of ``KEYWORDS`` (links inside modal
dialogs are searched too; hidden links and social networks are skipped). For the
institutions in ``LIST_PAGE_INSTITUTIONS`` the given URL already *is* the project
list, so it is recorded as is. The output is a candidate list for manual curation
(the curated result is ``dh_center_projects.csv``), not a list of projects.
"""

import argparse
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from dhlife import paths

KEYWORDS = [
    "project", "progetti",
    "digital humanities", "umanistica digitale",
    "digital", "digitale",
    "research", "ricerca",
    "laboratorio", "laboratory",
    "archivio", "archive",
]
EXCLUDED_DOMAINS = [
    "facebook.com", "twitter.com", "linkedin.com", "instagram.com",
    "youtube.com", "blogspot.com", "wordpress.com", "tumblr.com",
]
MODAL_CLASSES = ["modal", "popup", "dialog", "overlay", "lightbox"]
LIST_PAGE_INSTITUTIONS = ["Torino", "Catania", "Tatti", "Hertziana"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def valid_url(url):
    """The URL with an https:// scheme added if missing, or None if it is not a URL."""
    url = (url or "").strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    return url if parsed.scheme and parsed.netloc else None


def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:  # noqa: BLE001 - report and carry on with the next site
        print(f"  Error fetching {url}: {e}")
        return None


def _hidden(link) -> bool:
    for parent in link.parents:
        style = (parent.get("style") or "").lower()
        if "display: none" in style or "visibility: hidden" in style:
            return True
    return False


def find_project_links(soup, base_url) -> list[dict]:
    modals = soup.find_all(["div", "section", "aside"],
                           class_=lambda c: c and any(m in c.lower() for m in MODAL_CLASSES))
    projects, seen = [], set()
    for area in [soup] + modals:
        for link in area.find_all("a", href=True):
            href, text = link["href"], link.text.lower().strip()
            if not href or href.startswith(("javascript:", "#", "mailto:", "tel:")):
                continue
            href = urljoin(base_url, href)
            if any(d in href for d in EXCLUDED_DOMAINS):
                continue
            if any(k in text or k in href.lower() for k in KEYWORDS) and href not in seen and not _hidden(link):
                seen.add(href)
                projects.append({"project_name": text or href, "project_link": href})
    return projects


def crawl_center(center) -> list[dict]:
    if pd.isna(center.urls):
        return []
    base = {"category": center.category, "institution": center.name, "location": center.location}
    list_page = any(inst in str(center.name) for inst in LIST_PAGE_INSTITUTIONS)
    rows = []
    for url in filter(None, (valid_url(u) for u in str(center.urls).split(";"))):
        if list_page:
            rows.append({**base, "institution_url": url, "project_name": f"Project at {center.name}",
                         "project_link": url})
            continue
        print(f"  {url}")
        soup = fetch(url)
        if soup:
            rows += [{**base, "institution_url": url, **p} for p in find_project_links(soup, url)]
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=paths.Path, default=paths.SOURCES / "dh_centers.csv")
    parser.add_argument("--output", type=paths.Path, default=paths.SOURCES / "dh_center_projects_crawled.csv")
    args = parser.parse_args(argv)

    centers = pd.read_csv(args.input)
    rows = []
    for center in centers.itertuples(index=False):
        print(f"Processing {center.name}...")
        rows += crawl_center(center)
    results = pd.DataFrame(rows).drop_duplicates(subset=["institution", "project_link"])
    results.to_csv(args.output, index=False)
    print(f"Found {len(results)} candidate links across {results['institution'].nunique()} institutions -> {args.output}")


if __name__ == "__main__":
    main()

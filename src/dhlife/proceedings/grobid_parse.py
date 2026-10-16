"""Split a proceedings PDF into articles and extract their metadata with GROBID.

Needs GROBID running locally:

    docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
    python -m dhlife grobid-parse AIUCD2019.pdf --output-dir work/aiucd2019

Writes ``<output-dir>/articles/article_NNNN_pages_A-B.json`` (title, authors, abstract,
keywords, footnotes) plus ``_summary.json``; split PDFs go to ``<output-dir>/split_pdfs``.
Article boundaries are found by running ``processHeaderDocument`` on every single page:
a page where GROBID detects a title longer than 10 characters starts a new article.
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz  # PyMuPDF
import requests
from tqdm import tqdm

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
MIN_TITLE_CHARS = 10

log = logging.getLogger(__name__)


class Grobid:
    def __init__(self, url: str, delay: float):
        self.api = url.rstrip("/") + "/api"
        self.delay = delay

    def is_alive(self) -> bool:
        try:
            return requests.get(f"{self.api}/isalive", timeout=5).status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def _post(self, service: str, pdf: Path, data: dict, timeout: int):
        with open(pdf, "rb") as f:
            try:
                r = requests.post(f"{self.api}/{service}", files={"input": (pdf.name, f, "application/pdf")},
                                  data=data, timeout=timeout)
            except requests.exceptions.RequestException as e:
                log.error("GROBID %s failed on %s: %s", service, pdf.name, e)
                return None
        if r.status_code != 200:
            log.error("GROBID %s returned %s on %s", service, r.status_code, pdf.name)
            return None
        return r.text

    def header(self, pdf: Path):
        return self._post("processHeaderDocument", pdf, {"consolidateHeader": "0"}, timeout=30)

    def fulltext(self, pdf: Path):
        data = {"generateIDs": "1", "consolidateHeader": "0", "segmentSentences": "0"}
        return self._post("processFulltextDocument", pdf, data, timeout=120)


def extract_pages(src: Path, start: int, end: int, dest: Path) -> None:
    """Save pages [start, end] (0-indexed, inclusive) of ``src`` to ``dest``."""
    with fitz.open(src) as doc, fitz.open() as out:
        out.insert_pdf(doc, from_page=start, to_page=end)
        out.save(str(dest))


def detect_article_boundaries(grobid: Grobid, pdf: Path, tmp_dir: Path, min_pages: int):
    with fitz.open(pdf) as doc:
        total = len(doc)
    log.info("%d pages, looking for article boundaries...", total)

    starts = []
    for page in tqdm(range(total), desc="Scanning pages"):
        tmp = tmp_dir / f"_tmp_page_{page}.pdf"
        extract_pages(pdf, page, page, tmp)
        tei = grobid.header(tmp)
        tmp.unlink(missing_ok=True)
        if tei and tei.strip():
            try:
                title = ET.fromstring(tei).find(".//tei:titleStmt/tei:title", TEI_NS)
            except ET.ParseError:
                title = None
            if title is not None and title.text and len(title.text.strip()) > MIN_TITLE_CHARS:
                log.info("New article on page %d: %s", page + 1, title.text.strip()[:60])
                starts.append(page)
        time.sleep(0.3)

    if not starts:
        log.warning("No boundary detected, treating the whole PDF as one document.")
        return [(0, total - 1)]

    boundaries = []
    for i, start in enumerate(starts):
        end = starts[i + 1] - 1 if i + 1 < len(starts) else total - 1
        if end - start + 1 >= min_pages:
            boundaries.append((start, end))
        else:
            log.debug("Skipping article on page %d (only %d pages)", start + 1, end - start + 1)
    log.info("Articles detected: %d", len(boundaries))
    return boundaries


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def extract_fields(tei_xml: str) -> dict:
    """Title, authors, abstract, keywords and footnotes from a GROBID TEI document."""
    result = {"title": None, "abstract": None, "footnotes": [], "authors": [], "keywords": []}
    try:
        root = ET.fromstring(tei_xml)
    except ET.ParseError as e:
        log.error("Invalid TEI: %s", e)
        return result

    title = root.find(".//tei:titleStmt/tei:title[@type='main']", TEI_NS)
    if title is None:
        title = root.find(".//tei:titleStmt/tei:title", TEI_NS)
    result["title"] = _text(title) or None

    for author in root.findall(".//tei:sourceDesc//tei:author", TEI_NS):
        parts = [el.text.strip() for el in (author.find(".//tei:forename", TEI_NS), author.find(".//tei:surname", TEI_NS))
                 if el is not None and el.text]
        if parts:
            result["authors"].append(" ".join(parts))

    result["abstract"] = _text(root.find(".//tei:profileDesc/tei:abstract", TEI_NS)) or None
    result["keywords"] = [kw.text.strip() for kw in root.findall(".//tei:keywords/tei:term", TEI_NS) if kw.text]

    # Footnotes are <note place="foot"> in the body; some GROBID versions put them in <back>.
    for section in ("body", "back"):
        for note in root.findall(f".//tei:{section}//tei:note[@place='foot']", TEI_NS):
            text = _text(note)
            if text and text not in result["footnotes"]:
                result["footnotes"].append(text)
    return result


def run(pdf: Path, output_dir: Path, grobid: Grobid, min_pages: int) -> None:
    split_dir, articles_dir = output_dir / "split_pdfs", output_dir / "articles"
    split_dir.mkdir(parents=True, exist_ok=True)
    articles_dir.mkdir(parents=True, exist_ok=True)

    boundaries = detect_article_boundaries(grobid, pdf, split_dir, min_pages)
    summary, failed = [], []
    for idx, (start, end) in enumerate(tqdm(boundaries, desc="Parsing articles"), start=1):
        article_pdf = split_dir / f"article_{idx:04d}_pages_{start + 1}-{end + 1}.pdf"
        extract_pages(pdf, start, end, article_pdf)
        tei = grobid.fulltext(article_pdf)
        if not tei:
            failed.append(article_pdf.name)
            continue
        fields = extract_fields(tei)
        if not fields["title"] and not fields["abstract"]:
            log.warning("%s: no title or abstract (front matter?), skipped", article_pdf.name)
            continue
        out = articles_dir / f"{article_pdf.stem}.json"
        out.write_text(json.dumps({"source_file": article_pdf.name, "article_index": idx, **fields},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        summary.append({"file": out.name, "title": fields["title"], "has_abstract": bool(fields["abstract"]),
                        "footnotes_count": len(fields["footnotes"])})
        time.sleep(grobid.delay)

    (articles_dir / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Done: %d articles saved, %d failed. Output in %s", len(summary), len(failed), articles_dir)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path, help="proceedings PDF")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--grobid-url", default="http://localhost:8070")
    parser.add_argument("--min-pages", type=int, default=3, help="minimum pages per article")
    parser.add_argument("--delay", type=float, default=1.0, help="pause between GROBID full-text calls (s)")
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler(args.output_dir / "grobid_parse.log", encoding="utf-8"),
                                  logging.StreamHandler()])
    if not args.pdf.exists():
        parser.error(f"{args.pdf} not found")
    grobid = Grobid(args.grobid_url, args.delay)
    if not grobid.is_alive():
        parser.exit(1, f"GROBID is not reachable at {args.grobid_url}. Start it with:\n"
                       "  docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf\n")
    run(args.pdf, args.output_dir, grobid, args.min_pages)


if __name__ == "__main__":
    main()

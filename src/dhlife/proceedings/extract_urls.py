"""Pick the official project URL among the footnote URLs of each article, with a local LLM.

Input: the article JSON files written by ``grobid-parse``. Needs Ollama:

    ollama serve & ollama pull llama3.1:8b
    python -m dhlife extract-urls work/aiucd2019/articles/article_*.json -o work/aiucd2019/project_urls.json

Every footnote URL is fetched (first 1500 characters of visible text) and passed to the
model together with the article title and abstract. For Google Colab (GPU) see
``notebooks/extract_project_urls_colab.ipynb``, which runs the same prompt.
"""

import argparse
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

FETCH_TIMEOUT = 10
MAX_CONTENT_CHARS = 1500  # characters kept per page
PROMPT_SNIPPET_CHARS = 600  # characters per page sent to the model
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
SKIP_PATTERNS = ["doi.org", "raw.githubusercontent.com", ".pdf", ".zip", ".xml", ".json"]

URL_PATTERN = re.compile(r'https?://[^\s\)\]\},"\'>]+', re.IGNORECASE)

SYSTEM_PROMPT = (
    "You are an expert analyst of academic papers in digital humanities.\n"
    "Your task: given a paper's title, abstract, and a list of URLs found in its footnotes "
    "(each with a snippet of their actual web content), "
    "identify which URL is the official website of the research PROJECT described in the paper.\n\n"
    "Rules:\n"
    "- Return ONLY valid JSON, no markdown, no explanation.\n"
    "- A project website is a page CREATED AND MAINTAINED BY THE PROJECT TEAM to present the project itself — "
    "not a page that merely mentions or references the project.\n"
    "- The URL must point to the project's own dedicated online presence: its homepage, portal, or interface.\n"
    "- CRITICALLY, the URL must provide access to actual project OUTPUT or DATA, such as:\n"
    "  * Digital editions or critical editions of texts\n"
    "  * Digital libraries or archives with browsable/searchable content\n"
    "  * Datasets or corpora produced by the project\n"
    "  * Annotated collections, databases, or catalogues\n"
    "  * Interactive portals giving access to the project's resources\n"
    "- USE THE PAGE CONTENT SNIPPETS to verify whether a URL actually contains project data/outputs "
    "rather than just describing them.\n"
    "- EXCLUDE the following types of URLs:\n"
    "  * Pages that only DESCRIBE what the project has done, without providing access to the actual outputs\n"
    "  * Research center or university institutional pages\n"
    "  * Tools, libraries, or software frameworks used by the project (e.g. EVT, Transkribus)\n"
    "  * Standards or specification pages (e.g. IIIF, XML TEI, Dublin Core)\n"
    "  * 'Showcase' or aggregator pages (e.g. project directories, conference listings, blog posts about the project)\n"
    "  * DOI links, Wikipedia pages, or generic academic repositories\n"
    "  * GitHub repos (acceptable ONLY if no dedicated website exists AND the repo contains the actual project data/edition)\n"
    "- If multiple URLs seem plausible, prefer the one that gives direct access to the project's data or digital edition "
    "over one that merely describes the project.\n"
    "- If no URL fits, return null.\n\n"
    'Response format (strictly):\n'
    '{"project_url": "https://example.com"}\n'
    '{"project_url": null}'
)


def fetch_url_content(url: str) -> dict:
    """{'status': ok|error|timeout|skip, 'http_code': int|None, 'content': text or message}."""
    if any(p in url.lower() for p in SKIP_PATTERNS):
        return {"status": "skip", "http_code": None, "content": "[skipped: non-HTML resource]"}
    try:
        r = requests.get(url, timeout=FETCH_TIMEOUT, headers=HEADERS, allow_redirects=True)
    except requests.exceptions.Timeout:
        return {"status": "timeout", "http_code": None, "content": "[timeout]"}
    except Exception as e:  # noqa: BLE001 - any failure is reported to the model as text
        return {"status": "error", "http_code": None, "content": f"[error: {str(e)[:80]}]"}
    if r.status_code != 200:
        return {"status": "error", "http_code": r.status_code, "content": f"[HTTP {r.status_code}]"}
    content_type = r.headers.get("Content-Type", "")
    if "html" not in content_type:
        return {"status": "skip", "http_code": r.status_code, "content": f"[non-HTML content-type: {content_type}]"}
    soup = BeautifulSoup(r.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ", strip=True).split())
    return {"status": "ok", "http_code": 200, "content": text[:MAX_CONTENT_CHARS]}


def extract_urls(footnotes) -> list[str]:
    seen, urls = set(), []
    for note in footnotes or []:
        for url in URL_PATTERN.findall(note):
            url = url.rstrip(".,;:)")
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def ask_model(client, model: str, title, abstract, urls, fetched):
    blocks = []
    for url in urls:
        info = fetched.get(url, {})
        content = info.get("content", "")
        snippet = content[:PROMPT_SNIPPET_CHARS] if info.get("status") == "ok" else content
        blocks.append(f"  URL: {url}\n  Page content snippet: {snippet}")
    prompt = (
        f"Title: {title or '(no title)'}\n\n"
        f"Abstract: {abstract or '(no abstract)'}\n\n"
        "URLs from footnotes (with page content snippets):\n\n" + "\n\n".join(blocks) + "\n\n"
        "Which URL is the official project website?"
    )
    try:
        response = client.chat(model=model, options={"temperature": 0}, messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
    except Exception as e:  # noqa: BLE001
        tqdm.write(f"  Ollama error: {e}")
        return None
    match = re.search(r'\{[^{}]*"project_url"[^{}]*\}', response["message"]["content"], re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group()).get("project_url")
    except json.JSONDecodeError:
        return None


def main(argv=None):
    import ollama

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("articles", nargs="+", type=Path, help="article JSON files from grobid-parse")
    parser.add_argument("-o", "--output", type=Path, default=Path("project_urls.json"))
    parser.add_argument("--host", default="http://localhost:11434", help="Ollama server")
    parser.add_argument("--model", default="llama3.1:8b")
    args = parser.parse_args(argv)

    client = ollama.Client(host=args.host)
    results, skipped = [], 0
    for path in tqdm(sorted(p for p in args.articles if not p.name.startswith("_")), desc="Articles"):
        article = json.loads(path.read_text(encoding="utf-8"))
        urls = extract_urls(article.get("footnotes"))
        if not urls:
            skipped += 1
            continue
        fetched = {url: fetch_url_content(url) for url in urls}
        project_url = ask_model(client, args.model, article.get("title"), article.get("abstract"), urls, fetched)
        tqdm.write(f"{path.name}: {project_url or '(none)'}")
        results.append({
            "file": path.name,
            "title": article.get("title"),
            "project_url": project_url,
            "all_urls_found": urls,
            "fetch_summary": {u: {"status": v["status"], "http_code": v["http_code"]} for u, v in fetched.items()},
        })

    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    found = sum(1 for r in results if r["project_url"])
    print(f"Analysed {len(results)} articles: {found} with a project URL, {len(results) - found} without, "
          f"{skipped} skipped (no URLs in footnotes). Wrote {args.output}")


if __name__ == "__main__":
    main()

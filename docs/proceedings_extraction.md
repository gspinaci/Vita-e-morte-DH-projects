# Project URLs from conference proceedings (experimental)

A two-phase pipeline that finds the project URL of each article of a proceedings volume
(AIUCD, IRCDL). It was used to help build `data/sources/aiucd_proceedings.csv` and
`ircdl_proceedings.csv`; its output was always checked by hand.

```
proceedings.pdf ─grobid-parse─▶ article_NNNN.json (title, authors, abstract, footnotes) ─extract-urls─▶ project_urls.json
```

Install the extra dependencies with `pip install -e '.[extract]'`.

## Phase 1: split and parse the proceedings (`grobid-parse`)

It needs [GROBID](https://github.com/kermitt2/grobid) running locally:

```bash
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
curl http://localhost:8070/api/isalive      # true
```

Then:

```bash
dhlife grobid-parse AIUCD2019.pdf --output-dir out/aiucd2019
```

| option | default | |
|---|---|---|
| `--output-dir` | (required) | where the JSON files go |
| `--grobid-url` | `http://localhost:8070` | |
| `--min-pages` | 3 | minimum length of an article; lower it if articles are merged |
| `--delay` | 1.0 | seconds between GROBID calls; raise it on timeouts |

How it works: every page is sent to GROBID `processHeaderDocument`; a page with a title is
the start of a new article. Each article is cut into its own PDF, parsed with
`processFulltextDocument`, and title, authors, abstract, keywords and footnotes are taken from
the TEI. One JSON per article plus `_summary.json` are written:

```json
{
  "source_file": "article_0001_pages_1-12.pdf",
  "article_index": 1,
  "title": "…",
  "authors": ["…"],
  "abstract": "…",
  "keywords": ["…"],
  "footnotes": ["…"]
}
```

## Phase 2: pick the project URL (`extract-urls`)

For every article, the URLs in the footnotes are fetched (first 1500 characters of text; DOIs,
PDFs and other files are skipped) and given to a local LLM together with title and abstract.
The model must answer with the URL of the **official project website**, which:

- is made and maintained by the project team;
- gives access to the data or outputs (edition, database, archive…), not a description;
- is not a university page, a tool or standard used by the project, an aggregator, a DOI, or a
  GitHub repository when a dedicated site exists.

Locally, with [Ollama](https://ollama.com):

```bash
ollama serve &
ollama pull llama3.1:8b
dhlife extract-urls out/aiucd2019/article_*.json -o out/aiucd2019/project_urls.json
```

Options: `--host` (default `http://localhost:11434`), `--model` (default `llama3.1:8b`).

Without a local GPU, use [`notebooks/extract_project_urls_colab.ipynb`](../notebooks/extract_project_urls_colab.ipynb)
on Google Colab (Runtime → T4 GPU, run the cells in order, upload the JSON files, download
`project_urls.json`). It uses the same prompt.

Output:

```json
[
  {
    "file": "article_0001_pages_1-12.json",
    "title": "…",
    "project_url": "https://…",
    "all_urls_found": ["…"],
    "fetch_summary": {}
  }
]
```

## Troubleshooting

- *GROBID unreachable*: check `docker ps`, restart the container and wait ~10 s.
- *No articles detected*: the PDF may be a single article, have an unusual layout or bad OCR;
  try `--min-pages 1`.
- *GROBID timeouts*: raise `--delay`, give the container more memory (`docker run -m 4g …`).

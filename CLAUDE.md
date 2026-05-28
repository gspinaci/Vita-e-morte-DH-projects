# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Research dataset and scripts for the paper *"Life and Death of DH Projects: A Preliminary Investigation of Their Lifecycles in Italy"* (AIUCD XIV). The published dataset is [`DH_Projects_Survey_20250530_v01.csv`](DH_Projects_Survey_20250530_v01.csv) (also on [Zenodo](https://doi.org/10.5281/zenodo.15551858)). The code here is the pipeline that produced and maintains that dataset — it is research code, not a deployable application.

## Environment

- Python 3.8+ with a local `.venv/` (already present).
- Install deps from the top-level [`requirements.txt`](requirements.txt). The `automatic_extraction_url/` subproject has its own [`requirements.txt`](automatic_extraction_url/requirements.txt) (PDF/LLM stack).
- No build, lint, or test suite is configured. Scripts are run directly.

## Architecture / pipeline

The repo is organised by pipeline stage, not by module. Four logically separate stages feed each other through CSV files in [`dataset/`](dataset/):

1. **Retrieval** — [`retriever/crawlerDHprojects.ipynb`](retriever/crawlerDHprojects.ipynb) crawls candidate Italian DH project listings, producing [`retriever/dh_projects_results.csv`](retriever/dh_projects_results.csv) and the filtering spreadsheet.
2. **URL extraction from proceedings** — [`automatic_extraction_url/`](automatic_extraction_url/) is a two-phase pipeline (see its own [README](automatic_extraction_url/README.md)):
   - Phase 1: [`parsing_pdf_grobid.py`](automatic_extraction_url/parsing_pdf_grobid.py) needs a local GROBID at `http://localhost:8070` (`docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf`). Splits a proceedings PDF into per-article JSON with title/authors/abstract/footnotes.
   - Phase 2: [`extract_project_urls_colab.ipynb`](automatic_extraction_url/extract_project_urls_colab.ipynb) runs on Colab (or local Ollama with `llama3.1:8b`) to pick the official project URL out of footnote URLs.
3. **Archive / liveness checking** — `archivechecker.py`, `archivechecker2.py`, [`archivechecker3.py`](archivechecker3.py) are *successive iterations*; **`archivechecker3.py` is the current one**. It reads `dataset/lista_finale_post_script.csv`, hits the Wayback CDX API (`https://web.archive.org/cdx/search/cdx`) plus a live HTTP check per URL, and writes `dataset/lista_finale_post_script_2026.csv`. Logs go to `logs/script_final.log`. Helper one-offs live in [`helper_scripts/`](helper_scripts/) (`single_url_archive_checker.py`, `wayback_compare_filter.py`).
4. **Qualitative analysis & charts** — [`dataset/input/make_chart.ipynb`](dataset/input/make_chart.ipynb) produces figures (e.g. `output.png`); [`qualitative/data/`](qualitative/data/) holds the manually-coded *progetti-vivi* / *progetti-morti* split.

### Dataset flow (important for editing CSV paths)

`dataset/input/` holds *intermediate* CSVs (gitignored except for the directory). `dataset/` holds the curated outputs that *are* committed. Naming convention: `*_post_script.csv` = output of the archive checker; year suffix (`_2026`) = the most recent re-run. When updating the archive checker, the input/output filenames are hard-coded near the bottom of the script (currently [archivechecker3.py:181-182](archivechecker3.py#L181)) — update both together.

## Running the archive checker

```bash
python archivechecker3.py
```

It is rate-limit-aware (Wayback CDX: `RATE_LIMIT_DELAY`, `MAX_RETRIES`, `BACKOFF_FACTOR` at the top of the file) and uses a descriptive `User-Agent` per Internet Archive automation guidelines — preserve that if you refactor. The CDX call deliberately omits `collapse` and filters 4xx/5xx in Python, so changes there affect the "first seen / last seen" semantics that feed the paper's analysis.

## Conventions

- CSVs are the source of truth between stages — do not rename a committed `dataset/*.csv` without updating every script that reads it.
- The older `archivechecker.py` / `archivechecker2.py` are kept for provenance; new work goes into `archivechecker3.py` (or a successor).
- Output column names in the survey CSV (e.g. `url_first_seen`, `url_last_seen`, `functioning_website`) are the public schema of the Zenodo release — treat them as stable.

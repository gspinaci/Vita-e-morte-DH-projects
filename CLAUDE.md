# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Research dataset and code for *"Life and Death of DH Projects"* (AIUCD 2025 paper and its
extended version). The dataset is on Zenodo (concept DOI 10.5281/zenodo.15551857). This is
research code, not a deployable application. Overview in [README.md](README.md).

## Environment

- Python ≥ 3.10, local `.venv/`. `make install` (= `pip install -r requirements.txt`).
- Dependency ranges in [pyproject.toml](pyproject.toml); exact pins in [requirements.txt](requirements.txt). Keep both in sync.
- `make test` runs the pytest suite in [tests/](tests/) (offline: every HTTP call is mocked; fixture projects in `tests/conftest.py`). Also check a change by diffing command outputs (`reports/stats.md`, `reports/figures/*.png`, the CSVs) against the committed version.

## Architecture

Package [src/dhlife/](src/dhlife/); every stage is a subcommand, `python -m dhlife <cmd>`
(dispatcher in [__main__.py](src/dhlife/__main__.py)); each module has `main(argv=None)`.

- [paths.py](src/dhlife/paths.py): every file location. Never hard-code a path elsewhere.
- [schema.py](src/dhlife/schema.py): column lists, sentinels (`NOTPROVIDED`, `NOSTATUSCODE`),
  `read_projects` / `write_projects` (TRUE/FALSE booleans).
- [wayback.py](src/dhlife/wayback.py): CDX API client and live HTTP check.
- [analysis.py](src/dhlife/analysis.py): all logic behind the paper numbers; used by
  `stats.py` and `charts.py`.
- `sources`, `crawl`, `archive_check`, `check_url`, `stats`, `charts`, `release`,
  `qualitative/`, `proceedings/` (experimental GROBID + LLM URL extraction).

Data layers in [data/](data/README.md): `sources/` (frozen Google Sheet snapshot + cleaned
CSVs) → `curated/italian_dh_projects.csv` (hand-edited, source of truth) → `processed/` (generated) →
`release/` (Zenodo files, never edited). Outputs of `stats`/`charts`/`qualitative` go to
`reports/`.

## Rules

- The Google Sheet is frozen: never read it at analysis time; work from `data/sources/raw/`.
- Column names in [docs/data_dictionary.md](docs/data_dictionary.md) (`url_first_seen`,
  `functioning_website`, …) are the public Zenodo schema: keep them stable.
- Wayback semantics in `wayback.get_wayback_info` feed the paper's first/last-seen analysis:
  no `collapse`, `matchType=exact`, 4xx/5xx snapshots dropped in Python (3xx kept), previous
  values kept on fetch failure. Keep the descriptive `User-Agent` and the rate-limit/backoff
  constants (Internet Archive automation guidelines).
- `archive-check` takes ~1 hour; test changes with `check-url` or a few-row `--input`.
- Releases are new files (`dhlife release --version NN`, UTF-8); never overwrite one in
  `data/release/`.
- Qualitative data: see the memory notes on anonymisation; `.audit/` is never committed.

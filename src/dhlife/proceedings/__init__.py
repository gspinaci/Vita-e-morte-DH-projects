"""EXPERIMENTAL: find project URLs in conference proceedings (future work in the paper).

1. ``grobid_parse`` splits a proceedings PDF into articles and extracts title, authors,
   abstract, keywords and footnotes with GROBID (one JSON per article).
2. ``extract_urls`` asks a local LLM (Ollama) which footnote URL is the project website.

Not used to build the published dataset. Install with ``pip install -e '.[extract]'``.
"""

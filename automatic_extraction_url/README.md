# Automatic Extraction and disambiguation of Project URLs related to Italian DH projects. 

Automated pipeline to extract project URLs from footnotes in academic proceedings articles derived from AIUCD and IRCDL conferences.

## Overview

The project consists of two phases:

1. **Parsing and segmentation of proceedings** (`parsing_pdf_grobid.py`)  
   Converts a PDF containing conference proceedings into individual articles, extracting metadata (title, authors, abstract, footnotes).

2. **Project URL extraction** (`extract_project_urls_colab.ipynb`)  
   Analyzes URLs found in article footnotes and identifies the official project website using AI.

---

## Workflow

```
PDF proceedings (e.g., AIUCD2019.pdf)
         ↓
    GROBID API
         ↓
Automatic article boundary detection
         ↓
Split PDF → individual articles (article_0001.pdf, article_0002.pdf, ...)
         ↓
GROBID parsing of each article
         ↓
Extraction: title, authors, abstract, keywords, footnotes
         ↓
Save → JSON per article (article_0001.json, ...)
         ↓
         ↓↓↓ (Phase 2) ↓↓↓
         ↓
URL extraction from footnotes
         ↓
HTTP fetch content of each URL
         ↓
Ollama (llama3.1:8b) identifies project URL
         ↓
Save → project_urls.json
```

---

## Requirements

### Software

- **Python 3.8+**
- **Docker** (for GROBID)
- **Ollama** (for phase 2, optional if you don't use the notebook)

### Python packages

See `requirements.txt`:
```
pymupdf           # PDF reading/manipulation
requests          # HTTP calls
tqdm              # progress bars
langchain-community  # (optional, for future extensions)
ollama            # Ollama client
beautifulsoup4    # HTML parsing
lxml              # XML/HTML parsing
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Phase 1: Parsing and Segmentation of Proceedings

### Configuration

Modify the constants at the beginning of `parsing_pdf_grobid.py`:

```python
GROBID_BASE = "http://localhost:8070/api"           # GROBID URL
INPUT_PDF = "C:\\path\\to\\your\\proceedings.pdf"   # Input PDF
OUTPUT_DIR = Path("C:\\path\\output\\articles")     # Output folder for JSON
SPLIT_DIR = Path("C:\\path\\temp\\split_pdfs")      # Temp folder for split PDFs
MIN_PAGES_PER_ARTICLE = 3                           # Minimum pages threshold
GROBID_DELAY = 1.0                                  # Pause between requests (sec)
```

### Starting GROBID

GROBID is a REST service that must run on `localhost:8070`.  
Use Docker to start it easily:

```bash
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
```

This command:
- Downloads the GROBID Docker image (if not present)
- Starts the service on port 8070
- Keeps it running until you press `Ctrl+C`

**Verify GROBID is active:**
```bash
curl http://localhost:8070/api/isalive
# Expected response: 200 OK
```

### Execution

With GROBID running on another terminal:

```bash
python parsing_pdf_grobid.py "C:\path\to\proceedings.pdf"
```

Or if you configured `INPUT_PDF` in the script:
```bash
python parsing_pdf_grobid.py
```

**Output:**
- **JSON per article**: `output/articles/article_0001_pages_1-12.json`, etc.  
  Contains:
  ```json
  {
    "source_file": "article_0001_pages_1-12.pdf",
    "article_index": 1,
    "title": "Article Title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Abstract text...",
    "keywords": ["keyword1", "keyword2"],
    "footnotes": ["Note 1", "Note 2", ...]
  }
  ```

- **Summary**: `output/articles/_summary.json`  
  Summary list of all processed articles.

- **Log**: `pipeline.log`  
  Detailed execution tracking.

### How it works

1. **Automatic article boundary detection**  
   The script scans the PDF page by page, calling GROBID `/processHeaderDocument` to detect "headers" (titles + authors) that signal the start of a new article.

2. **PDF segmentation**  
   For each detected article, extracts the corresponding pages and saves them as a separate PDF.

3. **Full GROBID parsing**  
   Processes each segmented PDF with `/processFulltextDocument`, which returns XML in TEI format.

4. **XML extraction**  
   From the TEI XML extracts:
   - Main title
   - Authors (first name + last name)
   - Abstract
   - Keywords
   - Footnotes

5. **JSON save**  
   Each article is saved as JSON for easy further processing.

---

## Phase 2: Project URL Extraction

### Setup on Google Colab

Use the notebook `extract_project_urls_colab.ipynb` in Google Colab:

1. **Open on Colab:**  
   Load the notebook in [colab.research.google.com](https://colab.research.google.com)

2. **Enable GPU:**  
   Runtime → Change runtime type → T4 GPU

3. **Execute cells in order:**
   - **Cell 1**: Install Ollama and Python dependencies
   - **Cell 2**: Start the Ollama server
   - **Cell 3**: Download the `llama3.1:8b` model (~4.7GB)
   - **Cell 4**: Load JSON files from `parsing_pdf_grobid.py`
   - **Cell 5**: Fetch URL content + call Ollama
   - **Cell 6**: Download results

### How it works

1. **URL extraction**  
   From article footnotes, extracts all URLs using regex.

2. **HTTP fetch**  
   For each URL:
   - Makes an HTTP GET request
   - Extracts page text content (max 1500 characters)
   - Skips non-web URLs (DOI, PDF, binaries, etc.)

3. **AI evaluation**  
   Passes to Ollama:
   - Article title
   - Abstract
   - List of URLs with page content snippets
   
   The model identifies which URL is the **official project website** using strict criteria:
   - Must be created and maintained by the project team
   - Must provide access to project data/outputs (digital editions, databases, archives, etc.)
   - Not simple project descriptions, but access to actual results
   - Excludes: university pages, tools used, standards, aggregators, GitHub (if dedicated site exists), DOI, etc.

4. **Output**  
   File `project_urls.json`:
   ```json
   [
     {
       "file": "article_0001_pages_1-12.json",
       "title": "Article Title",
       "project_url": "https://example.com/project",
       "all_urls_found": ["https://example.com", "https://other.org", ...],
       "fetch_summary": { ... }
     },
     ...
   ]
   ```

### Offline use (local machine)

If you prefer not to use Colab:

1. Install Ollama locally from [ollama.com](https://ollama.com)
2. Start: `ollama serve`
3. Download the model: `ollama pull llama3.1:8b`
4. Adapt the notebook cells for your local environment (e.g., file dialogs instead of `google.colab.files`)

---

## Troubleshooting

### GROBID unreachable

```
ERROR: GROBID unreachable on localhost:8070
```

**Solution:**
- Verify Docker is running: `docker ps`
- Restart the container:
  ```bash
  docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
  ```
- Wait ~10 seconds for startup

### No articles detected

The script found 0 article boundaries.

**Causes:**
- The PDF is not a proceedings (is it a single article?)
- The format is very different from expected
- GROBID cannot detect titles

**Solutions:**
- Lower `MIN_PAGES_PER_ARTICLE` to 1-2
- Increase `GROBID_DELAY` if server is overloaded
- Verify the PDF is good quality OCR

### GROBID timeout

```
Timeout on article_0042.pdf
```

**Solutions:**
- Increase `GROBID_DELAY` to 2-3 seconds
- Restart the GROBID container
- Increase container memory: `docker run ... -m 4g ...`

### Ollama not responding (Colab)

```
ERROR: Ollama not responding, re-run this cell
```

**Solutions:**
- Re-run cell 2
- Wait a few more seconds before using the model
- Restart the runtime (Runtime → Restart runtime)

---

## Output Structure

```
automatic_extraction_url/
├── README.md
├── requirements.txt
├── parsing_pdf_grobid.py          # Main script for phase 1
├── extract_project_urls_colab.ipynb # Notebook for phase 2
├── pipeline.log                    # Execution log
├── output_articles/                # Phase 1 output
│   ├── article_0001.json
│   ├── article_0002.json
│   └── _summary.json
└── split_pdfs/                     # Split PDFs (temp)
```

---

## Specific Requirements by Task

### For `parsing_pdf_grobid.py`:
- Python 3.8+
- Docker (for GROBID)
- Packages: `pymupdf`, `requests`, `tqdm`

### For `extract_project_urls_colab.ipynb`:
- Google Colab (or local environment with Ollama)
- GPU (T4 recommended, for speed)
- Packages: `ollama`, `requests`, `beautifulsoup4`, `lxml`

---

## References

- **GROBID**: https://github.com/kermitt2/grobid
- **Ollama**: https://ollama.com
- **PyMuPDF**: https://pymupdf.readthedocs.io
- **TEI XML**: https://www.tei-c.org

---

## License

See main project: [Vita-e-morte-DH-projects](https://github.com/crosi/Vita-e-morte-DH-projects)

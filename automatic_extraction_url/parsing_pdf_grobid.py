"""
Pipeline per processare proceedings di conferenze:
1. Split del PDF unico in articoli singoli (tramite GROBID document segmentation)
2. Parse di ogni articolo con GROBID
3. Estrazione di titolo, abstract e footnotes
4. Salvataggio in JSON (un file per articolo)

Requisiti:
    pip install pymupdf requests langchain-community tqdm

GROBID deve girare su localhost:8070 (Docker):
    docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
"""

import json
import logging
import re
import time
from pathlib import Path

import fitz  # PyMuPDF
import requests
from tqdm import tqdm
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

GROBID_BASE = "http://localhost:8070/api"
INPUT_PDF = "C:\\Users\\crosi\\Downloads\\AIUCD2019%20BoA_DEF.pdf"       # <-- cambia con il tuo file
OUTPUT_DIR = Path("C:\\Users\\crosi\\Downloads\\output_articles") # cartella dove verranno salvati i JSON
SPLIT_DIR  = Path("C:\\Users\\crosi\\Downloads\\split_pdfs")      # cartella temporanea per i PDF splittati

# Quante pagine minime deve avere un articolo per essere considerato valido
MIN_PAGES_PER_ARTICLE = 3

# Pausa tra una chiamata GROBID e l'altra (secondi) — evita di sovraccaricare il server
GROBID_DELAY = 1.0

# Namespace XML usato da GROBID nel TEI output
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log", encoding="utf-8"),
        logging.StreamHandler(stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Verifica che GROBID sia raggiungibile
# ---------------------------------------------------------------------------

def check_grobid() -> bool:
    try:
        r = requests.get(f"{GROBID_BASE[:-4]}/api/isalive", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


# ---------------------------------------------------------------------------
# 2. Segmentazione del PDF in articoli singoli
#    Strategia: usa GROBID /processHeaderDocument su finestre di pagine
#    per individuare dove inizia ogni nuovo articolo (nuovo titolo/header).
#    Poi ritaglia e salva ogni segmento come PDF separato.
# ---------------------------------------------------------------------------

def extract_page_range_pdf(src_path: str, start: int, end: int, dest_path: Path):
    """Estrae le pagine [start, end] (0-indexed) da src e le salva in dest."""
    doc = fitz.open(src_path)
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=start, to_page=end)
    new_doc.save(str(dest_path))
    new_doc.close()
    doc.close()


def grobid_segment_pdf(pdf_path: Path) -> list[dict]:
    """
    Chiama GROBID /processFulltextDocument sul PDF e restituisce
    i range di pagine dei singoli articoli rilevati nella struttura TEI.
    """
    with open(pdf_path, "rb") as f:
        files = {"input": (pdf_path.name, f, "application/pdf")}
        data = {
            "generateIDs": "1",
            "consolidateHeader": "0",
            "segmentSentences": "0",
        }
        try:
            r = requests.post(
                f"{GROBID_BASE}/processFulltextDocument",
                files=files,
                data=data,
                timeout=300,
            )
        except requests.exceptions.ReadTimeout:
            log.error("GROBID timeout sul documento principale.")
            return []

    if r.status_code != 200:
        log.error(f"GROBID ha restituito status {r.status_code}")
        return []

    return r.text  # TEI XML grezzo


def detect_article_boundaries(pdf_path: str) -> list[tuple[int, int]]:
    """
    Strategia semplice ma robusta per trovare i confini degli articoli
    in un proceedings: scansiona il PDF pagina per pagina e usa GROBID
    /processHeaderDocument su singole pagine per rilevare i "nuovi header"
    (titolo + autori), indicatori di un nuovo articolo.

    Restituisce una lista di tuple (pagina_inizio, pagina_fine) 0-indexed.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    log.info(f"Totale pagine: {total_pages}. Ricerca confini articoli...")

    article_starts = []

    for page_idx in tqdm(range(total_pages), desc="Scansione pagine"):
        # Estrai una singola pagina come PDF temporaneo
        tmp_path = SPLIT_DIR / f"_tmp_page_{page_idx}.pdf"
        extract_page_range_pdf(pdf_path, page_idx, page_idx, tmp_path)

        with open(tmp_path, "rb") as f:
            files = {"input": (tmp_path.name, f, "application/pdf")}
            try:
                r = requests.post(
                    f"{GROBID_BASE}/processHeaderDocument",
                    files=files,
                    data={"consolidateHeader": "0"},
                    timeout=30,
                )
            except Exception:
                tmp_path.unlink(missing_ok=True)
                continue

        tmp_path.unlink(missing_ok=True)

        if r.status_code == 200 and r.text.strip():
            # Verifica che ci sia un titolo rilevato (elemento <title>)
            try:
                root = ET.fromstring(r.text)
                title_el = root.find(".//tei:titleStmt/tei:title", TEI_NS)
                if title_el is not None and title_el.text and len(title_el.text.strip()) > 10:
                    log.info(f"  Nuovo articolo rilevato a pagina {page_idx + 1}: {title_el.text.strip()[:60]}")
                    article_starts.append(page_idx)
            except ET.ParseError:
                pass

        time.sleep(0.3)  # piccola pausa

    if not article_starts:
        log.warning("Nessun confine rilevato automaticamente. Tratto tutto il PDF come un unico documento.")
        return [(0, total_pages - 1)]

    # Costruisce i range (start, end) da lista di start
    boundaries = []
    for i, start in enumerate(article_starts):
        end = article_starts[i + 1] - 1 if i + 1 < len(article_starts) else total_pages - 1
        if (end - start + 1) >= MIN_PAGES_PER_ARTICLE:
            boundaries.append((start, end))
        else:
            log.debug(f"Articolo a pagina {start+1} scartato (troppo corto: {end-start+1} pag.)")

    log.info(f"Articoli rilevati: {len(boundaries)}")
    return boundaries


def split_pdf_into_articles(pdf_path: str, boundaries: list[tuple[int, int]]) -> list[Path]:
    """Salva ogni segmento come PDF nella SPLIT_DIR e restituisce i path."""
    paths = []
    for i, (start, end) in enumerate(boundaries):
        out_path = SPLIT_DIR / f"article_{i+1:04d}_pages_{start+1}-{end+1}.pdf"
        extract_page_range_pdf(pdf_path, start, end, out_path)
        paths.append(out_path)
    log.info(f"PDF splittati salvati in: {SPLIT_DIR}")
    return paths


# ---------------------------------------------------------------------------
# 3. Parse GROBID + estrazione campi
# ---------------------------------------------------------------------------

def parse_with_grobid(pdf_path: Path) -> str | None:
    """Chiama GROBID processFulltextDocument e restituisce il TEI XML."""
    with open(pdf_path, "rb") as f:
        files = {"input": (pdf_path.name, f, "application/pdf")}
        data = {
            "generateIDs": "1",
            "consolidateHeader": "0",
            "segmentSentences": "0",
        }
        try:
            r = requests.post(
                f"{GROBID_BASE}/processFulltextDocument",
                files=files,
                data=data,
                timeout=120,
            )
        except requests.exceptions.ReadTimeout:
            log.error(f"Timeout su {pdf_path.name}")
            return None

    if r.status_code != 200:
        log.error(f"GROBID error {r.status_code} su {pdf_path.name}")
        return None
    return r.text


def clean_text(text: str) -> str:
    """Pulizia base del testo estratto."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_fields(tei_xml: str) -> dict:
    """
    Estrae titolo, abstract e footnotes dal TEI XML di GROBID.
    Restituisce un dizionario con i campi estratti.
    """
    result = {
        "title": None,
        "abstract": None,
        "footnotes": [],
        "authors": [],
        "keywords": [],
    }

    try:
        root = ET.fromstring(tei_xml)
    except ET.ParseError as e:
        log.error(f"Errore parsing XML: {e}")
        return result

    # -- Titolo --
    title_el = root.find(".//tei:titleStmt/tei:title[@type='main']", TEI_NS)
    if title_el is None:
        title_el = root.find(".//tei:titleStmt/tei:title", TEI_NS)
    if title_el is not None:
        result["title"] = clean_text("".join(title_el.itertext()))

    # -- Autori --
    for author_el in root.findall(".//tei:sourceDesc//tei:author", TEI_NS):
        forename = author_el.find(".//tei:forename", TEI_NS)
        surname  = author_el.find(".//tei:surname", TEI_NS)
        name_parts = []
        if forename is not None and forename.text:
            name_parts.append(forename.text.strip())
        if surname is not None and surname.text:
            name_parts.append(surname.text.strip())
        if name_parts:
            result["authors"].append(" ".join(name_parts))

    # -- Abstract --
    abstract_el = root.find(".//tei:profileDesc/tei:abstract", TEI_NS)
    if abstract_el is not None:
        result["abstract"] = clean_text("".join(abstract_el.itertext()))

    # -- Keywords --
    for kw_el in root.findall(".//tei:keywords/tei:term", TEI_NS):
        if kw_el.text:
            result["keywords"].append(kw_el.text.strip())

    # -- Footnotes --
    # In TEI GROBID le footnotes sono <note place="foot"> nel body
    for note_el in root.findall(".//tei:body//tei:note[@place='foot']", TEI_NS):
        text = clean_text("".join(note_el.itertext()))
        if text:
            result["footnotes"].append(text)

    # Alcune versioni le mettono anche nel back
    for note_el in root.findall(".//tei:back//tei:note[@place='foot']", TEI_NS):
        text = clean_text("".join(note_el.itertext()))
        if text and text not in result["footnotes"]:
            result["footnotes"].append(text)

    return result


# ---------------------------------------------------------------------------
# 4. Salvataggio JSON
# ---------------------------------------------------------------------------

def save_json(data: dict, pdf_path: Path, index: int):
    """Salva il dizionario estratto come file JSON."""
    stem = pdf_path.stem  # es. article_0001_pages_1-12
    out_path = OUTPUT_DIR / f"{stem}.json"
    payload = {
        "source_file": pdf_path.name,
        "article_index": index,
        **data,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path


# ---------------------------------------------------------------------------
# 5. Pipeline principale
# ---------------------------------------------------------------------------

def run_pipeline(pdf_path: str):
    # Crea directory
    SPLIT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Verifica GROBID
    if not check_grobid():
        log.error(
            "GROBID non raggiungibile su localhost:8070.\n"
            "Avvia il container con:\n"
            "  docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf"
        )
        return

    log.info(f"=== Inizio pipeline su: {pdf_path} ===")

    # Step 1: rileva confini articoli
    boundaries = detect_article_boundaries(pdf_path)
    if not boundaries:
        log.error("Impossibile rilevare articoli nel PDF.")
        return

    # Step 2: splitta il PDF
    article_pdfs = split_pdf_into_articles(pdf_path, boundaries)

    # Step 3 & 4: per ogni articolo, parse GROBID + estrai + salva
    results_summary = []
    failed = []

    for idx, pdf in enumerate(tqdm(article_pdfs, desc="Parsing articoli"), start=1):
        log.info(f"[{idx}/{len(article_pdfs)}] Processing: {pdf.name}")

        tei_xml = parse_with_grobid(pdf)
        if not tei_xml:
            failed.append(pdf.name)
            continue

        fields = extract_fields(tei_xml)

        # Salta articoli senza titolo né abstract (probabilmente pagine di frontespizio)
        if not fields["title"] and not fields["abstract"]:
            log.warning(f"  -> Nessun titolo/abstract rilevato, skip.")
            continue

        out_path = save_json(fields, pdf, idx)
        log.info(f"  -> Salvato: {out_path.name} | Titolo: {fields['title'] or '(none)'}")

        results_summary.append({
            "file": out_path.name,
            "title": fields["title"],
            "has_abstract": bool(fields["abstract"]),
            "footnotes_count": len(fields["footnotes"]),
        })

        time.sleep(GROBID_DELAY)

    # Report finale
    log.info("\n=== Pipeline completata ===")
    log.info(f"Articoli processati con successo: {len(results_summary)}")
    log.info(f"Articoli falliti: {len(failed)}")

    summary_path = OUTPUT_DIR / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    log.info(f"Summary salvato in: {summary_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    pdf_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_PDF

    if not Path(pdf_file).exists():
        print(f"Errore: file '{pdf_file}' non trovato.")
        print("Uso: python process_proceedings.py <path/al/proceedings.pdf>")
        sys.exit(1)

    run_pipeline(pdf_file)
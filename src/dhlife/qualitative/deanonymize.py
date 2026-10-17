"""Rimuovi timestamp dai CSV qualitativi e salvali in un file separato per audit trail.

Già eseguito una volta sui CSV in data/qualitative/ (lo script è idempotente):

    python -m dhlife.qualitative.deanonymize
"""

import csv

from dhlife import paths

DATA_DIR = paths.QUALITATIVE_DATA
AUDIT_DIR = DATA_DIR / ".audit"


def main(argv=None):
    AUDIT_DIR.mkdir(exist_ok=True)

    for fname in ["survey_discontinued_projects.csv", "survey_active_projects.csv"]:
        csv_path = DATA_DIR / fname
        audit_path = AUDIT_DIR / f".{fname}.timestamps"

        rows = list(csv.reader(csv_path.open(encoding="utf-8")))
        if not rows:
            continue

        # Header: rimuovi "Informazioni cronologiche". Se manca, il file è già stato
        # anonimizzato: non toccarlo (altrimenti si perderebbe la prima colonna di risposte
        # e si sovrascriverebbe l'audit trail).
        header = rows[0]
        if not header or header[0].strip() != "Informazioni cronologiche":
            print(f"- {fname}: nessun timestamp, già anonimizzato")
            continue
        header = header[1:]

        # Data rows: estrai timestamp (col 0) e dati (col 1+)
        data_rows = []
        timestamps = []

        for i, row in enumerate(rows[1:], 1):
            if row:
                ts = row[0] if row else ""
                data = row[1:] if len(row) > 1 else []
                timestamps.append(ts)
                data_rows.append(data)

        # Scrivi CSV anonimizzato
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(data_rows)

        # Scrivi audit trail (row_index, timestamp) — solo con permessi ristretti
        with audit_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["row_index", "submission_timestamp"])
            for i, ts in enumerate(timestamps, 1):
                w.writerow([i, ts])

        print(f"✓ {fname}: rimossi {len(timestamps)} timestamp → {audit_path.name}")

    print("\nAudit trail salvato in .audit/ (ignorato da git)")


if __name__ == "__main__":
    main()

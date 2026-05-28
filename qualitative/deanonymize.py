"""Rimuovi timestamp dai CSV qualitavi e salvali in un file separato per audit trail."""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
AUDIT_DIR = DATA_DIR / ".audit"

AUDIT_DIR.mkdir(exist_ok=True)

for fname in ["progetti-morti.csv", "progetti-vivi.csv"]:
    csv_path = DATA_DIR / fname
    audit_path = AUDIT_DIR / f".{fname}.timestamps"

    rows = list(csv.reader(csv_path.open(encoding="utf-8")))
    if not rows:
        continue

    # Header: rimuovi "Informazioni cronologiche"
    header = rows[0]
    if header and header[0].strip() == "Informazioni cronologiche":
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

"""Genera report Markdown in italiano dalle due survey qualitative.

Input:  qualitative/data/progetti-morti.csv, qualitative/data/progetti-vivi.csv
Output: qualitative/report-progetti-morti.md, qualitative/report-progetti-vivi.md
"""

import csv
import statistics
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR = Path(__file__).resolve().parent

MORTI_CSV = DATA_DIR / "progetti-morti.csv"
VIVI_CSV = DATA_DIR / "progetti-vivi.csv"

MORTI_D2_FACTORS = [
    "Finanziamento insufficiente o temporaneo",
    "Perdita di personale chiave",
    "Obsolescenza tecnologica (bit rot)",
    "Assenza di pianificazione della sostenibilità",
    "Mancanza di supporto istituzionale",
    "Guasto del server o del servizio di hosting",
    "Dipendenza da tecnologie deprecate",
    "Documentazione tecnica insufficiente",
    "Assenza di una figura responsabile della manutenzione",
    "Scarsa interoperabilità con altri sistemi",
    "Problemi legali o di conformità normativa",
    "Mancato rinnovo del dominio o dell'hosting",
    "Dispute sui diritti o sulla proprietà del progetto",
]


def read_rows(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    data = rows[1:]
    return [r for r in data if any((c or "").strip() for c in r[1:])]


def col(rows, idx):
    return [(r[idx] if idx < len(r) else "").strip() for r in rows]


def counts(values, *, drop_empty=True):
    c = Counter()
    for v in values:
        if drop_empty and not v:
            continue
        c[v] += 1
    return c


def _split_multi(value: str) -> list[str]:
    parts, buf, depth = [], [], 0
    for ch in value:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip().strip('"') for p in parts if p.strip().strip('"')]


def multi_counts(values):
    c = Counter()
    for v in values:
        if not v:
            continue
        for p in _split_multi(v):
            c[p] += 1
    return c


def likert_stats(values):
    nums = []
    for v in values:
        if not v or v.upper() == "N/A":
            continue
        try:
            n = int(v)
        except ValueError:
            try:
                n = int(float(v))
            except ValueError:
                continue
        if 1 <= n <= 5:
            nums.append(n)
    if not nums:
        return None
    return {
        "n": len(nums),
        "media": statistics.mean(nums),
        "mediana": statistics.median(nums),
        "moda": Counter(nums).most_common(1)[0][0],
        "distribuzione": Counter(nums),
    }


def pct(n, total):
    return f"{(100 * n / total):.0f}%" if total else "—"


def fmt_counter(c: Counter, total: int, *, top=None) -> str:
    items = c.most_common(top) if top else c.most_common()
    if not items:
        return "_nessun dato_"
    lines = [f"- {k}: **{v}** ({pct(v, total)})" for k, v in items]
    return "\n".join(lines)


def fmt_likert_table(likerts: dict[str, dict]) -> str:
    header = "| Item | n | Media | Mediana | Moda | Distribuzione (1→5) |\n|---|---|---|---|---|---|"
    lines = [header]
    for label, s in likerts.items():
        if s is None:
            lines.append(f"| {label} | 0 | — | — | — | — |")
            continue
        dist = " · ".join(str(s["distribuzione"].get(i, 0)) for i in range(1, 6))
        lines.append(
            f"| {label} | {s['n']} | {s['media']:.2f} | {s['mediana']:.1f} | {s['moda']} | {dist} |"
        )
    return "\n".join(lines)


def report_morti(rows: list[list[str]]) -> str:
    n = len(rows)
    roles = counts(col(rows, 1))
    institutions = counts(col(rows, 2))
    starts = counts(col(rows, 3))
    durations = counts(col(rows, 4))
    outputs = multi_counts(col(rows, 5))
    funding = counts(col(rows, 6))
    team = counts(col(rows, 7))
    tech_figure = counts(col(rows, 8))
    hosting = counts(col(rows, 9))

    c_items = {
        "C1 — piano di sostenibilità iniziale": likert_stats(col(rows, 10)),
        "C2 — discussione fine finanziamento": likert_stats(col(rows, 11)),
        "C3 — documentazione tecnica": likert_stats(col(rows, 12)),
        "C4 — accessibilità a lungo termine (FAIR)": likert_stats(col(rows, 13)),
    }
    c5 = counts(col(rows, 14))
    c6 = counts(col(rows, 15))

    d1_causes = multi_counts(col(rows, 16))
    d2_by_factor = {
        f: likert_stats(col(rows, 17 + i)) for i, f in enumerate(MORTI_D2_FACTORS)
    }
    d3_mode = counts(col(rows, 30))
    d4 = counts(col(rows, 31))
    d4a = multi_counts(col(rows, 32))

    d2_ranked = sorted(
        ((f, s) for f, s in d2_by_factor.items() if s is not None),
        key=lambda x: x[1]["media"],
        reverse=True,
    )

    patterns = []
    inst_top, inst_top_n = institutions.most_common(1)[0] if institutions else ("—", 0)
    if inst_top_n:
        patterns.append(
            f"Istituzione prevalente: **{inst_top}** ({pct(inst_top_n, n)} dei progetti)."
        )
    host_top = hosting.most_common(1)[0] if hosting else None
    if host_top:
        patterns.append(
            f"Modello di hosting più frequente: **{host_top[0]}** ({pct(host_top[1], n)})."
        )
    c1 = c_items["C1 — piano di sostenibilità iniziale"]
    if c1:
        giudizio = "debole" if c1["media"] < 3 else ("intermedia" if c1["media"] < 4 else "solida")
        patterns.append(
            f"La pianificazione di sostenibilità iniziale (C1) risulta **{giudizio}** "
            f"(media {c1['media']:.2f}/5)."
        )
    c6_no = c6.get("No", 0)
    if c6_no:
        patterns.append(
            f"Nel **{pct(c6_no, n)}** dei casi l'ente finanziatore **non** ha richiesto "
            f"un piano di sostenibilità o di gestione dei dati (C6)."
        )
    if d2_ranked:
        top_factors = ", ".join(
            f"_{f}_ (media {s['media']:.2f})" for f, s in d2_ranked[:3]
        )
        patterns.append(f"Top 3 fattori di rischio per gravità percepita (D2): {top_factors}.")
    if d1_causes:
        top_cause, top_cause_n = d1_causes.most_common(1)[0]
        patterns.append(
            f"Causa di discontinuazione più ricorrente (D1): **{top_cause}** "
            f"({top_cause_n} menzioni su {n} risposte)."
        )

    d2_lines = ["| Fattore | n | Media | Mediana | Moda |", "|---|---|---|---|---|"]
    for f, s in d2_ranked:
        d2_lines.append(
            f"| {f} | {s['n']} | {s['media']:.2f} | {s['mediana']:.1f} | {s['moda']} |"
        )

    return f"""# Report — Progetti DH discontinuati (`progetti-morti.csv`)

_Analisi automatica generata da `analyze_surveys.py`._

## 1. Panoramica

- Risposte valide: **{n}**
- Ruoli dei rispondenti (A1):
{fmt_counter(roles, n)}
- Tipo di istituzione ospitante (A2):
{fmt_counter(institutions, n)}

## 2. Periodo di avvio e durata

- Anno di avvio (A3):
{fmt_counter(starts, n)}
- Durata online (A4):
{fmt_counter(durations, n)}

## 3. Struttura del progetto

- Output principali (B1, risposta multipla):
{fmt_counter(outputs, n)}
- Modello di finanziamento (B2):
{fmt_counter(funding, n)}
- Dimensione del team (B3):
{fmt_counter(team, n)}
- Figura tecnica dedicata (B4):
{fmt_counter(tech_figure, n)}
- Infrastruttura di hosting (B5):
{fmt_counter(hosting, n)}

## 4. Sostenibilità (C1–C6)

{fmt_likert_table(c_items)}

- C5 — figura responsabile della manutenzione a lungo termine:
{fmt_counter(c5, n)}
- C6 — piano di sostenibilità richiesto dal finanziatore:
{fmt_counter(c6, n)}

## 5. Fine vita e fattori di rischio

- Cause principali di discontinuazione (D1, risposta multipla):
{fmt_counter(d1_causes, n)}

- Fattori di rischio D2 ordinati per gravità media percepita:

{chr(10).join(d2_lines)}

- Modalità di discontinuazione (D3):
{fmt_counter(d3_mode, n)}
- Presenza di segnali premonitori (D4):
{fmt_counter(d4, n)}
- Tipologia di segnali premonitori (D4a, risposta multipla):
{fmt_counter(d4a, n)}

## 6. Pattern osservati

{chr(10).join(f"- {p}" for p in patterns) if patterns else "_nessun pattern rilevante_"}
"""


def report_vivi(rows: list[list[str]]) -> str:
    n = len(rows)
    roles = counts(col(rows, 1))
    institutions = counts(col(rows, 2))
    starts = counts(col(rows, 3))
    durations = counts(col(rows, 4))
    outputs = multi_counts(col(rows, 5))
    funding = counts(col(rows, 6))
    team = counts(col(rows, 7))
    tech_figure = counts(col(rows, 8))
    hosting = counts(col(rows, 9))

    c_items = {
        "C1 — piano di sostenibilità iniziale": likert_stats(col(rows, 10)),
        "C2 — discussione fine finanziamento": likert_stats(col(rows, 11)),
        "C3 — documentazione tecnica": likert_stats(col(rows, 12)),
        "C4 — accessibilità a lungo termine (FAIR)": likert_stats(col(rows, 13)),
    }
    c4a_tools = multi_counts(col(rows, 14))
    c5 = counts(col(rows, 15))
    c6 = counts(col(rows, 16))

    d1_incidents = counts(col(rows, 17))
    d1a_motivi = [v for v in col(rows, 18) if v]
    d2_prob = likert_stats(col(rows, 19))
    d3_causes = multi_counts(col(rows, 20))
    d4 = counts(col(rows, 21))
    d4a = multi_counts(col(rows, 22))

    patterns = []
    inst_top = institutions.most_common(1)[0] if institutions else None
    if inst_top:
        patterns.append(
            f"Istituzione prevalente: **{inst_top[0]}** ({pct(inst_top[1], n)} dei progetti)."
        )
    host_top = hosting.most_common(1)[0] if hosting else None
    if host_top:
        patterns.append(
            f"Modello di hosting più frequente: **{host_top[0]}** ({pct(host_top[1], n)})."
        )
    c1 = c_items["C1 — piano di sostenibilità iniziale"]
    if c1:
        giudizio = "debole" if c1["media"] < 3 else ("intermedia" if c1["media"] < 4 else "solida")
        patterns.append(
            f"La pianificazione di sostenibilità iniziale (C1) risulta **{giudizio}** "
            f"(media {c1['media']:.2f}/5)."
        )
    if d2_prob:
        patterns.append(
            f"Probabilità percepita di future problematiche di mantenimento (D2): "
            f"media **{d2_prob['media']:.2f}/5**, mediana {d2_prob['mediana']:.1f}."
        )
    if d3_causes:
        top3 = ", ".join(f"_{k}_ ({v})" for k, v in d3_causes.most_common(3))
        patterns.append(f"Top 3 cause di discontinuazione attese (D3): {top3}.")
    d1_yes = d1_incidents.get("Sì", 0)
    if d1_yes:
        patterns.append(
            f"Il **{pct(d1_yes, n)}** dei progetti dichiara di aver già avuto episodi "
            f"di accessibilità compromessa (D1)."
        )
    c6_no = c6.get("No", 0)
    if c6_no:
        patterns.append(
            f"Nel **{pct(c6_no, n)}** dei casi il finanziatore **non** ha richiesto "
            f"un piano di sostenibilità (C6)."
        )

    motivi_block = (
        "\n".join(f"  - _{m}_" for m in d1a_motivi) if d1a_motivi else "  _nessuna motivazione testuale fornita_"
    )

    return f"""# Report — Progetti DH attivi (`progetti-vivi.csv`)

_Analisi automatica generata da `analyze_surveys.py`._

## 1. Panoramica

- Risposte valide: **{n}**
- Ruoli dei rispondenti (A1):
{fmt_counter(roles, n)}
- Tipo di istituzione ospitante (A2):
{fmt_counter(institutions, n)}

## 2. Periodo di avvio e durata online

- Anno di avvio (A3):
{fmt_counter(starts, n)}
- Tempo di accessibilità online (A4):
{fmt_counter(durations, n)}

## 3. Struttura del progetto

- Output principali (B1, risposta multipla):
{fmt_counter(outputs, n)}
- Modello di finanziamento (B2):
{fmt_counter(funding, n)}
- Dimensione del team (B3):
{fmt_counter(team, n)}
- Figura tecnica dedicata (B4):
{fmt_counter(tech_figure, n)}
- Infrastruttura di hosting (B5):
{fmt_counter(hosting, n)}

## 4. Sostenibilità (C1–C6)

{fmt_likert_table(c_items)}

- C4a — strumenti adottati per l'accessibilità a lungo termine (risposta multipla):
{fmt_counter(c4a_tools, n)}
- C5 — figura responsabile della manutenzione a lungo termine:
{fmt_counter(c5, n)}
- C6 — piano di sostenibilità richiesto dal finanziatore:
{fmt_counter(c6, n)}

## 5. Rischi e prospettive di continuità

- D1 — incidenti di accessibilità durante il ciclo di vita:
{fmt_counter(d1_incidents, n)}
- D1a — motivazioni testuali riportate:
{motivi_block}
- D2 — probabilità percepita di future problematiche di mantenimento (Likert 1–5):
{("  - n=" + str(d2_prob['n']) + ", media **" + f"{d2_prob['media']:.2f}" + "**, mediana " + f"{d2_prob['mediana']:.1f}" + ", moda " + str(d2_prob['moda'])) if d2_prob else "  _nessun dato_"}
- D3 — cause attese di possibile discontinuazione (risposta multipla):
{fmt_counter(d3_causes, n)}
- D4 — presenza di segnali premonitori:
{fmt_counter(d4, n)}
- D4a — tipologia dei segnali (risposta multipla):
{fmt_counter(d4a, n)}

## 6. Pattern osservati

{chr(10).join(f"- {p}" for p in patterns) if patterns else "_nessun pattern rilevante_"}
"""


def main() -> None:
    morti_rows = read_rows(MORTI_CSV)
    vivi_rows = read_rows(VIVI_CSV)

    (OUT_DIR / "report-progetti-morti.md").write_text(report_morti(morti_rows), encoding="utf-8")
    (OUT_DIR / "report-progetti-vivi.md").write_text(report_vivi(vivi_rows), encoding="utf-8")

    print(f"Scritti: report-progetti-morti.md ({len(morti_rows)} risposte), "
          f"report-progetti-vivi.md ({len(vivi_rows)} risposte)")


if __name__ == "__main__":
    main()

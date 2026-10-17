# Sources

Where the candidate projects come from. Everything here is input to the manual curation
that produced `data/curated/italian_dh_projects.csv`; it is kept for provenance and reproducibility.

The working spreadsheet ([Google Sheet](https://docs.google.com/spreadsheets/d/1G3WiRMoopP8Y2FlVJfwCRqZVLilw-aMQRBxF_SoMF20))
is **frozen**: it was snapshotted on 2026-10-16 to `raw/working_sheet_snapshot_2026-10-16.xlsx` and is
never read at analysis time. `python -m dhlife sources` turns the relevant tabs of the
snapshot into the clean CSVs below (English snake_case columns, empty rows and columns
dropped, `TRUE`/`FALSE` booleans). Free-text notes are left in the original Italian.

| file | sheet tab | rows | content | `provenance` value |
|---|---|---:|---|---|
| `italian_dh_centres.csv` | Centri DH | 22 | Italian DH centres and institutions; `urls` lists their project pages (`; `-separated). Input of `dhlife crawl`. | |
| `italian_dh_centres_crawled_links.csv` | – | 329 | Candidate links found by `dhlife crawl` (Dec 2024 run). Uncurated. | |
| `italian_dh_centres_projects.csv` | dh italian projects | 116 | Projects of the DH centres, curated from the crawl. | `Italian DH Institutions` |
| `knot_all_homepages.csv` | KNOT aggregator | 99 | KNOT records and their homepage (`?s foaf:homepage ?o`). | |
| `knot_selected_projects.csv` | KNOT finale | 75 | KNOT projects retained. | `KNOT` |
| `aiucd_proceedings_projects.csv` | Proceedings AIUCD | 50 | Projects found in the AIUCD conference proceedings. | `AIUCD` |
| `ircdl_proceedings_articles.csv` | IRCDL | 140 | Articles of the IRCDL proceedings (2005–) and the project URL, when any. | `IRCDL` |
| `dh_awards_all_nominees.csv` | DH Awards | 719 | All DH Awards nominees. | |
| `dh_awards_italian_nominees.csv` | DH Awards (Italians) | 16 | Italian nominees. | `DH Awards` |
| `digital_editions_catalogue_italian.csv` | – | 8 | Italian editions from the [Catalogue of Digital Editions](https://dig-ed-cat.acdh.oeaw.ac.at/) (April 2025 export, filtered). | `Catalogue Digital Editions` |

The `dead_projects` tab was extracted once to `data/curated/last_seen_manual_corrections.csv`
(manually verified last-seen dates of 15 discontinued projects). That file is now edited by
hand, so `dhlife sources` no longer writes it.

Two informal remarks in the AIUCD notes are reworded by `dhlife sources` (`NOTE_REWORDING`);
the raw snapshot still has the original text.

`raw/` also holds `italian_dh_centres_link_filtering.xlsx`, the worksheet used to filter
the crawled links.

The other tabs of the snapshot ("Lista finale", "Lista finale (Post script) 4/5",
"LF (PS) 5 - Corretto", "old …", "Foglio21", "Planning", "Aggregatori",
"post script non risolvono", "dead_project_with_snapshot") are earlier versions of the
project list or scratch work. They are superseded by `data/curated/italian_dh_projects.csv` and are
not extracted. "Lista finale" is the 270-project list of the AIUCD 2025 paper.

The Zenodo record also lists the dataset *Classification of web-based Digital Humanities
projects* among the sources; no file from it is in this repository or in the spreadsheet.

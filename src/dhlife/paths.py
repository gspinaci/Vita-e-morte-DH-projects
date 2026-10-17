"""Canonical locations of every file the pipeline reads or writes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
SOURCES = DATA / "sources"
SOURCES_RAW = SOURCES / "raw"
SHEET_SNAPSHOT = SOURCES_RAW / "working_sheet_snapshot_2026-10-16.xlsx"

CURATED = DATA / "curated"
PROJECTS = CURATED / "italian_dh_projects.csv"
LAST_SEEN_CORRECTIONS = CURATED / "last_seen_manual_corrections.csv"

PROCESSED = DATA / "processed"
PROJECTS_ARCHIVE = PROCESSED / "italian_dh_projects_wayback_check_2026.csv"
UNAVAILABLE_PROJECTS = PROCESSED / "unavailable_projects_2026.csv"
STATUS_DISCREPANCIES = PROCESSED / "live_status_vs_manual_check_2026.csv"

RELEASE = DATA / "release"
QUALITATIVE_DATA = DATA / "qualitative"

REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
QUALITATIVE_REPORTS = REPORTS / "qualitative"
STATS_REPORT = REPORTS / "stats.md"

LOGS = ROOT / "logs"

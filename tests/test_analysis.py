import pandas as pd
import pytest

from dhlife import analysis


@pytest.fixture
def dated(projects):
    return analysis.add_years(projects)


def test_migrated(projects):
    assert analysis.migrated(projects).tolist() == [False, True, False, False]


def test_add_years_handles_sentinels(dated):
    assert dated["year_first_seen"].tolist()[:3] == [2010, 2012, 2008]
    assert pd.isna(dated.loc[3, "year_first_seen"])
    assert dated["year_last_seen"].tolist()[:3] == [2026, 2020, 2018]


def test_apply_last_seen_corrections(tmp_path, projects):
    path = tmp_path / "corrections.csv"
    path.write_text(
        "title,project_url,correct_last_seen\n"
        "Ended,https://ended.it,2015-05-05 00:00:00\n"
        "Ghost,https://ghost.it,2001-01-01 00:00:00\n"
        "No date,https://active.it,\n"
    )
    corrected, unmatched = analysis.apply_last_seen_corrections(projects, path)
    assert corrected.loc[2, "url_last_seen"] == "2015-05-05 00:00:00"
    assert corrected.loc[0, "url_last_seen"] == projects.loc[0, "url_last_seen"]
    assert projects.loc[2, "url_last_seen"] == "2018-01-01 00:00:00"  # input untouched
    assert corrected.attrs["corrections_applied"] == 1
    assert unmatched["project_url"].tolist() == ["https://ghost.it"]


def test_yearly_counts(dated):
    yearly = analysis.yearly_counts(dated).set_index("year")
    # new: every first-seen year; unavailable: only the discontinued, non-migrated project
    assert yearly["new"].to_dict() == {2008: 1, 2010: 1, 2012: 1, 2018: 0}
    assert yearly["unavailable"].to_dict() == {2008: 0, 2010: 0, 2012: 0, 2018: 1}


def test_yearly_counts_excludes_current_year(projects):
    projects.loc[0, "url_first_seen"] = f"{analysis.CURRENT_YEAR}-01-01 00:00:00"
    yearly = analysis.yearly_counts(analysis.add_years(projects))
    assert analysis.CURRENT_YEAR not in yearly["year"].tolist()


def test_growth_table():
    yearly = pd.DataFrame({"year": [2004, 2005, 2006], "new": [4, 2, 0], "unavailable": [0, 0, 2]})
    t = analysis.growth_table(yearly)
    assert t["year"].tolist() == [analysis.GROWTH_BASELINE_YEAR, 2004, 2005, 2006]
    assert t["total_projects"].tolist() == [0, 4, 6, 4]
    assert pd.isna(t.loc[0, "normalized_growth_rate"])
    # arc growth 2005: (6-4)/5*100 = 40% -> * 6/100
    assert t.loc[2, "normalized_growth_rate"] == pytest.approx(2.4)
    assert t.loc[3, "normalized_growth_rate"] == pytest.approx(-1.6)  # (4-6)/5 = -40% -> * 4/100


def test_discontinued_and_lifespans(dated):
    assert analysis.discontinued(dated)["title"].tolist() == ["Ended"]
    life = analysis.lifespans(dated)
    assert life["lifespan_years_by_year"].tolist() == [10]
    assert life["lifespan_days"].tolist() == [3653]


@pytest.mark.parametrize("code, expected", [
    ("200", "2xx"), (301, "3xx"), ("404.0", "4xx"), ("503", "5xx"),
    ("NOSTATUSCODE", "none"), ("", "none"), (None, "none"), (float("nan"), "none"),
    ("NOTPROVIDED", "NOTPROVIDED"), ("999", "other:999"), ("abc", "other:abc"),
])
def test_macro_status(code, expected):
    assert analysis.macro_status(code) == expected


def test_status_discrepancies(projects):
    d = analysis.status_discrepancies(projects)
    assert len(d) == 1
    assert d.loc[0, "title"] == "Ended"
    assert d.loc[0, "discrepancy"].startswith("false_positive")

    projects.loc[0, "url_status_code"] = "404"
    d = analysis.status_discrepancies(projects)
    assert set(d["title"]) == {"Active", "Ended"}


def test_unavailable_projects(tmp_path, projects):
    path = tmp_path / "c.csv"
    path.write_text("title,project_url,correct_last_seen\nEnded,https://ended.it,2015-05-05 00:00:00\n")
    corrected, _ = analysis.apply_last_seen_corrections(projects, path)
    out = analysis.unavailable_projects(projects, analysis.add_years(corrected)).set_index("title")
    assert list(out.index) == ["Migrated", "Ended", "No URL"]
    assert out.loc["Migrated", "unavailability"] == "not functioning; not redirected"
    assert out.loc["Migrated", "migrated_to"] == "https://new.it"
    assert out.loc["Ended", "last_seen_corrected"] == True  # noqa: E712
    assert out.loc["Migrated", "last_seen_corrected"] == False  # noqa: E712
    assert out.loc["No URL", "last_seen_corrected"] == False  # noqa: E712
    assert out.loc["Ended", "lifespan_years"] == pytest.approx(7.34, abs=0.01)


def test_taxonomy(projects):
    t = analysis.taxonomy(projects)
    assert t["project_status"].tolist() == ["active", "migrated", "ended", "never_published"]
    assert t["accessibility"].fillna("").tolist() == ["fully_accessible", "inaccessible", "inaccessible", ""]
    assert set(t["data_preservation"]) == {"unknown"}


def test_taxonomy_partial_and_functioning_migrated(projects):
    projects.loc[0, "partially_unaccessible_website"] = True
    projects.loc[1, "functioning_website"] = True
    t = analysis.taxonomy(projects)
    assert t.loc[0, "accessibility"] == "partially_accessible"
    assert t.loc[1, ["project_status", "accessibility"]].tolist() == ["migrated", "fully_accessible"]

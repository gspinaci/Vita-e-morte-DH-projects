import pandas as pd

from dhlife import release
from dhlife.schema import RELEASE_COLUMNS, write_projects


def test_build_utf8(tmp_path, projects):
    projects.loc[0, "title"] = "Progetto śivadharma"
    src, out = tmp_path / "in.csv", tmp_path / "rel" / "release.csv"
    write_projects(projects, src)
    release.build(src, out)
    df = pd.read_csv(out, sep=";", dtype=str, encoding="utf-8")
    assert df.columns.tolist() == RELEASE_COLUMNS
    assert df.loc[0, "title"] == "Progetto śivadharma"
    assert df["functioning_website"].tolist() == ["TRUE", "FALSE", "FALSE", "FALSE"]


def test_build_cp1252_replaces_unencodable(tmp_path, projects):
    projects.loc[0, "title"] = "Piłsudski è"
    src, out = tmp_path / "in.csv", tmp_path / "release.csv"
    write_projects(projects, src)
    release.build(src, out, encoding="cp1252")
    df = pd.read_csv(out, sep=";", dtype=str, encoding="cp1252")
    assert df.loc[0, "title"] == "Pi?sudski è"


def test_main_names_file(tmp_path, projects, monkeypatch, capsys):
    src = tmp_path / "in.csv"
    write_projects(projects, src)
    monkeypatch.setattr(release.paths, "RELEASE", tmp_path / "release")
    monkeypatch.setattr(release.paths, "ROOT", tmp_path)
    release.main(["--version", "09", "--date", "20270101", "--input", str(src)])
    assert (tmp_path / "release" / "DH_Projects_Survey_20270101_v09.csv").exists()
    assert "4 rows" in capsys.readouterr().out

import pandas as pd
import pytest

from dhlife import sources
from dhlife.sources import Tab


@pytest.mark.parametrize("value, expected", [
    ("TRUE", "TRUE"), ("Sì", "TRUE"), (" si ", "TRUE"), ("yes", "TRUE"),
    ("false", "FALSE"), ("No", "FALSE"), ("forse", "forse"),
])
def test_to_bool(value, expected):
    assert sources.to_bool(value) == expected


def test_to_bool_keeps_missing():
    assert pd.isna(sources.to_bool(pd.NA))


def test_clean():
    tab = Tab("t", "t.csv", {"Nome": "name", "URL": "urls", "Attivo?": "active"},
              keys=["name", "urls"], booleans=["active"])
    raw = pd.DataFrame({
        "Nome\xa0": [" Centro A ", None, "  ", "Centro B"],
        "URL": ["http://a.it ;http://b.it", None, "", None],
        "Attivo?": ["Sì", None, None, "no"],
        "Ignored": ["x", "y", "z", "w"],
    })
    df = sources.clean(raw, tab)
    assert df.columns.tolist() == ["name", "urls", "active"]
    assert df["name"].tolist() == ["Centro A", "Centro B"]
    assert df.loc[0, "urls"] == "http://a.it; http://b.it"
    assert df["active"].tolist() == ["TRUE", "FALSE"]


def test_every_tab_has_unique_output():
    outputs = [t.output for t in sources.TABS]
    assert len(outputs) == len(set(outputs))
    for t in sources.TABS:
        assert set(t.keys) <= set(t.columns.values())
        assert set(t.booleans) <= set(t.columns.values())


def test_build_never_touches_curated_data(tmp_path, monkeypatch):
    """Curated files are edited by hand: rebuilding the sources must not overwrite them."""
    monkeypatch.setattr(sources.paths, "SOURCES", tmp_path / "sources")
    book = {t.sheet: pd.DataFrame({c: ["x"] for c in t.columns}) for t in sources.TABS}
    monkeypatch.setattr(sources.pd, "read_excel", lambda *a, **k: book)
    sources.build("snapshot.xlsx")
    written = sorted(p.name for p in (tmp_path / "sources").iterdir())
    assert written == sorted(t.output for t in sources.TABS)
    assert "dead_projects" not in {t.sheet for t in sources.TABS}


def test_clean_rewords_informal_notes():
    tab = Tab("t", "t.csv", {"Title": "title", "NOTE": "notes"}, keys=["title"])
    raw = pd.DataFrame({"Title": ["A", "B"], "NOTE": ["Coming soon LOL", "endpoint x. non si capisce un cazzo"]})
    assert sources.clean(raw, tab)["notes"].tolist() == ["Coming soon", "endpoint x. di difficile comprensione"]

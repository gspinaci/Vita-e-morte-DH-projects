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
    outputs = [(t.destination, t.output) for t in sources.TABS]
    assert len(outputs) == len(set(outputs))
    for t in sources.TABS:
        assert set(t.keys) <= set(t.columns.values())
        assert set(t.booleans) <= set(t.columns.values())

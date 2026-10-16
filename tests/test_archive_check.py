from datetime import datetime

import pytest

from dhlife import archive_check, wayback
from dhlife.schema import NO_STATUS_CODE, NOT_PROVIDED, read_projects, write_projects

PREV = {"first": "2010-01-01 00:00:00", "last": "2019-01-01 00:00:00",
        "status": "200", "snapshot": "https://web.archive.org/web/2019/x"}


@pytest.fixture
def fake_net(monkeypatch):
    """Configurable live status and Wayback answer; records the URLs checked."""
    state = {"status": 200, "info": (datetime(2011, 2, 3, 4, 5, 6), datetime(2024, 1, 1),
                                     "https://web.archive.org/web/20240101000000/x", wayback.OK),
             "checked": []}

    def live(url):
        state["checked"].append(url)
        return state["status"]

    monkeypatch.setattr(wayback, "check_live_status", live)
    monkeypatch.setattr(wayback, "get_wayback_info", lambda url: state["info"])
    monkeypatch.setattr(wayback, "RATE_LIMIT_DELAY", 0)
    return state


@pytest.mark.parametrize("url", [None, float("nan"), "", "   ", "not a url"])
def test_process_url_without_valid_url(fake_net, url):
    assert archive_check.process_url(url, PREV) == [NOT_PROVIDED, NOT_PROVIDED, NOT_PROVIDED, ""]
    assert fake_net["checked"] == []


def test_process_url_ok(fake_net):
    out = archive_check.process_url("  www.x.it ", {})
    assert out == ["2011-02-03 04:05:06", "2024-01-01 00:00:00", "200",
                   "https://web.archive.org/web/20240101000000/x"]
    assert fake_net["checked"] == ["http://www.x.it"]


def test_process_url_live_check_failed(fake_net):
    fake_net["status"] = None
    assert archive_check.process_url("https://x.it", PREV)[2] == NO_STATUS_CODE


def test_process_url_empty_wayback(fake_net):
    fake_net["info"] = (None, None, None, wayback.EMPTY)
    assert archive_check.process_url("https://x.it", PREV) == ["", "", "200", ""]


def test_process_url_fetch_failed_keeps_previous_dates(fake_net):
    fake_net["info"] = (None, None, None, wayback.FETCH_FAILED)
    fake_net["status"] = 404
    assert archive_check.process_url("https://x.it", PREV) == [PREV["first"], PREV["last"], "404", PREV["snapshot"]]


def test_process_url_fetch_failed_and_offline_keeps_previous_status(fake_net):
    fake_net["info"] = (None, None, None, wayback.FETCH_FAILED)
    fake_net["status"] = None
    assert archive_check.process_url("https://x.it", PREV) == list(PREV.values())
    assert archive_check.process_url("https://x.it", {}) == ["", "", NO_STATUS_CODE, ""]


def test_run_writes_archive_columns(tmp_path, fake_net, projects):
    src, out = tmp_path / "in.csv", tmp_path / "out" / "archive.csv"
    write_projects(projects, src)
    archive_check.run(src, out)
    df = read_projects(out)
    assert len(df) == 4
    assert df["url_first_seen"].tolist()[:3] == ["2011-02-03 04:05:06"] * 3
    assert df.loc[3, "url_first_seen"] == NOT_PROVIDED
    assert (df["showcase_url_first_seen"] == NOT_PROVIDED).all()
    assert df["functioning_website"].tolist() == [True, False, False, False]


def test_run_uses_previous_on_fetch_failure(tmp_path, fake_net, projects):
    src, prev = tmp_path / "in.csv", tmp_path / "prev.csv"
    write_projects(projects, src)
    write_projects(projects, prev)
    fake_net["info"] = (None, None, None, wayback.FETCH_FAILED)
    out = tmp_path / "out.csv"
    archive_check.run(src, out, prev)
    assert read_projects(out)["url_last_seen"].tolist() == projects["url_last_seen"].tolist()


def test_run_ignores_previous_with_other_rows(tmp_path, fake_net, projects):
    src, prev = tmp_path / "in.csv", tmp_path / "prev.csv"
    write_projects(projects, src)
    write_projects(projects.iloc[::-1].reset_index(drop=True), prev)
    fake_net["info"] = (None, None, None, wayback.FETCH_FAILED)
    out = tmp_path / "out.csv"
    archive_check.run(src, out, prev)
    assert read_projects(out)["url_last_seen"].iloc[:3].isna().all()

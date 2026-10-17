from datetime import datetime

import pytest
import requests

from dhlife import wayback
from dhlife.wayback import Snapshot


@pytest.mark.parametrize("url, valid", [
    ("https://example.org", True),
    ("http://example.org/a?b=1", True),
    ("www.example.org", True),
    ("example.org", False),
    ("ftp://example.org", False),
    ("https://exa mple.org", False),
    ("", False),
    (None, False),
])
def test_is_valid_url(url, valid):
    assert wayback.is_valid_url(url) is valid


@pytest.mark.parametrize("url, expected", [
    ("www.example.org", "http://www.example.org"),
    ("example.org", "http://example.org"),
    ("https://example.org", "https://example.org"),
])
def test_normalize_url(url, expected):
    assert wayback.normalize_url(url) == expected


def test_snapshot_properties():
    s = Snapshot("20200102030405", "http://x.it/", "200")
    assert s.datetime == datetime(2020, 1, 2, 3, 4, 5)
    assert s.link == "https://web.archive.org/web/20200102030405/http://x.it/"


def _with_snapshots(monkeypatch, snapshots):
    monkeypatch.setattr(wayback, "list_snapshots", lambda url: snapshots)


def test_wayback_info_drops_4xx_5xx_keeps_3xx(monkeypatch):
    _with_snapshots(monkeypatch, [
        Snapshot("20150101000000", "http://x.it", "404"),  # earliest, but an error page
        Snapshot("20160101000000", "http://x.it", "301"),
        Snapshot("20220101000000", "http://x.it", "200"),
        Snapshot("20240101000000", "http://x.it", "503"),  # latest, but an error page
        Snapshot("20250101000000", "http://x.it", "-"),    # revisit record
    ])
    first, last, link, outcome = wayback.get_wayback_info("http://x.it")
    assert outcome == wayback.OK
    assert first == datetime(2016, 1, 1)
    assert last == datetime(2022, 1, 1)
    assert link == "https://web.archive.org/web/20220101000000/http://x.it"


def test_wayback_info_sorts_by_timestamp(monkeypatch):
    _with_snapshots(monkeypatch, [
        Snapshot("20200101000000", "http://x.it", "200"),
        Snapshot("20100101000000", "http://x.it", "200"),
    ])
    first, last, _, _ = wayback.get_wayback_info("http://x.it")
    assert (first.year, last.year) == (2010, 2020)


def test_wayback_info_empty(monkeypatch):
    _with_snapshots(monkeypatch, [Snapshot("20200101000000", "http://x.it", "404")])
    assert wayback.get_wayback_info("http://x.it") == (None, None, None, wayback.EMPTY)
    _with_snapshots(monkeypatch, [])
    assert wayback.get_wayback_info("http://x.it")[3] == wayback.EMPTY


def test_wayback_info_fetch_failed(monkeypatch):
    _with_snapshots(monkeypatch, None)
    assert wayback.get_wayback_info("http://x.it") == (None, None, None, wayback.FETCH_FAILED)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


@pytest.fixture
def fake_session(monkeypatch):
    """Replace the HTTP session with a queue of responses; record calls and sleeps."""
    state = {"responses": [], "calls": [], "sleeps": []}

    def get(url, params=None, timeout=None):
        state["calls"].append((url, params))
        r = state["responses"].pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(wayback.SESSION, "get", get)
    monkeypatch.setattr(wayback.time, "sleep", state["sleeps"].append)
    return state


HEADER = ["timestamp", "original", "statuscode"]


def test_list_snapshots_query_and_header(fake_session):
    fake_session["responses"] = [FakeResponse(json_data=[HEADER, ["20200101000000", "http://x.it", "200"]])]
    snaps = wayback.list_snapshots("http://x.it")
    assert snaps == [Snapshot("20200101000000", "http://x.it", "200")]
    url, params = fake_session["calls"][0]
    assert url == wayback.CDX_API_URL
    assert params["matchType"] == "exact"
    assert "collapse" not in params and "filter" not in params


def test_list_snapshots_options(fake_session):
    fake_session["responses"] = [FakeResponse(json_data=[HEADER])]
    assert wayback.list_snapshots("http://x.it", only_200=True, limit=1, reverse=True) == []
    params = fake_session["calls"][0][1]
    assert params["filter"] == "statuscode:200"
    assert params["limit"] == "1"
    assert params["sort"] == "reverse"


def test_cdx_honours_retry_after(fake_session):
    fake_session["responses"] = [
        FakeResponse(429, headers={"Retry-After": "7"}),
        FakeResponse(429),
        FakeResponse(json_data=[HEADER]),
    ]
    assert wayback.list_snapshots("http://x.it") == []
    assert fake_session["sleeps"] == [7.0, wayback.BACKOFF_FACTOR ** 1]


def test_cdx_gives_up_after_max_retries(fake_session):
    fake_session["responses"] = [requests.ConnectionError("down")] * wayback.MAX_RETRIES
    assert wayback.list_snapshots("http://x.it") is None
    assert len(fake_session["calls"]) == wayback.MAX_RETRIES
    assert len(fake_session["sleeps"]) == wayback.MAX_RETRIES - 1


def test_cdx_invalid_json(fake_session):
    fake_session["responses"] = [FakeResponse(json_data=ValueError("not json"))]
    assert wayback.list_snapshots("http://x.it") is None


def test_check_live_status(fake_session):
    fake_session["responses"] = [FakeResponse(301), requests.Timeout("slow")]
    assert wayback.check_live_status("http://x.it") == 301
    assert wayback.check_live_status("http://x.it") is None


def test_user_agent_is_descriptive():
    assert wayback.SESSION.headers["User-Agent"] == wayback.USER_AGENT
    assert "research" in wayback.USER_AGENT

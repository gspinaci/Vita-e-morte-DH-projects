import csv

from dhlife.qualitative import analyze_surveys

FUNDING, INSTITUTION, ORPHANING, TECH = analyze_surveys.CAUSE_GROUPS


def _survey(path, idx, answers):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([f"Q{i}" for i in range(idx + 1)])
        for a in answers:
            w.writerow(["x"] * idx + [a])


def test_cause_shares_keeps_only_the_charted_causes(tmp_path, monkeypatch):
    monkeypatch.setattr(analyze_surveys, "ACTIVE_CSV", tmp_path / "active.csv")
    monkeypatch.setattr(analyze_surveys, "DISCONTINUED_CSV", tmp_path / "discontinued.csv")
    _survey(tmp_path / "active.csv", 19, [f"{TECH}, {ORPHANING}", f"{TECH}, Altro"])
    _survey(tmp_path / "discontinued.csv", 15, [f"{FUNDING}, {INSTITUTION}"])

    shares = analyze_surveys.cause_shares()
    assert shares["active"][0] == 2
    assert dict(shares["active"][1]) == {FUNDING: 0, INSTITUTION: 0, TECH: 2, ORPHANING: 1}
    assert dict(shares["discontinued"][1]) == {FUNDING: 1, INSTITUTION: 1, TECH: 0, ORPHANING: 0}

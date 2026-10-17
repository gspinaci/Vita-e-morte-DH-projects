import csv

from dhlife.qualitative import deanonymize


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)


def _read(path):
    return list(csv.reader(path.open(encoding="utf-8")))


def test_strips_timestamps_once(tmp_path, monkeypatch):
    monkeypatch.setattr(deanonymize, "DATA_DIR", tmp_path)
    monkeypatch.setattr(deanonymize, "AUDIT_DIR", tmp_path / ".audit")
    for name in ("survey_discontinued_projects.csv", "survey_active_projects.csv"):
        _write(tmp_path / name, [["Informazioni cronologiche", "A1", "A2"],
                                 ["2025/05/01 10:00", "si", "3"], ["2025/05/02 11:00", "no", "5"]])

    deanonymize.main()
    survey = tmp_path / "survey_active_projects.csv"
    audit = tmp_path / ".audit" / ".survey_active_projects.csv.timestamps"
    assert _read(survey) == [["A1", "A2"], ["si", "3"], ["no", "5"]]
    assert _read(audit)[1] == ["1", "2025/05/01 10:00"]

    deanonymize.main()  # second run: nothing may change
    assert _read(survey) == [["A1", "A2"], ["si", "3"], ["no", "5"]]
    assert _read(audit)[1] == ["1", "2025/05/01 10:00"]

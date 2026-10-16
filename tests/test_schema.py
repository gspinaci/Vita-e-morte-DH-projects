from dhlife import schema


def test_release_schema_is_stable():
    assert len(schema.CURATED_COLUMNS) == 16
    assert schema.ARCHIVE_COLUMNS == [
        "url_first_seen", "url_last_seen", "url_status_code", "last_url_snapshot",
        "showcase_url_first_seen", "showcase_url_last_seen", "showcase_url_status_code",
        "showcase_last_url_snapshot",
    ]
    assert schema.RELEASE_COLUMNS == schema.CURATED_COLUMNS + schema.ARCHIVE_COLUMNS
    assert set(schema.BOOLEAN_COLUMNS) <= set(schema.CURATED_COLUMNS)


def test_read_write_roundtrip(tmp_path, projects):
    path = tmp_path / "p.csv"
    schema.write_projects(projects, path)
    text = path.read_text()
    assert "TRUE" in text and "FALSE" in text and "True" not in text

    back = schema.read_projects(path)
    assert back["functioning_website"].tolist() == [True, False, False, False]
    assert back["not_redirected_website"].isna().tolist() == [True, False, True, True]
    assert back["url_status_code"].tolist() == ["200", "NOSTATUSCODE", "200", "NOTPROVIDED"]


def test_read_projects_accepts_lowercase_booleans(tmp_path):
    path = tmp_path / "p.csv"
    path.write_text("title,functioning_website\nA,true\nB,False\nC,\n")
    df = schema.read_projects(path)
    assert df["functioning_website"].iloc[:2].tolist() == [True, False]
    assert df["functioning_website"].isna().iloc[2]

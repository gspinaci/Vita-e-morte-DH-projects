from dhlife import stats


def test_reconciliation_adds_up(projects):
    r = dict(stats.reconciliation(projects))
    assert r["Projects"] == 4
    assert r["  without a project URL (website not found)"] == 1
    assert r["  with a project URL"] == 3
    assert r["    functioning"] == 1
    assert r["      migrated (alive at a new address)"] == 1
    assert r["      discontinued"] == 1
    assert r["  without a project URL (website not found)"] + r["  with a project URL"] == r["Projects"]
    assert (r["    functioning"] + r["    no longer reachable at the original URL"]
            == r["  with a project URL"])


def test_flag_counts(projects):
    counts = dict(stats.flag_counts(projects))
    assert counts["functioning_website"] == 1
    assert counts["non_functioning_website"] == 2
    assert counts["new_website_url set (migrated)"] == 1

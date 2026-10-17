from dhlife import stats


def test_reconciliation_adds_up(projects):
    r = dict(stats.reconciliation(projects))
    assert r["Projects"] == 4
    assert r["  never published (no project URL)"] == 1
    assert r["  with a project URL"] == 3
    assert r["    functioning"] == 1
    assert r["      migrated (active at a new address)"] == 1
    assert r["      ended (discontinued)"] == 1
    assert r["  never published (no project URL)"] + r["  with a project URL"] == r["Projects"]
    assert (r["    functioning"] + r["    inaccessible at the original URL"]
            == r["  with a project URL"])


def test_flag_counts(projects):
    counts = dict(stats.flag_counts(projects))
    assert counts["functioning_website"] == 1
    assert counts["non_functioning_website"] == 2
    assert counts["new_website_url set (migrated)"] == 1


def test_tree_draws_nesting():
    rows = [("All", 10), ("  a", 4), ("    a1", 4), ("  b", 6), ("    b1", 1), ("    b2", 5)]
    assert stats._tree(rows).splitlines()[1:-1] == [
        "All           10",
        "├── a          4",
        "│   └── a1     4",
        "└── b          6",
        "    ├── b1     1",
        "    └── b2     5",
    ]

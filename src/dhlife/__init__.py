"""Life and Death of DH Projects — data pipeline.

Stages (each is a module with a ``main()`` and is reachable via ``python -m dhlife <cmd>``):

    sources        frozen Google Sheet snapshot -> clean source CSVs  (data/sources/)
    crawl          crawl Italian DH centre websites for project links
    archive-check  Wayback CDX + live HTTP check                      (data/processed/)
    check-url      inspect the Wayback history of a single URL
    stats          paper numbers, lifespan, discrepancies             (reports/stats.md)
    charts         paper figures                                      (reports/figures/)
    release        build the Zenodo release CSV                       (data/release/)
"""

__version__ = "2026.1"

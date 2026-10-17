PYTHON ?= .venv/bin/python
DHLIFE  = $(PYTHON) -m dhlife

.PHONY: help install test sources crawl archive-check stats charts qualitative release analysis

help:
	@echo "make install         install pinned requirements (incl. the package)"
	@echo "make test            run the unit tests"
	@echo "make sources         rebuild data/sources/*.csv from the sheet snapshot"
	@echo "make crawl           crawl the DH centres for project links"
	@echo "make archive-check   Wayback + live check of every project (slow)"
	@echo "make stats charts    numbers and figures of the paper"
	@echo "make qualitative     survey syntheses"
	@echo "make release VERSION=04"
	@echo "extra options: make <target> ARGS='--input x.csv'"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest $(ARGS)

sources:
	$(DHLIFE) sources $(ARGS)

crawl:
	$(DHLIFE) crawl $(ARGS)

archive-check:
	$(DHLIFE) archive-check $(ARGS)

stats:
	$(DHLIFE) stats $(ARGS)

charts:
	$(DHLIFE) charts $(ARGS)

analysis: stats charts

qualitative:
	$(DHLIFE) qualitative $(ARGS)

release:
	@test -n "$(VERSION)" || (echo "usage: make release VERSION=04" && exit 1)
	$(DHLIFE) release --version $(VERSION) $(ARGS)

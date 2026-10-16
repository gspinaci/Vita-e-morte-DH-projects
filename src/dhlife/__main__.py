"""``python -m dhlife <command> [options]`` — run ``<command> --help`` for details."""

import importlib
import sys

COMMANDS = {
    "sources": "dhlife.sources",
    "crawl": "dhlife.crawl",
    "archive-check": "dhlife.archive_check",
    "check-url": "dhlife.check_url",
    "stats": "dhlife.stats",
    "charts": "dhlife.charts",
    "release": "dhlife.release",
    "qualitative": "dhlife.qualitative.analyze_surveys",
    "grobid-parse": "dhlife.proceedings.grobid_parse",
    "extract-urls": "dhlife.proceedings.extract_urls",
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Commands:\n  " + "\n  ".join(COMMANDS))
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    command = sys.argv[1]
    sys.argv[0] = f"dhlife {command}"  # so argparse usage shows the full command
    importlib.import_module(COMMANDS[command]).main(sys.argv[2:])


if __name__ == "__main__":
    main()

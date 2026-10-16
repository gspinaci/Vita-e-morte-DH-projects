"""Build the public release CSV (the file deposited on Zenodo).

    python -m dhlife release --version 04

Writes ``data/release/DH_Projects_Survey_<YYYYMMDD>_v<version>.csv``: curated and archive
columns in the public schema order, ``;``-separated (as all previous releases).
Use UTF-8 (default); ``--encoding cp1252`` matches the v03 file,
but replaces characters cp1252 cannot encode (e.g. "ś", "ł") with "?".
"""

import argparse
import datetime as dt

from dhlife import paths
from dhlife.schema import BOOLEAN_COLUMNS, RELEASE_COLUMNS, read_projects


def build(input_path, output_path, encoding="utf-8", sep=";"):
    df = read_projects(input_path)[RELEASE_COLUMNS]
    for col in BOOLEAN_COLUMNS:
        df[col] = df[col].map({True: "TRUE", False: "FALSE"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding=encoding, errors="replace", newline="") as f:
        df.to_csv(f, sep=sep, index=False)
    return df


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="release number, e.g. 04")
    parser.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"), help="YYYYMMDD (default: today)")
    parser.add_argument("--input", type=paths.Path, default=paths.PROJECTS_ARCHIVE)
    parser.add_argument("--encoding", default="utf-8")
    args = parser.parse_args(argv)
    output = paths.RELEASE / f"DH_Projects_Survey_{args.date}_v{args.version}.csv"
    df = build(args.input, output, encoding=args.encoding)
    print(f"Wrote {output.relative_to(paths.ROOT)} ({len(df)} rows, {args.encoding})")


if __name__ == "__main__":
    main()

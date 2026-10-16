"""Draw the paper figures into ``reports/figures/``.

    python -m dhlife charts
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from dhlife import analysis, paths  # noqa: E402

NEW_COLOR = "lightgrey"
UNAVAILABLE_COLOR = "orange"
TOTAL_COLOR = "#0371ad"
GROWTH_COLOR = "pink"


def _save(fig, name):
    path = paths.FIGURES / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path.relative_to(paths.ROOT)}")


def provenance(df):
    pct = df["provenance"].value_counts(normalize=True) * 100
    fig, ax = plt.subplots()
    pct.plot(kind="barh", ax=ax, color="darkgrey")
    ax.set_title("Percentage of Projects per Provenance")
    ax.set_xlabel("Percentage")
    ax.set_ylabel("Provenance")
    fig.tight_layout()
    for bar in ax.patches:
        ax.text(bar.get_width() - 1, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.1f}%",
                va="center", ha="right", color="white", fontsize=10)
    _save(fig, "provenance.png")


def new_vs_unavailable(yearly):
    fig, ax = plt.subplots()
    yearly.rename(columns={"new": "New", "unavailable": "Unavailable"}).plot(
        kind="bar", x="year", y=["New", "Unavailable"], ax=ax, color=[NEW_COLOR, UNAVAILABLE_COLOR])
    ax.set_title("New and Unavailable Projects per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Projects")
    plt.setp(ax.get_xticklabels(), rotation=45)
    fig.tight_layout()
    _save(fig, "new_vs_unavailable_per_year.png")


def cumulative_existing(yearly):
    t = yearly[yearly["year"] != analysis.CURRENT_YEAR].copy()
    t["existing"] = (t["new"] - t["unavailable"]).cumsum()
    fig, ax = plt.subplots()
    ax.plot(t["year"], t["existing"], label="Cumulative Existing Projects", color=NEW_COLOR)
    last = t.tail(3)
    ax.plot(last["year"], last["existing"], color=UNAVAILABLE_COLOR)
    ax.set_title("Existing Projects per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Projects")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_xticks(t["year"])
    ax.set_xticklabels(t["year"].astype(str), rotation=45)
    ax.legend()
    fig.tight_layout()
    _save(fig, "cumulative_existing.png")


def growth_and_cumulative(growth):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))
    x = np.arange(len(growth))
    labels = growth["year"].astype(str)
    width = 0.4

    # (A) new vs unavailable per year
    ax1.bar(x - width / 2, growth["new"], width=width, color=NEW_COLOR, label="New Projects")
    ax1.bar(x + width / 2, growth["unavailable"], width=width, color=UNAVAILABLE_COLOR, label="Unavailable Projects")
    ax1.set_ylabel("Number of Projects")
    ax1.set_xlabel("Year")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45)
    ax1.legend(loc="upper left")
    ax1.set_title("(A) Number of Projects per Year")
    for y in range(0, growth["new"].max() + 1, 5):
        ax1.axhline(y=y, color=NEW_COLOR, linestyle="--", linewidth=0.7)

    # (B) normalised growth rate + cumulative available projects
    ax3 = ax2.twinx()
    line_growth, = ax2.plot(x, growth["normalized_growth_rate"], color=GROWTH_COLOR, marker="o",
                            linewidth=2, label="Normalized Growth Rate", zorder=5)
    ax2.set_ylabel("Normalized Growth Rate")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.set_xlabel("Year")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45)
    line_total, = ax3.plot(x, growth["total_projects"], color=TOTAL_COLOR, marker="o", linewidth=2,
                           label="Cumulative Available Projects", zorder=5)
    ax3.set_ylabel("Cumulative Available Projects")
    for xi in x:
        ax2.axvline(x=xi, color=NEW_COLOR, linestyle="--", linewidth=0.7)
    ax3.legend([line_growth, line_total], [line_growth.get_label(), line_total.get_label()], loc="upper left")
    ax2.set_title("(B) Normalized Growth Rate and Cumulative Projects")
    fig.tight_layout()
    _save(fig, "growth_and_cumulative.png")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=paths.Path, default=paths.PROJECTS_ARCHIVE)
    args = parser.parse_args(argv)

    raw = analysis.load(args.input)
    corrected, _ = analysis.apply_last_seen_corrections(raw)
    yearly = analysis.yearly_counts(analysis.add_years(corrected))

    paths.FIGURES.mkdir(parents=True, exist_ok=True)
    provenance(raw)
    new_vs_unavailable(yearly)
    cumulative_existing(yearly)
    growth_and_cumulative(analysis.growth_table(yearly))


if __name__ == "__main__":
    main()

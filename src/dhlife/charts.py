"""Draw the paper figures into ``reports/figures/``: project growth and survey causes.

    python -m dhlife charts
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from dhlife import analysis, paths  # noqa: E402
from dhlife.qualitative import analyze_surveys  # noqa: E402

NEW_COLOR = "lightgrey"
UNAVAILABLE_COLOR = "orange"
TOTAL_COLOR = "#0371ad"
GROWTH_COLOR = "pink"
ACTIVE_COLOR = "#3565a8"
DISCONTINUED_COLOR = "#bf5b23"
GROUP_COLORS = {"Financial": "#7a3a10", "Institutional": "#5c4a1e", "Technological": "#1f3f6e"}


def _save(fig, name):
    path = paths.FIGURES / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path.relative_to(paths.ROOT)}")


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


def survey_causes(shares):
    """Causes anticipated by active projects vs. reported by discontinued ones, as the
    share of selections within each group (only the four causes of ``CAUSE_GROUPS``)."""
    causes = list(analyze_surveys.CAUSE_GROUPS)
    x = np.arange(len(causes))
    width = 0.37
    fig, ax = plt.subplots(figsize=(10, 5.8))
    for offset, (name, label, color) in zip(
            (-width / 2, width / 2),
            (("active", "Anticipated by active projects", ACTIVE_COLOR),
             ("discontinued", "Reported by discontinued projects", DISCONTINUED_COLOR))):
        respondents, counts = shares[name]
        total = sum(counts.values())
        values = [100 * counts[c] / total for c in causes]
        bars = ax.bar(x + offset, values, width=width, color=color, label=f"{label} (n = {respondents})")
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.8, f"{v:.1f}%",
                    ha="center", va="bottom", fontweight="bold", color="#333333")

    groups = [analyze_surveys.CAUSE_GROUPS[c][1] for c in causes]
    top = ax.get_ylim()[1] * 1.2
    ax.set_ylim(0, top)
    for g in dict.fromkeys(groups):
        idx = [i for i, gi in enumerate(groups) if gi == g]
        ax.text((idx[0] + idx[-1]) / 2, top * 0.96, g, ha="center", va="top",
                style="italic", color=GROUP_COLORS.get(g, "#333333"))
    for i in range(1, len(groups)):
        if groups[i] != groups[i - 1]:
            ax.axvline(i - 0.5, color="lightgrey", linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels([analyze_surveys.CAUSE_GROUPS[c][0] for c in causes])
    ax.set_ylabel("Share of selections within group (%)")
    ax.yaxis.grid(True, color="#eeeeee")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    ax.set_title("Relative emphasis on each cause of discontinuation (normalized)",
                 pad=34, color="#555555")
    fig.suptitle("The misalignment of risk:", fontsize=15, fontweight="bold")
    fig.tight_layout()
    _save(fig, "survey_causes_anticipated_vs_reported.png")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=paths.PROJECTS_ARCHIVE)
    args = parser.parse_args(argv)

    raw = analysis.load(args.input)
    corrected, _ = analysis.apply_last_seen_corrections(raw)
    yearly = analysis.yearly_counts(analysis.add_years(corrected))

    paths.FIGURES.mkdir(parents=True, exist_ok=True)
    growth_and_cumulative(analysis.growth_table(yearly))
    survey_causes(analyze_surveys.cause_shares())


if __name__ == "__main__":
    main()

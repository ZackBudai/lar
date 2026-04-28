from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "results.json"
FIGURES_DIR = ROOT / "figures"
ROOT_OUTPUT_DIR = ROOT


def load_rows() -> list[dict]:
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def add_value_labels(ax, values, *, fmt: str = "{:.3g}", offset: float = 0.0) -> None:
    for rect, value in zip(ax.patches, values):
        if value == 0:
            ax.text(rect.get_x() + rect.get_width() / 2, offset, "0", ha="center", va="bottom", fontsize=8)
            continue
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height() + offset,
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=8,
        )


def plot_runtime_comparison(rows: list[dict]) -> None:
    cases = [row["name"] for row in rows]
    baseline = [row["baseline"]["elapsed_sec"] for row in rows]
    improved = [row["improved"]["elapsed_sec"] for row in rows]

    x = np.arange(len(cases))
    width = 0.38

    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.bar(x - width / 2, baseline, width, label="Baseline", color="#8aa6c1")
    ax.bar(x + width / 2, improved, width, label="Improved", color="#d97b55")
    ax.set_yscale("log")
    ax.set_ylabel("Elapsed time (s, log scale)")
    ax.set_title("Per-case runtime comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(cases, rotation=35, ha="right")
    ax.grid(axis="y", which="both", linestyle="--", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "runtime_comparison.png", dpi=200, bbox_inches="tight")
    fig.savefig(ROOT_OUTPUT_DIR / "runtime_comparison.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_summary_metrics(rows: list[dict]) -> None:
    baseline_avg = sum(row["baseline"]["elapsed_sec"] for row in rows) / len(rows)
    improved_avg = sum(row["improved"]["elapsed_sec"] for row in rows) / len(rows)

    baseline_median = statistics.median(row["baseline"]["elapsed_sec"] for row in rows)
    improved_median = statistics.median(row["improved"]["elapsed_sec"] for row in rows)

    baseline_clauses = sum(row["baseline"]["clauses_generated"] for row in rows)
    improved_clauses = sum(row["improved"]["clauses_generated"] for row in rows)

    metrics = [
        ("Average time (s)", baseline_avg, improved_avg),
        ("Median time (s)", baseline_median, improved_median),
        ("Clauses generated", baseline_clauses, improved_clauses),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    colors = ["#8aa6c1", "#d97b55"]

    for ax, (title, base_value, imp_value) in zip(axes, metrics):
        bars = ax.bar([0, 1], [base_value, imp_value], color=colors, width=0.6)
        ax.set_title(title)
        ax.set_xticks([0, 1], ["Baseline", "Improved"])
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.bar_label(bars, labels=[f"{base_value:.3g}", f"{imp_value:.3g}"], padding=3, fontsize=8)

    axes[0].set_ylim(0, max(baseline_avg, improved_avg) * 1.35)
    axes[1].set_ylim(0, max(baseline_median, improved_median) * 1.8)
    axes[2].set_ylim(0, max(baseline_clauses, improved_clauses) * 1.2)

    fig.suptitle("Aggregate baseline vs improved metrics", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "summary_metrics.png", dpi=200, bbox_inches="tight")
    fig.savefig(ROOT_OUTPUT_DIR / "summary_metrics.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(exist_ok=True)
    rows = load_rows()
    plot_runtime_comparison(rows)
    plot_summary_metrics(rows)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Generate all figures for the TPTP FOF benchmark report."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "results" / "results_tptp_fof.json"
FIGURES_DIR = ROOT / "figures"

BLUE = "#5b8db8"
ORANGE = "#d97b55"
GREEN = "#5a9e6f"
RED = "#c94040"
GREY = "#aaaaaa"

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def load() -> list[dict]:
    return json.loads(RESULTS_PATH.read_text())


def domain(name: str) -> str:
    return name[:3].upper()


# ── Figure 1: Overall correctness ──────────────────────────────────────────
def fig_correctness(rows: list[dict]) -> None:
    n = len(rows)
    base_ok = sum(1 for r in rows if r["baseline_correct"])
    imp_ok  = sum(1 for r in rows if r["improved_correct"])

    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(["Baseline", "Improved"], [base_ok, imp_ok],
                  color=[BLUE, ORANGE], width=0.5)
    ax.set_ylim(0, n + 4)
    ax.axhline(n, color="#888", linestyle="--", linewidth=0.8, label=f"Total ({n})")
    ax.bar_label(bars, labels=[f"{base_ok}/{n}", f"{imp_ok}/{n}"],
                 padding=4, fontsize=11, fontweight="bold")
    ax.set_ylabel("Problems solved correctly")
    ax.set_title("Correctness: Baseline vs Improved")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_correctness.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_correctness.png")


# ── Figure 2: Per-domain correctness ──────────────────────────────────────
def fig_domain_correctness(rows: list[dict]) -> None:
    domains = ["SYN", "LCL", "PUZ"]
    totals = {d: sum(1 for r in rows if domain(r["name"]) == d) for d in domains}
    base   = {d: sum(1 for r in rows if domain(r["name"]) == d and r["baseline_correct"]) for d in domains}
    imp    = {d: sum(1 for r in rows if domain(r["name"]) == d and r["improved_correct"])  for d in domains}

    x = np.arange(len(domains))
    w = 0.32
    fig, ax = plt.subplots(figsize=(6, 4))
    b1 = ax.bar(x - w/2, [base[d] for d in domains], w, label="Baseline", color=BLUE)
    b2 = ax.bar(x + w/2, [imp[d]  for d in domains], w, label="Improved",  color=ORANGE)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d}\n(n={totals[d]})" for d in domains])
    ax.set_ylabel("Problems solved correctly")
    ax.set_title("Per-domain correctness")
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_domain_correctness.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_domain_correctness.png")


# ── Figure 3: Failure breakdown (stacked bar) ──────────────────────────────
def fig_failure_breakdown(rows: list[dict]) -> None:
    def breakdown(key: str) -> tuple[int, int, int]:
        correct  = sum(1 for r in rows if r[f"{key}_correct"])
        timeouts = sum(1 for r in rows if not r[f"{key}_correct"] and r[key]["timeout"])
        fast_f   = sum(1 for r in rows if not r[f"{key}_correct"] and not r[key]["timeout"])
        return correct, timeouts, fast_f

    bc, bt, bf = breakdown("baseline")
    ic, it_, if_ = breakdown("improved")

    labels = ["Baseline", "Improved"]
    corrects  = [bc, ic]
    timeouts  = [bt, it_]
    fast_fails = [bf, if_]

    fig, ax = plt.subplots(figsize=(5, 4))
    x = np.arange(2)
    p1 = ax.bar(x, corrects,   color=GREEN, label="Correct")
    p2 = ax.bar(x, timeouts,   bottom=corrects, color=RED,  label="Timeout")
    p3 = ax.bar(x, fast_fails, bottom=[c+t for c,t in zip(corrects, timeouts)],
                color=GREY, label="Fast-fail (incomplete)")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("Number of problems")
    ax.set_title("Outcome breakdown")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    # annotate counts inside bars
    for i, (c, t, f) in enumerate(zip(corrects, timeouts, fast_fails)):
        if c: ax.text(i, c/2, str(c), ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        if t: ax.text(i, c + t/2, str(t), ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        if f: ax.text(i, c + t + f/2, str(f), ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_failure_breakdown.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_failure_breakdown.png")


# ── Figure 4: Runtime scatter (per-problem, log scale) ─────────────────────
def fig_runtime_scatter(rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    colors_b = []
    colors_i = []
    for r in rows:
        colors_b.append(GREEN if r["baseline_correct"] else (RED if r["baseline"]["timeout"] else GREY))
        colors_i.append(GREEN if r["improved_correct"]  else (RED if r["improved"]["timeout"]  else GREY))

    base_t = [r["baseline"]["elapsed_sec"] for r in rows]
    imp_t  = [r["improved"]["elapsed_sec"] for r in rows]
    xs = np.arange(len(rows))

    ax.scatter(xs, base_t, c=colors_b, s=30, marker="o", label="Baseline", alpha=0.85, zorder=3)
    ax.scatter(xs, imp_t,  c=colors_i, s=30, marker="^", label="Improved",  alpha=0.85, zorder=3)
    ax.set_yscale("log")
    ax.set_ylabel("Elapsed time (s, log scale)")
    ax.set_xlabel("Problem index (sorted by name)")
    ax.set_title("Per-problem runtime (50 TPTP FOF problems)")
    ax.axhline(6, color="#888", linestyle="--", linewidth=0.7, label="Timeout (6 s)")
    ax.grid(axis="y", which="both", linestyle="--", alpha=0.2)

    # Legend: shape for algorithm, colour for outcome
    handles = [
        mpatches.Patch(color=GREEN, label="Correct"),
        mpatches.Patch(color=RED,   label="Timeout"),
        mpatches.Patch(color=GREY,  label="Fast-fail"),
        plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="#555", label="Baseline", markersize=7),
        plt.Line2D([0],[0], marker="^", color="w", markerfacecolor="#555", label="Improved",  markersize=7),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=8, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_runtime_scatter.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_runtime_scatter.png")


# ── Figure 5: Clauses generated comparison ────────────────────────────────
def fig_clauses(rows: list[dict]) -> None:
    domains = ["SYN", "LCL", "PUZ", "ALL"]
    base_cls, imp_cls = {}, {}
    for d in ["SYN", "LCL", "PUZ"]:
        subset = [r for r in rows if domain(r["name"]) == d]
        base_cls[d] = sum(r["baseline"]["clauses_generated"] for r in subset)
        imp_cls[d]  = sum(r["improved"]["clauses_generated"] for r in subset)
    base_cls["ALL"] = sum(r["baseline"]["clauses_generated"] for r in rows)
    imp_cls["ALL"]  = sum(r["improved"]["clauses_generated"] for r in rows)

    x = np.arange(len(domains))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    b1 = ax.bar(x - w/2, [base_cls[d] for d in domains], w, label="Baseline", color=BLUE)
    b2 = ax.bar(x + w/2, [imp_cls[d]  for d in domains], w, label="Improved",  color=ORANGE)
    ax.set_xticks(x); ax.set_xticklabels(domains)
    ax.set_ylabel("Total clauses generated")
    ax.set_title("Clauses generated by domain")
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}k"))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_clauses.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_clauses.png")


# ── Figure 6: Head-to-head runtime for correctly-solved problems ───────────
def fig_speedup(rows: list[dict]) -> None:
    """Log-log scatter of baseline vs improved time on problems each solved correctly."""
    # All problems where both had an outcome (any)
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for r in rows:
        bt = r["baseline"]["elapsed_sec"]
        it = r["improved"]["elapsed_sec"]
        if r["baseline_correct"] and r["improved_correct"]:
            c, m = GREEN, "o"
        elif r["improved_correct"]:
            c, m = ORANGE, "^"
        elif r["baseline_correct"]:
            c, m = BLUE, "s"
        else:
            c, m = GREY, "x"
        ax.scatter(bt, it, c=c, marker=m, s=30, alpha=0.8, zorder=3)

    lo, hi = 5e-5, 10
    ax.plot([lo, hi], [lo, hi], "k--", linewidth=0.7, label="Equal time")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel("Baseline time (s)")
    ax.set_ylabel("Improved time (s)")
    ax.set_title("Baseline vs Improved runtime (log–log)")
    handles = [
        mpatches.Patch(color=GREEN,  label="Both correct"),
        mpatches.Patch(color=ORANGE, label="Improved only"),
        mpatches.Patch(color=BLUE,   label="Baseline only"),
        mpatches.Patch(color=GREY,   label="Both wrong"),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=8)
    ax.grid(True, which="both", linestyle="--", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_speedup.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_speedup.png")


def main() -> None:
    FIGURES_DIR.mkdir(exist_ok=True)
    rows = load()
    print(f"Loaded {len(rows)} results. Generating figures...")
    fig_correctness(rows)
    fig_domain_correctness(rows)
    fig_failure_breakdown(rows)
    fig_runtime_scatter(rows)
    fig_clauses(rows)
    fig_speedup(rows)
    print("Done.")


if __name__ == "__main__":
    main()

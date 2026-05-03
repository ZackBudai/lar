#!/usr/bin/env python3
"""Generate all figures for the TPTP FOF benchmark report."""
from __future__ import annotations

import json
import re
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

    DARK_GREY = "#777777"
    fig, ax = plt.subplots(figsize=(5, 4.5))
    x = np.arange(2)
    ax.bar(x, corrects,   color=GREEN, label="Correct")
    ax.bar(x, timeouts,   bottom=corrects, color=RED,  label="Timeout")
    ax.bar(x, fast_fails, bottom=[c+t for c,t in zip(corrects, timeouts)],
           color=DARK_GREY, label="Fast-fail (incomplete)")
    n = len(rows)
    ax.set_ylim(0, n * 1.22)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Number of problems")
    ax.set_title("Outcome breakdown")
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    # annotate counts inside bars
    for i, (c, t, f) in enumerate(zip(corrects, timeouts, fast_fails)):
        if c: ax.text(i, c/2, str(c), ha="center", va="center", fontsize=10, color="white", fontweight="bold")
        if t: ax.text(i, c + t/2, str(t), ha="center", va="center", fontsize=10, color="white", fontweight="bold")
        if f: ax.text(i, c + t + f/2, str(f), ha="center", va="center", fontsize=10, color="white", fontweight="bold")
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

    # Two separate legends: outcome colour (left) and solver shape (right)
    outcome_handles = [
        mpatches.Patch(color=GREEN, label="Correct"),
        mpatches.Patch(color=RED,   label="Timeout"),
        mpatches.Patch(color=GREY,  label="Fast-fail"),
    ]
    solver_handles = [
        plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="#555", label="Baseline", markersize=8),
        plt.Line2D([0],[0], marker="^", color="w", markerfacecolor="#555", label="Improved",  markersize=8),
    ]
    leg1 = ax.legend(handles=outcome_handles, frameon=True, framealpha=0.85,
                     fontsize=8, loc="lower left", title="Outcome", title_fontsize=8)
    ax.add_artist(leg1)
    ax.legend(handles=solver_handles, frameon=True, framealpha=0.85,
              fontsize=8, loc="lower right", title="Solver", title_fontsize=8)
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


# ── Figure 7: Solve outcome vs TPTP difficulty rating ─────────────────────
def _load_ratings(rows: list[dict]) -> dict[str, float]:
    dataset_dir = ROOT / "datasets" / "tptp_fof"
    ratings = {}
    for r in rows:
        text = (dataset_dir / f"{r['name']}.p").read_text()
        m = re.search(r"%\s*Rating\s*:\s*([0-9.]+)", text)
        ratings[r["name"]] = float(m.group(1)) if m else 0.0
    return ratings


def fig_rating_outcome(rows: list[dict]) -> None:
    ratings = _load_ratings(rows)
    unique_ratings = sorted(set(ratings.values()))

    # Accumulate outcome counts per (rating, solver)
    from collections import defaultdict
    counts: dict = defaultdict(lambda: {"correct": 0, "timeout": 0, "fast_fail": 0})
    for r in rows:
        rat = ratings[r["name"]]
        for key, ck in [("baseline", "baseline_correct"), ("improved", "improved_correct")]:
            bucket = "correct" if r[ck] else ("timeout" if r[key]["timeout"] else "fast_fail")
            counts[(rat, key)][bucket] += 1

    n_groups = len(unique_ratings)
    x = np.arange(n_groups)
    w = 0.35

    fig, ax = plt.subplots(figsize=(9, 4.5))

    # Baseline = solid bars, Improved = hatched bars
    solver_styles = [
        ("baseline", -w / 2, "Baseline", ""),
        ("improved",  w / 2, "Improved", "///"),
    ]

    for i, (key, offset, label, hatch) in enumerate(solver_styles):
        c = [counts[(r, key)]["correct"]   for r in unique_ratings]
        t = [counts[(r, key)]["timeout"]   for r in unique_ratings]
        f = [counts[(r, key)]["fast_fail"] for r in unique_ratings]

        kw = dict(width=w, zorder=3, hatch=hatch, edgecolor="white" if not hatch else "#555555", linewidth=0.5)
        ax.bar(x + offset, c, color=GREEN,      **kw)
        ax.bar(x + offset, t, bottom=c, color=RED,        **kw)
        ax.bar(x + offset, f, bottom=[a+b for a,b in zip(c,t)], color="#777777", **kw)

        # Annotate each bar with counts (skip zeros and tiny bars)
        for j, (cv, tv, fv) in enumerate(zip(c, t, f)):
            xpos = x[j] + offset
            if cv: ax.text(xpos, cv / 2,           str(cv), ha="center", va="center", fontsize=7, color="white", fontweight="bold")
            if tv: ax.text(xpos, cv + tv / 2,      str(tv), ha="center", va="center", fontsize=7, color="white", fontweight="bold")
            if fv: ax.text(xpos, cv + tv + fv / 2, str(fv), ha="center", va="center", fontsize=7, color="white", fontweight="bold")

    # x-axis: show rating + total n
    n_at = {r: sum(1 for row in rows if ratings[row["name"]] == r) for r in unique_ratings}
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}\n(n={n_at[r]})" for r in unique_ratings], fontsize=9)
    ax.set_xlabel("TPTP difficulty rating")
    ax.set_ylabel("Number of problems")
    ax.set_title("Solve outcome vs TPTP difficulty rating")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    # Legend: colour = outcome, hatch = solver
    outcome_patches = [
        mpatches.Patch(color=GREEN,     label="Correct"),
        mpatches.Patch(color=RED,       label="Timeout"),
        mpatches.Patch(color="#777777", label="Fast-fail"),
    ]
    solver_patches = [
        mpatches.Patch(facecolor="#aaaaaa", edgecolor="#555555", hatch="",    label="Baseline (left)"),
        mpatches.Patch(facecolor="#aaaaaa", edgecolor="#555555", hatch="///", label="Improved (right)"),
    ]
    leg1 = ax.legend(handles=outcome_patches, frameon=True, framealpha=0.85,
                     fontsize=8, loc="upper right", title="Outcome", title_fontsize=8)
    ax.add_artist(leg1)
    ax.legend(handles=solver_patches, frameon=True, framealpha=0.85,
              fontsize=8, loc="center right", title="Solver", title_fontsize=8)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_rating_outcome.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  fig_rating_outcome.png")


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
    fig_rating_outcome(rows)
    print("Done.")


if __name__ == "__main__":
    main()

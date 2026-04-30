#!/usr/bin/env python3
"""
Generate comparison figures for benchmarks across different dataset sources.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"


def load_source_results(source: str) -> list[dict] | None:
    """Load benchmark results for a specific source."""
    results_file = RESULTS_DIR / f"results_{source}.json"
    if not results_file.exists():
        return None
    return json.loads(results_file.read_text(encoding="utf-8"))


def plot_source_comparison() -> None:
    """Compare baseline vs improved across dataset sources."""
    FIGURES_DIR.mkdir(exist_ok=True)
    
    sources = ["tptp_syn", "ai_generated"]
    source_data = {}
    
    for source in sources:
        results = load_source_results(source)
        if results is None:
            print(f"⚠️  No results found for {source}")
            continue
        
        baseline_time = sum(r["baseline"]["elapsed_sec"] for r in results)
        improved_time = sum(r["improved"]["elapsed_sec"] for r in results)
        baseline_clauses = sum(r["baseline"]["clauses_generated"] for r in results)
        improved_clauses = sum(r["improved"]["clauses_generated"] for r in results)
        
        source_data[source] = {
            "baseline_time": baseline_time,
            "improved_time": improved_time,
            "baseline_clauses": baseline_clauses,
            "improved_clauses": improved_clauses,
            "case_count": len(results),
        }
    
    if not source_data:
        print("✗ No valid results found")
        print("   Run 'python scripts/run_benchmarks.py' to generate benchmark results first")
        return
    
    print(f"📊 Generating comparison figures for {len(source_data)} source(s)...\n")
    
    # Plot 1: Total runtime comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(source_data))
    width = 0.35
    
    baseline_times = [source_data[s]["baseline_time"] for s in source_data.keys()]
    improved_times = [source_data[s]["improved_time"] for s in source_data.keys()]
    
    ax.bar(x - width/2, baseline_times, width, label="Baseline", color="#8aa6c1")
    ax.bar(x + width/2, improved_times, width, label="Improved", color="#d97b55")
    
    ax.set_ylabel("Total time (s)")
    ax.set_title("Total Runtime Comparison Across Dataset Sources")
    ax.set_xticks(x)
    ax.set_xticklabels([s.upper() for s in source_data.keys()])
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    
    for i, (b, im) in enumerate(zip(baseline_times, improved_times)):
        speedup = b / im if im > 0 else 0
        ax.text(i, max(b, im) * 1.05, f"{speedup:.2f}x", ha="center", fontsize=10, weight="bold")
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "source_runtime_comparison.png", dpi=200, bbox_inches="tight")
    print(f"✓ Saved: source_runtime_comparison.png")
    plt.close(fig)
    
    # Plot 2: Clauses generated comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    baseline_clauses = [source_data[s]["baseline_clauses"] for s in source_data.keys()]
    improved_clauses = [source_data[s]["improved_clauses"] for s in source_data.keys()]
    
    ax.bar(x - width/2, baseline_clauses, width, label="Baseline", color="#8aa6c1")
    ax.bar(x + width/2, improved_clauses, width, label="Improved", color="#d97b55")
    
    ax.set_ylabel("Clauses generated")
    ax.set_title("Clause Generation Comparison Across Dataset Sources")
    ax.set_xticks(x)
    ax.set_xticklabels([s.upper() for s in source_data.keys()])
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "source_clauses_comparison.png", dpi=200, bbox_inches="tight")
    print(f"✓ Saved: source_clauses_comparison.png")
    plt.close(fig)
    
    # Plot 3: Speedup by source
    speedups = []
    valid_sources = []
    
    for source in source_data.keys():
        improved_time = source_data[source]["improved_time"]
        if improved_time > 0:
            speedup = source_data[source]["baseline_time"] / improved_time
            speedups.append(speedup)
            valid_sources.append(source)
    
    if speedups:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#d97b55" if speedup > 1 else "#8aa6c1" for speedup in speedups]
        ax.bar(range(len(speedups)), speedups, color=colors)
        ax.axhline(y=1, color="black", linestyle="--", linewidth=1, alpha=0.5)
        
        ax.set_ylabel("Speedup ratio")
        ax.set_title("Improvement Speedup by Dataset Source")
        ax.set_xticks(range(len(speedups)))
        ax.set_xticklabels([s.upper() for s in valid_sources])
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        
        for i, speedup in enumerate(speedups):
            ax.text(i, speedup + 0.05, f"{speedup:.2f}x", ha="center", fontsize=10, weight="bold")
        
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "speedup_comparison.png", dpi=200, bbox_inches="tight")
        print(f"✓ Saved: speedup_comparison.png")
        plt.close(fig)
    else:
        print("⚠️  No valid speedup data to plot (all sources have zero improved time)")


def main() -> None:
    print("Generating comparison figures...\n")
    plot_source_comparison()
    print(f"\n✓ All figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Run benchmarks on multiple dataset sources (SYN TPTP and AI-generated).
Generates separate results and comparison figures for each.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lar.benchmark import run_benchmark, print_table


ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT / "datasets"
RESULTS_DIR = ROOT / "results"


def run_benchmarks_for_sources(
    timeout_sec: float = 6.0,
    sources: list[str] | None = None,
) -> dict[str, list[dict]]:
    """
    Run benchmarks on specified dataset sources.
    
    Args:
        timeout_sec: Timeout for each test case
        sources: List of source names ('tptp_syn', 'ai_generated'). If None, runs all available.
    
    Returns:
        Dictionary mapping source name to benchmark results
    """
    if sources is None:
        sources = ["tptp_syn", "ai_generated"]
    
    RESULTS_DIR.mkdir(exist_ok=True)
    all_results = {}
    
    for source in sources:
        dataset_path = DATASETS_DIR / source
        if not dataset_path.exists():
            print(f"⚠️  Dataset source '{source}' not found at {dataset_path}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Running benchmark for: {source.upper()}")
        print(f"Dataset path: {dataset_path}")
        print(f"{'='*60}\n")
        
        try:
            results = run_benchmark(dataset_path, timeout_sec)
            all_results[source] = results
            
            # Print table for this source
            print_table(results)
            
            # Save results to JSON
            results_file = RESULTS_DIR / f"results_{source}.json"
            results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
            print(f"\n✓ Results saved to: {results_file}")
            
        except Exception as e:
            print(f"✗ Error running benchmark for {source}: {e}")
            import traceback
            traceback.print_exc()
    
    return all_results


def summarize_results(all_results: dict[str, list[dict]]) -> None:
    """Print summary comparison across all sources."""
    print(f"\n{'='*60}")
    print("SUMMARY ACROSS ALL SOURCES")
    print(f"{'='*60}\n")
    
    for source, results in all_results.items():
        if not results:
            continue
        
        baseline_time = sum(r["baseline"]["elapsed_sec"] for r in results)
        improved_time = sum(r["improved"]["elapsed_sec"] for r in results)
        baseline_correct = sum(1 for r in results if r["baseline_correct"])
        improved_correct = sum(1 for r in results if r["improved_correct"])
        
        print(f"{source.upper()}:")
        print(f"  Cases: {len(results)}")
        print(f"  Total baseline time: {baseline_time:.4f}s")
        print(f"  Total improved time: {improved_time:.4f}s")
        print(f"  Speedup: {baseline_time/improved_time:.2f}x")
        print(f"  Baseline correct: {baseline_correct}/{len(results)}")
        print(f"  Improved correct: {improved_correct}/{len(results)}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run benchmarks on multiple dataset sources"
    )
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        default=None,
        help="Dataset sources to benchmark (default: all available)",
        choices=["tptp_syn", "ai_generated"],
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=6.0,
        help="Timeout per test case in seconds (default: 6.0)",
    )
    args = parser.parse_args()
    
    all_results = run_benchmarks_for_sources(timeout_sec=args.timeout, sources=args.sources)
    summarize_results(all_results)


if __name__ == "__main__":
    main()

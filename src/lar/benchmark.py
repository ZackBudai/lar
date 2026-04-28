from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_case_pipeline
from .tptp import parse_tptp_problem


def _run_jsonl_benchmark(dataset_path: Path, timeout_sec: float) -> list[dict]:
    rows: list[dict] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            case = json.loads(line)
            rows.append(run_case_pipeline(case, timeout_sec))
    return rows


def _load_tptp_cases(dataset_path: Path) -> list[dict]:
    files: list[Path]
    if dataset_path.is_dir():
        files = sorted(dataset_path.glob("*.p"))
    else:
        files = [dataset_path]

    cases: list[dict] = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        case = parse_tptp_problem(text, fallback_name=file_path.stem)
        cases.append(case)
    return cases


def run_benchmark(dataset_path: Path, timeout_sec: float) -> list[dict]:
    if dataset_path.suffix == ".jsonl":
        return _run_jsonl_benchmark(dataset_path, timeout_sec)

    cases = _load_tptp_cases(dataset_path)
    return [run_case_pipeline(case, timeout_sec) for case in cases]


def print_table(rows: list[dict]) -> None:
    headers = ["name", "exp", "base", "imp", "base_t", "imp_t", "base_ok", "imp_ok"]
    body = []
    for r in rows:
        body.append(
            [
                r["name"],
                str(r["expected"]),
                str(r["baseline"]["entailed"]),
                str(r["improved"]["entailed"]),
                f"{r['baseline']['elapsed_sec']:.4f}",
                f"{r['improved']['elapsed_sec']:.4f}",
                str(r["baseline_correct"]),
                str(r["improved_correct"]),
            ]
        )

    widths = [len(h) for h in headers]
    for row in body:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(row: list[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for row in body:
        print(fmt(row))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline vs improved FOL benchmark")
    parser.add_argument(
        "dataset",
        type=Path,
        help="Path to a TPTP .p file, a directory of .p files, or a legacy JSONL dataset",
    )
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--save", type=Path, default=None, help="Optional output JSON file")
    args = parser.parse_args()

    rows = run_benchmark(args.dataset, timeout_sec=args.timeout)
    print_table(rows)

    if args.save is not None:
        args.save.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

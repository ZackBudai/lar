from __future__ import annotations

from dataclasses import asdict

from .parser import parse_formula
from .solver import baseline_entails, improved_entails


def parse_stage(axiom_lines: list[str], query_line: str):
    axioms = []
    for line in axiom_lines:
        axioms.append(parse_formula(line))
    query = parse_formula(query_line)
    return axioms, query


def solve_stage(axioms, query, timeout_sec: float):
    baseline = baseline_entails(axioms, query, timeout_sec=timeout_sec)
    improved = improved_entails(axioms, query, timeout_sec=timeout_sec)
    return baseline, improved


def assemble_stage(name: str, expected: bool, baseline, improved) -> dict:
    row = {
        "name": name,
        "expected": expected,
        "baseline": asdict(baseline),
        "improved": asdict(improved),
        "baseline_correct": baseline.entailed == expected,
        "improved_correct": improved.entailed == expected,
    }
    return row


def run_case_pipeline(case: dict, timeout_sec: float) -> dict:
    axioms, query = parse_stage(case["axioms"], case["query"])
    baseline, improved = solve_stage(axioms, query, timeout_sec)
    return assemble_stage(case["name"], case["expected"], baseline, improved)

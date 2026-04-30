# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

3806ICT Assignment 1 — a first-order logic (FOL) theorem prover with baseline and improved algorithms, benchmarked against TPTP datasets.

## Setup

```bash
python -m pip install -e .
```

No test suite exists. Validation is done via benchmarks and the ad-hoc debug scripts in the repo root.

## Key Commands

**Run benchmark (primary way to validate):**
```bash
python -m lar.benchmark datasets/ai_generated --timeout 6 --save results.json
python -m lar.benchmark datasets/tptp_syn --timeout 6 --save results/results_tptp_syn.json
lar-benchmark datasets/ai_generated --timeout 6
```

**Generate figures:**
```bash
python scripts/generate_benchmark_figures.py
python scripts/generate_comparison_figures.py
```

**Debug scripts (root-level, not installed):**
```bash
python debug_resolve.py
python trace_resolution.py
python test_resolve_pair.py
```

## Architecture

The pipeline flows: TPTP file → `tptp.py` → raw `dict` → `pipeline.py` → `solver.py` → `SolveResult`

### Core modules (`src/lar/`)

- **`logic.py`** — frozen dataclasses: `Term`, `Atom`, `Formula`, `Literal`. `Clause = frozenset[Literal]`. Variables are lowercase names with no args; constants/predicates are lowercase but prefixed `C_` when parsed from TPTP.
- **`parser.py`** — tokenizer + recursive-descent parser for the internal formula syntax (`forall X.`, `~`, `&`, `|`, `->`, `<->`).
- **`tptp.py`** — separate TPTP syntax parser (`!`, `?`, `=>`, `<=>`) that maps TPTP uppercase vars to internal lowercase vars and prefixes constants with `C_`. Produces a `dict` with `axioms: list[Formula]`, `query: Formula`, `expected: bool`.
- **`cnf.py`** — implication elimination, negation normal form, Skolemization, variable standardization, CNF distribution, tautology check.
- **`unify.py`** — first-order unification with occurs-check (`unify_atoms`).
- **`solver.py`** — two entailment strategies both returning `SolveResult`:
  - `baseline_entails()` → `algorithm_2_entails()`: backward LK sequent calculus proof search with memoization.
  - `improved_entails()` → `optimized_algorithm_2_entails()`: Horn-clause backward chaining with predicate indexing and memoization; falls back to baseline for non-Horn or failed proofs.
- **`pipeline.py`** — thin glue: parse → solve both strategies → assemble result dict.
- **`benchmark.py`** — CLI entry point (`lar-benchmark`); loads `.p` files or directories, calls pipeline, prints table, optionally saves JSON.

### Key design decisions

- TPTP uppercase variables are mapped to lowercase internally; TPTP constants get `C_` prefix to avoid colliding with internal variables (`is_var` checks `name[0].islower()`).
- The improved solver tries Horn backward-chaining first; if any axiom clause has ≠1 positive literal it immediately falls back to the baseline sequent search.
- `SolveResult` is a dataclass serialized via `asdict()` into benchmark JSON output.

## Datasets

- `datasets/ai_generated/` — 11 hand-crafted FOL problems in TPTP format.
- `datasets/tptp_syn/` — subset of TPTP SYN problems (syntactic benchmark cases).
- Expected outcome is derived from the `% Status : <X>` comment in each `.p` file.

# 3806ICT Assignment 1 - Coding Component

This repository implements the coding component for Assignment 1:

- first-order logic parser (one formula per line)
- baseline prover based on first-order resolution
- improved prover with practical performance optimizations
- benchmark runner and dataset format

## Implemented Components

1. Parser

- File: src/lar/parser.py
- Supports:
  - quantifiers: forall, exists
  - negation: ~
  - conjunction/disjunction: &, |
  - implication/biconditional: ->, <->
  - predicates, functions, constants, variables

1. Baseline Algorithm

- File: src/lar/solver.py
- Entry point: baseline_entails
- Method:
  - convert axioms plus negated query to CNF clauses
  - use naive pairwise resolution until empty clause, saturation, or timeout

1. Improved Algorithm

- File: src/lar/solver.py
- Entry point: improved_entails
- Improvements over baseline:
  - set-of-support strategy
  - unit preference (process shorter clauses first)
  - simple predicate indexing to reduce pair checks
  - tautology filtering and basic subsumption checks

1. CNF and Unification Pipeline

- Files: src/lar/cnf.py, src/lar/unify.py
- Includes:
  - implication elimination
  - negation normal form
  - variable standardization
  - skolemization
  - CNF distribution and clause extraction
  - first-order unification with occurs-check

1. Benchmarking

- File: src/lar/benchmark.py
- Input dataset format: JSONL (one case per line)
- Output: per-case correctness and timing for baseline vs improved

## Project Structure

- src/lar/logic.py: logic data structures (terms, atoms, formulae, literals)
- src/lar/parser.py: parser and tokenizer
- src/lar/cnf.py: CNF conversion and clause utilities
- src/lar/unify.py: unification
- src/lar/solver.py: baseline and improved provers
- src/lar/benchmark.py: benchmark runner
- datasets/benchmark.jsonl: benchmark cases

## Usage

### 1. Install package in editable mode

python -m pip install -e .

### 2. Run benchmark

python -m lar.benchmark datasets/benchmark.jsonl --timeout 6 --save results.json

or via console script:

lar-benchmark datasets/benchmark.jsonl --timeout 6 --save results.json

### 3. Dataset format

Each line in JSONL:

```json
{
  "name": "case_name",
  "axioms": ["forall x. (P(x) -> Q(x))", "P(A)"],
  "query": "Q(A)",
  "expected": true
}
```

## Notes

- Variables should use lowercase names (for example x, y, z)
- Constants are recommended to start with uppercase letters (for example A, Socrates) to avoid ambiguity
- This implementation is a teaching-oriented prover suitable for assignment experiments and comparison, not a full industrial theorem prover

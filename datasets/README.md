# Benchmark Datasets

This folder contains benchmark instances for first-order entailment tests.

- File: benchmark.jsonl
- Format: one JSON object per line
- Fields:
  - name: unique case identifier
  - axioms: list of first-order logic formula strings
  - query: formula to test as logical consequence
  - expected: true if axioms entail query, else false

Notes:

- Variables should use lowercase names (for example x, y, z).
- Constants, function symbols, and predicate symbols should start with uppercase/lowercase as desired, but constants are recommended to be capitalized (for example A, Socrates) to avoid ambiguity.
- Cases here are course-style synthetic benchmarks generated for assignment experimentation.

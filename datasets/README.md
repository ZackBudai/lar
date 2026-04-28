# Benchmark Datasets

This folder contains benchmark instances for first-order entailment tests.

- Primary sample set: `tptp/`
- Format: one TPTP problem per `.p` file
- Statement form: `fof(name, role, formula).`
- Required role: exactly one `conjecture` per problem
- Axioms: any `axiom`/`hypothesis`/`lemma`/`theorem`/`plain` entries
- Expected result source: `% Status : ...` comment in each file

Notes:

- Variables use TPTP uppercase style (for example `X`, `Y`, `Z`).
- Constants, function symbols, and predicate symbols use lowercase style (for example `a`, `f`, `human`).
- Cases here are course-style synthetic benchmarks written in TPTP syntax.

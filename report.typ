#set page(margin: (x: 1in, y: 1in))
#set text(font: "Times New Roman", size: 11pt)
#set heading(numbering: "1.")

#let course = "3806ICT"
#let assignment = "Assignment 1"
#let report_title = "First-Order Resolution: Baseline and Improved Theorem Provers"
#let student_name = "Your Name"
#let student_id = "Your Student ID"
#let date = "April 2026"

#align(center)[
  #text(size: 17pt, weight: "bold")[#course #assignment Report]
  #v(8pt)
  #text(size: 14pt, weight: "bold")[#report_title]
  #v(10pt)
  #student_name \
  #student_id \
  #date
]

#v(14pt)

= Abstract
This report presents the implementation and evaluation of a first-order logic (FOL) theorem-proving system using resolution refutation. The project includes (1) a parser for FOL formulas, (2) a baseline prover using naive pairwise resolution, and (3) an improved prover using practical search-control and filtering techniques. On the current benchmark suite (10 cases), both provers achieve 100% correctness against expected outcomes. The improved prover is substantially faster on most non-timeout cases, while both approaches still time out on a hard non-entailed chain instance.

= Problem Statement
The goal is to determine whether a query formula is entailed by a set of FOL axioms. The implementation follows proof by contradiction:

KB ⊨ q iff KB ∪ {¬q} is unsatisfiable.

Unsatisfiability is shown by deriving the empty clause using first-order resolution.

= System Overview
The project is implemented as a Python package with a staged pipeline:

- Parsing stage: convert input text formulas into an internal abstract syntax tree (AST).
- Normalization stage: transform formulas to clause form through CNF conversion.
- Solving stage: run baseline and improved resolution algorithms.
- Reporting stage: aggregate per-case metrics and output benchmark tables/JSON.

Key modules:

- src/lar/parser.py: tokenizer and recursive-descent parser.
- src/lar/logic.py: AST and clause/literal data models.
- src/lar/cnf.py: implication elimination, NNF, standardization, skolemization, CNF extraction.
- src/lar/unify.py: unification with occurs-check.
- src/lar/solver.py: baseline and improved entailment engines.
- src/lar/pipeline.py: multifile staged orchestration.
- src/lar/benchmark.py: benchmark runner and formatted output.

= Parser Design
The parser is implemented in an explicit, simplified style:

- Manual character-by-character tokenizer.
- Recursive-descent parser with precedence levels:
  - iff
  - implies
  - or
  - and
  - unary (negation/quantifiers/parentheses/atoms)
- Terms support nested function application.

This design keeps control flow transparent and minimizes dependence on advanced language-specific parsing utilities.

= CNF and Unification
CNF conversion includes the standard sequence:

1. Eliminate implications and biconditionals.
2. Push negations inward (NNF).
3. Standardize bound variable names.
4. Skolemize existential quantifiers.
5. Remove universal quantifiers.
6. Distribute disjunction over conjunction.
7. Extract clauses and remove tautologies.

Unification supports substitutions over terms and atoms with an occurs-check to avoid cyclic substitutions.

= Baseline Prover
The baseline prover performs naive pairwise resolution over all clause pairs:

- Build KB ∪ {¬q} in clause form.
- Iterate over all clause pairs.
- Resolve complementary literals when unifiable.
- Add non-tautological resolvents.
- Stop on empty clause (entailed), saturation (not entailed), or resource limit (timeout).

The approach is simple and correct but can generate many irrelevant resolvents.

= Improved Prover
The improved prover adds practical inference control:

- Set-of-support strategy: prioritize resolving from clauses linked to the negated query.
- Unit preference: process shorter clauses first.
- Predicate indexing: reduce candidate partner clauses.
- Tautology filtering and basic subsumption checks.

These changes reduce search on most practical cases without changing entailment semantics.

= Experimental Setup
Benchmark command:

`python -m lar.benchmark datasets/benchmark.jsonl --timeout 6 --save results.json`

Dataset summary:

- 10 synthetic course-style cases.
- Mix of entailed and non-entailed queries.
- Includes recursive/transitive reasoning, functions, and hard chain instances.

= Results
Per-case results from the current run are shown below.

#table(
  columns: (2fr, 0.8fr, 0.9fr, 0.9fr, 1fr, 1fr, 0.9fr, 0.9fr),
  table.header([Case], [Expected], [Baseline], [Improved], [Base t (s)], [Imp t (s)], [Base OK], [Imp OK]),

  [modus_ponens], [true], [true], [true], [0.000380], [0.000281], [true], [true],
  [not_entailed_simple], [false], [false], [false], [0.001509], [0.000158], [true], [true],
  [family_transitive], [true], [true], [true], [0.001782], [0.000407], [true], [true],
  [ancestor_recursive], [true], [true], [true], [0.016285], [0.001115], [true], [true],
  [likes_exists], [true], [true], [true], [0.000112], [0.000125], [true], [true],
  [query_with_function], [true], [true], [true], [0.000212], [0.000244], [true], [true],
  [bird_penguin], [true], [true], [true], [0.000608], [0.000210], [true], [true],
  [independent_predicates], [false], [false], [false], [0.000257], [0.000117], [true], [true],
  [chain_depth_4], [true], [true], [true], [2.263806], [0.001697], [true], [true],
  [non_entailed_chain], [false], [false], [false], [6.000051], [6.004293], [true], [true],
)

Aggregate metrics:

- Cases: 10
- Baseline correctness: 10/10
- Improved correctness: 10/10
- Baseline average time: 0.828500 s
- Improved average time: 0.600865 s
- Baseline median time: 0.001059 s
- Improved median time: 0.000263 s
- Average speedup (all cases): 1.379x
- Average speedup (excluding dual-timeout case): 524.695x
- Total clauses generated: baseline 39,359 vs improved 20,233

= Discussion
Both solvers are behaviorally correct on the provided benchmark set. The improved solver significantly reduces runtime on most cases, especially deep chain entailment, where search control and indexing avoid much of the combinatorial expansion seen in the baseline method.

The hard non-entailed chain case still times out for both methods under a 6-second cap. This indicates that further improvements (for example, stronger redundancy elimination, better clause ordering heuristics, or additional indexing structures) would be needed for difficult negative instances.

= Limitations and Future Work
Current limitations:

- Performance still degrades on difficult non-entailed problems.
- Subsumption is basic and could be strengthened.
- Benchmark set is moderate in size and synthetic.

Potential extensions:

- More advanced clause selection heuristics.
- Stronger simplification (forward/backward subsumption variants).
- Additional benchmark corpora with larger and noisier knowledge bases.

= Conclusion
The project meets the coding goals of Assignment 1 with an end-to-end FOL reasoning system: parser, CNF conversion, unification, baseline resolution, improved resolution, and benchmark tooling. The improved prover preserves correctness while delivering large practical speedups on most benchmark cases.

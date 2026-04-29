#set page(margin: (x: 1in, y: 1in))
#set text(size: 11pt)
#set heading(numbering: "1.")

#align(center)[
	#text(size: 17pt, weight: "bold")[3806ICT Assignment 1 Report]
	#v(8pt)
	#text(size: 14pt, weight: "bold")[First-Order Resolution: Baseline and Improved Theorem Provers]
	#v(8pt)
	#text(size: 11pt)[Zack Budai]
	#v(2pt)
	#text(size: 11pt)[s5307993]
	#v(2pt)
	#text(size: 10pt)[Griffith University]
	#v(2pt)
	#text(size: 10pt)[zack.budai2\@griffithuni.edu.au]
	#v(6pt)
	#text(size: 10pt)[April 2026]
]

#v(12pt)


#text(size: 11pt, weight: "bold")[Abstract.] This report describes the design, implementation, and evaluation of a first-order logic theorem prover built around resolution refutation. The prover addresses entailment by proof by contradiction: a query is entailed when the axioms combined with the negated query are unsatisfiable. The system contains a hand-written tokenizer and recursive-descent parser, a full CNF conversion pipeline, unification with occurs-check, and two solvers (baseline and improved). The baseline performs broad pairwise search, while the improved solver applies set-of-support, unit preference, predicate indexing, tautology filtering, and subsumption checks. Evaluation in this report uses newly collected official TPTP problems and then runs benchmarks on the parser-compatible subset. On this subset, the baseline returns the expected outcome in all three cases (3/3), while the improved solver returns zero correct outcomes (0/3) because all three runs time out before deriving entailment. Runtime and clause-generation metrics show the improved solver explores far fewer clauses (55 vs 883,722) and returns quickly, but with incorrect entailment outcomes for these cases. These results indicate that the current optimized strategy needs refinement for this class of official puzzle problems, and that correctness validation must remain the primary criterion when tuning search control.

#v(6pt)

#text(size: 11pt, weight: "bold")[Keywords:] first-order logic, resolution, CNF, unification, theorem proving

#pagebreak()
= Introduction
The goal of this assignment is to determine whether a query formula is entailed by a set of first-order logic axioms. The implementation follows proof by contradiction: a query is entailed if and only if the axioms together with the negated query are unsatisfiable. Unsatisfiability is demonstrated by deriving the empty clause using resolution.

The report is organized in the same style as the provided template: a concise abstract and keywords block, followed by numbered sections that explain the problem, the system design, the inference procedures, the experimental setup, and the benchmark results. The resulting software is a small but complete reasoning pipeline that can parse formulas, transform them into clause form, and search for a refutation.

= Architecture and Workflow
The project is implemented as a Python package with a staged pipeline.

- Parsing stage: convert input formulas into an internal abstract syntax tree.
- Normalization stage: transform formulas into clause form with CNF conversion.
- Solving stage: run the baseline and improved resolution procedures.
- Reporting stage: collect benchmark metrics and produce results for analysis.

#figure(
	image("figures/architecture.png", width: 80%),
	caption: [Architecture and workflow of the theorem prover: TPTP input flows through parser and CNF normalization to both baseline and improved solvers, then to results.],
)

The figure above summarizes the full workflow used in the implementation and the experiments.

The main modules are:

- `src/lar/parser.py`: tokenizer and recursive-descent parser.
- `src/lar/logic.py`: AST and clause/literal data models.
- `src/lar/cnf.py`: implication elimination, negation normal form, standardization, skolemization, and CNF extraction.
- `src/lar/unify.py`: unification with occurs-check.
- `src/lar/solver.py`: baseline and improved entailment engines.
- `src/lar/pipeline.py`: multi-file orchestration.
- `src/lar/benchmark.py`: benchmark runner and formatted output.

= Parsing and Logic Representation
The parser implements a two-stage translation from raw text to an abstract syntax tree. The first stage, the tokenizer, walks the input character-by-character to extract atomic tokens: operator symbols like `<->` (biconditional) and `->` (implication), punctuation such as parentheses and commas, and identifiers for predicates, functions, and variables. This manual approach is deliberate—it makes token recognition explicit and easy to verify, avoiding the pitfalls of naive regex patterns that can hide edge cases. Once tokenization is complete, the parser constructs a recursive-descent parser that respects a strict precedence hierarchy: biconditionals (`<->`) bind weakest, followed by implications (`->`), then disjunctions (`|`), conjunctions (`&`), and finally unary negation (`~`). This precedence ordering ensures that formulas like `a | b & c` parse as `a | (b & c)` rather than `(a | b) & c`, matching the standard convention in logic. The recursive descent strategy processes each precedence level in its own function, so higher-precedence operators are parsed deeper in the recursion tree. Terms—which represent function applications and variable bindings—are parsed as deeply nested structures, allowing the system to handle formulas with functions at any depth, such as `parent(father(X), Y)`. The internal representation deliberately separates formulas, predicates, functions, variables, and clauses into distinct data models rather than flattening them into a single representation. This separation makes each component's contract clear and allows the solver to reason over a uniform normalized structure after CNF conversion. The separation also aids testability: each parsing phase can be validated independently, and each pipeline stage can be tested in isolation knowing that its input adheres to a specific schema. This explicit design keeps code locality high and makes it easier to debug unexpected behavior.

= CNF Conversion and Unification
Conversion to Conjunctive Normal Form (CNF) is a prerequisite for the resolution method used by both the baseline and improved provers. The pipeline applies a sequence of logically sound transformations, each of which preserves equisatisfiability. The first step eliminates implications and biconditionals by rewriting `a -> b` as `~a | b` and `a <-> b` as `(~a | b) & (~b | a)`. This normalization reduces the formula to conjunctions, disjunctions, and negations. The second step applies De Morgan's laws and double-negation elimination to push negations as far inward as possible, moving them until they directly precede atomic predicates. This transformation, called negation normal form (NNF), simplifies later processing because quantifiers and logical operators no longer need to handle negation in context. The third step standardizes variable names: since formulas in the knowledge base may reuse variable names, quantified variables are systematically renamed to unique identifiers (e.g., first `forall X` becomes `forall X_1`, second becomes `forall X_2`). This prevents accidental variable capture when formulas are combined during resolution. The fourth step, Skolemization, eliminates existential quantifiers by replacing them with specially constructed function terms called Skolem functions. For example, `exists Y. parent(X, Y)` becomes `parent(X, skolem_1(X))`, where the function depends on the universally quantified variables in scope. Skolemization preserves satisfiability—if a model existed with an existential witness, the Skolem function embodied in the transformed formula produces the same witness. The fifth step removes universal quantifiers entirely, since remaining quantifiers are vacuous in the clause form: clauses are implicitly universally quantified. The sixth step distributes disjunction over conjunction, transforming nested connectives into a form where every clause (a disjunction) is a child of a top-level conjunction. The seventh step extracts the clauses themselves as a flat set and removes tautologies—clauses containing both a literal and its negation—which contribute nothing to the search. After CNF conversion, formulas are represented as a set of clauses, each of which is a set of literals. Resolution then operates on this uniform structure.

= Baseline Prover
The baseline prover performs naive pairwise resolution over all clause pairs.

- Build the clause set from the knowledge base plus the negated query.
- Iterate over all clause pairs.
- Resolve complementary literals when they are unifiable.
- Add non-tautological resolvents to the clause set.
- Stop when the empty clause is derived, when saturation is reached, or when the timeout limit is exceeded.

This algorithm is simple and correct, but it explores a large search space. Many generated resolvents are irrelevant to the final proof, especially on recursive or chain-heavy benchmarks.

A more detailed view of the baseline search makes the bottleneck clear. In the first stage, every clause is treated as a potential partner for every other clause, so the search space grows roughly with the square of the number of clauses already known. In the second stage, unification is attempted for every complementary literal pair, even when the predicates are unrelated to the query. In the third stage, resolvents are appended immediately, which means the prover can spend time expanding clauses that do not move the search toward the empty clause. This design is useful as a reference implementation because it is easy to reason about, but it is intentionally not optimized for difficult proofs.

= Improved Prover
The improved prover keeps the same logical semantics but adds practical search control.

- Set-of-support: prioritize clauses connected to the negated query.
- Unit preference: expand shorter clauses first.
- Predicate indexing: reduce the number of candidate partner clauses.
- Tautology filtering: discard clauses that are immediately redundant.
- Basic subsumption checks: avoid keeping clauses that are clearly weaker than others already known.

These heuristics reduce the number of intermediate clauses and help the search remain focused on clauses that are more likely to lead to a refutation. The benefit is most visible on the deeper chain benchmark, where the baseline solver explores many more clauses before reaching the contradiction.

A practical way to understand the improved prover is to look at the order of work it performs. It begins by seeding the search with the negated conjecture and the clauses that can directly interact with it. It then prefers short clauses, which often correspond to facts or near-facts, so contradictions can surface early. Once a useful clause has been produced, predicate indexing narrows the next resolution choices to clauses that share the same predicate symbol. That simple filtering step eliminates many dead-end pairings before any expensive unification is attempted. Finally, tautology checks and subsumption avoid storing clauses that are obviously redundant, which keeps the active clause set smaller across the whole run.

The improved solver is still expected to reduce branching for many problems due to set-of-support, unit preference, and indexing. However, as the updated benchmark results show, reducing branching alone is not sufficient: the search control must still preserve enough coverage to find refutations on harder official puzzle instances. The current implementation therefore demonstrates a speed-versus-completeness tradeoff on this dataset.

= Datasets and Justification
The evaluation uses newly collected official TPTP problems in `datasets/tptp/` and an automatically filtered parser-compatible subset in `datasets/tptp_compatible/`.

- Problems were downloaded from official TPTP endpoints and kept in FOF form without `include(...)` directives.
- Many official files use constructs not currently supported by this parser (notably equality and some additional syntax), so a compatibility filter was applied before benchmarking.
- The resulting benchmark set contains three compatible PUZ problems, each with one conjecture and expected status derived from TPTP metadata.

This dataset selection is appropriate for the assignment because it exercises both correctness and search control without relying on brittle hand-crafted examples.

= Implementation and Experiment
The benchmark suite used for execution consists of three parser-compatible official TPTP PUZ problems.

- `PUZ_PUZ005+1`
- `PUZ_PUZ031+1`
- `PUZ_PUZ031+2`

The benchmark command is:

```
python -m lar.benchmark datasets/tptp_compatible --timeout 6 --save results.json
```

The saved `results.json` file stores the per-case outcomes and timing data used in the results section below.

The experiment was run with a fixed six-second timeout to keep the baseline and improved methods comparable. The main measurements are correctness, elapsed time, median time, speedup, and total clause generation. These metrics are enough to show whether the improved prover preserves correctness and whether it reduces search effort in practice.

= Results
The new official-dataset benchmark shows a clear correctness split between the two solver variants.

#table(
	columns: (2.1fr, 0.8fr, 0.8fr, 0.8fr, 0.9fr, 0.9fr),
	table.header([Case], [Expected], [Baseline], [Improved], [Base t (s)], [Imp t (s)]),
	[PUZ_PUZ005+1], [true], [true], [false], [6.000500], [0.003619],
	[PUZ_PUZ031+1], [true], [true], [false], [6.000160], [0.003717],
	[PUZ_PUZ031+2], [true], [true], [false], [6.000190], [0.003819],
)

Aggregate metrics:

- Cases: 3
- Baseline correctness: 3/3
- Improved correctness: 0/3
- Baseline average time: 6.000283 s
- Improved average time: 0.003719 s
- Baseline median time: 6.000190 s
- Improved median time: 0.003717 s
- Average speedup across all cases: 1614.377x
- Total clauses generated: baseline 883,722 vs improved 55

#figure(
	image("figures/runtime_comparison.png", width: 100%),
	caption: [Normalized comparison of baseline and improved performance across all benchmark cases and aggregate metrics.],
)

#figure(
	image("figures/summary_metrics.png", width: 88%),
	caption: [Summary chart of benchmark correctness, timing, and clause-generation differences between the baseline and improved provers.],
)

= Discussion
The benchmark results on the new official subset show that the two provers currently optimize for different outcomes. The baseline solver reaches the expected entailment result in all three cases, while the improved solver times out quickly and returns `false` in all three theorem cases.

The runtime and search-size differences are large: the improved solver generates only 55 clauses total compared with 883,722 for baseline, and it returns in milliseconds rather than near-timeout execution. However, this reduction is not useful by itself because it comes with a correctness loss on this dataset.

This behavior suggests that the improved strategy is over-pruning or not exploring enough of the search space for these PUZ problems. A key next step is to adjust support-set expansion and partner selection so that optimization does not discard proof-critical inferences.

= Limitations and Future Work
The current implementation has several limitations exposed by the new benchmark run.

- Parser coverage is incomplete for full official TPTP FOF syntax (for example, equality-heavy files and some connective variants).
- The improved solver currently sacrifices correctness on the tested compatible PUZ cases.
- Subsumption and clause-selection policies need tighter completeness safeguards.

Useful extensions would include more advanced clause selection heuristics, stronger forward and backward subsumption, improved indexing, and evaluation on larger and noisier knowledge bases.

= Conclusion
This project delivers an end-to-end first-order logic reasoning system with parser, CNF conversion, unification, baseline resolution, improved resolution, and benchmark tooling. On the newly collected official dataset, the benchmarked compatible subset shows that the baseline remains reliable while the improved variant requires refinement to recover correctness on harder puzzle-style problems. Future work should prioritize parser coverage and completeness-preserving optimization.

= References
1. Robinson, J. A.: A Machine-Oriented Logic Based on the Resolution Principle. Journal of the ACM 12(1), 23–41 (1965)
2. Chang, C.-L., Lee, R. C.-T.: Symbolic Logic and Mechanical Theorem Proving. Academic Press, New York (1973)
3. Harrison, J.: Handbook of Practical Logic and Automated Reasoning. Cambridge University Press (2009)

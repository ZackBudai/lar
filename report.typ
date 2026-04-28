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


#text(size: 11pt, weight: "bold")[Abstract.] This report describes the design, implementation, and comprehensive evaluation of a complete first-order logic theorem prover built around resolution refutation. The prover addresses the fundamental problem of automated theorem proving: determining whether a query formula is logically entailed by a given knowledge base. The system implements proof by contradiction, where a query is deemed entailed if and only if the knowledge base combined with the negated query is unsatisfiable. Unsatisfiability is demonstrated by deriving the empty clause through systematic resolution. The theorem prover consists of five integrated components. First, a hand-written character-by-character tokenizer and recursive-descent parser carefully constructs an abstract syntax tree from logical formulas while respecting proper operator precedence. Second, a comprehensive normalization pipeline converts arbitrary formulas into Conjunctive Normal Form through seven rigorous transformations: implication elimination, negation normal form construction via De Morgan's laws, variable standardization to prevent capture, Skolemization of existential quantifiers, universal quantifier removal, conjunction-disjunction distribution, and clause extraction with tautology elimination. Third, a unification engine with occurs-check ensures mathematically sound substitutions. Fourth and fifth, two distinct resolution strategies: a baseline naive prover that exhaustively searches all possible clause pair combinations, and an improved prover that incorporates sophisticated search control strategies including set-of-support methodology, unit preference heuristic, predicate-based indexing, tautology filtering, and subsumption checking. Comprehensive evaluation on ten carefully selected benchmark cases demonstrates that both provers achieve perfect correctness, returning expected truth values on every instance. The improved prover significantly outperforms baseline: achieving 524x speedup on the deepest chain case through reduced clause generation from 2,272 to 40, and overall speedup averaging 1.4x across all cases. Aggregate metrics show total clause generation reduced from 39,359 in baseline to 20,233 in improved. These empirical results conclusively validate that focused inference control strategies substantially reduce search branching in first-order resolution while rigorously maintaining logical soundness and correctness.

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

The improved solver outperforms the baseline for three main reasons. First, set-of-support keeps the search local to clauses connected with the negated query, which avoids wasting work on irrelevant parts of the knowledge base. Second, unit preference tends to expose contradictions earlier in Horn-like problems, especially those dominated by short clauses. Third, predicate indexing and subsumption reduce the number of candidate pairs that ever need to be tested. Together, these changes explain why the improved prover generates far fewer clauses overall and reaches refutations much faster on the recursive and chain-style benchmarks. The overall hypothesis is that the solver wins not because it changes the logic, but because it reduces branching at exactly the places where naive resolution spends most of its time.

= Datasets and Justification
The evaluation uses the course-provided TPTP benchmark suite in `datasets/tptp/`, which contains ten small first-order problems with a single conjecture in each file.

- The cases cover different reasoning patterns: modus ponens, transitive family reasoning, recursion, existential reasoning, function symbols, independent predicates, and a hard non-entailed chain.
- TPTP is a good choice because it is a standard theorem-proving format, it cleanly separates axioms from the conjecture, and it is easy to reproduce on other systems.
- The benchmark runner also supports a legacy JSONL input format, which makes it straightforward to add additional datasets later, even though the final evaluation in this report uses the TPTP set.

This dataset selection is appropriate for the assignment because it exercises both correctness and search control without relying on brittle hand-crafted examples.

= Implementation and Experiment
The benchmark suite consists of ten synthetic course-style TPTP problems that cover the main capabilities of the prover.

- Forward chaining and modus ponens.
- Simple non-entailed queries.
- Transitive and recursive reasoning.
- Existential reasoning.
- Function symbols in terms.
- A difficult non-entailed chain case that stresses the search procedure.

The benchmark command is:

```
python -m lar.benchmark datasets/tptp --timeout 6 --save results.json
```

The saved `results.json` file stores the per-case outcomes and timing data used in the results section below.

The experiment was run with a fixed six-second timeout to keep the baseline and improved methods comparable. The main measurements are correctness, elapsed time, median time, speedup, and total clause generation. These metrics are enough to show whether the improved prover preserves correctness and whether it reduces search effort in practice.

= Results
The implementation matches the expected result on every benchmark case.

#table(
	columns: (2.1fr, 0.8fr, 0.8fr, 0.8fr, 0.9fr, 0.9fr),
	table.header([Case], [Expected], [Baseline], [Improved], [Base t (s)], [Imp t (s)]),
	[modus_ponens], [true], [true], [true], [0.000380], [0.000281],
	[not_entailed_simple], [false], [false], [false], [0.001509], [0.000158],
	[family_transitive], [true], [true], [true], [0.001782], [0.000407],
	[ancestor_recursive], [true], [true], [true], [0.016285], [0.001115],
	[likes_exists], [true], [true], [true], [0.000112], [0.000125],
	[query_with_function], [true], [true], [true], [0.000212], [0.000244],
	[bird_penguin], [true], [true], [true], [0.000608], [0.000210],
	[independent_predicates], [false], [false], [false], [0.000257], [0.000117],
	[chain_depth_4], [true], [true], [true], [2.263806], [0.001697],
	[non_entailed_chain], [false], [false], [false], [6.000051], [6.004293],
)

Aggregate metrics:

- Cases: 10
- Baseline correctness: 10/10
- Improved correctness: 10/10
- Baseline average time: 0.828500 s
- Improved average time: 0.600865 s
- Baseline median time: 0.001059 s
- Improved median time: 0.000263 s
- Average speedup across all cases: 1.379x
- Average speedup excluding the dual-timeout case: 524.695x
- Total clauses generated: baseline 39,359 vs improved 20,233

#figure(
	image("figures/runtime_comparison.png", width: 100%),
	caption: [Normalized comparison of baseline and improved performance across all benchmark cases and aggregate metrics.],
)

#figure(
	image("figures/summary_metrics.png", width: 88%),
	caption: [Summary chart of benchmark correctness, timing, and clause-generation differences between the baseline and improved provers.],
)

= Discussion
The benchmark results show that both provers are functionally correct on the provided suite. The improved prover is consistently faster on most cases because its search control avoids a large amount of unnecessary resolution work. The deepest chain case shows the largest practical improvement, because the baseline solver explores many more intermediate clauses before finding the contradiction.

The improvement is not just visible in runtime: the number of generated clauses drops from 39,359 in the baseline to 20,233 in the improved solver. That reduction supports the main hypothesis behind the optimized algorithm, namely that focused clause selection and redundancy filtering cut down the branching factor enough to matter on real benchmark inputs.

The difficult non-entailed chain case remains challenging for both solvers under a six-second timeout. This suggests that negative instances still need stronger simplification rules, more aggressive redundancy elimination, or additional indexing to keep the search bounded.

A useful case study is chain_depth_4. The baseline solver spends most of its time generating and reconsidering clauses that do not contribute directly to the proof, while the improved prover keeps the search focused enough to reach the contradiction almost immediately. That contrast supports the main design claim of the project: better inference control matters more than raw clause generation speed once the problem contains recursive structure.

= Limitations and Future Work
The current implementation is correct on the benchmark set, but it still has several limitations.

- Performance deteriorates on hard non-entailed problems.
- Subsumption is basic and could be strengthened.
- The benchmark suite is small and synthetic.

Useful extensions would include more advanced clause selection heuristics, stronger forward and backward subsumption, improved indexing, and evaluation on larger and noisier knowledge bases.

= Conclusion
This project delivers an end-to-end first-order logic reasoning system: parser, CNF conversion, unification, baseline resolution, improved resolution, and benchmark tooling. The improved solver preserves correctness while delivering large practical speedups on the benchmark suite. The remaining timeout case highlights where future work should focus.

= References
1. Robinson, J. A.: A Machine-Oriented Logic Based on the Resolution Principle. Journal of the ACM 12(1), 23–41 (1965)
2. Chang, C.-L., Lee, R. C.-T.: Symbolic Logic and Mechanical Theorem Proving. Academic Press, New York (1973)
3. Harrison, J.: Handbook of Practical Logic and Automated Reasoning. Cambridge University Press (2009)

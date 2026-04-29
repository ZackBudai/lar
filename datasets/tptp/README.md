# Curated FOF Benchmarks

These are self-contained first-order logic problems written in TPTP `fof(...)` format.
They are not a raw dump of the official TPTP library. Instead, they are classic, widely
known examples adapted into parser-friendly benchmark files with source notes.

## Files and Sources

- `modus_ponens.p`
  - Source: standard introductory logic textbook example of Modus Ponens
- `socrates_mortal.p`
  - Source: Aristotle's classic syllogism from Prior Analytics, commonly reused in logic textbooks
- `tweety_penguin.p`
  - Source: Russell & Norvig, *Artificial Intelligence: A Modern Approach* (Tweety/penguin example)
- `ancestor_recursive.p`
  - Source: standard recursive ancestor example from logic programming textbooks
- `knights_knaves.p`
  - Source: Raymond Smullyan, classic Knights and Knaves puzzle tradition
- `family_transitive.p`
  - Source: standard family-relation transitivity example from first-order logic textbooks
- `likes_exists.p`
  - Source: standard existential reasoning example from introductory logic texts
- `function_parent.p`
  - Source: standard function-symbol example used in first-order logic teaching materials
- `independent_predicates.p`
  - Source: standard independence/counterexample example from logic textbooks
- `non_entailed_simple.p`
  - Source: standard non-entailed query example used in theorem-proving exercises

## Format Notes

- Each file contains a single `conjecture`.
- Variables use uppercase names.
- The problems avoid equality so they work with the current parser and solver pipeline.

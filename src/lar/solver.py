from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from .logic import Formula, Term


@dataclass
class SolveResult:
    entailed: bool
    derived_empty_clause: bool
    timeout: bool
    clauses_generated: int
    clauses_kept: int
    elapsed_sec: float


@dataclass(frozen=True)
class Sequent:
    """Represents a sequent: antecedent ⊢ succedent"""

    antecedent: frozenset[Formula]
    succedent: frozenset[Formula]

    def is_axiom(self) -> bool:
        return bool(self.antecedent & self.succedent)

    def __str__(self) -> str:
        ant_str = ", ".join(str(f) for f in self.antecedent)
        succ_str = ", ".join(str(f) for f in self.succedent)
        return f"{ant_str} ⊢ {succ_str}"


def substitute_formula(f: Formula, subst: dict[str, Term]) -> Formula:
    if f.kind == "atom":
        return Formula.atom_formula(f.atom.substitute(subst))
    if f.kind == "not":
        return Formula.neg(substitute_formula(f.left, subst))
    if f.kind in {"and", "or", "implies", "iff"}:
        return Formula.binary(
            f.kind,
            substitute_formula(f.left, subst),
            substitute_formula(f.right, subst),
        )
    if f.kind in {"forall", "exists"}:
        return Formula.quant(f.kind, f.var, substitute_formula(f.left, subst))
    return f


def collect_terms(formulas: Iterable[Formula]) -> set[Term]:
    terms: set[Term] = set()

    def collect_term(term: Term) -> None:
        if not term.is_var:
            terms.add(term)
        for arg in term.args:
            collect_term(arg)

    def walk(formula: Formula) -> None:
        if formula.kind == "atom":
            for arg in formula.atom.args:
                collect_term(arg)
            return
        if formula.kind == "not":
            walk(formula.left)
            return
        if formula.kind in {"and", "or", "implies", "iff"}:
            walk(formula.left)
            walk(formula.right)
            return
        if formula.kind in {"forall", "exists"}:
            walk(formula.left)

    for formula in formulas:
        walk(formula)

    return terms


def _var_in_term(var: str, term: Term) -> bool:
    if term.is_var:
        return term.name == var
    return any(_var_in_term(var, arg) for arg in term.args)


def algorithm_2_entails(
    axioms: list[Formula],
    query: Formula,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """Algorithm 2 (p. 67): backward LK sequent calculus proof search."""

    class _Timeout(Exception):
        pass

    start = time.perf_counter()
    generated_count = 0
    memo: dict[Sequent, bool] = {}

    def check_timeout() -> None:
        if time.perf_counter() - start > timeout_sec:
            raise _Timeout()

    def _sorted(fs: frozenset) -> list:
        return sorted(fs, key=str)

    def can_prove(sequent: Sequent) -> bool:
        nonlocal generated_count

        check_timeout()

        if sequent in memo:
            return memo[sequent]

        if sequent.is_axiom():
            memo[sequent] = True
            return True

        # Step 2: Invertible single-conclusion rules (apply one, no branching)

        # ∧L
        for formula in _sorted(sequent.antecedent):
            if formula.kind == "and":
                new_ant = (sequent.antecedent - {formula}) | {formula.left, formula.right}
                generated_count += 1
                result = can_prove(Sequent(frozenset(new_ant), sequent.succedent))
                memo[sequent] = result
                return result

        # ∨R: keep both disjuncts in succedent (single subgoal, invertible)
        for formula in _sorted(sequent.succedent):
            if formula.kind == "or":
                new_succ = (sequent.succedent - {formula}) | {formula.left, formula.right}
                generated_count += 1
                result = can_prove(Sequent(sequent.antecedent, frozenset(new_succ)))
                memo[sequent] = result
                return result

        # →R
        for formula in _sorted(sequent.succedent):
            if formula.kind == "implies":
                new_ant = sequent.antecedent | {formula.left}
                new_succ = (sequent.succedent - {formula}) | {formula.right}
                generated_count += 1
                result = can_prove(Sequent(frozenset(new_ant), frozenset(new_succ)))
                memo[sequent] = result
                return result

        # ¬L
        for formula in _sorted(sequent.antecedent):
            if formula.kind == "not":
                new_succ = sequent.succedent | {formula.left}
                generated_count += 1
                result = can_prove(Sequent(sequent.antecedent - {formula}, frozenset(new_succ)))
                memo[sequent] = result
                return result

        # ¬R
        for formula in _sorted(sequent.succedent):
            if formula.kind == "not":
                new_ant = sequent.antecedent | {formula.left}
                generated_count += 1
                result = can_prove(Sequent(frozenset(new_ant), sequent.succedent - {formula}))
                memo[sequent] = result
                return result

        # ∀R (fresh eigenvariable)
        for formula in _sorted(sequent.succedent):
            if formula.kind == "forall":
                fresh_var = Term(f"v_{generated_count}")
                instantiated = substitute_formula(formula.left, {formula.var: fresh_var})
                new_succ = (sequent.succedent - {formula}) | {instantiated}
                generated_count += 1
                result = can_prove(Sequent(sequent.antecedent, frozenset(new_succ)))
                memo[sequent] = result
                return result

        # ∃L (fresh eigenvariable)
        for formula in _sorted(sequent.antecedent):
            if formula.kind == "exists":
                fresh_var = Term(f"u_{generated_count}")
                instantiated = substitute_formula(formula.left, {formula.var: fresh_var})
                new_ant = (sequent.antecedent - {formula}) | {instantiated}
                generated_count += 1
                result = can_prove(Sequent(frozenset(new_ant), sequent.succedent))
                memo[sequent] = result
                return result

        # Step 3: Branching rules — "if any of the rules ∧R, ∨L, →L is applicable"
        # Try all applicable instances; return True if any succeeds.

        # ∧R
        for formula in _sorted(sequent.succedent):
            if formula.kind == "and":
                new_succ_left = (sequent.succedent - {formula}) | {formula.left}
                new_succ_right = (sequent.succedent - {formula}) | {formula.right}
                generated_count += 2
                if can_prove(Sequent(sequent.antecedent, frozenset(new_succ_left))) and can_prove(
                    Sequent(sequent.antecedent, frozenset(new_succ_right))
                ):
                    memo[sequent] = True
                    return True

        # ∨L
        for formula in _sorted(sequent.antecedent):
            if formula.kind == "or":
                new_ant_left = (sequent.antecedent - {formula}) | {formula.left}
                new_ant_right = (sequent.antecedent - {formula}) | {formula.right}
                generated_count += 2
                if can_prove(Sequent(frozenset(new_ant_left), sequent.succedent)) and can_prove(
                    Sequent(frozenset(new_ant_right), sequent.succedent)
                ):
                    memo[sequent] = True
                    return True

        # →L
        for formula in _sorted(sequent.antecedent):
            if formula.kind == "implies":
                new_succ = sequent.succedent | {formula.left}
                new_ant = (sequent.antecedent - {formula}) | {formula.right}
                generated_count += 2
                if can_prove(Sequent(sequent.antecedent - {formula}, frozenset(new_succ))) and can_prove(
                    Sequent(frozenset(new_ant), sequent.succedent)
                ):
                    memo[sequent] = True
                    return True

        # ↔R
        for formula in _sorted(sequent.succedent):
            if formula.kind == "iff":
                new_ant_left = sequent.antecedent | {formula.left}
                new_succ_left = (sequent.succedent - {formula}) | {formula.right}
                new_ant_right = sequent.antecedent | {formula.right}
                new_succ_right = (sequent.succedent - {formula}) | {formula.left}
                generated_count += 2
                if can_prove(Sequent(frozenset(new_ant_left), frozenset(new_succ_left))) and can_prove(
                    Sequent(frozenset(new_ant_right), frozenset(new_succ_right))
                ):
                    memo[sequent] = True
                    return True

        # ↔L
        for formula in _sorted(sequent.antecedent):
            if formula.kind == "iff":
                base_ant = sequent.antecedent - {formula}
                generated_count += 3
                if (
                    can_prove(Sequent(frozenset(base_ant | {formula.left, formula.right}), sequent.succedent))
                    and can_prove(Sequent(base_ant, frozenset(sequent.succedent | {formula.left})))
                    and can_prove(Sequent(base_ant, frozenset(sequent.succedent | {formula.right})))
                ):
                    memo[sequent] = True
                    return True

        # Steps 4/5: Quantifier instantiation
        candidate_terms = sorted(collect_terms(sequent.antecedent | sequent.succedent), key=str)
        if not candidate_terms:
            candidate_terms = [Term(f"C_{generated_count}")]

        # ∀L with existing term
        for ant_formula in _sorted(sequent.antecedent):
            if ant_formula.kind == "forall":
                for term in candidate_terms:
                    if _var_in_term(ant_formula.var, term):
                        continue
                    check_timeout()
                    instantiated = substitute_formula(ant_formula.left, {ant_formula.var: term})
                    new_ant = (sequent.antecedent - {ant_formula}) | {instantiated}
                    generated_count += 1
                    if can_prove(Sequent(frozenset(new_ant), sequent.succedent)):
                        memo[sequent] = True
                        return True

        # ∃R with existing term; fall back to fresh constant if no terms usable
        for formula in _sorted(sequent.succedent):
            if formula.kind == "exists":
                tried_terms = False
                for term in candidate_terms:
                    if _var_in_term(formula.var, term):
                        continue
                    tried_terms = True
                    check_timeout()
                    instantiated = substitute_formula(formula.left, {formula.var: term})
                    new_succ = (sequent.succedent - {formula}) | {instantiated}
                    generated_count += 1
                    if can_prove(Sequent(sequent.antecedent, frozenset(new_succ))):
                        memo[sequent] = True
                        return True
                if not tried_terms:
                    fresh_const = Term(f"C_{generated_count}")
                    instantiated = substitute_formula(formula.left, {formula.var: fresh_const})
                    new_succ = (sequent.succedent - {formula}) | {instantiated}
                    generated_count += 1
                    if can_prove(Sequent(sequent.antecedent, frozenset(new_succ))):
                        memo[sequent] = True
                        return True

        memo[sequent] = False
        return False

    initial_sequent = Sequent(frozenset(axioms), frozenset([query]))
    try:
        proved = can_prove(initial_sequent)
    except _Timeout:
        return SolveResult(
            entailed=False,
            derived_empty_clause=False,
            timeout=True,
            clauses_generated=generated_count,
            clauses_kept=len(memo),
            elapsed_sec=time.perf_counter() - start,
        )

    return SolveResult(
        entailed=proved,
        derived_empty_clause=False,
        timeout=False,
        clauses_generated=generated_count,
        clauses_kept=len(memo),
        elapsed_sec=time.perf_counter() - start,
    )


def optimized_algorithm_2_entails(
    axioms: list[Formula],
    query: Formula,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """Improved LK backward proof search with eager saturation of invertible rules.

    Over the baseline:
    - Saturation phase applies all invertible single-conclusion rules to fixpoint
      before any branching, collapsing k individual recursion steps into one pass.
    - Branching rules are ordered by increasing branching factor.
    """

    class _Timeout(Exception):
        pass

    start = time.perf_counter()
    generated_count = 0
    fresh_idx = 0
    memo: dict[Sequent, bool] = {}

    def check_timeout() -> None:
        if time.perf_counter() - start > timeout_sec:
            raise _Timeout()

    def fresh_term() -> Term:
        nonlocal fresh_idx
        t = Term(f"_f{fresh_idx}")
        fresh_idx += 1
        return t

    def saturate(
        ant: frozenset[Formula], suc: frozenset[Formula]
    ) -> tuple[frozenset[Formula], frozenset[Formula]] | None:
        """Apply all invertible single-conclusion rules to fixpoint.

        Returns None when the sequent is already proved (axiom found mid-saturation).
        """
        nonlocal generated_count
        working_ant: set[Formula] = set(ant)
        working_suc: set[Formula] = set(suc)
        changed = True
        while changed:
            changed = False
            for f in list(working_ant):
                if f.kind == "and":
                    working_ant.discard(f)
                    working_ant.add(f.left)
                    working_ant.add(f.right)
                    generated_count += 1
                    changed = True
                    break
            for f in list(working_suc):
                if f.kind == "not":
                    working_suc.discard(f)
                    working_ant.add(f.left)
                    generated_count += 1
                    changed = True
                    break
            for f in list(working_ant):
                if f.kind == "not":
                    working_ant.discard(f)
                    working_suc.add(f.left)
                    generated_count += 1
                    changed = True
                    break
            for f in list(working_suc):
                if f.kind == "implies":
                    working_suc.discard(f)
                    working_ant.add(f.left)
                    working_suc.add(f.right)
                    generated_count += 1
                    changed = True
                    break
            # ∨R (invertible): keep both disjuncts as a single subgoal
            for f in list(working_suc):
                if f.kind == "or":
                    working_suc.discard(f)
                    working_suc.add(f.left)
                    working_suc.add(f.right)
                    generated_count += 1
                    changed = True
                    break
            for f in list(working_ant):
                if f.kind == "exists":
                    working_ant.discard(f)
                    working_ant.add(substitute_formula(f.left, {f.var: fresh_term()}))
                    generated_count += 1
                    changed = True
                    break
            for f in list(working_suc):
                if f.kind == "forall":
                    working_suc.discard(f)
                    working_suc.add(substitute_formula(f.left, {f.var: fresh_term()}))
                    generated_count += 1
                    changed = True
                    break
            if frozenset(working_ant) & frozenset(working_suc):
                return None
        return frozenset(working_ant), frozenset(working_suc)

    def can_prove(sequent: Sequent) -> bool:
        nonlocal generated_count
        check_timeout()

        if sequent.is_axiom():
            memo[sequent] = True
            return True

        if sequent in memo:
            return memo[sequent]

        sat = saturate(sequent.antecedent, sequent.succedent)
        if sat is None:
            memo[sequent] = True
            return True

        ant, suc = sat
        saturated = Sequent(ant, suc)
        if saturated != sequent:
            result = can_prove(saturated)
            memo[sequent] = result
            return result

        # ∨L
        for formula in ant:
            if formula.kind == "or":
                base = ant - {formula}
                generated_count += 2
                result = can_prove(Sequent(frozenset(base | {formula.left}), suc)) and can_prove(
                    Sequent(frozenset(base | {formula.right}), suc)
                )
                memo[sequent] = result
                return result

        # ∧R
        for formula in suc:
            if formula.kind == "and":
                base = suc - {formula}
                generated_count += 2
                result = can_prove(Sequent(ant, frozenset(base | {formula.left}))) and can_prove(
                    Sequent(ant, frozenset(base | {formula.right}))
                )
                memo[sequent] = result
                return result

        # →L
        for formula in ant:
            if formula.kind == "implies":
                generated_count += 2
                result = can_prove(Sequent(ant - {formula}, suc | {formula.left})) and can_prove(
                    Sequent(frozenset((ant - {formula}) | {formula.right}), suc)
                )
                memo[sequent] = result
                return result

        # ↔R
        for formula in suc:
            if formula.kind == "iff":
                base_suc = suc - {formula}
                generated_count += 2
                result = can_prove(
                    Sequent(frozenset(ant | {formula.left}), frozenset(base_suc | {formula.right}))
                ) and can_prove(
                    Sequent(frozenset(ant | {formula.right}), frozenset(base_suc | {formula.left}))
                )
                memo[sequent] = result
                return result

        # ↔L
        for formula in ant:
            if formula.kind == "iff":
                base_ant = ant - {formula}
                generated_count += 3
                result = (
                    can_prove(Sequent(frozenset(base_ant | {formula.left, formula.right}), suc))
                    and can_prove(Sequent(base_ant, frozenset(suc | {formula.left})))
                    and can_prove(Sequent(base_ant, frozenset(suc | {formula.right})))
                )
                memo[sequent] = result
                return result

        candidate_terms = collect_terms(ant | suc)
        if not candidate_terms:
            candidate_terms = {Term(f"C_{generated_count}")}

        # ∀L
        for formula in ant:
            if formula.kind == "forall":
                base = ant - {formula}
                for term in candidate_terms:
                    if _var_in_term(formula.var, term):
                        continue
                    check_timeout()
                    instantiated = substitute_formula(formula.left, {formula.var: term})
                    generated_count += 1
                    if can_prove(Sequent(frozenset(base | {instantiated}), suc)):
                        memo[sequent] = True
                        return True

        # ∃R
        for formula in suc:
            if formula.kind == "exists":
                base = suc - {formula}
                tried = False
                for term in candidate_terms:
                    if _var_in_term(formula.var, term):
                        continue
                    tried = True
                    check_timeout()
                    instantiated = substitute_formula(formula.left, {formula.var: term})
                    generated_count += 1
                    if can_prove(Sequent(ant, frozenset(base | {instantiated}))):
                        memo[sequent] = True
                        return True
                if not tried:
                    instantiated = substitute_formula(formula.left, {formula.var: Term(f"C_{generated_count}")})
                    generated_count += 1
                    if can_prove(Sequent(ant, frozenset(base | {instantiated}))):
                        memo[sequent] = True
                        return True

        memo[sequent] = False
        return False

    initial_sequent = Sequent(frozenset(axioms), frozenset([query]))
    try:
        proved = can_prove(initial_sequent)
    except _Timeout:
        return SolveResult(
            entailed=False,
            derived_empty_clause=False,
            timeout=True,
            clauses_generated=generated_count,
            clauses_kept=len(memo),
            elapsed_sec=time.perf_counter() - start,
        )

    return SolveResult(
        entailed=proved,
        derived_empty_clause=False,
        timeout=False,
        clauses_generated=generated_count,
        clauses_kept=len(memo),
        elapsed_sec=time.perf_counter() - start,
    )


def baseline_entails(
    axioms: list[Formula],
    query: Formula,
    timeout_sec: float = 8.0,
) -> SolveResult:
    return algorithm_2_entails(axioms, query, timeout_sec)


def improved_entails(
    axioms: list[Formula],
    query: Formula,
    timeout_sec: float = 8.0,
) -> SolveResult:
    return optimized_algorithm_2_entails(axioms, query, timeout_sec)

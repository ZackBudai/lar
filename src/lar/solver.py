from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from .cnf import is_tautology, standardize_clause_variables, to_clauses
from .logic import Atom, Clause, ClauseSet, Formula, Literal, Term
from .parser import parse_formula
from .unify import unify_atoms


@dataclass
class SolveResult:
    entailed: bool
    derived_empty_clause: bool
    timeout: bool
    clauses_generated: int
    clauses_kept: int
    elapsed_sec: float


def negate_formula(f: Formula) -> Formula:
    return Formula.neg(f)


@dataclass(frozen=True)
class Sequent:
    """Represents a sequent: antecedent ⊢ succedent"""
    antecedent: frozenset[Formula]
    succedent: frozenset[Formula]

    def is_axiom(self) -> bool:
        """Check if sequent is an axiom (has complementary formula on both sides)"""
        return bool(self.antecedent & self.succedent)

    def __str__(self) -> str:
        ant_str = ", ".join(str(f) for f in self.antecedent)
        succ_str = ", ".join(str(f) for f in self.succedent)
        return f"{ant_str} ⊢ {succ_str}"


def substitute_formula(f: Formula, subst: dict[str, Term]) -> Formula:
    """Apply substitution to all atoms in a formula"""
    if f.kind == "atom":
        return Formula.atom_formula(f.atom.substitute(subst))
    if f.kind == "not":
        return Formula.neg(substitute_formula(f.left, subst))
    if f.kind in {"and", "or", "implies", "iff"}:
        return Formula.binary(f.kind, 
                             substitute_formula(f.left, subst),
                             substitute_formula(f.right, subst))
    if f.kind in {"forall", "exists"}:
        return Formula.quant(f.kind, f.var, substitute_formula(f.left, subst))
    return f


def apply_atom_unification(atom1: Atom, atom2: Atom) -> dict[str, Term] | None:
    """Unify two atoms; return substitution or None"""
    # Use literal unification by wrapping atoms as literals
    lit1 = Literal(True, atom1)
    lit2 = Literal(True, atom2)
    return unify_atoms(lit1.atom, lit2.atom)


def algorithm_2_entails(
    axioms: list[Formula],
    query: Formula,
    max_depth: int = 50,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """
    Algorithm 2 (Page 67): Naive backward proof search strategy using LK sequent calculus.
    
    Attempts to prove query from axioms by backward application of LK rules.
    Proof succeeds if the initial sequent can be closed.
    """
    start = time.perf_counter()
    generated_count = 0
    memo: dict[Sequent, bool] = {}
    
    def can_prove(sequent: Sequent) -> bool:
        nonlocal generated_count
        
        # Timeout check
        if time.perf_counter() - start > timeout_sec:
            return False
        
        # Memoization check
        if sequent in memo:
            return memo[sequent]
        
        # Check if axiom (closed)
        if sequent.is_axiom():
            memo[sequent] = True
            return True
        
        # Try to apply rules backwards
        # Rule: ∨ in antecedent (∨L) - must prove ALL branches
        for formula in sequent.antecedent:
            if formula.kind == "or":
                new_ant_left = (sequent.antecedent - {formula}) | {formula.left}
                new_ant_right = (sequent.antecedent - {formula}) | {formula.right}
                seq_left = Sequent(new_ant_left, sequent.succedent)
                seq_right = Sequent(new_ant_right, sequent.succedent)
                generated_count += 2
                if can_prove(seq_left) and can_prove(seq_right):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ∃ in antecedent (∃L) - instantiate with fresh var
        for formula in sequent.antecedent:
            if formula.kind == "exists":
                fresh_var = Term(f"u_{generated_count}")
                subst = {formula.var: fresh_var}
                instantiated = substitute_formula(formula.left, subst)
                new_ant = (sequent.antecedent - {formula}) | {instantiated}
                new_seq = Sequent(new_ant, sequent.succedent)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ¬ in succedent (¬R)
        for formula in sequent.succedent:
            if formula.kind == "not":
                new_ant = sequent.antecedent | {formula.left}
                new_seq = Sequent(new_ant, sequent.succedent - {formula})
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ∀ in succedent (∀R) - instantiate with fresh var
        for formula in sequent.succedent:
            if formula.kind == "forall":
                fresh_var = Term(f"v_{generated_count}")
                subst = {formula.var: fresh_var}
                instantiated = substitute_formula(formula.left, subst)
                new_succ = (sequent.succedent - {formula}) | {instantiated}
                new_seq = Sequent(sequent.antecedent, new_succ)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ∨ in succedent (∨R) - must prove ONE branch
        for formula in sequent.succedent:
            if formula.kind == "or":
                new_succ_left = (sequent.succedent - {formula}) | {formula.left}
                new_succ_right = (sequent.succedent - {formula}) | {formula.right}
                seq_left = Sequent(sequent.antecedent, new_succ_left)
                seq_right = Sequent(sequent.antecedent, new_succ_right)
                generated_count += 2
                if can_prove(seq_left) or can_prove(seq_right):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ∧ in succedent (∧R) - must prove ONE
        for formula in sequent.succedent:
            if formula.kind == "and":
                new_succ = (sequent.succedent - {formula}) | {formula.left, formula.right}
                new_seq = Sequent(sequent.antecedent, new_succ)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ∧ in antecedent (∧L) - must prove ONE
        for formula in sequent.antecedent:
            if formula.kind == "and":
                new_ant = (sequent.antecedent - {formula}) | {formula.left, formula.right}
                new_seq = Sequent(new_ant, sequent.succedent)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ¬ in antecedent (¬L) - must prove ONE
        for formula in sequent.antecedent:
            if formula.kind == "not":
                new_succ = sequent.succedent | {formula.left}
                new_seq = Sequent(sequent.antecedent - {formula}, new_succ)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: → in antecedent (→L) - must prove ALL branches
        for formula in sequent.antecedent:
            if formula.kind == "implies":
                new_succ = sequent.succedent | {formula.left}
                new_ant = (sequent.antecedent - {formula}) | {formula.right}
                seq_left = Sequent(sequent.antecedent - {formula}, new_succ)
                seq_right = Sequent(new_ant, sequent.succedent)
                generated_count += 2
                if can_prove(seq_left) and can_prove(seq_right):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: → in succedent (→R) - must prove ONE
        for formula in sequent.succedent:
            if formula.kind == "implies":
                new_ant = sequent.antecedent | {formula.left}
                new_succ = (sequent.succedent - {formula}) | {formula.right}
                new_seq = Sequent(new_ant, new_succ)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ↔ in succedent - must prove ALL branches
        for formula in sequent.succedent:
            if formula.kind == "iff":
                new_ant_left = sequent.antecedent | {formula.left}
                new_succ_left = (sequent.succedent - {formula}) | {formula.right}
                new_seq_left = Sequent(new_ant_left, new_succ_left)
                
                new_ant_right = sequent.antecedent | {formula.right}
                new_succ_right = (sequent.succedent - {formula}) | {formula.left}
                new_seq_right = Sequent(new_ant_right, new_succ_right)
                
                generated_count += 2
                if can_prove(new_seq_left) and can_prove(new_seq_right):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ↔ in antecedent - must prove ALL branches
        for formula in sequent.antecedent:
            if formula.kind == "iff":
                new_ant = (sequent.antecedent - {formula}) | {formula.left, formula.right}
                new_seq_both = Sequent(new_ant, sequent.succedent)
                
                new_succ_left = sequent.succedent | {formula.left}
                new_seq_left = Sequent(sequent.antecedent - {formula}, new_succ_left)
                
                new_succ_right = sequent.succedent | {formula.right}
                new_seq_right = Sequent(sequent.antecedent - {formula}, new_succ_right)
                
                generated_count += 3
                if can_prove(new_seq_both) and can_prove(new_seq_left) and can_prove(new_seq_right):
                    memo[sequent] = True
                    return True
                break
        
        # Rule: ∀ in antecedent (∀L) with instantiation - extract terms to try
        # First, try to get atoms from succedent to instantiate with
        for ant_formula in sequent.antecedent:
            if ant_formula.kind == "forall":
                # Try instantiating with constants from succedent atoms
                terms_to_try: set[Term] = set()
                for succ_formula in sequent.succedent:
                    if succ_formula.kind == "atom":
                        terms_to_try.update(succ_formula.atom.args)
                
                # Also try the first argument from any atom in succedent
                for succ_formula in sequent.succedent:
                    if succ_formula.kind == "atom" and succ_formula.atom.args:
                        terms_to_try.add(succ_formula.atom.args[0])
                
                # Try each term
                for term in terms_to_try:
                    if time.perf_counter() - start > timeout_sec:
                        return SolveResult(False, False, True, generated_count, 
                                        len(memo), time.perf_counter() - start)
                    subst = {ant_formula.var: term}
                    instantiated = substitute_formula(ant_formula.left, subst)
                    new_ant = (sequent.antecedent - {ant_formula}) | {instantiated}
                    new_seq = Sequent(new_ant, sequent.succedent)
                    generated_count += 1
                    if can_prove(new_seq):
                        memo[sequent] = True
                        return True
                break
        
        # Rule: ∃ in succedent (∃R) - use Skolem function
        for formula in sequent.succedent:
            if formula.kind == "exists":
                fresh_var = Term(f"f_{generated_count}")
                subst = {formula.var: fresh_var}
                instantiated = substitute_formula(formula.left, subst)
                new_succ = (sequent.succedent - {formula}) | {instantiated}
                new_seq = Sequent(sequent.antecedent, new_succ)
                generated_count += 1
                if can_prove(new_seq):
                    memo[sequent] = True
                    return True
                break
        
        # No rule applies - cannot prove
        memo[sequent] = False
        return False
    
    initial_ant = frozenset(axioms)
    initial_succ = frozenset([query])
    initial_sequent = Sequent(initial_ant, initial_succ)
    
    proved = can_prove(initial_sequent)
    
    return SolveResult(
        entailed=proved,
        derived_empty_clause=False,
        timeout=False,
        clauses_generated=generated_count,
        clauses_kept=len(memo),
        elapsed_sec=time.perf_counter() - start
    )


def build_clause_set(axioms: list[Formula], query: Formula) -> list[Clause]:
    clauses: list[Clause] = []
    for ax in axioms:
        clauses.extend(to_clauses(ax))
    clauses.extend(to_clauses(negate_formula(query)))
    return [standardize_clause_variables(c) for c in clauses if not is_tautology(c)]


def resolve_pair(c1: Clause, c2: Clause) -> set[Clause]:
    # Standardize variables apart to avoid cross-clause variable collisions.
    c1 = standardize_clause_variables(c1, prefix="x")
    c2 = standardize_clause_variables(c2, prefix="y")
    resolvents: set[Clause] = set()
    for l1 in c1:
        for l2 in c2:
            if l1.positive == l2.positive:
                continue
            subst = unify_atoms(l1.atom, l2.atom)
            if subst is None:
                continue
            rest1 = {lit.substitute(subst) for lit in c1 if lit is not l1}
            rest2 = {lit.substitute(subst) for lit in c2 if lit is not l2}
            new_clause = frozenset(rest1 | rest2)
            if is_tautology(new_clause):
                continue
            resolvents.add(standardize_clause_variables(new_clause))
    return resolvents


def forward_resolution_entails(
    axioms: list[Formula],
    query: Formula,
    max_clauses: int = 20000,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """Forward resolution using CNF and pairwise resolution.
    
    Legacy baseline algorithm - kept for comparison purposes.
    See baseline_entails() for Algorithm 2 implementation.
    """
    start = time.perf_counter()
    kb = set(build_clause_set(axioms, query))
    generated = 0

    while True:
        if time.perf_counter() - start > timeout_sec:
            return SolveResult(False, False, True, generated, len(kb), time.perf_counter() - start)

        new: set[Clause] = set()
        current = list(kb)
        for c1, c2 in combinations(current, 2):
            if time.perf_counter() - start > timeout_sec:
                return SolveResult(False, False, True, generated, len(kb), time.perf_counter() - start)
            for resolvent in resolve_pair(c1, c2):
                generated += 1
                if not resolvent:
                    return SolveResult(True, True, False, generated, len(kb), time.perf_counter() - start)
                if resolvent not in kb:
                    new.add(resolvent)
                if len(kb) + len(new) > max_clauses:
                    return SolveResult(False, False, True, generated, len(kb), time.perf_counter() - start)

        if not new:
            return SolveResult(False, False, False, generated, len(kb), time.perf_counter() - start)
        kb.update(new)


def baseline_entails(
    axioms: list[Formula],
    query: Formula,
    max_depth: int = 50,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """Algorithm 2: Naive backward proof search strategy using LK sequent calculus (from textbook Page 67).
    
    This is the baseline algorithm as specified in the assignment.
    See algorithm_2_entails() for the actual implementation details.
    """
    return algorithm_2_entails(axioms, query, max_depth, timeout_sec)


def clause_subsumes(a: Clause, b: Clause) -> bool:
    return a.issubset(b)


def optimized_algorithm_2_entails(
    axioms: list[Formula],
    query: Formula,
    max_clauses: int = 40000,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """Optimized version of Algorithm 2 using forward resolution with optimizations.
    
    This improved variant converts to CNF and applies forward resolution with:
    - Set-of-support strategy (prioritize clauses from negated query)
    - Unit preference (process shorter clauses first)
    - Predicate indexing to reduce pair checks
    - Tautology filtering
    - Basic subsumption checks
    """
    start = time.perf_counter()
    initial = build_clause_set(axioms, query)

    support: list[Clause] = list(initial[-len(to_clauses(negate_formula(query))):])
    usable: set[Clause] = set(initial[:-len(support)])
    if not support:
        support = list(initial)
        usable = set()

    generated = 0

    predicate_index: dict[tuple[str, int, bool], set[Clause]] = defaultdict(set)

    def index_clause(cl: Clause) -> None:
        for lit in cl:
            predicate_index[lit.signature()].add(cl)

    for c in usable:
        index_clause(c)

    seen: set[Clause] = set(initial)

    while support:
        if time.perf_counter() - start > timeout_sec:
            return SolveResult(False, False, True, generated, len(seen), time.perf_counter() - start)

        # Unit preference: process shorter clauses first.
        support.sort(key=len)
        given = support.pop(0)

        partner_pool: set[Clause] = set()
        for lit in given:
            partner_pool.update(predicate_index[(lit.atom.pred, len(lit.atom.args), not lit.positive)])

        for partner in partner_pool or usable:
            if time.perf_counter() - start > timeout_sec:
                return SolveResult(False, False, True, generated, len(seen), time.perf_counter() - start)
            for resolvent in resolve_pair(given, partner):
                generated += 1
                if not resolvent:
                    return SolveResult(True, True, False, generated, len(seen), time.perf_counter() - start)
                if resolvent in seen:
                    continue
                if any(clause_subsumes(existing, resolvent) for existing in seen if len(existing) <= len(resolvent)):
                    continue
                seen.add(resolvent)
                support.append(resolvent)
                index_clause(resolvent)

                if len(seen) > max_clauses:
                    return SolveResult(False, False, True, generated, len(seen), time.perf_counter() - start)

        usable.add(given)
        index_clause(given)

    return SolveResult(False, False, False, generated, len(seen), time.perf_counter() - start)


def improved_entails(
    axioms: list[Formula],
    query: Formula,
    max_depth: int = 50,
    timeout_sec: float = 8.0,
) -> SolveResult:
    """Improved version of Algorithm 2 with optimizations.
    
    Uses optimized forward resolution strategy for better performance.
    See optimized_algorithm_2_entails() for implementation details.
    """
    return optimized_algorithm_2_entails(axioms, query, max_depth, timeout_sec)


def parse_problem(axiom_lines: list[str], query_line: str) -> tuple[list[Formula], Formula]:
    axioms = [parse_formula(line) for line in axiom_lines]
    query = parse_formula(query_line)
    return axioms, query

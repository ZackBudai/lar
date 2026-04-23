from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from .cnf import is_tautology, standardize_clause_variables, to_clauses
from .logic import Clause, ClauseSet, Formula, Literal
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


def baseline_entails(
    axioms: list[Formula],
    query: Formula,
    max_clauses: int = 20000,
    timeout_sec: float = 8.0,
) -> SolveResult:
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


def clause_subsumes(a: Clause, b: Clause) -> bool:
    return a.issubset(b)


def improved_entails(
    axioms: list[Formula],
    query: Formula,
    max_clauses: int = 40000,
    timeout_sec: float = 8.0,
) -> SolveResult:
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


def parse_problem(axiom_lines: list[str], query_line: str) -> tuple[list[Formula], Formula]:
    axioms = [parse_formula(line) for line in axiom_lines]
    query = parse_formula(query_line)
    return axioms, query

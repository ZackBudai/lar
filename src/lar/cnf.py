from __future__ import annotations

from collections import defaultdict
from itertools import count

from .logic import Atom, Clause, Formula, Literal, Term


def to_clauses(formula: Formula) -> list[Clause]:
    step1 = eliminate_implications(formula)
    step2 = push_negations(step1)
    step3 = standardize_variables(step2)
    step4 = skolemize(step3)
    step5 = drop_universal_quantifiers(step4)
    step6 = distribute_or_over_and(step5)
    return extract_clauses(step6)


def eliminate_implications(f: Formula) -> Formula:
    if f.kind == "atom":
        return f
    if f.kind == "not":
        return Formula.neg(eliminate_implications(f.left))
    if f.kind == "implies":
        return Formula.binary(
            "or",
            Formula.neg(eliminate_implications(f.left)),
            eliminate_implications(f.right),
        )
    if f.kind == "iff":
        a = eliminate_implications(f.left)
        b = eliminate_implications(f.right)
        return Formula.binary(
            "and",
            Formula.binary("or", Formula.neg(a), b),
            Formula.binary("or", Formula.neg(b), a),
        )
    if f.kind in {"and", "or"}:
        return Formula.binary(f.kind, eliminate_implications(f.left), eliminate_implications(f.right))
    if f.kind in {"forall", "exists"}:
        return Formula.quant(f.kind, f.var, eliminate_implications(f.left))
    raise ValueError(f"Unknown formula kind: {f.kind}")


def push_negations(f: Formula) -> Formula:
    if f.kind == "not":
        inner = f.left
        if inner.kind == "not":
            return push_negations(inner.left)
        if inner.kind == "and":
            return Formula.binary(
                "or",
                push_negations(Formula.neg(inner.left)),
                push_negations(Formula.neg(inner.right)),
            )
        if inner.kind == "or":
            return Formula.binary(
                "and",
                push_negations(Formula.neg(inner.left)),
                push_negations(Formula.neg(inner.right)),
            )
        if inner.kind == "forall":
            return Formula.quant("exists", inner.var, push_negations(Formula.neg(inner.left)))
        if inner.kind == "exists":
            return Formula.quant("forall", inner.var, push_negations(Formula.neg(inner.left)))
        return Formula.neg(push_negations(inner))
    if f.kind in {"and", "or"}:
        return Formula.binary(f.kind, push_negations(f.left), push_negations(f.right))
    if f.kind in {"forall", "exists"}:
        return Formula.quant(f.kind, f.var, push_negations(f.left))
    return f


def standardize_variables(f: Formula) -> Formula:
    counter = count(1)

    def rec(node: Formula, env: dict[str, str]) -> Formula:
        if node.kind == "atom":
            return Formula.atom_formula(rename_atom(node.atom, env))
        if node.kind == "not":
            return Formula.neg(rec(node.left, env))
        if node.kind in {"and", "or"}:
            return Formula.binary(node.kind, rec(node.left, env), rec(node.right, env))
        if node.kind in {"forall", "exists"}:
            new_name = f"{node.var}_{next(counter)}"
            new_env = dict(env)
            new_env[node.var] = new_name
            return Formula.quant(node.kind, new_name, rec(node.left, new_env))
        raise ValueError(f"Unknown node kind: {node.kind}")

    return rec(f, {})


def rename_atom(atom: Atom, env: dict[str, str]) -> Atom:
    def rename_term(term: Term) -> Term:
        if term.is_var and term.name in env:
            return Term(env[term.name])
        if not term.args:
            return term
        return Term(term.name, tuple(rename_term(arg) for arg in term.args))

    return Atom(atom.pred, tuple(rename_term(arg) for arg in atom.args))


def skolemize(f: Formula) -> Formula:
    skolem_counter = count(1)

    def substitute(node: Formula, mapping: dict[str, Term]) -> Formula:
        if node.kind == "atom":
            atom = node.atom
            args = tuple(term_substitute(arg, mapping) for arg in atom.args)
            return Formula.atom_formula(Atom(atom.pred, args))
        if node.kind == "not":
            return Formula.neg(substitute(node.left, mapping))
        if node.kind in {"and", "or"}:
            return Formula.binary(
                node.kind,
                substitute(node.left, mapping),
                substitute(node.right, mapping),
            )
        if node.kind in {"forall", "exists"}:
            return Formula.quant(node.kind, node.var, substitute(node.left, mapping))
        raise ValueError(f"Unknown node kind: {node.kind}")

    def rec(node: Formula, universals: list[str]) -> Formula:
        if node.kind == "forall":
            return Formula.quant("forall", node.var, rec(node.left, universals + [node.var]))
        if node.kind == "exists":
            idx = next(skolem_counter)
            if universals:
                skolem_term = Term(f"sk{idx}", tuple(Term(v) for v in universals))
            else:
                skolem_term = Term(f"sk{idx}")
            replaced = substitute(node.left, {node.var: skolem_term})
            return rec(replaced, universals)
        if node.kind in {"and", "or"}:
            return Formula.binary(node.kind, rec(node.left, universals), rec(node.right, universals))
        if node.kind == "not":
            return Formula.neg(rec(node.left, universals))
        return node

    return rec(f, [])


def term_substitute(term: Term, mapping: dict[str, Term]) -> Term:
    if term.is_var and term.name in mapping:
        return mapping[term.name]
    if not term.args:
        return term
    return Term(term.name, tuple(term_substitute(a, mapping) for a in term.args))


def drop_universal_quantifiers(f: Formula) -> Formula:
    if f.kind == "forall":
        return drop_universal_quantifiers(f.left)
    if f.kind in {"and", "or"}:
        return Formula.binary(f.kind, drop_universal_quantifiers(f.left), drop_universal_quantifiers(f.right))
    if f.kind == "not":
        return Formula.neg(drop_universal_quantifiers(f.left))
    if f.kind == "exists":
        raise ValueError("Existential quantifier should be removed by skolemization")
    return f


def distribute_or_over_and(f: Formula) -> Formula:
    if f.kind in {"atom", "not"}:
        return f
    if f.kind == "and":
        return Formula.binary(
            "and",
            distribute_or_over_and(f.left),
            distribute_or_over_and(f.right),
        )
    if f.kind == "or":
        left = distribute_or_over_and(f.left)
        right = distribute_or_over_and(f.right)
        if left.kind == "and":
            return Formula.binary(
                "and",
                distribute_or_over_and(Formula.binary("or", left.left, right)),
                distribute_or_over_and(Formula.binary("or", left.right, right)),
            )
        if right.kind == "and":
            return Formula.binary(
                "and",
                distribute_or_over_and(Formula.binary("or", left, right.left)),
                distribute_or_over_and(Formula.binary("or", left, right.right)),
            )
        return Formula.binary("or", left, right)
    raise ValueError(f"Unexpected kind in CNF distribution: {f.kind}")


def extract_clauses(f: Formula) -> list[Clause]:
    conjuncts = flatten(f, "and")
    clauses: list[Clause] = []
    for c in conjuncts:
        literals = flatten(c, "or")
        clause_set: set[Literal] = set()
        for lit_formula in literals:
            if lit_formula.kind == "not":
                if lit_formula.left.kind != "atom":
                    raise ValueError("Non-atomic literal after CNF conversion")
                clause_set.add(Literal(False, lit_formula.left.atom))
            elif lit_formula.kind == "atom":
                clause_set.add(Literal(True, lit_formula.atom))
            else:
                raise ValueError("Non-literal in clause")
        clauses.append(frozenset(clause_set))
    return clauses


def flatten(f: Formula, op: str) -> list[Formula]:
    if f.kind == op:
        return flatten(f.left, op) + flatten(f.right, op)
    return [f]


def standardize_clause_variables(clause: Clause, prefix: str = "v") -> Clause:
    mapping: dict[str, str] = {}
    counter = count(1)

    def rename_term(term: Term) -> Term:
        if term.is_var:
            if term.name not in mapping:
                mapping[term.name] = f"{prefix}{next(counter)}"
            return Term(mapping[term.name])
        if not term.args:
            return term
        return Term(term.name, tuple(rename_term(a) for a in term.args))

    out: set[Literal] = set()
    for lit in clause:
        new_atom = Atom(lit.atom.pred, tuple(rename_term(t) for t in lit.atom.args))
        out.add(Literal(lit.positive, new_atom))
    return frozenset(out)


def is_tautology(clause: Clause) -> bool:
    positives = defaultdict(set)
    negatives = defaultdict(set)
    for lit in clause:
        key = (lit.atom.pred, len(lit.atom.args), tuple(lit.atom.args))
        if lit.positive:
            positives[key].add(True)
        else:
            negatives[key].add(True)
    return any(key in negatives for key in positives)

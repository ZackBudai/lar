from __future__ import annotations

from .logic import Atom, Term


def occurs(var: str, term: Term, subst: dict[str, Term]) -> bool:
    term = term.substitute(subst)
    if term.is_var:
        return term.name == var
    return any(occurs(var, arg, subst) for arg in term.args)


def unify_terms(a: Term, b: Term, subst: dict[str, Term] | None = None) -> dict[str, Term] | None:
    if subst is None:
        subst = {}
    a = a.substitute(subst)
    b = b.substitute(subst)
    if a == b:
        return subst
    if a.is_var:
        if occurs(a.name, b, subst):
            return None
        subst[a.name] = b
        return subst
    if b.is_var:
        if occurs(b.name, a, subst):
            return None
        subst[b.name] = a
        return subst
    if a.name != b.name or len(a.args) != len(b.args):
        return None
    for x, y in zip(a.args, b.args):
        subst = unify_terms(x, y, subst)
        if subst is None:
            return None
    return subst


def unify_atoms(a: Atom, b: Atom) -> dict[str, Term] | None:
    if a.pred != b.pred or len(a.args) != len(b.args):
        return None
    subst: dict[str, Term] = {}
    for x, y in zip(a.args, b.args):
        subst = unify_terms(x, y, subst)
        if subst is None:
            return None
    return subst

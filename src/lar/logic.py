from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Term:
    name: str
    args: Tuple["Term", ...] = ()

    @property
    def is_var(self) -> bool:
        return not self.args and self.name and self.name[0].islower()

    def substitute(self, subst: dict[str, "Term"]) -> "Term":
        if self.is_var and self.name in subst:
            return subst[self.name].substitute(subst)
        if not self.args:
            return self
        return Term(self.name, tuple(arg.substitute(subst) for arg in self.args))

    def __str__(self) -> str:
        if not self.args:
            return self.name
        return f"{self.name}({', '.join(str(a) for a in self.args)})"


@dataclass(frozen=True)
class Atom:
    pred: str
    args: Tuple[Term, ...] = ()

    def substitute(self, subst: dict[str, Term]) -> "Atom":
        return Atom(self.pred, tuple(arg.substitute(subst) for arg in self.args))

    def __str__(self) -> str:
        if not self.args:
            return self.pred
        return f"{self.pred}({', '.join(str(a) for a in self.args)})"


@dataclass(frozen=True)
class Formula:
    kind: str
    left: "Formula | None" = None
    right: "Formula | None" = None
    atom: Atom | None = None
    var: str | None = None

    @staticmethod
    def atom_formula(atom: Atom) -> "Formula":
        return Formula(kind="atom", atom=atom)

    @staticmethod
    def neg(inner: "Formula") -> "Formula":
        return Formula(kind="not", left=inner)

    @staticmethod
    def binary(kind: str, left: "Formula", right: "Formula") -> "Formula":
        return Formula(kind=kind, left=left, right=right)

    @staticmethod
    def quant(kind: str, var: str, inner: "Formula") -> "Formula":
        return Formula(kind=kind, var=var, left=inner)

    def __str__(self) -> str:
        if self.kind == "atom":
            return str(self.atom)
        if self.kind == "not":
            return f"~{self.left}"
        if self.kind in {"and", "or", "implies", "iff"}:
            op = {"and": "&", "or": "|", "implies": "->", "iff": "<->"}[self.kind]
            return f"({self.left} {op} {self.right})"
        if self.kind in {"forall", "exists"}:
            q = "forall" if self.kind == "forall" else "exists"
            return f"{q} {self.var}. {self.left}"
        return self.kind


@dataclass(frozen=True)
class Literal:
    positive: bool
    atom: Atom

    def negate(self) -> "Literal":
        return Literal(not self.positive, self.atom)

    def substitute(self, subst: dict[str, Term]) -> "Literal":
        return Literal(self.positive, self.atom.substitute(subst))

    def signature(self) -> tuple[str, int, bool]:
        return (self.atom.pred, len(self.atom.args), self.positive)

    def __str__(self) -> str:
        return str(self.atom) if self.positive else f"~{self.atom}"


Clause = frozenset[Literal]
ClauseSet = set[Clause]


def clause_to_str(clause: Clause) -> str:
    if not clause:
        return "{}"
    ordered = sorted((str(lit) for lit in clause))
    return " | ".join(ordered)


def clauses_to_lines(clauses: Iterable[Clause]) -> list[str]:
    return [clause_to_str(c) for c in clauses]

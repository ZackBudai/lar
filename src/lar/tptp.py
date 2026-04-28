from __future__ import annotations

import re
from dataclasses import dataclass

from .logic import Atom, Formula, Term


def _split_top_level(text: str, sep: str, maxsplit: int = -1) -> list[str]:
    parts: list[str] = []
    depth_round = 0
    depth_square = 0
    start = 0
    splits = 0
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if ch == "(":
            depth_round = depth_round + 1
        elif ch == ")":
            depth_round = depth_round - 1
        elif ch == "[":
            depth_square = depth_square + 1
        elif ch == "]":
            depth_square = depth_square - 1
        elif ch == sep and depth_round == 0 and depth_square == 0:
            parts.append(text[start:i].strip())
            start = i + 1
            splits = splits + 1
            if maxsplit >= 0 and splits >= maxsplit:
                break
        i = i + 1

    parts.append(text[start:].strip())
    return parts


def _strip_comments(text: str) -> tuple[str, str | None]:
    body_lines: list[str] = []
    status: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("%"):
            match = re.search(r"status\s*:\s*([A-Za-z_]+)", line, flags=re.IGNORECASE)
            if match is not None:
                status = match.group(1)
            continue
        if line == "":
            continue
        body_lines.append(line)
    return "\n".join(body_lines), status


def _canonical_symbol(name: str) -> str:
    if name == "$true":
        return "TRUE"
    if name == "$false":
        return "FALSE"
    return name


@dataclass
class _Tokens:
    values: list[str]
    pos: int = 0

    def peek(self) -> str | None:
        if self.pos >= len(self.values):
            return None
        return self.values[self.pos]

    def pop(self, expected: str | None = None) -> str:
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of TPTP formula")
        if expected is not None and tok != expected:
            raise ValueError("Expected '" + expected + "' but found '" + tok + "'")
        self.pos = self.pos + 1
        return tok


def _tokenize_formula(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            i = i + 1
            continue

        if i + 2 < n and text[i : i + 3] == "<=>":
            tokens.append("<=>")
            i = i + 3
            continue

        if i + 1 < n and text[i : i + 2] == "=>":
            tokens.append("=>")
            i = i + 2
            continue

        if ch in "(),[]:~&|!?":
            tokens.append(ch)
            i = i + 1
            continue

        if ch.isalnum() or ch in "_$":
            start = i
            i = i + 1
            while i < n and (text[i].isalnum() or text[i] in "_$"):
                i = i + 1
            tokens.append(text[start:i])
            continue

        raise ValueError("Invalid TPTP token near: '" + text[i:].strip() + "'")

    return tokens


class _TptpParser:
    def __init__(self, text: str):
        self.ts = _Tokens(_tokenize_formula(text))
        self.var_map: dict[str, str] = {}

    def parse(self) -> Formula:
        out = self.parse_iff()
        if self.ts.peek() is not None:
            raise ValueError("Unexpected token in TPTP formula: " + str(self.ts.peek()))
        return out

    def parse_iff(self) -> Formula:
        left = self.parse_implies()
        while self.ts.peek() == "<=>":
            self.ts.pop("<=>")
            right = self.parse_implies()
            left = Formula.binary("iff", left, right)
        return left

    def parse_implies(self) -> Formula:
        left = self.parse_or()
        while self.ts.peek() == "=>":
            self.ts.pop("=>")
            right = self.parse_or()
            left = Formula.binary("implies", left, right)
        return left

    def parse_or(self) -> Formula:
        left = self.parse_and()
        while self.ts.peek() == "|":
            self.ts.pop("|")
            right = self.parse_and()
            left = Formula.binary("or", left, right)
        return left

    def parse_and(self) -> Formula:
        left = self.parse_unary()
        while self.ts.peek() == "&":
            self.ts.pop("&")
            right = self.parse_unary()
            left = Formula.binary("and", left, right)
        return left

    def parse_unary(self) -> Formula:
        tok = self.ts.peek()
        if tok == "~":
            self.ts.pop("~")
            return Formula.neg(self.parse_unary())

        if tok == "!" or tok == "?":
            return self.parse_quantified()

        if tok == "(":
            self.ts.pop("(")
            inner = self.parse_iff()
            self.ts.pop(")")
            return inner

        return Formula.atom_formula(self.parse_atom())

    def parse_quantified(self) -> Formula:
        quant_tok = self.ts.pop()
        quant = "forall" if quant_tok == "!" else "exists"
        self.ts.pop("[")
        tptp_vars: list[str] = []
        tptp_vars.append(self.ts.pop())
        while self.ts.peek() == ",":
            self.ts.pop(",")
            tptp_vars.append(self.ts.pop())
        self.ts.pop("]")
        self.ts.pop(":")

        old = dict(self.var_map)
        internal_vars: list[str] = []
        for tptp_var in tptp_vars:
            internal = tptp_var.lower()
            self.var_map[tptp_var] = internal
            internal_vars.append(internal)

        inner = self.parse_unary()
        self.var_map = old

        result = inner
        for internal in reversed(internal_vars):
            result = Formula.quant(quant, internal, result)
        return result

    def parse_atom(self) -> Atom:
        pred = _canonical_symbol(self.ts.pop())
        if self.ts.peek() != "(":
            return Atom(pred, ())

        self.ts.pop("(")
        args: list[Term] = []
        if self.ts.peek() != ")":
            args.append(self.parse_term())
            while self.ts.peek() == ",":
                self.ts.pop(",")
                args.append(self.parse_term())
        self.ts.pop(")")
        return Atom(pred, tuple(args))

    def parse_term(self) -> Term:
        raw = self.ts.pop()
        if raw in self.var_map:
            name = self.var_map[raw]
        elif raw and raw[0].isalpha() and raw[0].islower():
            # Keep constants from TPTP distinct from variables in the internal model.
            name = "C_" + raw
        else:
            name = raw

        name = _canonical_symbol(name)

        if self.ts.peek() != "(":
            return Term(name, ())

        self.ts.pop("(")
        args: list[Term] = []
        if self.ts.peek() != ")":
            args.append(self.parse_term())
            while self.ts.peek() == ",":
                self.ts.pop(",")
                args.append(self.parse_term())
        self.ts.pop(")")
        return Term(name, tuple(args))


def parse_tptp_formula(formula_text: str) -> Formula:
    return _TptpParser(formula_text).parse()


def _iter_fof_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        start = text.find("fof(", i)
        if start < 0:
            break
        j = start + 4
        depth = 1
        while j < n and depth > 0:
            ch = text[j]
            if ch == "(":
                depth = depth + 1
            elif ch == ")":
                depth = depth - 1
            j = j + 1

        if depth != 0:
            raise ValueError("Malformed TPTP input: unbalanced parentheses")
        if j >= n or text[j] != ".":
            raise ValueError("Malformed TPTP input: expected '.' after fof(...) block")

        blocks.append(text[start : j + 1])
        i = j + 1

    return blocks


def parse_tptp_problem(text: str, fallback_name: str) -> dict:
    body, status = _strip_comments(text)
    blocks = _iter_fof_blocks(body)

    axioms: list[Formula] = []
    query: Formula | None = None
    problem_name = fallback_name

    for block in blocks:
        inside = block[len("fof(") : -2].strip()
        parts = _split_top_level(inside, ",", maxsplit=2)
        if len(parts) != 3:
            raise ValueError("Invalid fof entry: " + block)

        _name_part, role_part, formula_part = parts

        role = role_part.strip().lower()
        formula = parse_tptp_formula(formula_part.strip())

        if role in {"axiom", "hypothesis", "assumption", "lemma", "theorem", "plain"}:
            axioms.append(formula)
        elif role == "conjecture":
            query = formula

    if query is None:
        raise ValueError("TPTP problem must include one 'conjecture' formula")

    expected = True
    if status is not None:
        normalized = status.lower()
        if normalized in {"countersatisfiable", "satisfiable"}:
            expected = False
        elif normalized in {"theorem", "unsatisfiable", "contradictoryaxioms"}:
            expected = True

    return {
        "name": problem_name,
        "axioms": axioms,
        "query": query,
        "expected": expected,
    }
from __future__ import annotations

from .logic import Atom, Formula, Term


class TokenStream:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def pop(self, expected=None):
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of input")
        if expected is not None and tok != expected:
            raise ValueError("Expected '" + expected + "' but found '" + tok + "'")
        self.pos = self.pos + 1
        return tok


def _is_ident_start(ch: str) -> bool:
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"


def _is_ident_char(ch: str) -> bool:
    return _is_ident_start(ch) or ("0" <= ch <= "9")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if ch in " \t\r\n":
            i = i + 1
            continue

        if i + 2 < n and text[i : i + 3] == "<->":
            tokens.append("<->")
            i = i + 3
            continue

        if i + 1 < n and text[i : i + 2] == "->":
            tokens.append("->")
            i = i + 2
            continue

        if ch in "(),.~&|":
            tokens.append(ch)
            i = i + 1
            continue

        if _is_ident_start(ch):
            start = i
            i = i + 1
            while i < n and _is_ident_char(text[i]):
                i = i + 1
            tokens.append(text[start:i])
            continue

        raise ValueError("Invalid token near: '" + text[i:].strip() + "'")

    return tokens


class Parser:
    def __init__(self, tokens: list[str]):
        self.ts = TokenStream(tokens)

    def parse_formula(self) -> Formula:
        expr = self.parse_iff()
        if self.ts.peek() is not None:
            raise ValueError("Unexpected token: " + str(self.ts.peek()))
        return expr

    def parse_iff(self) -> Formula:
        left = self.parse_implies()
        while self.ts.peek() == "<->":
            self.ts.pop("<->")
            right = self.parse_implies()
            left = Formula.binary("iff", left, right)
        return left

    def parse_implies(self) -> Formula:
        left = self.parse_or()
        while self.ts.peek() == "->":
            self.ts.pop("->")
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

        if tok == "forall" or tok == "exists":
            quant = self.ts.pop()
            var = self.ts.pop()
            self.ts.pop(".")
            inner = self.parse_unary()
            return Formula.quant(quant, var, inner)

        if tok == "(":
            self.ts.pop("(")
            inner = self.parse_iff()
            self.ts.pop(")")
            return inner

        return Formula.atom_formula(self.parse_atom())

    def parse_atom(self) -> Atom:
        name = self.ts.pop()
        if self.ts.peek() != "(":
            return Atom(name, ())

        self.ts.pop("(")
        args: list[Term] = []

        if self.ts.peek() != ")":
            args.append(self.parse_term())
            while self.ts.peek() == ",":
                self.ts.pop(",")
                args.append(self.parse_term())

        self.ts.pop(")")
        return Atom(name, tuple(args))

    def parse_term(self) -> Term:
        name = self.ts.pop()
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


def parse_formula(text: str) -> Formula:
    parser = Parser(tokenize(text))
    return parser.parse_formula()


def load_formula_lines(path: str) -> list[Formula]:
    formulas: list[Formula] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line == "":
                continue
            if line.startswith("#"):
                continue
            formulas.append(parse_formula(line))
    return formulas

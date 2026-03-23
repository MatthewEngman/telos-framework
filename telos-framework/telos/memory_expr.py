"""
Separately scoped safe evaluator for memory ``update`` strings (scalar floats only).

Allows ``+ - *``, parentheses, identifiers resolved from a float env, and whitelisted
callables ``max(...)`` and ``min(...)`` with comma-separated arguments. Arguments are passed to
the builtins as a single list (``max([a, b, ...])``) so a one-argument ``max((x))`` stays valid
under Python 3 rules. No ``eval``.
**Division is intentionally omitted** until a real manifest needs it (smaller grammar,
easier review). Parenthesis nesting is capped (``telos.expr_limits``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Sequence

from .expr_limits import DEFAULT_MAX_PAREN_NESTING_DEPTH

Scalar = float


class MemoryExpressionError(ValueError):
    """Invalid syntax or unsupported call in a memory update expression."""


_ALLOWED_CALLS: dict[str, Callable[..., Scalar]] = {
    "max": max,
    "min": min,
}


@dataclass
class _Tok:
    kind: str
    value: Any = None


def _tokenize(source: str) -> List[_Tok]:
    s = source.strip()
    i = 0
    n = len(s)
    out: List[_Tok] = []
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "+-*(),":
            out.append(_Tok(c))
            i += 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and s[i + 1].isdigit()):
            j = i + 1
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            lex = s[i:j]
            try:
                num = float(lex)
            except ValueError as exc:
                raise MemoryExpressionError(
                    f"Invalid numeric literal {lex!r} at column {i}"
                ) from exc
            out.append(_Tok("NUM", num))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            out.append(_Tok("IDENT", s[i:j]))
            i = j
            continue
        raise MemoryExpressionError(f"Unexpected character {c!r} at column {i}")
    out.append(_Tok("EOF"))
    return out


class _MemoryParser:
    def __init__(self, tokens: Sequence[_Tok], env: dict[str, Scalar]) -> None:
        self.toks = list(tokens)
        self.pos = 0
        self.env = env
        self._paren_depth = 0

    def _push_paren(self) -> None:
        if self._paren_depth >= DEFAULT_MAX_PAREN_NESTING_DEPTH:
            raise MemoryExpressionError(
                "Expression nesting exceeds maximum depth "
                f"({DEFAULT_MAX_PAREN_NESTING_DEPTH})"
            )
        self._paren_depth += 1

    def _pop_paren(self) -> None:
        self._paren_depth -= 1

    def _peek(self) -> _Tok:
        return self.toks[self.pos]

    def _eat(self, kind: str | None = None) -> _Tok:
        t = self.toks[self.pos]
        if kind is not None and t.kind != kind:
            raise MemoryExpressionError(
                f"Expected {kind!r}, got {t.kind!r} (value={t.value!r})"
            )
        self.pos += 1
        return t

    def parse(self) -> Scalar:
        v = self._parse_expr()
        if self._peek().kind != "EOF":
            raise MemoryExpressionError(
                f"Trailing input after expression: {self._peek().kind!r}"
            )
        return float(v)

    def _parse_expr(self) -> Scalar:
        left = self._parse_term()
        while self._peek().kind in ("+", "-"):
            op = self._eat().kind
            right = self._parse_term()
            left = float(left + right if op == "+" else left - right)
        return float(left)

    def _parse_term(self) -> Scalar:
        left = self._parse_unary()
        while self._peek().kind == "*":
            self._eat("*")
            right = self._parse_unary()
            left = float(left * right)
        return float(left)

    def _parse_unary(self) -> Scalar:
        if self._peek().kind == "-":
            self._eat("-")
            return float(-self._parse_unary())
        if self._peek().kind == "+":
            self._eat("+")
            return float(self._parse_unary())
        return float(self._parse_primary())

    def _parse_primary(self) -> Scalar:
        t = self._peek()
        if t.kind == "NUM":
            return float(self._eat("NUM").value)
        if t.kind == "IDENT":
            name = self._eat("IDENT").value
            if self._peek().kind == "(":
                return float(self._parse_call(name))
            if name not in self.env:
                raise MemoryExpressionError(f"Unknown name {name!r} in memory expression")
            return float(self.env[name])
        if t.kind == "(":
            self._push_paren()
            try:
                self._eat("(")
                inner = self._parse_expr()
                self._eat(")")
            finally:
                self._pop_paren()
            return float(inner)
        raise MemoryExpressionError(f"Unexpected token {t.kind!r}")

    def _parse_call(self, name: str) -> Scalar:
        if name not in _ALLOWED_CALLS:
            raise MemoryExpressionError(
                f"Call {name!r} is not allowed in memory expressions (only max, min)"
            )
        self._push_paren()
        try:
            self._eat("(")
            args: List[Scalar] = []
            if self._peek().kind != ")":
                args.append(self._parse_expr())
                while self._peek().kind == ",":
                    self._eat(",")
                    args.append(self._parse_expr())
            self._eat(")")
        finally:
            self._pop_paren()
        fn = _ALLOWED_CALLS[name]
        if not args:
            raise MemoryExpressionError(f"Call {name!r} requires at least one argument")
        # max(*[x]) becomes max(x), which in Python 3 is invalid (x is not iterable).
        return float(fn(args))


def eval_memory_update(source: str, env: dict[str, Scalar]) -> Scalar:
    """Evaluate a memory ``update`` string; all names must resolve to floats."""
    if not source or not source.strip():
        raise MemoryExpressionError("Empty memory expression")
    toks = _tokenize(source)
    return _MemoryParser(toks, env).parse()

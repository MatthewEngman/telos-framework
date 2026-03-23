"""
Safe linear expression engine for MILP objectives and invariants (PuLP).

**Invariant:** every accepted expression is **linear with respect to decision
variables** (ontology variables mapped to ``LpVariable``): no products of two
decision-bearing subexpressions, and ``/`` only when the denominator subtree is
free of decision variables (so it is a compile-time constant multiplier).

Grammar: numbers, identifiers, ``+``, ``-``, ``*``, ``/``, parentheses. No ``eval``.
Parenthesis nesting is capped (see ``telos.expr_limits``) so parse cost and stack depth stay bounded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple, Union

import pulp

from .expr_limits import DEFAULT_MAX_PAREN_NESTING_DEPTH

Number = Union[int, float]
Expr = Union[Number, pulp.LpAffineExpression, pulp.LpVariable]

_DENOM_EPS = 1e-12


class LinearMilpExpressionError(ValueError):
    """Invalid syntax or non-linear expression for MILP."""


@dataclass
class _Tok:
    kind: str
    value: Any = None


def _is_pulp_affine(x: Any) -> bool:
    return isinstance(x, (pulp.LpVariable, pulp.LpAffineExpression))


def _uses_decision_variables(expr: Expr) -> bool:
    return _is_pulp_affine(expr)


def _tokenize(source: str) -> List[_Tok]:
    s = source.strip()
    i = 0
    out: List[_Tok] = []
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "+-*/()":
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
                raise LinearMilpExpressionError(
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
        raise LinearMilpExpressionError(f"Unexpected character {c!r} at column {i}")
    out.append(_Tok("EOF"))
    return out


def _as_constant_float(x: Expr) -> float:
    if isinstance(x, bool):  # bool is int subclass
        raise LinearMilpExpressionError("Invalid constant type")
    if isinstance(x, (int, float)):
        return float(x)
    raise LinearMilpExpressionError(
        "Division denominator must reduce to a numeric constant (no decision variables)"
    )


def _mul_linear(a: Expr, b: Expr) -> Expr:
    pa, pb = _is_pulp_affine(a), _is_pulp_affine(b)
    if pa and pb:
        raise LinearMilpExpressionError(
            "Non-linear expression: product of two decision-related terms is not allowed"
        )
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) * float(b)
    if isinstance(a, (int, float)):
        return float(a) * b  # type: ignore[operator]
    if isinstance(b, (int, float)):
        return a * float(b)  # type: ignore[operator]
    raise LinearMilpExpressionError("Unsupported multiplication operands")


def _mul_linear_pair(a: Expr, ad: bool, b: Expr, bd: bool) -> Tuple[Expr, bool]:
    if ad and bd:
        raise LinearMilpExpressionError(
            "Non-linear expression: product of two decision-related terms is not allowed"
        )
    return _mul_linear(a, b), (ad or bd)


def _div_linear_pair(a: Expr, ad: bool, b: Expr, bd: bool) -> Tuple[Expr, bool]:
    if bd:
        raise LinearMilpExpressionError(
            "Division denominator must not depend on decision variables "
            "(must be constant w.r.t. solver variables)"
        )
    denom = _as_constant_float(b)
    if abs(denom) < _DENOM_EPS:
        raise LinearMilpExpressionError("Division by zero or near-zero denominator")
    inv = 1.0 / denom
    if not ad:
        return float(a) * inv, False
    return a * inv, True  # type: ignore[operator]


def _neg_linear(x: Expr) -> Expr:
    if isinstance(x, (int, float)):
        return -float(x)
    return -x  # type: ignore[operator]


class _LinearParser:
    def __init__(self, tokens: Sequence[_Tok], env: dict[str, Any]) -> None:
        self.toks = list(tokens)
        self.pos = 0
        self.env = env
        self._paren_depth = 0

    def _push_paren(self) -> None:
        if self._paren_depth >= DEFAULT_MAX_PAREN_NESTING_DEPTH:
            raise LinearMilpExpressionError(
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
            raise LinearMilpExpressionError(
                f"Expected {kind!r}, got {t.kind!r} (value={t.value!r})"
            )
        self.pos += 1
        return t

    def parse(self) -> Expr:
        e, _ = self._parse_expr()
        if self._peek().kind != "EOF":
            raise LinearMilpExpressionError(
                f"Trailing input after expression: {self._peek().kind!r}"
            )
        return e

    def _parse_expr(self) -> Tuple[Expr, bool]:
        left, ld = self._parse_term()
        while self._peek().kind in ("+", "-"):
            op = self._eat().kind
            right, rd = self._parse_term()
            if op == "+":
                left = left + right  # type: ignore[operator]
            else:
                left = left - right  # type: ignore[operator]
            ld = ld or rd
        return left, ld

    def _parse_term(self) -> Tuple[Expr, bool]:
        left, ld = self._parse_factor()
        while self._peek().kind in ("*", "/"):
            op = self._eat().kind
            right, rd = self._parse_factor()
            if op == "*":
                left, ld = _mul_linear_pair(left, ld, right, rd)
            else:
                left, ld = _div_linear_pair(left, ld, right, rd)
        return left, ld

    def _parse_factor(self) -> Tuple[Expr, bool]:
        if self._peek().kind == "-":
            self._eat("-")
            e, d = self._parse_factor()
            return _neg_linear(e), d
        if self._peek().kind == "+":
            self._eat("+")
            return self._parse_factor()
        if self._peek().kind == "NUM":
            return float(self._eat("NUM").value), False
        if self._peek().kind == "IDENT":
            name = self._eat("IDENT").value
            if name not in self.env:
                raise LinearMilpExpressionError(f"Unknown name {name!r} in expression")
            val = self.env[name]
            return val, _uses_decision_variables(val)  # type: ignore[arg-type]
        if self._peek().kind == "(":
            self._push_paren()
            try:
                self._eat("(")
                inner, inner_d = self._parse_expr()
                self._eat(")")
            finally:
                self._pop_paren()
            return inner, inner_d
        raise LinearMilpExpressionError(
            f"Unexpected token {self._peek().kind!r} in expression"
        )


def parse_linear_milp_expression(source: str, env: dict[str, Any]) -> Expr:
    """
    Parse ``source``; resolve identifiers from ``env`` (``float`` or PuLP symbols).

    **Linearity:** at most one factor in each multiplication may depend on decision
    variables; each divisor must be decision-free and non-zero (see module docstring).
    """
    if not source or not source.strip():
        raise LinearMilpExpressionError("Empty expression")
    toks = _tokenize(source)
    return _LinearParser(toks, env).parse()

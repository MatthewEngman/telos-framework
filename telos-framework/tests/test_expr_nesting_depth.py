"""Parenthesis nesting depth caps (linear_milp + memory_expr)."""

from __future__ import annotations

import pytest

from telos.expr_limits import DEFAULT_MAX_PAREN_NESTING_DEPTH
from telos.linear_milp import LinearMilpExpressionError, parse_linear_milp_expression
from telos.memory_expr import MemoryExpressionError, eval_memory_update


def _nested_parens_around_one(n: int) -> str:
    return "(" * n + "1" + ")" * n


def test_linear_milp_accepts_nesting_at_limit() -> None:
    n = DEFAULT_MAX_PAREN_NESTING_DEPTH
    s = _nested_parens_around_one(n)
    e = parse_linear_milp_expression(s, {})
    assert isinstance(e, float) and e == 1.0


def test_linear_milp_rejects_nesting_over_limit() -> None:
    n = DEFAULT_MAX_PAREN_NESTING_DEPTH + 1
    s = _nested_parens_around_one(n)
    with pytest.raises(LinearMilpExpressionError, match="nesting exceeds maximum depth"):
        parse_linear_milp_expression(s, {})


def test_memory_expr_accepts_nesting_at_limit() -> None:
    n = DEFAULT_MAX_PAREN_NESTING_DEPTH
    s = _nested_parens_around_one(n)
    assert eval_memory_update(s, {}) == 1.0


def test_memory_expr_rejects_nesting_over_limit() -> None:
    n = DEFAULT_MAX_PAREN_NESTING_DEPTH + 1
    s = _nested_parens_around_one(n)
    with pytest.raises(MemoryExpressionError, match="nesting exceeds maximum depth"):
        eval_memory_update(s, {})


def test_memory_expr_call_parens_count_toward_limit() -> None:
    # ``max(`` + (MAX-1) grouping opens around 0.0 ⇒ depth reaches MAX, still valid.
    inner_n = DEFAULT_MAX_PAREN_NESTING_DEPTH - 1
    inner = "(" * inner_n + "0.0" + ")" * inner_n
    src = "max(" + inner + ")"
    assert eval_memory_update(src, {}) == 0.0

"""Safe scalar memory update evaluator."""

from __future__ import annotations

import pytest

from telos.memory_expr import MemoryExpressionError, eval_memory_update


def test_max_single_argument_parenthesized() -> None:
    """``max(*[x])`` would call ``max(x)``, which is invalid in Python 3; parser uses ``max([x])``."""
    assert eval_memory_update("max((0.0))", {}) == 0.0
    assert eval_memory_update("max(0.0)", {}) == 0.0


def test_infrastructure_style_heat_update() -> None:
    env = {"heat_us": 5.0, "load_us": 0.7, "dt": 0.05}
    src = "max(0.0, min(40.0, heat_us + (load_us - 0.6) * 15.0 * dt))"
    v = eval_memory_update(src, env)
    assert 0.0 <= v <= 40.0


def test_disallowed_call_raises() -> None:
    with pytest.raises(MemoryExpressionError, match="not allowed"):
        eval_memory_update("abs(-1)", {})


def test_unknown_identifier_raises() -> None:
    with pytest.raises(MemoryExpressionError, match="Unknown name"):
        eval_memory_update("foo + 1", {})


def test_invalid_numeric_literal_is_domain_error() -> None:
    with pytest.raises(MemoryExpressionError, match="Invalid numeric"):
        eval_memory_update("0..", {"x": 1.0})

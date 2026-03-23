"""
Property/fuzz tests: malformed input must not crash; each sample stays within a time budget.

Install dev extras: ``pip install -e ".[dev]"`` (includes Hypothesis).
"""

from __future__ import annotations

import pytest

pytest.importorskip("hypothesis", reason='install dev extras: pip install -e ".[dev]"')

import pulp

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from telos.linear_milp import LinearMilpExpressionError, parse_linear_milp_expression
from telos.memory_expr import MemoryExpressionError, eval_memory_update

_FUZZ_ENV_LINEAR = {
    "x": pulp.LpVariable("x", lowBound=0, upBound=10),
    "y": pulp.LpVariable("y", lowBound=0, upBound=10),
    "a": 2.5,
    "b": -1.0,
    "k": 0.25,
    "cap_us": 1.0,
}

_FUZZ_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789+-*/()._ \t",
    min_size=0,
    max_size=96,
)


@settings(
    max_examples=120,
    deadline=900,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(_FUZZ_TEXT)
def test_fuzz_linear_milp_no_crash_bounded(s: str) -> None:
    try:
        parse_linear_milp_expression(s, _FUZZ_ENV_LINEAR)
    except LinearMilpExpressionError:
        pass


@settings(
    max_examples=120,
    deadline=900,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(_FUZZ_TEXT)
def test_fuzz_memory_expr_no_crash_bounded(s: str) -> None:
    mem_env = {"x": 0.5, "y": 0.3, "heat_us": 1.0, "dt": 0.05}
    try:
        eval_memory_update(s, mem_env)
    except MemoryExpressionError:
        pass

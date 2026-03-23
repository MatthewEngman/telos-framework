"""Safe linear MILP expression parser."""

from __future__ import annotations

import pulp
import pytest

import telos.linear_milp as linear_milp_module
from telos.compiler import TelosCompiler
from telos.linear_milp import LinearMilpExpressionError, parse_linear_milp_expression
from telos.models import TelosSchema


def test_module_documents_linearity_invariant() -> None:
    assert linear_milp_module.__doc__ is not None
    assert "linear with respect to decision" in linear_milp_module.__doc__


def test_parse_linear_product_float_and_var() -> None:
    x = pulp.LpVariable("x", lowBound=0, upBound=1)
    env = {"x": x, "k": 3.0}
    e = parse_linear_milp_expression("k * x + 0.5", env)
    assert isinstance(e, pulp.LpAffineExpression)


def test_parse_rejects_var_times_var() -> None:
    x = pulp.LpVariable("x", lowBound=0, upBound=1)
    y = pulp.LpVariable("y", lowBound=0, upBound=1)
    with pytest.raises(LinearMilpExpressionError, match="Non-linear"):
        parse_linear_milp_expression("x * y", {"x": x, "y": y})


def test_compiler_wraps_parse_error_in_valueerror() -> None:
    schema = TelosSchema.model_validate(
        {
            "ontology": {
                "variables": [
                    {"name": "x", "type": "float", "bounds": [0.0, 1.0]},
                    {"name": "y", "type": "float", "bounds": [0.0, 1.0]},
                ],
                "parameters": [],
            },
            "teleology": {"direction": "minimize", "objective": "x * y"},
            "invariants": [],
        }
    )
    with pytest.raises(ValueError, match="Invalid objective"):
        TelosCompiler.compile(schema, {})


def test_parse_unknown_name_raises() -> None:
    with pytest.raises(LinearMilpExpressionError, match="Unknown name"):
        parse_linear_milp_expression("z + 1", {"x": pulp.LpVariable("x")})


def test_division_by_constant_preserves_linearity() -> None:
    x = pulp.LpVariable("x", lowBound=0, upBound=1)
    env = {"x": x, "k": 4.0}
    e = parse_linear_milp_expression("(x + k) / 2.0", env)
    assert isinstance(e, pulp.LpAffineExpression)


def test_division_rejects_decision_in_denominator() -> None:
    x = pulp.LpVariable("x", lowBound=0.1, upBound=2)
    y = pulp.LpVariable("y", lowBound=0.1, upBound=2)
    with pytest.raises(LinearMilpExpressionError, match="denominator"):
        parse_linear_milp_expression("x / y", {"x": x, "y": y})
    with pytest.raises(LinearMilpExpressionError, match="denominator"):
        parse_linear_milp_expression("x / (y + 1.0)", {"x": x, "y": y})


def test_division_rejects_zero_denominator() -> None:
    x = pulp.LpVariable("x", lowBound=0, upBound=1)
    with pytest.raises(LinearMilpExpressionError, match="zero"):
        parse_linear_milp_expression("x / 0.0", {"x": x})


def test_invalid_numeric_literal_is_domain_error_not_valueerror() -> None:
    with pytest.raises(LinearMilpExpressionError, match="Invalid numeric"):
        parse_linear_milp_expression("0..", {"x": pulp.LpVariable("x")})

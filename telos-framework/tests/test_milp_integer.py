"""Integer MILP variables."""

from __future__ import annotations

from telos.compiler import TelosCompiler
from telos.models import TelosSchema


def test_integer_variable_round_trip() -> None:
    schema = TelosSchema.model_validate(
        {
            "ontology": {
                "variables": [{"name": "n", "type": "int", "bounds": [0, 5]}],
                "parameters": [],
            },
            "teleology": {"direction": "minimize", "objective": "n"},
            "invariants": [{"type": "ineq", "expression": "n - 3"}],
        }
    )
    out = TelosCompiler.compile(schema, {})
    assert out is not None
    assert out["n"] == 3.0

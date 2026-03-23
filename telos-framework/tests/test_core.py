"""Core MILP/parser/runtime/debugger smoke tests (no network, no Docker)."""

from __future__ import annotations

from pathlib import Path

from telos.compiler import TelosCompiler
from telos.debugger import LatentDebugger
from telos.models import TelosSchema
from telos.parser import TelosParser
from telos.runtime import TelosRuntime

ROOT = Path(__file__).resolve().parents[1]


def test_parser_loads_minimal_yaml() -> None:
    yaml = """
ontology:
  variables:
    - name: x
      type: float
      bounds: [0.0, 1.0]
  parameters: []
teleology:
  direction: minimize
  objective: "x"
invariants:
  - type: eq
    expression: "x - 0.5"
"""
    d = TelosParser.loads(yaml.strip(), silent=True)
    assert d["ontology"]["variables"][0]["name"] == "x"


def test_compiler_simple() -> None:
    schema = TelosSchema.model_validate(
        {
            "ontology": {
                "variables": [{"name": "x", "type": "float", "bounds": [0.0, 1.0]}],
                "parameters": [],
            },
            "teleology": {"direction": "minimize", "objective": "x"},
            "invariants": [{"type": "eq", "expression": "x - 0.25"}],
        }
    )
    out = TelosCompiler.compile(schema, {})
    assert out is not None
    assert abs(out["x"] - 0.25) < 1e-5


def test_runtime_tick_main() -> None:
    schema = TelosSchema.model_validate(
        {
            "ontology": {
                "variables": [{"name": "x", "type": "float", "bounds": [0.0, 1.0]}],
                "parameters": [],
            },
            "teleology": {"direction": "minimize", "objective": "x"},
            "invariants": [{"type": "eq", "expression": "x - 0.5"}],
        }
    )
    rt = TelosRuntime()
    r = rt.tick({"main": schema.model_dump()}, {})
    assert r["status"] == "HEALTHY"
    assert abs(r["state"]["x"] - 0.5) < 1e-5


def test_vulnerable_manifest_infeasible_with_low_cap() -> None:
    path = ROOT / "vulnerable.telos"
    schema = TelosSchema.model_validate(
        TelosParser.loads(path.read_text(encoding="utf-8"), silent=True)
    )
    assert LatentDebugger._is_feasible(schema, {"us_cap": 0.5}) is False


def test_vulnerable_deletion_filter_returns_constraints() -> None:
    path = ROOT / "vulnerable.telos"
    schema = TelosSchema.model_validate(
        TelosParser.loads(path.read_text(encoding="utf-8"), silent=True)
    )
    core = LatentDebugger._find_iis(schema, {"us_cap": 0.5})
    assert len(core) >= 1

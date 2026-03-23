"""LatentDebugger edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from telos.debugger import LatentDebugger
from telos.models import TelosSchema
from telos.parser import TelosParser

ROOT = Path(__file__).resolve().parents[1]


def test_simulate_skips_when_no_parameters(capsys: pytest.CaptureFixture[str]) -> None:
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
    assert LatentDebugger.simulate(schema, iterations=10) is True
    err = capsys.readouterr().out
    assert "No ontology.parameters to fuzz" in err


def test_infrastructure_file_stays_feasible_under_random_fuzz() -> None:
    path = ROOT / "infrastructure.telos"
    schema = TelosSchema.model_validate(
        TelosParser.loads(path.read_text(encoding="utf-8"), silent=True)
    )
    assert LatentDebugger.simulate(schema, iterations=30) is True

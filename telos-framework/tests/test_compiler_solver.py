"""MILP backend selection (CBC vs HiGHS) for Apple Silicon and overrides."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from telos.compiler import (
    TelosCompiler,
    build_milp_solver,
    resolve_milp_solver_name,
)
from telos.models import TelosSchema


def test_resolve_auto_is_cbc_on_non_darwin_arm64() -> None:
    with patch("telos.compiler.platform.system", return_value="Windows"):
        with patch("telos.compiler.platform.machine", return_value="AMD64"):
            assert resolve_milp_solver_name("auto") == "cbc"


def test_resolve_explicit_highs() -> None:
    with patch.dict("os.environ", {"TELOS_PULP_SOLVER": "cbc"}, clear=False):
        assert resolve_milp_solver_name("highs") == "highs"


def test_resolve_env_highs() -> None:
    with patch.dict("os.environ", {"TELOS_PULP_SOLVER": "highs"}, clear=False):
        assert resolve_milp_solver_name(None) == "highs"


def test_resolve_auto_darwin_arm64_prefers_highs_when_available() -> None:
    fake = MagicMock()
    fake.available.return_value = True
    with patch("telos.compiler.platform.system", return_value="Darwin"):
        with patch("telos.compiler.platform.machine", return_value="arm64"):
            with patch("telos.compiler.pulp.HiGHS", return_value=fake):
                assert resolve_milp_solver_name("auto") == "highs"


def test_resolve_auto_darwin_arm64_raises_without_highspy() -> None:
    fake = MagicMock()
    fake.available.return_value = False
    with patch("telos.compiler.platform.system", return_value="Darwin"):
        with patch("telos.compiler.platform.machine", return_value="arm64"):
            with patch("telos.compiler.pulp.HiGHS", return_value=fake):
                with pytest.raises(RuntimeError, match="Apple Silicon"):
                    resolve_milp_solver_name("auto")


def test_build_highs_raises_when_unavailable() -> None:
    fake = MagicMock()
    fake.available.return_value = False
    with patch("telos.compiler.pulp.HiGHS", return_value=fake):
        with pytest.raises(RuntimeError, match="highspy"):
            build_milp_solver("highs")


def test_compile_solver_cbc_override_on_arm64() -> None:
    """Passing solver='cbc' must not require highspy (e.g. Rosetta x86_64 Python)."""
    fake = MagicMock()
    fake.available.return_value = False
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
    with patch("telos.compiler.platform.system", return_value="Darwin"):
        with patch("telos.compiler.platform.machine", return_value="arm64"):
            with patch("telos.compiler.pulp.HiGHS", return_value=fake):
                out = TelosCompiler.compile(schema, {}, solver="cbc")
    assert out is not None
    assert abs(out["x"] - 0.25) < 1e-5

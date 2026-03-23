"""telos.experimental.tir re-exports stable TIR symbols."""

from __future__ import annotations

from telos.experimental.tir import TIRSchema, TelosAgent, TelosCompiler


def test_experimental_tir_imports() -> None:
    assert TIRSchema.__name__ == "TIRSchema"
    assert TelosAgent.__name__ == "TelosAgent"
    assert TelosCompiler.__name__ == "TelosCompiler"

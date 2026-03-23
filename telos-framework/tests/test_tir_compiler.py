"""SciPy TIR path (CLI / agent stack)."""

from __future__ import annotations

from telos.schema import Invariant, Ontology, Teleology, TIRSchema
from telos.tir_compiler import TelosCompiler


def test_tir_compiler_minimize_simple() -> None:
    tir = TIRSchema(
        ontology=Ontology(
            variables=["x"],
            bounds=[(0.0, 1.0)],
            parameters=[],
        ),
        teleology=Teleology(direction="minimize", objective="x"),
        invariants=[Invariant(type="eq", expression="x - 0.35")],
    )
    compiler = TelosCompiler(tir)
    out = compiler.compile(verbose=False)
    assert abs(out["x"] - 0.35) < 1e-2


def test_tir_compiler_maximize_with_ineq() -> None:
    tir = TIRSchema(
        ontology=Ontology(
            variables=["a", "b"],
            bounds=[(0.0, 1.0), (0.0, 1.0)],
            parameters=[],
        ),
        teleology=Teleology(direction="maximize", objective="a + 2*b"),
        invariants=[
            Invariant(type="eq", expression="a + b - 1.0"),
            Invariant(type="ineq", expression="a - 0.3"),
        ],
    )
    compiler = TelosCompiler(tir)
    out = compiler.compile(verbose=False)
    assert abs(out["a"] + out["b"] - 1.0) < 1e-2
    assert out["a"] >= 0.3 - 1e-2

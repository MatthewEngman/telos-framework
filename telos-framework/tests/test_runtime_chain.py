"""Canvas-style router -> hardware chained tick."""

from __future__ import annotations

from telos.runtime import TelosRuntime


def test_runtime_router_then_hardware() -> None:
    router = {
        "ontology": {
            "variables": [{"name": "load_s1", "type": "float", "bounds": [0.0, 1.0]}],
            "parameters": [],
        },
        "memory": [],
        "teleology": {"direction": "minimize", "objective": "load_s1"},
        "invariants": [{"type": "eq", "expression": "load_s1 - 1.0"}],
    }
    hardware = {
        "ontology": {
            "variables": [{"name": "shards_s1", "type": "int", "bounds": [0, 20]}],
            "parameters": [],
        },
        "teleology": {"direction": "minimize", "objective": "shards_s1"},
        "invariants": [{"type": "ineq", "expression": "shards_s1 - (load_s1 * 10)"}],
    }
    rt = TelosRuntime()
    r = rt.tick({"router": router, "hardware": hardware}, {})
    assert r["status"] == "HEALTHY"
    assert abs(r["router"]["load_s1"] - 1.0) < 1e-5
    assert r["db"]["shards_s1"] >= 10.0

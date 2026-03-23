"""Parse + one healthy tick per file in examples/*.telos."""

from __future__ import annotations

from pathlib import Path

import pytest

from telos.parser import TelosParser
from telos.runtime import TelosRuntime

ROOT = Path(__file__).resolve().parents[1]

_EXAMPLE_PARAMS: dict[str, dict[str, float]] = {
    "energy_dispatch.telos": {
        "demand_mw": 100.0,
        "clean_cap_mw": 70.0,
        "marginal_cost_clean": 10.0,
        "marginal_cost_dirty": 80.0,
    },
    "inventory_split.telos": {
        "order_units": 1000.0,
        "cap_a": 300.0,
        "cap_b": 800.0,
        "unit_cost_a": 5.0,
        "unit_cost_b": 8.0,
    },
    "k8s_replica_plan.telos": {
        "required_rps": 100.0,
        "rps_per_web_pod": 40.0,
        "rps_per_worker_pod": 30.0,
    },
    "manufacturing_mix.telos": {
        "margin_alpha": 20.0,
        "margin_beta": 15.0,
        "hours_per_alpha": 2.0,
        "hours_per_beta": 1.0,
        "machine_hours_available": 400.0,
    },
    "router_minimal.telos": {
        "east_latency_weight": 5.0,
        "west_latency_weight": 1.0,
    },
}


@pytest.mark.parametrize(
    "name",
    sorted(_EXAMPLE_PARAMS.keys()),
)
def test_example_manifest_ticks_healthy(name: str) -> None:
    path = ROOT / "examples" / name
    assert path.is_file(), f"missing {path}"
    data = TelosParser.loads(path.read_text(encoding="utf-8"), silent=True)
    rt = TelosRuntime()
    r = rt.tick({"main": data}, _EXAMPLE_PARAMS[name])
    assert r["status"] == "HEALTHY"

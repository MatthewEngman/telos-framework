"""
Corpus tests: every objective / invariant / memory expression in checked-in manifests
must parse with the safe engines (backward compatibility).
"""

from __future__ import annotations

from pathlib import Path

import pulp
import pytest

from telos.linear_milp import parse_linear_milp_expression
from telos.memory_expr import eval_memory_update
from telos.parser import TelosParser
from telos.probe_defaults import default_probe_parameters

ROOT = Path(__file__).resolve().parents[1]

_TELOS_FILES = (
    sorted((ROOT / "examples").glob("*.telos"))
    + sorted((ROOT / "templates").glob("*.telos"))
    + [
        ROOT / "infrastructure.telos",
        ROOT / "vulnerable.telos",
        ROOT / "hedge_fund.telos",
    ]
)


def _milp_env_for_manifest(data: dict) -> dict:
    lp: dict = {}
    for v in data["ontology"]["variables"]:
        lo, hi = v["bounds"]
        cat = pulp.LpInteger if v.get("type") == "int" else pulp.LpContinuous
        lp[v["name"]] = pulp.LpVariable(v["name"], lowBound=lo, upBound=hi, cat=cat)
    params = default_probe_parameters(data)
    mem_constants = {str(m["name"]): float(m["init"]) for m in (data.get("memory") or [])}
    return {**lp, **params, **mem_constants}


def _memory_env_for_manifest(data: dict) -> dict[str, float]:
    env: dict[str, float] = {"dt": 0.05}
    for v in data["ontology"]["variables"]:
        env[v["name"]] = 0.5
    for m in data.get("memory") or []:
        env[str(m["name"])] = float(m["init"])
    return env


@pytest.mark.parametrize("path", _TELOS_FILES, ids=lambda p: p.name)
def test_corpus_milp_expressions_parse(path: Path) -> None:
    assert path.is_file(), path
    raw = path.read_text(encoding="utf-8")
    data = TelosParser.loads(raw, silent=True)
    env = _milp_env_for_manifest(data)
    obj = data["teleology"]["objective"]
    parse_linear_milp_expression(str(obj).strip(), env)
    for inv in data.get("invariants") or []:
        parse_linear_milp_expression(str(inv["expression"]).strip(), env)


def test_corpus_memory_updates_parse() -> None:
    """Only manifests that define ``memory`` are exercised (today: infrastructure.telos)."""
    for path in _TELOS_FILES:
        assert path.is_file(), path
        raw = path.read_text(encoding="utf-8")
        data = TelosParser.loads(raw, silent=True)
        mem = data.get("memory") or []
        if not mem:
            continue
        env = _memory_env_for_manifest(data)
        for m in mem:
            env[str(m["name"])] = float(eval_memory_update(str(m["update"]), env))

"""Actuator units (no Docker / K8s)."""

from __future__ import annotations

from telos.actuators.fintech import FinTechActuator


def test_fintech_actuator_logs_targets(capsys) -> None:
    ft = FinTechActuator(initial_cash=50_000.0)
    ft.on_update({"shares_AAPL": 100.0, "shares_TSLA": 0.0})
    ft.on_update({"shares_AAPL": 100.0, "shares_TSLA": 50.0})
    out = capsys.readouterr().out
    assert "BUY" in out
    assert "AAPL" in out or "TSLA" in out

"""End-to-end ticks on checked-in .telos samples."""

from __future__ import annotations

from pathlib import Path

from telos.parser import TelosParser
from telos.runtime import TelosRuntime

ROOT = Path(__file__).resolve().parents[1]


def test_infrastructure_tick_healthy() -> None:
    data = TelosParser.loads(
        (ROOT / "infrastructure.telos").read_text(encoding="utf-8"), silent=True
    )
    rt = TelosRuntime()
    r = rt.tick({"main": data}, {"us_cap": 1.0, "eu_cost": 20.0})
    assert r["status"] == "HEALTHY"
    assert "load_us" in r["state"] and "shards_us" in r["state"]


def test_hedge_fund_tick_healthy() -> None:
    data = TelosParser.loads(
        (ROOT / "hedge_fund.telos").read_text(encoding="utf-8"), silent=True
    )
    rt = TelosRuntime()
    params = {
        "price_aapl": 150.0,
        "price_tsla": 200.0,
        "yield_aapl": 0.05,
        "yield_tsla": 0.08,
    }
    r = rt.tick({"main": data}, params)
    assert r["status"] == "HEALTHY"
    assert r["state"]["cash_reserve"] >= 20000.0 - 1.0

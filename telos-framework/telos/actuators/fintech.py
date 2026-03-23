"""Demo portfolio actuator: log BUY/SELL from MILP targets shares_<TICKER>."""

from __future__ import annotations

from typing import Any, Dict

from .base import BaseActuator


class FinTechActuator(BaseActuator):
    """Paper-trading style side effects; not a real broker integration."""

    def __init__(self, initial_cash: float = 100_000.0) -> None:
        self.portfolio: Dict[str, float] = {}
        self.cash_balance = float(initial_cash)
        print(
            f"[FinTechActuator] Desk ready. Notional capital: ${self.cash_balance:,.2f}"
        )

    def on_update(self, optimal_state: Dict[str, Any]) -> None:
        if not optimal_state:
            return

        target = {
            k.replace("shares_", "", 1).upper(): float(v)
            for k, v in optimal_state.items()
            if k.startswith("shares_") and v is not None
        }

        for ticker, target_shares in target.items():
            current = float(self.portfolio.get(ticker, 0.0))
            if target_shares > current + 1e-9:
                print(
                    f"[FinTechActuator] BUY {target_shares - current:.4f} {ticker} "
                    f"(target {target_shares:.4f})"
                )
            elif target_shares < current - 1e-9:
                print(
                    f"[FinTechActuator] SELL {current - target_shares:.4f} {ticker} "
                    f"(target {target_shares:.4f})"
                )
            self.portfolio[ticker] = target_shares

"""Actuator protocol: map optimal state to physical or external systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseActuator(ABC):
    @abstractmethod
    def on_update(self, optimal_state: Dict[str, Any]) -> None:
        """Consume merged MILP outputs (e.g. load_*, shards_*) from one tick."""
        ...

"""MILP **runtime**: clock, memory, chained router→hardware solves, actuator broadcast."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .actuators.base import BaseActuator
from .compiler import TelosCompiler
from .memory_expr import MemoryExpressionError, eval_memory_update
from .models import TelosSchema

_SCHEMA_ORDER = ("router", "hardware")


def _schema_keys_in_order(schemas_dict: Dict[str, Any]) -> List[str]:
    """Canvas: router then hardware. Otherwise: all non-empty keys in insertion order."""
    canvas = [k for k in _SCHEMA_ORDER if schemas_dict.get(k)]
    if canvas:
        return canvas
    return [k for k, v in schemas_dict.items() if v]


class TelosRuntime:
    def __init__(self) -> None:
        self.actuators: List[BaseActuator] = []
        self.memory_state: Dict[str, float] = {}
        self.last_router_state: Dict[str, float] = {}
        self.last_tick = time.perf_counter()

    def attach_actuator(self, actuator: BaseActuator) -> None:
        self.actuators.append(actuator)

    def _step_clock(self) -> float:
        now = time.perf_counter()
        dt = min(max(now - self.last_tick, 0.0), 1.0)
        self.last_tick = now
        return float(dt)

    def _advance_memory(self, schema: TelosSchema, dt: float) -> None:
        if not schema.memory:
            return

        valid_names = {m.name for m in schema.memory}
        for k in list(self.memory_state.keys()):
            if k not in valid_names:
                del self.memory_state[k]

        base: Dict[str, float] = {
            **{k: float(v) for k, v in self.memory_state.items()},
            "dt": float(dt),
        }
        for v in schema.ontology.variables:
            base[v.name] = float(self.last_router_state.get(v.name, 0.0))

        for m in schema.memory:
            name = m.name
            if name not in self.memory_state:
                self.memory_state[name] = float(m.init)
            base[name] = float(self.memory_state[name])
            try:
                mem_env = {k: float(v) for k, v in base.items()}
                val = eval_memory_update(m.update, mem_env)
                self.memory_state[name] = float(val)
                base[name] = float(self.memory_state[name])
            except MemoryExpressionError as e:
                print(f"[TelosRuntime] Memory update failed for {name}: {e}")
            except Exception as e:
                print(f"[TelosRuntime] Memory update failed for {name}: {e}")

    def _memory_schema_for_keys(
        self, keys: List[str], schemas_dict: Dict[str, Any]
    ) -> Optional[TelosSchema]:
        """Router block for canvas; else first schema in the chain that defines memory."""
        if "router" in keys:
            return TelosSchema.model_validate(schemas_dict["router"])
        for name in keys:
            sch = TelosSchema.model_validate(schemas_dict[name])
            if sch.memory:
                return sch
        return None

    def tick(
        self,
        schemas_dict: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        parameters = dict(parameters or {})
        keys = _schema_keys_in_order(schemas_dict)
        if not keys:
            return {"status": "FATAL CONFLICT", "detail": "no schema"}

        dt = self._step_clock()

        try:
            mem_schema = self._memory_schema_for_keys(keys, schemas_dict)
        except Exception as e:
            return {"status": "FATAL CONFLICT", "detail": str(e)}

        if mem_schema is not None:
            self._advance_memory(mem_schema, dt)

        context = {**parameters, **self.memory_state}
        global_state: Dict[str, float] = {}
        out_router: Optional[Dict[str, float]] = None
        out_hardware: Optional[Dict[str, float]] = None

        for name in keys:
            try:
                schema = TelosSchema.model_validate(schemas_dict[name])
            except Exception as e:
                return {"status": "FATAL CONFLICT", "detail": str(e)}

            matrix_context = {**context, **global_state}
            try:
                result = TelosCompiler.compile(schema, matrix_context)
            except Exception as e:
                return {"status": "FATAL CONFLICT", "detail": str(e)}

            if not result:
                return {"status": "FATAL CONFLICT"}

            global_state.update(result)
            if name == "router":
                out_router = result
            elif name == "hardware":
                out_hardware = result

        self.last_router_state = dict(global_state)

        physical = {**global_state}
        for actuator in self.actuators:
            actuator.on_update(physical)

        return {
            "status": "HEALTHY",
            "state": global_state,
            "router": out_router or {},
            "db": out_hardware or {},
            "memory": dict(self.memory_state),
        }

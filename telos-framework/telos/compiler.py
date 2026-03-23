"""PuLP MILP engine for canvas / dynamic TelosSchema (no I/O, no time)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pulp

from .models import TelosSchema


class TelosCompiler:
    @staticmethod
    def compile(
        schema: TelosSchema,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, float]]:
        context = dict(context or {})
        direction = (
            pulp.LpMinimize
            if schema.teleology.direction == "minimize"
            else pulp.LpMaximize
        )
        prob = pulp.LpProblem("Telos_Matrix", direction)

        lp_vars: Dict[str, pulp.LpVariable] = {}
        for v in schema.ontology.variables:
            cat = pulp.LpInteger if v.type == "int" else pulp.LpContinuous
            lp_vars[v.name] = pulp.LpVariable(
                v.name,
                lowBound=v.bounds[0],
                upBound=v.bounds[1],
                cat=cat,
            )

        env: Dict[str, Any] = {**lp_vars, **context, "max": max, "min": min}

        prob += eval(schema.teleology.objective, {"__builtins__": None}, env)
        for inv in schema.invariants:
            expr = eval(inv.expression, {"__builtins__": None}, env)
            if inv.type == "eq":
                prob += expr == 0
            else:
                prob += expr >= 0

        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[prob.status] != "Optimal":
            return None

        out: Dict[str, float] = {}
        for name, var in lp_vars.items():
            val = pulp.value(var)
            out[name] = 0.0 if val is None else float(val)
        return out

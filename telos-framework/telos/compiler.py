"""PuLP MILP compiler for ``TelosSchema`` / ``.telos`` geometry (canonical solver core)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pulp

from .linear_milp import LinearMilpExpressionError, parse_linear_milp_expression
from .models import TelosSchema


def _as_pulp_affine(expr: Any) -> pulp.LpAffineExpression:
    if isinstance(expr, (int, float)):
        return pulp.LpAffineExpression(float(expr))
    return expr  # LpVariable or LpAffineExpression


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

        env: Dict[str, Any] = {**lp_vars, **context}

        try:
            obj = parse_linear_milp_expression(schema.teleology.objective.strip(), env)
        except LinearMilpExpressionError as e:
            raise ValueError(f"[TelosCompiler] Invalid objective: {e}") from e
        prob += obj

        for inv in schema.invariants:
            try:
                raw = parse_linear_milp_expression(inv.expression.strip(), env)
            except LinearMilpExpressionError as e:
                raise ValueError(
                    f"[TelosCompiler] Invalid invariant expression {inv.expression!r}: {e}"
                ) from e
            lhs = _as_pulp_affine(raw)
            if inv.type == "eq":
                prob += lhs == 0
            else:
                prob += lhs >= 0

        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[prob.status] != "Optimal":
            return None

        out: Dict[str, float] = {}
        for name, var in lp_vars.items():
            val = pulp.value(var)
            out[name] = 0.0 if val is None else float(val)
        return out

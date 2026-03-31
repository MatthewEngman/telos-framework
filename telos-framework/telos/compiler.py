"""PuLP MILP compiler for ``TelosSchema`` / ``.telos`` geometry (canonical solver core)."""

from __future__ import annotations

import os
import platform
from typing import Any, Dict, Optional

import pulp

from .linear_milp import LinearMilpExpressionError, parse_linear_milp_expression
from .models import TelosSchema

_ARM64_DARWIN_HELP = (
    "Apple Silicon (arm64) macOS needs a native MILP backend: the PuLP CBC bundle is x86-only. "
    'Install HiGHS for Python: pip install highspy   (or pip install "telos-os[milp-highs]"). '
    "Override with TELOS_PULP_SOLVER=cbc if you use an x86_64 Python under Rosetta."
)


def resolve_milp_solver_name(explicit: Optional[str] = None) -> str:
    """
    Choose ``cbc`` or ``highs`` for ``TelosCompiler``.

    * ``explicit`` — when set, overrides the ``TELOS_PULP_SOLVER`` environment variable.
    * ``TELOS_PULP_SOLVER`` — ``auto`` (default), ``cbc``, or ``highs``.
    * ``auto`` on Darwin + arm64 prefers HiGHS when ``highspy`` is available; otherwise raises
      with install instructions. Other platforms default to CBC.
    """
    raw = (
        (explicit.strip().lower() if explicit is not None else None)
        or os.environ.get("TELOS_PULP_SOLVER", "auto").strip().lower()
    )
    if raw == "highs":
        return "highs"
    if raw == "cbc":
        return "cbc"
    if raw not in ("", "auto"):
        raise ValueError(
            f"Invalid MILP solver {raw!r}; use auto, cbc, or highs "
            "(or set TELOS_PULP_SOLVER)."
        )
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        if pulp.HiGHS(msg=False).available():
            return "highs"
        raise RuntimeError(_ARM64_DARWIN_HELP)
    return "cbc"


def build_milp_solver(name: str) -> pulp.LpSolver:
    if name == "cbc":
        return pulp.PULP_CBC_CMD(msg=False)
    sol = pulp.HiGHS(msg=False)
    if not sol.available():
        raise RuntimeError(
            "HiGHS was selected but highspy is not installed. "
            'Install: pip install highspy   (or pip install "telos-os[milp-highs]").'
        )
    return sol


def _as_pulp_affine(expr: Any) -> pulp.LpAffineExpression:
    if isinstance(expr, (int, float)):
        return pulp.LpAffineExpression(float(expr))
    return expr  # LpVariable or LpAffineExpression


class TelosCompiler:
    @staticmethod
    def compile(
        schema: TelosSchema,
        context: Optional[Dict[str, Any]] = None,
        *,
        solver: Optional[str] = None,
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

        backend = resolve_milp_solver_name(solver)
        pulp_solver = build_milp_solver(backend)
        try:
            prob.solve(pulp_solver)
        except OSError as exc:
            if getattr(exc, "errno", None) == 86 and platform.system() == "Darwin":
                raise RuntimeError(_ARM64_DARWIN_HELP) from exc
            raise
        if pulp.LpStatus[prob.status] != "Optimal":
            return None

        out: Dict[str, float] = {}
        for name, var in lp_vars.items():
            val = pulp.value(var)
            out[name] = 0.0 if val is None else float(val)
        return out

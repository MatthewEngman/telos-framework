"""
**Experimental — continuous mode.** SciPy/SymPy compiler for ``TIRSchema`` (``main.py`` demos).

Separate from the canonical PuLP MILP pipeline for ``.telos`` manifests.
"""

import numpy as np
import sympy as sp
from scipy.optimize import minimize
from typing import Dict, Optional

from .schema import TIRSchema


def _substitute_parameters(expr: sp.Expr, parameters: Dict[str, float]) -> sp.Expr:
    for name, value in parameters.items():
        expr = expr.subs(sp.Symbol(name), value)
    return expr


class TelosCompiler:
    def __init__(self, tir: TIRSchema):
        self.tir = tir
        self.var_names = self.tir.ontology.variables
        self.num_vars = len(self.var_names)

        self.sym_vars = sp.symbols(" ".join(self.var_names))
        if self.num_vars == 1:
            self.sym_vars = (self.sym_vars,)

    def compile(
        self,
        parameter_values: Optional[Dict[str, float]] = None,
        *,
        verbose: bool = True,
    ):
        parameter_values = parameter_values or {}
        param_decl = list(self.tir.ontology.parameters)
        for name in param_decl:
            if name not in parameter_values:
                raise ValueError(f"Missing value for declared parameter '{name}'")

        subs = {k: parameter_values[k] for k in param_decl}

        if verbose:
            print(f"[Compiler] Carving a {self.num_vars}-dimensional latent space...")

        direction = self.tir.teleology.direction
        obj_expr = _substitute_parameters(
            sp.sympify(self.tir.teleology.objective), subs
        )
        obj_func = sp.lambdify(self.sym_vars, obj_expr, "numpy")

        multiplier = -1 if direction == "maximize" else 1

        def cost_function(x):
            return multiplier * obj_func(*x)

        constraints = []
        for const in self.tir.invariants:
            expr = _substitute_parameters(sp.sympify(const.expression), subs)
            func = sp.lambdify(self.sym_vars, expr, "numpy")

            def make_constraint(f):
                return lambda x: f(*x)

            constraints.append({"type": const.type, "fun": make_constraint(func)})

        bounds = self.tir.ontology.bounds
        initial_state = np.zeros(self.num_vars)

        if verbose:
            print("[Compiler] Collapsing probability vectors into executable matrix...")
        result = minimize(
            cost_function,
            initial_state,
            bounds=bounds,
            constraints=constraints,
            method="SLSQP",
        )

        if result.success:
            if verbose:
                print("[Compiler] Compilation Successful. State Frozen.")
            return {var: round(float(val), 4) for var, val in zip(self.var_names, result.x)}
        else:
            raise Exception(f"[FATAL] Mathematical conflict. {result.message}")

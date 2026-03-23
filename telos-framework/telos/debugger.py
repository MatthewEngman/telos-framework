"""Monte Carlo stress tests + deletion-filter IIS for infeasible MILP manifests."""

from __future__ import annotations

import random
import time
from typing import List, Optional

from .compiler import TelosCompiler
from .models import Invariant, TelosSchema


class LatentDebugger:
    """Adversarial verification: random contexts + irreducible inconsistent subsystem hints."""

    @staticmethod
    def _compile_context(schema: TelosSchema, context: dict) -> dict:
        """Parameters + memory initials so objectives can reference heat_* etc."""
        merged = dict(context)
        for m in schema.memory:
            merged.setdefault(m.name, float(m.init))
        return merged

    @staticmethod
    def _is_feasible(
        schema: TelosSchema,
        context: dict,
        active_invariants: Optional[List[Invariant]] = None,
    ) -> bool:
        """Return True iff PuLP finds an optimal solution for this constraint set."""
        test = schema.model_copy(deep=True)
        if active_invariants is not None:
            test.invariants = list(active_invariants)
        ctx = LatentDebugger._compile_context(schema, context)
        try:
            result = TelosCompiler.compile(test, ctx)
            return result is not None
        except Exception:
            return False

    @staticmethod
    def _find_iis(schema: TelosSchema, context: dict) -> List[Invariant]:
        """
        Deletion filter: drop constraints that are redundant for infeasibility.
        Remaining set is a (typically small) witness subsystem; not a full CPLEX IIS.
        """
        core = list(schema.invariants)
        if not core:
            return []

        progress = True
        while progress and len(core) > 0:
            progress = False
            for i in range(len(core) - 1, -1, -1):
                temp = core[:i] + core[i + 1 :]
                still_bad = LatentDebugger._is_feasible(schema, context, temp) is False
                if still_bad:
                    core = temp
                    progress = True
                    break

        return core

    @staticmethod
    def _sample_context(parameters: List[str]) -> dict:
        chaotic: dict = {}
        for p in parameters:
            pl = p.lower()
            if "cap" in pl:
                chaotic[p] = round(random.uniform(0.0, 1.0), 3)
            elif "cost" in pl:
                chaotic[p] = round(random.uniform(1.0, 100.0), 2)
            else:
                chaotic[p] = round(random.uniform(0.0, 100.0), 2)
        return chaotic

    @staticmethod
    def simulate(schema: TelosSchema, iterations: int = 1000) -> bool:
        params = list(schema.ontology.parameters or [])
        if not params:
            print("[Chaos Monkey] No ontology.parameters to fuzz; skipping Monte Carlo.")
            return True

        print(f"\n[Chaos Monkey] Monte Carlo ({iterations} samples)...")
        t0 = time.perf_counter()

        for i in range(iterations):
            ctx = LatentDebugger._sample_context(params)
            if LatentDebugger._is_feasible(schema, ctx):
                continue

            print(f"\n[!] Sample #{i + 1} infeasible. Paradox autopsy...")
            print(f"    Context: {ctx}")

            iis = LatentDebugger._find_iis(schema, ctx)
            print("\n[!] Irreducible inconsistent witness (deletion filter):")
            if not iis:
                print("    (empty - infeasibility may come from bounds/objective only)")
            else:
                for rule in iis:
                    print(f"      -> {rule.type.upper()}: {rule.expression}")

            print("\n[Chaos Monkey] Halted. Tighten geometry or relax constraints.\n")
            return False

        ms = (time.perf_counter() - t0) * 1000.0
        print(
            f"\n[Chaos Monkey] OK: {iterations} random contexts feasible ({ms:.0f} ms).\n"
        )
        return True

"""Best-effort numeric parameters for CLI ``run`` and ``validate --strict`` probes."""

from __future__ import annotations

from typing import Any, Dict


def default_probe_parameters(schema: Dict[str, Any]) -> Dict[str, float]:
    """Fill ``ontology.parameters`` with heuristic defaults (same behavior as former CLI-only helper)."""
    names = (schema.get("ontology") or {}).get("parameters") or []
    params: Dict[str, float] = {}
    for name in names:
        lower = name.lower()
        if "yield" in lower:
            if "tsla" in lower:
                params[name] = 0.08
            elif "aapl" in lower:
                params[name] = 0.05
            else:
                params[name] = 0.05
        elif "price" in lower:
            if "tsla" in lower:
                params[name] = 200.0
            elif "aapl" in lower:
                params[name] = 150.0
            else:
                params[name] = 100.0
        elif "cost" in lower:
            params[name] = 20.0
        elif "cap" in lower:
            params[name] = 1.0
        else:
            params[name] = 1.0
    return params

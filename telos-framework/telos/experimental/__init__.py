"""
Experimental / non-canonical APIs.

The primary product path is MILP ``.telos`` manifests. Continuous **TIR** helpers
live under ``telos.experimental.tir`` (re-exports of ``telos.schema`` and
``telos.tir_compiler``) for clearer namespacing; existing ``telos.schema`` imports
remain stable.
"""

from . import tir

__all__ = ["tir"]

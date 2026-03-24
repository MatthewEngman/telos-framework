"""
Telos OS — Python framework for declarative optimization runtimes.

The canonical path is **``.telos`` YAML manifests** (``TelosParser``), **MILP** solving
via PuLP/CBC (``TelosCompiler``, ``TelosRuntime``), optional **actuators** for side
effects, **``LatentDebugger``** for parameter fuzzing, and **``TelosGenerator``** for
optional LLM-assisted draft manifests.

**Expression handling:** MILP objectives and invariants are built by a **safe linear
expression parser** (``telos.linear_milp``; no ``eval``). Router **memory** ``update``
strings use a **separate scalar evaluator** (``telos.memory_expr``) with ``max``/``min``
only. Treat manifests, canvas payloads, and LLM output as **trusted configuration**
(supply-chain and correctness), even though arbitrary Python execution from those
strings is no longer the failure mode for the MILP path.

Modules ``telos.schema``, ``telos.tir_compiler``, and ``telos.agent`` implement an
**experimental continuous-mode (TIR + SciPy)** track for demos; they are not the
primary product surface.
"""

from .actuators.base import BaseActuator
from .actuators.docker import DockerActuator
from .actuators.fintech import FinTechActuator
from .actuators.kubernetes import KubernetesActuator
from .debugger import LatentDebugger
from .generator import TelosGenerator
from .parser import TelosParser
from .runtime import TelosRuntime

__version__ = "1.3.0"

__all__ = [
    "BaseActuator",
    "DockerActuator",
    "FinTechActuator",
    "KubernetesActuator",
    "LatentDebugger",
    "TelosGenerator",
    "TelosParser",
    "TelosRuntime",
    "__version__",
]

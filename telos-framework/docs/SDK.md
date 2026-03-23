# Telos SDK (canvas / MILP path)

This document describes the **installable Python package** under `telos/`: validated schemas, the PuLP compiler, the temporal runtime, and pluggable **actuators**. It sits alongside the older **TIR + SciPy** stack used by `main.py` (see [README.md](../README.md)).

For **actuator conventions, FAQs, and custom implementations**, see [ACTUATORS.md](./ACTUATORS.md). For **sample `.telos` files** across domains, see [examples/README.md](../examples/README.md).

## Version

Package version is exposed as `telos.__version__` (see `telos/__init__.py`).

## Module map

| Module | Role |
|--------|------|
| `telos/models.py` | Pydantic **MILP canvas** models: `TelosSchema`, `Variable`, `Memory`, `Ontology`, `Teleology`, `Invariant`. |
| `telos/compiler.py` | **PuLP** `TelosCompiler.compile(schema, context)` — one-shot MILP; no clock, no I/O. |
| `telos/runtime.py` | `TelosRuntime`: `dt` cap, router **memory** updates, ordered **`router` → `hardware`** compiles, `actuator.on_update(...)`. |
| `telos/actuators/base.py` | `BaseActuator` — subclass for custom side effects. |
| `telos/actuators/docker.py` | `DockerActuator` — optional Docker SDK; syncs `shards_*` to `nginx:alpine` containers. |
| `telos/actuators/kubernetes.py` | `KubernetesActuator` — optional `kubernetes` client; scales Deployments from `replicas_<name>`. |
| `telos/actuators/fintech.py` | `FinTechActuator` — demo logs for `shares_<TICKER>` targets (not a real broker). |
| `telos/schema.py` | **TIR** models for LLM/CLI (`TIRSchema`, string variable lists, SymPy-oriented). |
| `telos/tir_compiler.py` | **SciPy `SLSQP`** compiler for `TIRSchema` (continuous optimization). |
| `telos/agent.py` | Natural language → TIR. |
| `telos/parser.py` | **`TelosParser.load` / `loads`** — YAML file or string → validated `TelosSchema` dict. |
| `telos/generator.py` | **`TelosGenerator`** — LLM intent → `.telos` file; re-validates with `TelosSchema`. |
| `telos/cli.py` | **`python -m telos generate`** / **`run`** / **`test`** — CLI entry point. |
| `telos/debugger.py` | **`LatentDebugger`** — Monte Carlo over `ontology.parameters`; deletion-filter witness for infeasibility. |
| `server.py` (repo root) | Thin **FastAPI** + WebSocket: JSON in, `TelosRuntime.tick`, JSON out to `index.html`. |
| `headless.py` (repo root) | Example **daemon**: manifest + timeline of parameters, no UI. |

Two **compilers** coexist on purpose:

- **`telos.tir_compiler.TelosCompiler`** — continuous TIR (`main.py`, demos).
- **`telos.compiler.TelosCompiler`** — MILP `TelosSchema` (canvas / SDK).

## Public imports

```python
from telos import TelosRuntime, TelosParser, TelosGenerator, LatentDebugger, BaseActuator, DockerActuator, __version__
```

### Prompt-to-physics (`TelosGenerator`)

```python
from telos import TelosGenerator

TelosGenerator().generate(
    "Route US/EU/Asia, minimize cost, EU load <= 20%, shards >= 10% load each",
    "out.telos",
)
```

Uses **`OPENAI_API_KEY`** or local **Ollama** (same rules as `TelosAgent`). Generated YAML is checked immediately with **`TelosParser.loads`**.

### Adversarial check (`LatentDebugger`)

```bash
python -m telos test manifest.telos --iters 1000
```

Random-samples declared **parameters** (caps, costs, etc.). On first infeasible PuLP outcome, prints a **small witness** subset of invariants (deletion filter; not a full commercial IIS). **Memory** `init` values are injected into the compile context so objectives like `(10 + heat_us)*load_us` still parse. Exit code **2** if a paradox is found, **0** if all samples feasible.

Lower-level pieces:

```python
from telos.models import TelosSchema
from telos.compiler import TelosCompiler as MilpCompiler
```

## `.telos` manifests (YAML)

Declarative MILP geometry lives in YAML on disk. **`TelosParser.load("path/to/file.telos")`** returns a **dict** that matches `TelosSchema` (same shape as the canvas JSON). Feed it into `tick` under any key name when you are **not** using the canvas split:

```python
schema_dict = TelosParser.load("infrastructure.telos")
runtime.tick({"main": schema_dict}, {"us_cap": 1.0, "eu_cost": 20.0})
```

Requirements: **`pyyaml`**. Expressions in the file are still evaluated with restricted `eval` at runtime — treat manifests as **trusted** (like code).

## `TelosRuntime.tick`

Signature:

```python
result = runtime.tick(
    schemas_dict,           # Canvas: {"router": {...}, "hardware": {...}}
    parameters or {},       # Numeric context: cap_*, cost_*, etc.
)
```

**Behavior:**

1. **Clock:** `dt` is advanced every tick (capped at 1s).
2. **Memory:** If the payload includes **`router`**, memory rules come from that block (canvas). Otherwise, the **first** schema in the dict (in insertion order) that defines **`memory`** is used — typical for a single key such as **`main`** from a `.telos` file.
3. **Compile order:** If **`router`** and/or **`hardware`** are present, only those run, in that order. Otherwise **all** non-empty keys are compiled **in insertion order** (e.g. one combined **`main`** matrix).
4. Merges outputs into one dict and calls **`on_update`** on each actuator with that merged state.
5. Returns `status`, `router` / `db` (canvas splits; empty for single-matrix runs), `memory`, and `state` (merged).

The **canvas** still sends `{ router, hardware }`; **headless** demos can send one combined matrix under a single key.

## Custom actuators

`on_update` receives **merged** MILP outputs (e.g. `load_*`, `shards_*`). Filter keys inside your actuator. Full guide (prefixes, threading, optional deps, FAQ): **[ACTUATORS.md](./ACTUATORS.md)**.

```python
from telos import TelosRuntime, BaseActuator, DockerActuator

class LoggingActuator(BaseActuator):
    def on_update(self, optimal_state: dict) -> None:
        print("tick", optimal_state)

rt = TelosRuntime()
rt.attach_actuator(LoggingActuator())
rt.attach_actuator(DockerActuator())  # optional; needs docker extra + daemon
```

## Docker actuator

- Requires **`docker`** on `PYTHONPATH` and a running **Docker Desktop** (or daemon).
- Containers are labeled `telos_framework=true` and `node=<id>` for cleanup and reconciliation.
- If Docker is missing or unreachable, the server still runs; the actuator stays in simulation mode.

## Security note

Both compilers evaluate **objective** and **constraint** strings with restricted `eval`. The **canvas** and any JSON you pass into `tick` must come from a **trusted** source, or you must replace evaluation with a safe expression layer.

## Publishing / layout

The PyPI project is **`telos-os`** (`pyproject.toml`). Extras: `[docker]`, `[kubernetes]`, `[server]`, `[all]`. Local development can still use `requirements.txt` alongside editable installs.

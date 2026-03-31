# Telos SDK (MILP runtime)

**If you are new**, read **[START_HERE.md](./START_HERE.md)** first (variables vs parameters, `.telos`, `tick`).

This document describes the **installable** `telos` package: **parser**, **MILP models/compiler**, **runtime**, **debugger**, **generator**, and **actuators**. The **canonical** integration surface is **`TelosParser` + `TelosRuntime` + `.telos` manifests**.

- **Actuators:** [ACTUATORS.md](./ACTUATORS.md)  
- **Examples:** [examples/README.md](../examples/README.md)

## Expression engines (MILP vs memory)

**Design rule:** every accepted MILP expression must be **classifiable as linear with respect to decision variables** (ontology variables mapped to PuLP symbols). That invariant is what blocks feature creep into non-linear or `eval`-style holes.

**Objectives and invariants** use **`telos.linear_milp`**: numbers, identifiers, `+`, `-`, `*`, `/`, parentheses. Multiplication may not combine two decision-bearing subexpressions. **Division** is allowed only when the **denominator does not depend on decision variables** (it is a constant multiplier at compile time); **zero** / near-zero denominators are rejected. Invalid numeric literals (e.g. `0..`) are parse errors, not process crashes. **Parenthesis nesting** is capped at **`telos.expr_limits.DEFAULT_MAX_PAREN_NESTING_DEPTH`** (64).

**Memory `update`** strings use **`telos.memory_expr`**: scalar floats, `+`, `-`, `*` (no `/` until a manifest needs it), parentheses, and whitelisted **`max`** / **`min`**. No `eval`. Uses the **same nesting cap** (grouping and function-call parens share one counter).

Treat manifests and canvas JSON as **trusted configuration**; see [../../SECURITY.md](../../SECURITY.md).

## Version

`telos.__version__` — see `telos/__init__.py`.

## Module map (MILP-first)

| Module | Role |
|--------|------|
| `telos/models.py` | `TelosSchema`, `Variable`, `Memory`, etc. |
| `telos/compiler.py` | PuLP `TelosCompiler.compile(schema, context, *, solver=None)`, plus `resolve_milp_solver_name` / `build_milp_solver` |
| `telos/expr_limits.py` | Internal caps (e.g. max parenthesis nesting depth) |
| `telos/linear_milp.py` | Safe linear expression parser for objectives / invariants |
| `telos/memory_expr.py` | Safe scalar evaluator for memory `update` strings |
| `telos/runtime.py` | `TelosRuntime.tick` — memory, router→hardware order, actuators |
| `telos/actuators/base.py` | `BaseActuator` |
| `telos/actuators/docker.py` | `DockerActuator` — `shards_*` |
| `telos/actuators/kubernetes.py` | `KubernetesActuator` — `replicas_*` |
| `telos/actuators/fintech.py` | `FinTechActuator` — `shares_*` (demo) |
| `telos/parser.py` | `TelosParser.load` / `loads` |
| `telos/generator.py` | `TelosGenerator` — optional LLM → `.telos` |
| `telos/debugger.py` | `LatentDebugger` — Monte Carlo parameters |
| `telos/cli.py` | `telos run`, `validate`, `test`, `generate` |
| `server.py` (repo root) | Optional FastAPI + WebSocket canvas |
| `headless.py` (repo root) | Example daemon: `.telos` + timeline |

### Experimental — continuous mode (TIR)

| Module | Role |
|--------|------|
| `telos/schema.py` | `TIRSchema` for SciPy-oriented demos |
| `telos/tir_compiler.py` | SciPy `SLSQP` compiler for TIR |
| `telos/agent.py` | Natural language → TIR (not the primary `.telos` path) |
| `telos/experimental/tir.py` | Re-exports TIR + `TelosAgent` + SciPy `TelosCompiler` (namespaced) |

There are two compilers by design: **`telos.compiler.TelosCompiler`** (MILP, canonical) and **`telos.tir_compiler.TelosCompiler`** (TIR/SciPy, experimental).

### MILP solver backend (CBC vs HiGHS)

- **`TelosCompiler.compile(..., solver=None)`** — optional **`solver`**: `"auto"`, `"cbc"`, or `"highs"`; when omitted, **`TELOS_PULP_SOLVER`** is read (default **`auto`**). **`auto`** on **Darwin arm64** prefers **HiGHS** if `highspy` is available; otherwise a **`RuntimeError`** explains how to install **`telos-os[milp-highs]`** or **`pip install highspy`**.
- **`resolve_milp_solver_name(explicit=None)`** / **`build_milp_solver(name)`** — resolve the solver string and construct the PuLP solver instance (used by the compiler and tests).

CLI: **`telos validate --solver …`** and **`telos run --solver …`** set **`TELOS_PULP_SOLVER`** for that process.

## Public imports

```python
from telos import TelosRuntime, TelosParser, TelosGenerator, LatentDebugger, BaseActuator, DockerActuator, __version__
```

### Optional: draft manifest (`TelosGenerator`)

```python
from telos import TelosGenerator

TelosGenerator().generate(
    "Route US/EU/Asia, minimize cost, EU load <= 20%, shards >= 10% load each",
    "out.telos",
)
```

Uses `OPENAI_API_KEY` or Ollama (same rules as `TelosAgent`). Output is re-validated with `TelosParser.loads`. **Treat as trusted input** after review.

### Debugger CLI

```bash
telos test manifest.telos --iters 1000
```

Random-samples declared **parameters**. On first infeasible outcome, prints a **witness** subset of invariants (deletion filter). Memory `init` values are injected into the compile context. Exit **2** if a paradox is found, **0** if all samples feasible.

```python
from telos.models import TelosSchema
from telos.compiler import TelosCompiler as MilpCompiler
```

### Validate CLI

```bash
telos validate manifest.telos
telos validate manifest.telos --strict --solver highs
```

Exit **0** if YAML parses and `TelosSchema` validates; **1** on failure. With **`--strict`**, also run one solve: **1** on compile/parse error, **4** if the probe context is infeasible or not optimal. **`--solver`** — `auto`, `cbc`, or `highs` (sets **`TELOS_PULP_SOLVER`**; same flag exists on **`telos run`**).

## `.telos` manifests (YAML)

```python
schema_dict = TelosParser.load("infrastructure.telos")
runtime.tick({"main": schema_dict}, {"us_cap": 1.0, "eu_cost": 20.0})
```

Requires `pyyaml`. Expression handling is described above.

## `TelosRuntime.tick`

```python
result = runtime.tick(
    schemas_dict,           # e.g. {"router": {...}, "hardware": {...}} or {"main": {...}}
    parameters or {},
)
```

**Behavior:**

1. **Clock:** `dt` advanced each tick (capped at 1s).
2. **Memory:** From `router` schema if present; else first schema in dict order that defines **`memory`** (typical for single **`main`** key).
3. **Compile order:** If **`router`** / **`hardware`** present, those only, in that order. Else all non-empty keys in insertion order.
4. Merge outputs; call **`on_update`** on each actuator with merged **state**.
5. Return `status`, optional `router`/`db`, `memory`, `state`.

## Custom actuators

`on_update` receives merged MILP outputs. See **[ACTUATORS.md](./ACTUATORS.md)**.

```python
from telos import TelosRuntime, BaseActuator, DockerActuator

class LoggingActuator(BaseActuator):
    def on_update(self, optimal_state: dict) -> None:
        print("tick", optimal_state)

rt = TelosRuntime()
rt.attach_actuator(LoggingActuator())
rt.attach_actuator(DockerActuator())
```

## Docker actuator

Needs `docker` extra and a running daemon. Labeled `telos_framework=true`, `node=<id>`. If unreachable, stays in simulation mode.

## Publishing / layout

PyPI **`telos-os`** (`pyproject.toml`). Extras: `[docker]`, `[kubernetes]`, `[server]`, `[milp-highs]` (`highspy`, recommended on **Apple Silicon** for MILP), `[all]`.

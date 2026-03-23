# Telos OS

**Telos OS** is a Python framework for **declarative optimization runtimes** using **`.telos` manifests**, **MILP** solving (PuLP / CBC), and **actuator-driven** execution after each solve.

*Infrastructure-as-Physics* — a tagline for the idea that infrastructure goals and constraints can be written as explicit math; the **primary** product surface is the **`.telos` + MILP** stack, not alternate representations.

**First run in a few minutes:** install from [`telos-framework/`](telos-framework/), then `telos validate`, `telos run`, and `telos test` as below. Beginners: **[telos-framework/docs/START_HERE.md](telos-framework/docs/START_HERE.md)**.

Source layout: the installable package and CLI live under [`telos-framework/`](telos-framework/).

---

## What it is

| Piece | Role |
|--------|------|
| **`.telos` manifests** | YAML describing variables, parameters, objective, and constraints; loaded with [`TelosParser`](telos-framework/telos/parser.py) and validated as [`TelosSchema`](telos-framework/telos/models.py) |
| **MILP runtime** | [`TelosRuntime.tick`](telos-framework/telos/runtime.py) — memory, optional router→hardware chain, PuLP compile/solve, merged **state** |
| **Actuators** | Pluggable [`BaseActuator`](telos-framework/telos/actuators/base.py) hooks (Docker, Kubernetes, demo FinTech) — side effects **after** a successful solve |
| **Debugger** | [`LatentDebugger`](telos-framework/telos/debugger.py) — Monte Carlo over parameters; witness-style hints when constraints cannot be satisfied |
| **Generator (optional)** | [`TelosGenerator`](telos-framework/telos/generator.py) — natural language → draft `.telos` (OpenAI or Ollama) |

**Expression safety:** MILP strings are parsed by **`telos.linear_milp`** under the invariant that **every accepted expression is linear in decision variables** (including **division only when the denominator is decision-free**). **Memory** updates use **`telos.memory_expr`**. There is **no Python `eval`** on those paths. **Corpus + Hypothesis fuzz tests** (see `telos-framework` dev install) harden the parser boundary in CI. Still treat **`.telos`**, **canvas JSON**, and **LLM-generated YAML** as **trusted configuration**. See [SECURITY.md](SECURITY.md) and [telos-framework/docs/SDK.md](telos-framework/docs/SDK.md).

---

## Quick install

```bash
cd telos-framework
python -m pip install -e .
# CLI: telos --help
```

Use `python -m pip install -e ".[all]"` if you want Docker, Kubernetes, and the FastAPI canvas server extras.

---

## First successful run

From `telos-framework/` (math only, no Docker):

```bash
telos validate examples/router_minimal.telos
telos validate examples/router_minimal.telos --strict
telos run examples/router_minimal.telos --actuator none --params examples/params/router_minimal.json
```

Press **Ctrl+C** to stop the loop. You should see `[MATH]` lines with variable values from the solver.

---

## First successful test (fuzz)

```bash
telos test vulnerable.telos --iters 500
```

Exit code **2** means an infeasible parameter context was found (debugger reports a small witness). Exit **0** means all sampled contexts were feasible.

---

## Core concepts

- **Variable** — decided by the solver within bounds you declare (`float` or `int` for MILP).
- **Parameter** — you supply each tick (JSON file, code, or CLI defaults); not optimized.
- **Objective / invariants** — linear expressions over variables and parameters; **`eq`** means expression == 0, **`ineq`** means expression ≥ 0 (Telos convention).
- **`tick`** — one solve cycle: update clock/memory if configured, run MILP(s), merge state, call actuators.

More detail: [telos-framework/docs/START_HERE.md](telos-framework/docs/START_HERE.md).

---

## CLI overview

| Command | Purpose |
|---------|---------|
| `telos run <file.telos>` | Load manifest, loop: solve each tick, optional actuators |
| `telos validate <file.telos>` | Parse YAML + validate `TelosSchema`; `--strict` adds one PuLP probe (exit **4** if not optimal at probe context) |
| `telos test <file.telos>` | Parameter fuzzing / paradox hunt (`--iters`) |
| `telos generate "..." --out x.telos` | Optional LLM draft manifest (review before use) |
| `telos install <id>` | **Experimental stub** — local placeholder only, not a package registry |

---

## SDK overview

```python
from pathlib import Path
from telos import TelosRuntime, TelosParser, DockerActuator

rt = TelosRuntime()
rt.attach_actuator(DockerActuator())

schema = TelosParser.load(Path("examples/router_minimal.telos"))
result = rt.tick({"main": schema}, {"east_latency_weight": 5.0, "west_latency_weight": 1.0})
```

Full API: [telos-framework/docs/SDK.md](telos-framework/docs/SDK.md). Actuators: [telos-framework/docs/ACTUATORS.md](telos-framework/docs/ACTUATORS.md).

---

## Optional: natural language and canvas

- **`telos generate`** — LLM-assisted `.telos`; requires `OPENAI_API_KEY` or local Ollama. Output is still **trusted-input** territory.
- **Spatial canvas** — [`telos-framework/server.py`](telos-framework/server.py) + `index.html`: WebSocket UI around `TelosRuntime`. Run `python server.py`, open `http://127.0.0.1:8000` (same host; not `file://`).

---

## Experimental: continuous mode (TIR + SciPy)

[`telos-framework/main.py`](telos-framework/main.py) demonstrates **TIR** (`telos/schema.py`, `telos/tir_compiler.py`) with **SciPy SLSQP** — useful for demos and fractional-variable experiments, **not** the same guarantees as the MILP `.telos` path (no mixed-integer certification). See [telos-framework/README.md](telos-framework/README.md) for a short pointer, not as a co-equal onboarding track.

---

## Documentation

| Doc | Audience |
|-----|----------|
| [telos-framework/docs/START_HERE.md](telos-framework/docs/START_HERE.md) | Glossary, first commands |
| [telos-framework/README.md](telos-framework/README.md) | Layout, env vars, deeper reference |
| [telos-framework/docs/SDK.md](telos-framework/docs/SDK.md) | Python API, `tick`, expression engines |
| [telos-framework/docs/ACTUATORS.md](telos-framework/docs/ACTUATORS.md) | Actuator contracts |
| [telos-framework/examples/README.md](telos-framework/examples/README.md) | Example manifests and one-liners |

---

## Requirements

- **Python** 3.10+ (3.13 OK in development)
- **Optional:** Docker Desktop for `DockerActuator`
- **Optional:** `OPENAI_API_KEY` or **Ollama** for `telos generate` / agent demos

---

## Security

**Do not** expose untrusted `.telos` or canvas payloads without policy controls. Parser overview and TIR (`sympify`) notes: [SECURITY.md](SECURITY.md).

---

## License

[MIT](telos-framework/LICENSE) — [`telos-framework/LICENSE`](telos-framework/LICENSE).

---

## Contributing

[telos-framework/CONTRIBUTING.md](telos-framework/CONTRIBUTING.md) — tests, CI, PR expectations.

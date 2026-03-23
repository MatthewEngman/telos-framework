# Telos Framework / Telos OS

[![CI](https://github.com/MatthewEngman/telos-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/MatthewEngman/telos-framework/actions/workflows/ci.yml)

**Telos OS** is a Python framework for **declarative optimization runtimes**: **`.telos` YAML manifests**, **MILP** solving with PuLP/CBC, a temporal **`TelosRuntime`** (memory, chained matrices), and optional **actuators**. *Infrastructure-as-Physics* is a **tagline** for describing goals and constraints as math—not a second product line.

**New here?** **[docs/START_HERE.md](docs/START_HERE.md)** — glossary, `telos validate` / `telos run` / `telos test`, how to read a manifest.

---

## Canonical path: `.telos` + MILP + runtime

1. Author or generate a **`.telos`** file (YAML → `TelosSchema`).
2. **`telos validate`** / **`telos run`** / **`telos test`** — or embed **`TelosParser`** + **`TelosRuntime`** in Python.
3. Optionally attach **actuators** so numeric solutions drive Docker, Kubernetes, or custom side effects.

**Expression handling:** objectives and invariants use **`telos.linear_milp`**—**every accepted expression is linear in decision variables**; `/` only when the denominator is decision-free. Memory **`update`** strings use **`telos.memory_expr`**. Checked-in manifests are covered by **corpus tests**; dev CI runs **Hypothesis fuzz** on the parsers (bounded time per sample). Still treat **`.telos`**, **canvas JSON**, and **LLM output** as **trusted configuration**. See [docs/SDK.md](docs/SDK.md) and [../SECURITY.md](../SECURITY.md).

---

## Architecture (MILP-first)

| Layer | Module | Role |
|--------|--------|------|
| **Manifests** | `telos/parser.py` | `TelosParser.load` / `loads` — YAML → validated dict |
| **MILP schema** | `telos/models.py` | `TelosSchema`, `Variable`, `Memory`, etc. |
| **MILP compiler** | `telos/compiler.py` | PuLP `TelosCompiler.compile` |
| **Linear expressions** | `telos/linear_milp.py` | Safe parser for objectives / invariants |
| **Memory expressions** | `telos/memory_expr.py` | Safe scalar `update` evaluator (`max`/`min`) |
| **Runtime** | `telos/runtime.py` | `TelosRuntime.tick` — memory, router→hardware order, actuators |
| **Actuators** | `telos/actuators/` | `DockerActuator`, `KubernetesActuator`, `FinTechActuator` |
| **Debugger** | `telos/debugger.py` | `LatentDebugger` — Monte Carlo parameters |
| **Generator (optional)** | `telos/generator.py` | LLM → draft `.telos` |
| **CLI** | `telos/cli.py` | `telos run`, `validate`, `test`, `generate`; `install` is stub |

### Experimental — continuous mode (TIR)

| Module | Role |
|--------|------|
| `telos/schema.py` | `TIRSchema` — string variable lists, SymPy-oriented (fractional variables) |
| `telos/tir_compiler.py` | SciPy `SLSQP` for `TIRSchema` |
| `telos/agent.py` | Natural language → **TIR** (not the primary `.telos` workflow) |
| `main.py` | Demos: intent → TIR → SciPy, or hand-authored finance TIR |

TIR does **not** provide mixed-integer guarantees. Prefer **`.telos` + PuLP** for production-style discrete decisions.

---

## Project layout

```
telos-framework/
├── telos/
│   ├── __init__.py          # exports; package story
│   ├── linear_milp.py       # safe linear parser (objectives / invariants)
│   ├── memory_expr.py       # safe scalar memory updates
│   ├── models.py            # MILP TelosSchema
│   ├── compiler.py          # PuLP
│   ├── parser.py            # .telos YAML
│   ├── runtime.py           # TelosRuntime
│   ├── debugger.py
│   ├── generator.py
│   ├── cli.py
│   ├── schema.py            # experimental TIR models
│   ├── tir_compiler.py      # experimental SciPy path
│   ├── agent.py             # experimental NL → TIR
│   └── actuators/
├── main.py                  # TIR / SciPy demos (experimental)
├── headless.py              # .telos + timeline (MILP)
├── server.py                # optional canvas (FastAPI + WebSocket)
├── examples/                # MILP .telos + params/
├── docs/
│   ├── START_HERE.md
│   ├── SDK.md
│   └── ACTUATORS.md
└── pyproject.toml
```

| Doc | Audience |
|-----|----------|
| [docs/START_HERE.md](docs/START_HERE.md) | Beginners |
| [docs/SDK.md](docs/SDK.md) | Python API, security |
| [docs/ACTUATORS.md](docs/ACTUATORS.md) | Actuator guide |
| [examples/README.md](examples/README.md) | Learning progression + CLI |

---

## Requirements

Python **3.10+** (3.13 works in development).

## Install

**Editable (registers `telos` CLI):**

```bash
cd telos-framework
python -m pip install -e ".[all]"   # + docker, k8s, server
# or minimal MILP SDK:
python -m pip install -e .
```

**PyPI:** `pip install telos-os` — extras `[docker]`, `[kubernetes]`, `[server]`, `[all]`.

**Legacy:** `python -m pip install -r requirements.txt`

License: **MIT** (`LICENSE`).

---

## First commands (MILP)

```bash
telos validate examples/router_minimal.telos
telos run examples/router_minimal.telos --actuator none --params examples/params/router_minimal.json
telos test vulnerable.telos --iters 500
```

Optional LLM draft (review output before running):

```bash
telos generate "Describe routing, costs, caps..." --out app.telos
```

**Experimental stub** (not a registry):

```bash
telos install vendor/my-actuator
```

Backends for `generate` / agent: `OPENAI_API_KEY`, or `TELOS_LLM_BACKEND=ollama` with `ollama serve`. See **Environment variables** below.

---

## Optional canvas

```bash
python server.py
```

Open **`http://127.0.0.1:8000`** (not `file://`). Port: `TELOS_PORT`. `TELOS_RELOAD=1` for uvicorn reload (WebSockets can be flaky on Windows).

---

## Headless MILP demo

```bash
python headless.py
```

Loads **`infrastructure.telos`** and a parameter timeline; uses **`DockerActuator`** when Docker is available.

---

## Experimental TIR demos (`main.py`)

```bash
python main.py          # intent → agent → TIR → SciPy (optional LLM)
python main.py finance  # hand-authored TIR, no LLM
```

These illustrate the **continuous** track only.

---

## SDK usage (MILP)

```python
from pathlib import Path
from telos import TelosRuntime, TelosParser, DockerActuator

rt = TelosRuntime()
rt.attach_actuator(DockerActuator())

result = rt.tick(
    {"router": router_dict, "hardware": hardware_dict},
    {"cap_s1": 1.0, "cost_s1": 20.0},
)

schema = TelosParser.load(Path("infrastructure.telos"))
result = rt.tick({"main": schema}, {"us_cap": 1.0, "eu_cost": 20.0})
```

See [docs/SDK.md](docs/SDK.md) for the full `tick` contract.

---

## Configuring the agent (TIR / experimental)

`TelosAgent` backend order when `auto`: OpenAI if `OPENAI_API_KEY`, else Ollama if reachable, else mock.

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI |
| `TELOS_LLM_BACKEND` | `auto` · `openai` · `ollama` · `mock` |
| `OLLAMA_HOST` | Ollama base URL |
| `TELOS_OLLAMA_MODEL` | Model name |
| `TELOS_GENERATOR_MODEL` | Chat model for `TelosGenerator` (default `gpt-4o`) |
| `TELOS_PORT` | Canvas port |
| `TELOS_RELOAD` | `1` for uvicorn autoreload |

---

## TIR JSON shape (reference only — experimental)

Expressions must be valid for SymPy (`sympify`). **`eq`** → == 0, **`ineq`** → ≥ 0.

```json
{
  "ontology": {
    "variables": ["x", "y"],
    "bounds": [[0.0, 1.0], [0.0, 1.0]]
  },
  "teleology": {
    "direction": "minimize",
    "objective": "x + 2*y"
  },
  "invariants": [
    { "type": "eq", "expression": "x + y - 1.0" },
    { "type": "ineq", "expression": "0.5 - x" }
  ]
}
```

---

## Limitations

- **MILP:** CBC via PuLP; linear expression parser for manifest strings.
- **TIR:** continuous `SLSQP` only; experimental / demo-oriented.
- Executable “matrix” is a **dict of numbers**, not a binary tensor format.

---

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) — pytest, CI, PRs.

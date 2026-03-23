# Telos Framework / Telos OS

[![CI](https://github.com/MatthewEngman/telos-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/MatthewEngman/telos-framework/actions/workflows/ci.yml)

**Telos** is an experimental stack for **teleological specification**: variables, optimization objectives, and constraints. Two representations coexist:

1. **TIR** (Telos Intermediate Representation) — domain-agnostic schema for **continuous** problems, typically produced by the LLM agent and solved with **SymPy + SciPy**.
2. **MILP canvas schema** — Pydantic **`TelosSchema`** (`telos/models.py`) for **mixed-integer** problems, used by the **spatial IDE** and solved with **PuLP (CBC)**.

## Architecture

| Layer | Module | Role |
|--------|--------|------|
| **TIR schema** | `telos/schema.py` | `TIRSchema`, `Ontology` (string variables + bounds), `Teleology`, `Invariant` |
| **MILP schema** | `telos/models.py` | `TelosSchema`, typed `Variable` / `Memory` for canvas JSON |
| **Agent** | `telos/agent.py` | Natural language → TIR (OpenAI, Ollama, mock) |
| **TIR compiler** | `telos/tir_compiler.py` | TIR → SciPy `SLSQP` |
| **MILP compiler** | `telos/compiler.py` | `TelosSchema` → PuLP (pure math) |
| **Canvas runtime** | `telos/runtime.py` | `TelosRuntime.tick` — memory, chained router → hardware, actuators |
| **Actuators** | `telos/actuators/` | `DockerActuator`, `KubernetesActuator` (`replicas_*`), `FinTechActuator` (`shares_*`) |
| **Canvas app** | `server.py` + `index.html` | FastAPI + WebSocket; thin shell around `TelosRuntime` |
| **Manifests** | `*.telos` + `telos/parser.py` | YAML → validated `TelosSchema` dict (`TelosParser.load`) |
| **Headless** | `headless.py` | `.telos` + parameter timeline + actuators (no UI) |
| **Demos** | `main.py` | CLI: intent → TIR → SciPy |

**SDK overview (imports, tick contract, custom actuators):** [docs/SDK.md](docs/SDK.md).

**OS design notes:** [docs/OS-V02-FRONTIERS.md](docs/OS-V02-FRONTIERS.md) · [docs/OS-V03-TEMPORAL.md](docs/OS-V03-TEMPORAL.md) · [docs/OS-V04-CANVAS.md](docs/OS-V04-CANVAS.md).

## Project layout

```
telos-framework/
├── telos/
│   ├── __init__.py          # TelosRuntime, actuators, __version__
│   ├── schema.py            # TIR (CLI / agent)
│   ├── models.py            # MILP TelosSchema (canvas)
│   ├── tir_compiler.py      # SciPy compiler for TIR
│   ├── compiler.py          # PuLP compiler for TelosSchema
│   ├── parser.py            # .telos YAML loader
│   ├── generator.py         # LLM -> .telos (TelosGenerator)
│   ├── debugger.py          # LatentDebugger / Chaos Monkey
│   ├── cli.py               # python -m telos
│   ├── __main__.py
│   ├── runtime.py           # Temporal OS loop + actuators
│   ├── agent.py
│   └── actuators/
│       ├── __init__.py
│       ├── base.py
│       └── docker.py
├── main.py                  # CLI demos (TIR + SciPy)
├── headless.py              # Daemon: infrastructure.telos + timeline
├── infrastructure.telos     # Example combined MILP manifest (YAML)
├── server.py                # FastAPI + WebSocket (uses SDK)
├── index.html               # Spatial canvas UI
├── docs/
│   ├── SDK.md               # Python SDK reference
│   ├── OS-V02-FRONTIERS.md
│   ├── OS-V03-TEMPORAL.md
│   └── OS-V04-CANVAS.md
├── requirements.txt
└── README.md
```

## Requirements

Python 3.10+ recommended (3.13 works in development).

## Install

**From a clone (editable, registers the `telos` CLI):**

```bash
cd telos-framework
python -m pip install -e ".[all]"   # core + docker + kubernetes + FastAPI server
# or minimal SDK only:
python -m pip install -e .
```

**PyPI-style package name:** `telos-os` (see `pyproject.toml`). Extras: `[docker]`, `[kubernetes]`, `[server]`, `[all]`.

**Legacy / dev requirements file:**

```bash
python -m pip install -r requirements.txt
```

License: **MIT** (`LICENSE`).

## Run

**Default demo** — load-balancing-style intent → agent → TIR → SciPy:

```bash
python main.py
```

**Finance demo** — hand-authored TIR (no LLM):

```bash
python main.py finance
```

## Telos OS canvas — `server.py` + `index.html`

The **spatial canvas** builds `{ router, hardware }` plus `parameters` and streams them over WebSocket (~20 Hz). The **heavy logic** lives in **`TelosRuntime`** inside `telos/runtime.py`; **`server.py`** only handles HTTP/WebSocket and JSON.

1. **Router MILP:** `load_<id>`, flow conservation, caps, **heat** memory, costed objective.
2. **Hardware MILP:** integer `shards_<id>` vs routed load.
3. **Optional:** `DockerActuator` reconciles `shards_*` with real **Docker** containers (`nginx:alpine`).

```bash
python server.py
```

Open **`http://127.0.0.1:8000`** from the same origin (not `file://`). If port **8000** is busy: `TELOS_PORT` (PowerShell: `$env:TELOS_PORT=8010`). Optional `TELOS_RELOAD=1` (reload can be flaky with WebSockets on Windows).

## CLI — `python -m telos`

From the **`telos-framework`** directory (so the `telos` package is on the path):

```bash
# Natural language -> validated .telos (OpenAI or Ollama; same env vars as TelosAgent)
python -m telos generate "Your architecture in English..." --out global_router.telos

# Headless loop (default tick key `main`; optional JSON parameters file)
python -m telos run global_router.telos --interval 2 --no-docker

# Same with explicit actuator (docker | k8s | fintech | none)
python -m telos run hedge_fund.telos --actuator fintech --fintech-demo

# Install stub (writes .telos_modules/<name>.py only — no remote registry)
python -m telos install vendor/my-actuator

# Monte Carlo adversarial check (exit 2 if infeasible context found)
python -m telos test vulnerable.telos --iters 500
```

After `pip install -e .`, you can run the **`telos`** command globally (same subcommands as `python -m telos`).

**Backends:** `OPENAI_API_KEY` for OpenAI, or `TELOS_LLM_BACKEND=ollama` with `ollama serve` and `TELOS_OLLAMA_MODEL`. Override chat model with **`TELOS_GENERATOR_MODEL`** (default `gpt-4o`).

## Headless — `.telos` + `headless.py`

**Infrastructure-as-Physics:** define one combined MILP (loads, shards, memory, constraints) in **`infrastructure.telos`**, load with **`TelosParser`**, and call **`TelosRuntime.tick({"main": schema}, parameters)`**. No browser.

```bash
python headless.py
```

Uses **`DockerActuator`** if Docker is available (see [docs/SDK.md](docs/SDK.md)). The script sleeps **3 seconds** between timeline steps so container reconciliation is visible.

## Using the SDK in code

```python
from pathlib import Path
from telos import TelosRuntime, TelosParser, DockerActuator

rt = TelosRuntime()
rt.attach_actuator(DockerActuator())

# Canvas-style chained matrices
result = rt.tick(
    {"router": router_dict, "hardware": hardware_dict},
    {"cap_s1": 1.0, "cost_s1": 20.0},
)

# Or a single combined matrix from a .telos file
schema = TelosParser.load(Path("infrastructure.telos"))
result = rt.tick({"main": schema}, {"us_cap": 1.0, "eu_cost": 20.0})
```

See [docs/SDK.md](docs/SDK.md) for the full contract and security notes.

## Configuring the agent

`TelosAgent` picks a backend from **`TELOS_LLM_BACKEND`** (if set) or the constructor; otherwise **`auto`**:

| Order (`auto`) | Condition |
|----------------|-----------|
| OpenAI | `OPENAI_API_KEY` is set |
| Ollama | Ollama is reachable **and** the configured model is installed |
| Mock | Fallback (prints a warning) |

### Environment variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key |
| `TELOS_LLM_BACKEND` | `auto` · `openai` · `ollama` · `mock` |
| `OLLAMA_HOST` | Ollama base URL (default `http://127.0.0.1:11434`) |
| `TELOS_OLLAMA_MODEL` | Model name (default `llama3.2`) |
| `TELOS_PORT` | Canvas HTTP port (default `8000`) |
| `TELOS_RELOAD` | `1` / `true` for uvicorn autoreload |

**Ollama:** run `ollama serve`, then `ollama pull <model>` for `TELOS_OLLAMA_MODEL`.

## TIR shape (SymPy / SciPy reference)

Expressions must be valid for **SymPy** (`sympify`). Invariants: **`eq`** → expression == 0, **`ineq`** → expression ≥ 0.

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

Build in code with `TIRSchema` / nested models (`telos/schema.py`, `main.py`). Optional **`ontology.parameters`** name symbols filled from runtime context.

## Limitations

- **TIR track:** continuous `SLSQP` only; no mixed-integer guarantees.
- **MILP track:** CBC via PuLP; `eval` on objectives/constraints — **trusted input only** unless you add a safe evaluator.
- Prototype “executable matrix” is a **dict of numbers**, not a binary tensor format.

## License

[MIT](LICENSE) — see `LICENSE` in this directory.

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for dev setup, **pytest**, and PR expectations. Issues and PRs welcome: safer parsing, extra solvers, actuator plugins, PyPI polish, or richer matrix graphs. By contributing, you agree your contributions are under the same terms as this project (MIT).

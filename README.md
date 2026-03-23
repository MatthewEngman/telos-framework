# Telos

**Telos** (Telos OS) is an experimental **Infrastructure-as-Physics** toolkit: you describe goals and constraints as math, and a solver plus optional **actuators** (for example Docker) turn that into behavior over time.

**First time here?** Open the beginner guide: **[telos-framework/docs/START_HERE.md](telos-framework/docs/START_HERE.md)** (glossary, first commands, no optimization background needed).

Source layout: the framework lives under [`telos-framework/`](telos-framework/).

## What you get

| Track | What it is |
|-------|------------|
| **MILP SDK** | Pydantic [`TelosSchema`](telos-framework/telos/models.py), PuLP compiler, [`TelosRuntime`](telos-framework/telos/runtime.py) (memory + chained solves), pluggable [`BaseActuator`](telos-framework/telos/actuators/base.py) |
| **`.telos` manifests** | YAML on disk, loaded with [`TelosParser`](telos-framework/telos/parser.py), validated before run |
| **LLM → `.telos`** | [`TelosGenerator`](telos-framework/telos/generator.py) + `python -m telos generate` (OpenAI or Ollama) |
| **QA / fuzz** | [`LatentDebugger`](telos-framework/telos/debugger.py) + `python -m telos test` (Monte Carlo parameters, witness constraints) |
| **Spatial canvas** | [`server.py`](telos-framework/server.py) + [`index.html`](telos-framework/index.html) — WebSocket IDE, router + hardware MILP |
| **TIR + SciPy** | Classic [`TIRSchema`](telos-framework/telos/schema.py) + [`tir_compiler`](telos-framework/telos/tir_compiler.py) for continuous optimization ([`main.py`](telos-framework/main.py) demos) |

## Quick start

```bash
cd telos-framework
python -m pip install -e ".[all]"
# Global CLI: telos --help
```

**Browser canvas** (open `http://127.0.0.1:8000` from that host, not `file://`):

```bash
python server.py
```

**Headless demo** (example timeline + optional Docker):

```bash
python headless.py
```

**CLI**:

```bash
python -m telos generate "Describe routing, costs, caps, shards..." --out app.telos
python -m telos run app.telos --no-docker
python -m telos test vulnerable.telos --iters 500
```

**TIR demos** (intent → LLM → SciPy, or hand-authored finance):

```bash
python main.py
python main.py finance
```

## Documentation

- **Start here (beginners):** [`telos-framework/docs/START_HERE.md`](telos-framework/docs/START_HERE.md)
- **Full framework guide** (architecture, env vars, TIR reference): [`telos-framework/README.md`](telos-framework/README.md)
- **SDK API** (tick contract, security): [`telos-framework/docs/SDK.md`](telos-framework/docs/SDK.md)
- **Actuators** (implement, naming, FAQ): [`telos-framework/docs/ACTUATORS.md`](telos-framework/docs/ACTUATORS.md)
- **Example `.telos` set**: [`telos-framework/examples/README.md`](telos-framework/examples/README.md)

## Requirements

- **Python** 3.10+ (3.13 OK in development)
- **Optional:** Docker Desktop for [`DockerActuator`](telos-framework/telos/actuators/docker.py)
- **Optional:** `OPENAI_API_KEY` or local **Ollama** for agent / `telos generate`

## Security

MILP objectives, constraints, and memory updates use restricted **`eval`**. Treat **canvas JSON**, **`.telos` files**, and **LLM output** as **trusted** input unless you add a hardened expression layer.

## License

The framework is released under the [MIT License](telos-framework/LICENSE) ([`telos-framework/LICENSE`](telos-framework/LICENSE)).

## Contributing

See [`telos-framework/CONTRIBUTING.md`](telos-framework/CONTRIBUTING.md) for environment setup and running tests. Issues and PRs welcome. Contributions are expected to be under the MIT license unless you state otherwise in the PR.

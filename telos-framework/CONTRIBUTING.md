# Contributing

Thanks for helping improve Telos. Contributions are licensed under the same terms as this project ([MIT](LICENSE)).

**New to the codebase?** Skim **[docs/START_HERE.md](docs/START_HERE.md)** so `.telos`, `tick`, and actuators match the mental model used in issues and PRs.

## Setup

```bash
cd telos-framework
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
python -m pip install -e ".[all]"
python -m pip install -e ".[dev]"
```

`[all]` pulls optional extras (Docker, Kubernetes, FastAPI server). For a minimal SDK-only environment you can use `pip install -e .` and `pip install -e ".[dev]"` only.

## Tests

```bash
cd telos-framework
pytest
```

Tests avoid the network, Docker, and Kubernetes. They cover the PuLP compiler, YAML parsing, a single-matrix `TelosRuntime.tick`, and the debugger’s feasibility check on `vulnerable.telos`.

## CI/CD

- **CI:** [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on push/PR to `main` or `master`: editable install `telos-os` with `[dev]`, then `pytest` on Ubuntu (Python 3.10–3.13) and Windows (3.12).
- **Publish (optional):** [`.github/workflows/publish.yml`](../.github/workflows/publish.yml) is **manual** (`workflow_dispatch`). Prefer **PyPI Trusted Publishing** (OIDC): in PyPI account settings add this repo + workflow as a publisher, then run the workflow (no token). Alternatively set **`PYPI_API_TOKEN`** and uncomment the password line in the workflow. Bump **`version`** in `pyproject.toml` before each release.

## Pull requests

- Keep changes focused on one concern when possible.
- Run `pytest` before opening a PR.
- If you change CLI behavior or public APIs, update `README.md` and/or `docs/SDK.md` as needed.

## Security

MILP objectives and constraints are evaluated with restricted `eval`. Do not point untrusted `.telos` or WebSocket payloads at a production server without a hardened expression layer.

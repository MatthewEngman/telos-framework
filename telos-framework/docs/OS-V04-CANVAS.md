# Telos OS v0.4+ — Latent canvas (dynamic topology)

## What changed

- **No hardcoded `schema_a` / `schema_b`** in the app server. The backend runs **`TelosCompiler.compile`** (PuLP) on JSON validated as **`TelosSchema`** (`telos/models.py`), orchestrated by **`TelosRuntime.tick`** (`telos/runtime.py`).
- **`server.py`** is a **thin FastAPI shell**: WebSocket in/out only; all math and memory live in the **SDK**.
- **`index.html`** is a **vanilla JS + SVG** node editor: **TRAFFIC** source, draggable **server** nodes, wires from source → servers, sliders for **capacity** and **base cost** per node.
- **`buildDynamicSchema()`** (client) constructs:
  - **Router MILP:** `load_<id>` variables, flow conservation `Σ load = 1`, caps `cap - load ≥ 0`, per-node **heat** memory and objective `(cost + heat) * load`.
  - **Hardware MILP:** integer `shards_<id>`, `shards ≥ load * 10`.
- **WebSocket payload:** `{ schema: { router, hardware }, parameters: { cap_*, cost_* } }` every **50 ms** while connected and geometry exists.

## Server / SDK behavior

- **Temporal memory:** `TelosRuntime` applies the same semantics as v0.3: **`dt`** capped to **1 s**; memory keys pruned when nodes disappear from `schema.router.memory`.
- **Chaining:** router solution is merged into the hardware context.
- **Actuators:** after a successful tick, merged state is passed to **`BaseActuator.on_update`** (e.g. **`DockerActuator`** for `shards_*` → containers).
- **Errors:** compile / validation failures → **`FATAL CONFLICT`** JSON (optional `detail` string).

See also: [SDK.md](SDK.md) for the Python API.

## Limits

- **Trusted client:** the canvas builds math strings; restricted **`eval`** on the server is only safe in this demo if you trust the page.
- **Topology:** only **source → server** edges are modeled (no server–server graph in this prototype).
- **CLI TIR** (`main.py`, `telos/tir_compiler.py`) is a **separate** stack from the canvas MILP path.

## Try it

```bash
python server.py
```

Open the app from **`http://127.0.0.1:<port>/`** (set **`TELOS_PORT`** if needed). Add two servers, wire both from TRAFFIC, then tighten one server’s capacity to see load shift.

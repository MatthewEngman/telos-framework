# Telos OS v0.2 — Architecture frontiers

This note records the **design intent** and **what the repository implements** for the step from a single-shot mathematical compiler to a **multi-matrix, hot-patchable runtime** exposed through the browser.

---

## Crossing the Rubicon

**Telos Framework (v0.1 lineage)** centered on a pipeline:

**human intent → TIR (validated schema) → continuous solver → numeric state.**

**Telos OS v0.2+** adds a second track aimed at an **operating-system metaphor**: multiple coupled optimizations, discrete decisions, live parameters, and in-session edits to the math—without redeploying code. The canvas is the first end-to-end sketch of that track.

The CLI path (`main.py`, `telos/tir_compiler.py`, `telos/schema.py`) **remains** on **SymPy + SciPy** and **Pydantic TIR**. The **canvas** uses **`TelosSchema`** (`telos/models.py`), **PuLP (CBC)**, and **`TelosRuntime`** (`telos/runtime.py`), with **`server.py`** as a thin transport layer. Both stacks coexist deliberately.

---

## Frontier 1 — Discrete variables (MILP engine)

### Intent

Replace “everything is a smooth percentage” with a solver that distinguishes:

- **Continuous** decision variables (e.g. fractional load splits), and  
- **Integer** decision variables (e.g. indivisible shards, servers, replicas).

Mixed-integer linear programming (MILP) is the standard industrial tool for that distinction.

### Implementation

- **`TelosCompiler`** in `telos/compiler.py` builds a **PuLP** problem per `TelosSchema`.
- Variable metadata includes `type: "float"` → `LpContinuous`, `type: "int"` → `LpInteger`.
- Objectives and constraints are **linear** in those variables (CBC requirement). Expressions are still assembled via restricted **`eval`** over an environment of PuLP variables and numeric context—**not safe for untrusted input**; a production system would replace this with a vetted AST or codegen layer.

### Relation to SciPy

SciPy is **not** removed: it powers **`telos/tir_compiler.py`** for the original TIR demos. The **OS canvas** is the MILP frontier; unifying both under one IR is future work.

---

## Frontier 2 — Matrix composability (the DAG)

### Intent

Treat the system as a **directed acyclic graph** of **matrices** (optimization problems): outputs of upstream nodes become **constants** (or parameters) in downstream constraints. In the story:

- **Matrix A (Traffic Router):** continuous loads under cost and capacity “walls.”
- **Matrix B (Hardware provisioning):** integer shard counts so that capacity tracks routed load (e.g. shards sufficient for each region’s share).

This is **compositional economics**: routing and provisioning are separate problems **chained** by data, not by hand-written `if/else` routing code.

### Implementation (prototype scope)

The current graph is intentionally minimal: a **linear chain** `A → B`, implemented inside **`TelosRuntime.tick`** (`router` then `hardware`), not a general DAG editor.

1. Solve **A** with context from sliders (`cap_*`, `cost_*`, …) and decision variables `load_*`.
2. Merge **`out_a`** into the context for **B** as fixed floats (`load_*`, …).
3. Solve **B** for integer `shards_*` subject to e.g. `shards_k ≥ load_k * 10` (encoded as `ineq`: `shards_k - (load_k * 10) ≥ 0`).

The WebSocket payload returns both **`router`** and **`db`** so the UI can show fluid percentages and discrete “shard” glyphs together.

### Future

- Explicit **graph definition** (nodes, edges, topological tick).
- Cycles forbidden by construction; **scc**-style validation if the model grows.

---

## Frontier 3 — Local agent terminal (intent → hot patch)

### Intent

Embed a **command line** in the UI so operators can steer the system with **natural language**—interpreted as **edits to the live schema** (new invariants, parameter semantics, etc.) **without restart**.

### Implementation (prototype scope)

Earlier prototypes described a **keyword router** over the WebSocket (`ban asia`, `reset`, etc.). The **current canvas** focuses on **spatial geometry** (nodes + wires + sliders); a full in-UI terminal may be reintroduced as a layer that mutates the same JSON the client already sends. Plugging in **`TelosAgent`** or another parser for free-form English remains a direct extension.

### Narrative vs. math (good to know)

With **ban asia**-style constraints active, optimal traffic splits still follow **costs** and remaining caps. The **machinery** (hot constraints + MILP) is what the prototype proves; scenario copy can be tightened separately.

---

## How to run the canvas

```bash
cd telos-framework
python -m pip install -r requirements.txt
python server.py
```

Open **`http://127.0.0.1:8000`** from a **normal browser** (Chrome/Edge). Do **not** open `index.html` via `file://`—the WebSocket URL will be wrong.

| Environment variable | Purpose |
|---------------------|---------|
| `TELOS_PORT` | Listen port (default `8000` if busy, e.g. `8010`). |
| `TELOS_RELOAD` | Set to `1` for uvicorn reload (can be flaky with WebSockets on Windows). |

The UI **auto-reconnects** if the socket drops; uvicorn can use WebSocket ping options to reduce idle timeouts.

---

## Test protocol (MILP + composition)

### 1. Chaining and integer shards

1. Load the canvas; confirm **OS STABLE** and non-zero shard boxes when traffic splits.
2. Move **capacity** on one server down. Watch **load** shift; **shard** counts move in **whole** steps per the MILP constraints.

### 2. Latency

Solve time is typically **milliseconds** on a laptop for this toy size; the UI shows **`ms`** in the status line. This is not a guarantee for large MILPs.

---

## Honest scope summary

| Claim | Prototype reality |
|--------|-------------------|
| “Ripped out SciPy” | SciPy **remains** for `telos/tir_compiler.py` / CLI; **canvas** uses PuLP. |
| Full DAG | **Two-node chain** A→B inside `TelosRuntime` only. |
| “AI” terminal | **Spatial canvas** in tree; keyword/LLM terminal is an optional extension. |
| No `if/else` | **Routing** is optimization; any **agent** layer still uses `if` to map phrases to schema edits. |

---

## Closing line of sight

Telos OS v0.2 is a **working sketch**: MILP for discrete structure, **composition** of two matrices over a WebSocket tick, and room for **live schema mutation** from an intent layer. The **SDK** (`telos/runtime.py`, `telos/actuators/`) packages that loop for reuse outside FastAPI. Tightening the IR, securing expression evaluation, generalizing the graph, and wiring a real intent layer are the next engineering passes—not contradictions of the frontier, but the work that turns the metaphor into production.

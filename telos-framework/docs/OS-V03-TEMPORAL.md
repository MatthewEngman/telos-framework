# Telos OS v0.3 — Temporal calculus (memory / “heat”)

## Idea

Instead of imperative rate limits (`if requests > N then block`), the **router MILP** sees **time-varying effective costs**: each tick, regions (or nodes) accumulate **heat** when their *previous* load share stayed above a threshold (~60%). Heat is a **constant** in the next linear objective (e.g. `(10 + heat_us) * load_us`), so the solver can **shift traffic away** as if that region became more expensive. Heat also **decays** when load drops below the threshold.

Older fixed-topology demos singled out US/EU; the **canvas** applies the same law per **wired server node**.

## Where it lives

- **`schema.router.memory`** — list of `{ name, init, update }`. The `update` string is evaluated with previous **router** decision values, current `memory_state`, `dt`, and `min`/`max`. Still **`eval`** — treat as **trusted** config only.
- **`TelosRuntime`** (`telos/runtime.py`) — memory runs **before** each router/hardware compile chain; `dt` is capped (0–1s) to avoid huge jumps after tab sleep or reconnect.
- **WebSocket payload** — includes `"memory": { "heat_s1": …, … }` for the UI.
- **UI** (`index.html`) — ~**20 Hz** telemetry (`setInterval` 50ms) so `dt` stays small; heat bars reflect accumulated heat.

## What did not change

- **Hardware** matrix (integer shards) still chains off **router** outputs.
- **CLI TIR** path (`main.py`, `telos/tir_compiler.py`, `telos/schema.py`) is unchanged: **SciPy** continuous optimization, not PuLP.

## Limits

- This is a **discrete-time integrator**, not a continuous ODE solver.
- Objective must stay **linear in decision variables**; heat must enter as **constants** per tick.

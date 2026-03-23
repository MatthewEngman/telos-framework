# Start here (beginner-friendly)

This page assumes you know **basic Python** (run scripts, `pip install`) and can use a **terminal**. You do **not** need a background in optimization or operations research.

---

## 1. What Telos does in one paragraph

You describe a **decision problem** in a YAML file (a **`.telos` manifest**): *what* the solver may change (**variables**), *what* you want to achieve (**objective**), and *what rules* must hold (**constraints** / **invariants**). A **MILP solver** (PuLP/CBC) finds values that respect the rules and optimize the goal. **`TelosRuntime`** runs that solve on a schedule (a **tick**), optionally updates **memory**, and calls **actuators** so numbers can drive Docker, Kubernetes, or your own code—**only if** you attach them.

---

## 2. Glossary

| Term | Plain meaning |
|------|----------------|
| **Variable** | A number the solver chooses within bounds (`float` or `int` in `.telos`). |
| **Parameter** | A number **you** supply each run—not chosen by the solver. |
| **Objective** | Minimize or maximize a **linear** expression over variables and parameters. |
| **Constraint / invariant** | **`eq`**: expression == 0 when satisfied. **`ineq`**: expression ≥ 0. |
| **MILP** | Mixed-integer linear programming. Telos builds a MILP from your manifest. |
| **Manifest (`.telos`)** | YAML: ontology, teleology, invariants (and optional memory). |
| **`tick`** | One cycle: compile/solve, merge **state**, notify actuators. |
| **Actuator** | Runs **after** a successful solve; reads `state` and performs side effects. |
| **Trusted configuration** | MILP strings use a **linear parser**; memory updates use a **scalar** grammar with `max`/`min`. No `eval` on those paths—still treat manifests and LLM drafts as **trusted** (supply chain + correctness). |

---

## 3. Experimental note: TIR / continuous mode

The repository also contains **TIR** (`telos/schema.py`) and **SciPy** demos in `main.py`—**fractional** variables, no mixed-integer guarantees. That path is **experimental** and separate from the **canonical** `.telos` MILP workflow. New users should ignore it until the MILP path is comfortable.

---

## 4. Your first five minutes

**A — Python 3.10+**  
`python --version` or `py --version` (Windows).

**B — Install**

```bash
cd telos-framework
python -m pip install -e .
```

**C — Validate and run (no Docker)**

```bash
telos validate examples/router_minimal.telos
telos run examples/router_minimal.telos --actuator none --params examples/params/router_minimal.json
```

- **`validate`** — YAML + schema check; **`--strict`** runs one PuLP solve with probe parameters (optional `--params` JSON).  
- **`run`** — solver loop; **`--actuator none`** — math only.  
- **`--params`** — JSON for `ontology.parameters`. **Ctrl+C** stops the loop.

**D — Fuzz test (quality check)**

```bash
telos test vulnerable.telos --iters 200
```

Exit **2** if an infeasible random context is found.

**E — Another domain**

```bash
telos run examples/energy_dispatch.telos --actuator none --params examples/params/energy_dispatch.json
```

More examples: [examples/README.md](../examples/README.md).

---

## 5. How to read a `.telos` file

Open `examples/router_minimal.telos`.

1. **`ontology.variables`** — Names, types (`float`/`int`), bounds.
2. **`ontology.parameters`** — Names you must supply (JSON or code).
3. **`teleology.direction`** — `minimize` or `maximize`.
4. **`teleology.objective`** — Linear expression string.
5. **`invariants`** — `eq` / `ineq` rules as above.

If constraints cannot be satisfied, the runtime reports a non-healthy status.

---

## 6. What `telos run` does

1. Load and validate YAML → schema dict.  
2. Build **`TelosRuntime`**, optionally attach an **actuator**.  
3. Each iteration: **`tick`** with your parameters.  
4. Inside **`tick`**: MILP compile/solve → **`state`** → **`actuator.on_update`**.  
5. Print **`[MATH]`** or an error; sleep **`--interval`**; repeat.

Router/hardware splits and memory: [SDK.md](./SDK.md).

---

## 7. Actuators

Optional. When you want real side effects, read **[ACTUATORS.md](./ACTUATORS.md)** (`shards_*`, `replicas_*`, `shares_*`).

---

## 8. Other commands

| Command | Purpose |
|---------|---------|
| `telos --help` | Subcommands |
| `telos generate "..." --out x.telos` | Optional LLM draft (trusted input; review before use) |
| `python server.py` | Optional browser canvas |
| `python main.py` | **Experimental** TIR + SciPy demo only |

---

## 9. Where to read next

| Document | Best for |
|----------|----------|
| [README.md](../README.md) | Layout, env vars, canvas |
| [SDK.md](./SDK.md) | Python API, expression engines |
| [ACTUATORS.md](./ACTUATORS.md) | Custom actuators |
| [examples/README.md](../examples/README.md) | Learning progression |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Tests, PRs |

---

## 10. Common issues

- **`ModuleNotFoundError: telos`** — Install with `-e .` from `telos-framework` or activate the venv you used.  
- **Missing parameters** — Supply `--params` JSON matching `ontology.parameters`.  
- **Docker/K8s errors** — Use `--actuator none` until you intend real side effects.  
- **Untrusted files** — Do not load random `.telos` from the internet without inspection; they still define executable optimization geometry for your process.

If you are stuck, open an issue with the **command** and **full error text**.

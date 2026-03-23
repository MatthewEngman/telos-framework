# Start here (beginner-friendly)

This page assumes you know **basic Python** (run scripts, `pip install`) and can use a **terminal**. You do **not** need a background in optimization or operations research.

---

## 1. What Telos does in one paragraph

You describe a **decision problem** in a YAML file (a **`.telos` manifest**): *what* you can adjust (variables), *what* you want to achieve (objective), and *what rules* must hold (constraints). A **solver** finds numeric values for those variables that obey the rules and optimize the goal. Optionally, **actuators** take those numbers and drive real systems (Docker, Kubernetes) or print demo trading logs—but the math engine itself only computes; it does not call APIs unless you attach an actuator.

---

## 2. Glossary (terms you will see everywhere)

| Term | Plain meaning |
|------|----------------|
| **Variable** | A number the solver is allowed to choose (within bounds you give), e.g. “how much load goes to Europe.” |
| **Parameter** | A number **you** supply each run (from code or a JSON file)—not chosen by the solver. Example: “current price of electricity.” |
| **Objective** | What you want to minimize or maximize, written as a formula using variables and parameters. |
| **Constraint / invariant** | A rule that must hold. **`eq`** means “this expression equals zero.” **`ineq`** means “this expression is greater than or equal to zero” (Telos convention). |
| **MILP** | **Mixed-integer linear programming.** “Linear” = only sums and multiples (no `x*y` in the official model). “Mixed-integer” = some variables must be whole numbers (e.g. container counts). Telos builds a MILP from your `.telos` file and sends it to **PuLP** (solver backend **CBC**). |
| **Manifest (`.telos`)** | A YAML file listing ontology (variables + parameters), teleology (direction + objective), and invariants (constraints). |
| **`tick`** | One full cycle: advance simulated time a bit, run the solver(s), merge results, notify actuators, return status and **state** (the variable values). |
| **Actuator** | A small Python class that runs **after** each successful solve. It reads the solution (e.g. `shards_us=3`) and can start Docker containers, scale Kubernetes Deployments, or log fake trades. |
| **TIR** | **Telos Intermediate Representation**—another, older JSON-shaped format for **continuous** problems solved with **SciPy**, often produced by an LLM. Used by `main.py` demos. Different code path from `.telos` MILP. |
| **Trusted input** | Manifests use string expressions evaluated in Python. Only load `.telos` files you trust—treat them like code. |

---

## 3. Two tracks (do not mix them up at first)

| Track | Typical entry | Solver | Good for |
|--------|----------------|--------|----------|
| **MILP + `.telos`** | `telos run file.telos`, `examples/`, [SDK.md](./SDK.md) | PuLP / CBC | Integer decisions (shards, replicas), YAML workflows |
| **TIR + SciPy** | `python main.py` | SciPy SLSQP | Quick continuous demos, LLM → TIR |

This repo supports **both**. New users should pick **one** path for the first day. The **easiest** path is: install → run an **example** `.telos` with **`--params`** (next section).

---

## 4. Your first 15 minutes

**Step A — Install Python 3.10+**  
Check: `python --version` or `py --version` (Windows).

**Step B — Get the code and install Telos (editable)**  

```bash
cd telos-framework
python -m pip install -e .
```

This installs the **`telos`** command and the `telos` Python package. For Docker/Kubernetes extras later: `python -m pip install -e ".[all]"`.

**Step C — Run one example (math only, no Docker required)**  

From inside `telos-framework/`:

```bash
python -m telos run examples/router_minimal.telos --actuator none --params examples/params/router_minimal.json
```

- **`run`** — load the manifest, loop, call the solver each tick.  
- **`--actuator none`** — no Docker/Kubernetes; only print the math result.  
- **`--params ...json`** — fills in **parameters** named in the manifest (`east_latency_weight`, etc.). Press **Ctrl+C** to stop.

You should see lines like `[MATH] ...` with variable names and numbers. That is the solver’s answer for that tick.

**Step D — Try another domain**  

Same pattern; only the file and params change:

```bash
python -m telos run examples/energy_dispatch.telos --actuator none --params examples/params/energy_dispatch.json
```

More samples: [examples/README.md](../examples/README.md).

---

## 5. How to read a `.telos` file

Open `examples/router_minimal.telos` in an editor.

1. **`ontology.variables`** — Names and types the solver may change (`float` or `int`), each with **bounds** (allowed min/max).
2. **`ontology.parameters`** — Names of inputs **you** must supply (via `--params` JSON or code). They appear in formulas but are not “decision variables.”
3. **`teleology.direction`** — `minimize` or `maximize`.
4. **`teleology.objective`** — A string expression (linear in variables) using `+`, `*`, etc.
5. **`invariants`** — Rules:
   - **`eq`**: expression should be **0** when satisfied (e.g. total load sums to 1).
   - **`ineq`**: expression should be **≥ 0** (e.g. capacity minus usage).

If something is “infeasible,” no assignment of variables satisfies all constraints; the runtime reports a failure status (see CLI output).

---

## 6. What `telos run` does (step by step)

1. Load and validate YAML → internal **schema**.  
2. Build a **TelosRuntime** and optionally attach an **actuator** (`docker`, `k8s`, `fintech`, or `none`).  
3. Each loop iteration: pass your **parameters** (dict) and run **`tick`**.  
4. Inside **`tick`**: compile to a MILP, solve, collect variable values into **`state`**, call **`actuator.on_update(state)`**.  
5. Print **`[MATH]`** (or an error). Sleep **`--interval`** seconds. Repeat until Ctrl+C.

Details and edge cases (router/hardware split, memory): [SDK.md](./SDK.md).

---

## 7. Actuators (when you are ready)

You do **not** need actuators to learn Telos. When you want side effects (containers, cluster scale, demo “trades”), read **[ACTUATORS.md](./ACTUATORS.md)**. It explains naming (`shards_*`, `replicas_*`, `shares_*`) and how to write your own small plugin.

---

## 8. Other useful commands

| Command | Purpose |
|---------|---------|
| `telos --help` | List subcommands. |
| `python -m telos test some.telos` | Randomly vary parameters to hunt for impossible constraint sets (quality check). |
| `python -m telos generate "..." --out out.telos` | LLM writes a draft `.telos` (needs API key or Ollama—see main README). |
| `python server.py` | Browser **canvas** demo (optional; see [README](../README.md)). |

---

## 9. Where to read next

| Document | Best for |
|----------|----------|
| [README.md](../README.md) | Full project layout, env vars, canvas, TIR reference |
| [SDK.md](./SDK.md) | Python API, `tick` contract, module map |
| [ACTUATORS.md](./ACTUATORS.md) | Implementing and choosing actuators |
| [examples/README.md](../examples/README.md) | Table of example manifests + CLI one-liners |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Tests, PRs, dev setup |

---

## 10. Common beginner issues

- **`ModuleNotFoundError: telos`** — Run commands from the **`telos-framework`** directory after `pip install -e .`, or use a virtual environment where you installed the package.  
- **Missing parameters** — If the manifest lists `ontology.parameters`, you must pass them (JSON file with `--params` or defaults from the CLI for some demos).  
- **Docker/K8s errors** — Use `--actuator none` until you intentionally want real side effects; install `[docker]` or `[kubernetes]` extras when needed.  
- **“Trusted input”** — Do not run random `.telos` files from the internet without inspection; expressions execute as code under a restricted evaluator.

If you are stuck, open an issue with the **command you ran** and the **full error text**.

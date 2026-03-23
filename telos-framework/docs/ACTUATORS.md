# Actuators: guide and FAQ

**Actuators** are optional plugins that run **after** each successful MILP solve. `TelosRuntime` merges variable values from the compiler(s), then calls `on_update(optimal_state)` on every attached actuator. The solver does not talk to Docker, Kubernetes, or brokers by itself—the actuator is the narrow bridge from **math** to **machinery**.

## Built-in actuators

| Class | Extra / dependency | Watches keys in `optimal_state` | Effect |
|--------|-------------------|----------------------------------|--------|
| `DockerActuator` | `pip install 'telos-os[docker]'`, Docker daemon | `shards_<node_id>` (integers) | Reconciles `nginx:alpine` containers per node id |
| `KubernetesActuator` | `pip install 'telos-os[kubernetes]'`, kubeconfig | `replicas_<deployment>` (integers) | Patches Deployment scale in a namespace |
| `FinTechActuator` | core only | `shares_<TICKER>` (floats) | Logs paper BUY/SELL (not a real broker) |

If the optional SDK is missing or the cluster/daemon is unreachable, Docker and Kubernetes actuators stay in **simulation mode** (no fatal error; they log and skip side effects).

## Naming convention for new actuators

Pick a **stable prefix** for MILP variable names so your actuator can filter `optimal_state` without colliding with unrelated variables:

- `shards_*` — already used by Docker
- `replicas_*` — already used by Kubernetes
- `shares_*` — already used by FinTech demo

For a custom integration (e.g. `valve_open_*`, `budget_usd_*`), use a clear prefix and document it next to your `.telos` files.

## How to implement a custom actuator

1. Subclass `BaseActuator` from `telos.actuators.base`.
2. Implement `on_update(self, optimal_state: dict) -> None`.
3. **Filter** keys you care about; ignore the rest.
4. Attach before ticking:

```python
from telos import TelosRuntime, BaseActuator

class PrintDeltaActuator(BaseActuator):
    def __init__(self) -> None:
        self._prev: dict = {}

    def on_update(self, optimal_state: dict) -> None:
        for k, v in optimal_state.items():
            if k.startswith("load_") and k in self._prev and self._prev[k] != v:
                print(f"{k}: {self._prev[k]} -> {v}")
        self._prev = dict(optimal_state)

rt = TelosRuntime()
rt.attach_actuator(PrintDeltaActuator())
```

5. **Threading:** long-running reconciliation (like the stock Docker/K8s loops) should use a daemon thread and a lock around shared `desired_state`, so `on_update` stays fast and the runtime is not blocked.

6. **Optional heavy dependencies:** use the same pattern as `kubernetes.py` / `docker.py`—`try: import ... except ImportError` and degrade to simulation so `pip install telos-os` still works without every backend.

7. **CLI:** `python -m telos run` only knows `docker`, `k8s`, `fintech`, `none`. To use a custom class from the shell, run a small Python script that attaches your actuator, or extend `telos/cli.py` locally.

## FAQ

**Why doesn’t the MILP compiler call my API directly?**  
Separation of concerns: the compiler is pure math (PuLP). Actuators are I/O and operational risk. You can test math without credentials or clusters.

**Can I attach multiple actuators?**  
Yes. `TelosRuntime.attach_actuator` stacks them; each receives the same merged `optimal_state` every tick. Order matters only if you rely on side effects from earlier actuators in the same process (there is no guaranteed cross-actuator ordering contract—keep actuators independent).

**What keys are in `optimal_state`?**  
Whatever variables the solved MILP produced for that tick, merged across router/hardware stages when applicable. Inspect with a logging actuator or print `result["state"]` from `tick`.

**Do I need an actuator for planning-only runs?**  
No. Use `--actuator none` or `TelosRuntime()` with no attachments.

**Are `.telos` files safe to download from the internet?**  
Treat them like code: objectives and constraints are evaluated with restricted `eval`. Only load manifests you trust, or replace evaluation with a safer layer.

**How do I test without real infrastructure?**  
Use `--actuator none`, or install without `[docker]` / `[kubernetes]`; built-in actuators log simulation mode. Unit tests can attach a `BaseActuator` that records `on_update` calls.

**Will `telos install` load my actuator from a hub?**  
Not yet. `telos install` is a **local stub** (writes under `.telos_modules/`). For now, ship actuators as Python modules (your package or `pip install`).

## See also

- [SDK.md](./SDK.md) — `tick` contract, module map, security note  
- [examples/README.md](../examples/README.md) — domain-diverse `.telos` samples and CLI hints  

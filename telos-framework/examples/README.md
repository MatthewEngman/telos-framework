# Example `.telos` manifests

Small, self-contained **MILP** stories in different domains. If you are new to Telos, read **[docs/START_HERE.md](../docs/START_HERE.md)** for a glossary (**MILP**, variables vs parameters) and your first terminal commands.

**What these files are:** Each `.telos` file is **YAML** text Telos loads as a **manifest**—a list of variables, an objective to minimize/maximize, and constraint rules. **Parameters** (inputs you set) are listed under `ontology.parameters` and supplied at run time via a **JSON** file (`examples/params/*.json`) or Python code. Each example here is written so `TelosParser` accepts it and one `TelosRuntime.tick({"main": schema}, parameters)` run reaches a **HEALTHY** solution with the matching params.

| File | Domain | Typical actuator |
|------|--------|------------------|
| `router_minimal.telos` | Two-region traffic + integer shards | `docker` (`shards_*`) |
| `k8s_replica_plan.telos` | Integer pod counts vs load | `k8s` (`replicas_*`) |
| `inventory_split.telos` | Two-warehouse fulfillment | `none` (planning only) |
| `energy_dispatch.telos` | Clean vs dirty generation mix | `none` |
| `manufacturing_mix.telos` | Product mix under hour budget | `none` |

The **portfolio** demo (`shares_*`, `fintech` actuator) lives at the package root: **`../hedge_fund.telos`**.

## Run from the `telos-framework` directory

```bash
# Planning-only (no Docker/K8s side effects)
python -m telos run examples/router_minimal.telos --actuator none --params examples/params/router_minimal.json

# With Docker reconciliation (needs Docker + pip install -e ".[docker]")
python -m telos run examples/router_minimal.telos --actuator docker

# Integer replica plan → cluster (needs kubeconfig + pip install -e ".[kubernetes]")
python -m telos run examples/k8s_replica_plan.telos --actuator k8s --params examples/params/k8s_replica_plan.json
```

JSON **parameter** files live under `examples/params/` and match each manifest’s `ontology.parameters` names exactly (`router_minimal.json`, `k8s_replica_plan.json`, etc.).

## Implementing your own actuator

See **[docs/ACTUATORS.md](../docs/ACTUATORS.md)** for naming conventions (`shards_*`, `replicas_*`, `shares_*`), FAQs, and a minimal `BaseActuator` subclass.

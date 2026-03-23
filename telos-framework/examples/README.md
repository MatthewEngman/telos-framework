# Example `.telos` manifests

Small, self-contained **MILP** stories in different domains. Each file is valid YAML for `TelosParser` and a single `TelosRuntime.tick({"main": schema}, parameters)`.

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

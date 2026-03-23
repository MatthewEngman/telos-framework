# Example `.telos` manifests — learning progression

Small **MILP** manifests in different domains. New users: **[docs/START_HERE.md](../docs/START_HERE.md)** (glossary, `telos validate` / `run` / `test`).

Each file is valid YAML that **`TelosParser`** accepts; with the matching **`examples/params/*.json`**, one **`TelosRuntime.tick({"main": schema}, params)`** reaches **HEALTHY**.

---

## Suggested order

1. **Minimal manifest** — `router_minimal.telos` + `params/router_minimal.json`: two-region traffic, integer **shards** (routing + discrete capacity story).
2. **Routing + hardware-style chain** — use the **canvas** or **`infrastructure.telos`** at repo root with [README](../README.md) headless/server docs (router + hardware matrices in one workflow).
3. **Memory over time** — see [docs/SDK.md](../docs/SDK.md) (`memory` on ontology, heat-style updates in canvas manifests).
4. **Actuator integration** — `router_minimal` with `--actuator docker` or `k8s_replica_plan.telos` with `--actuator k8s`; portfolio demo **`../hedge_fund.telos`** with `--actuator fintech`. Details: [docs/ACTUATORS.md](../docs/ACTUATORS.md).
5. **Debugger / paradox detection** — `telos test vulnerable.telos --iters 500` from repo root (see [README](../README.md)).
6. **Optional natural language** — `telos generate "..." --out draft.telos` then **`telos validate draft.telos`** before `run` (LLM output = **trusted input** after human review).

---

## Catalog

| File | Domain | Typical actuator |
|------|--------|------------------|
| `router_minimal.telos` | Two-region traffic + integer shards | `docker` (`shards_*`) |
| `k8s_replica_plan.telos` | Integer pod counts vs load | `k8s` (`replicas_*`) |
| `inventory_split.telos` | Two-warehouse fulfillment | `none` |
| `energy_dispatch.telos` | Clean vs dirty generation | `none` |
| `manufacturing_mix.telos` | Product mix under hour budget | `none` |

Portfolio demo (`shares_*`, fintech): **`../hedge_fund.telos`**.

---

## Commands (from `telos-framework/`)

```bash
telos validate examples/router_minimal.telos
telos validate examples/router_minimal.telos --strict

telos run examples/router_minimal.telos --actuator none --params examples/params/router_minimal.json

telos run examples/router_minimal.telos --actuator docker

telos run examples/k8s_replica_plan.telos --actuator k8s --params examples/params/k8s_replica_plan.json
```

Parameter JSON files under `examples/params/` must match each manifest’s `ontology.parameters` names.

---

## Custom actuators

[docs/ACTUATORS.md](../docs/ACTUATORS.md) — prefixes (`shards_*`, `replicas_*`, `shares_*`), `BaseActuator` subclass pattern.

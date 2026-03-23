"""`python -m telos` — generate .telos from intent, or run a manifest headlessly."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

from .actuators.docker import DockerActuator
from .actuators.fintech import FinTechActuator
from .actuators.kubernetes import KubernetesActuator
from .debugger import LatentDebugger
from .generator import TelosGenerator
from .models import TelosSchema
from .parser import TelosParser
from .runtime import TelosRuntime


def _attach_actuator(rt: TelosRuntime, choice: str) -> None:
    if choice == "docker":
        rt.attach_actuator(DockerActuator())
    elif choice == "k8s":
        rt.attach_actuator(KubernetesActuator())
    elif choice == "fintech":
        rt.attach_actuator(FinTechActuator())
    elif choice == "none":
        pass
    else:
        raise ValueError(f"Unknown actuator {choice!r}")


def _default_parameters(schema: Dict[str, Any]) -> Dict[str, float]:
    """Best-effort defaults for ontology.parameters when none are supplied."""
    names = (schema.get("ontology") or {}).get("parameters") or []
    params: Dict[str, float] = {}
    for name in names:
        lower = name.lower()
        if "yield" in lower:
            if "tsla" in lower:
                params[name] = 0.08
            elif "aapl" in lower:
                params[name] = 0.05
            else:
                params[name] = 0.05
        elif "price" in lower:
            if "tsla" in lower:
                params[name] = 200.0
            elif "aapl" in lower:
                params[name] = 150.0
            else:
                params[name] = 100.0
        elif "cost" in lower:
            params[name] = 20.0
        elif "cap" in lower:
            params[name] = 1.0
        else:
            params[name] = 1.0
    return params


def _cmd_generate(args: argparse.Namespace) -> int:
    try:
        gen = TelosGenerator()
        gen.generate(args.prompt, args.out)
    except Exception as e:
        print(f"\n[Telos CLI] ERROR: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        schema = TelosParser.load(path)
    except Exception as e:
        print(f"\n[Telos CLI] ERROR: {e}", file=sys.stderr)
        return 1

    if args.params:
        raw = Path(args.params).read_text(encoding="utf-8")
        telemetry = {k: float(v) for k, v in json.loads(raw).items()}
    else:
        telemetry = _default_parameters(schema)

    actuator = "none" if args.no_docker else args.actuator
    rt = TelosRuntime()
    try:
        _attach_actuator(rt, actuator)
    except Exception as e:
        print(f"\n[Telos CLI] ERROR: {e}", file=sys.stderr)
        return 1

    tick_key = args.matrix_key
    interval = float(args.interval)
    fintech_demo = bool(getattr(args, "fintech_demo", False))
    shock_applied = False

    print(f"[*] Running {path} (key={tick_key!r}, interval={interval}s, actuator={actuator})...")
    print(f"[*] Parameters: {telemetry}")
    print("    Ctrl+C to stop.\n")

    try:
        while True:
            result = rt.tick({tick_key: schema}, telemetry)
            if result["status"] == "HEALTHY":
                state = result["state"]
                parts = [f"{k}={float(v):.4g}" for k, v in sorted(state.items())]
                print(f"[MATH] {' | '.join(parts)}")
                if (
                    fintech_demo
                    and actuator == "fintech"
                    and not shock_applied
                    and "yield_tsla" in telemetry
                ):
                    shock_applied = True
                    time.sleep(min(interval, 2.0))
                    print("\n--- MARKET SHOCK: TSLA yield drops to 2% ---\n")
                    telemetry = dict(telemetry)
                    telemetry["yield_tsla"] = 0.02
                    continue
            else:
                detail = result.get("detail", "")
                print(f"[FATAL] {result['status']}" + (f" - {detail}" if detail else ""))
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[OS] Stopped.")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    """Stub for a future hub.telos.dev registry."""
    print("[*] Telos Actuator Hub (preview) - not yet connected to hub.telos.dev")
    time.sleep(0.3)
    print(f"[*] Reserving package name: {args.package!r}")
    time.sleep(0.3)
    root = Path.cwd() / ".telos_modules"
    root.mkdir(parents=True, exist_ok=True)
    safe = args.package.replace("/", "_").replace("\\", "_") + ".py"
    out = root / safe
    out.write_text(
        f"# Telos hub stub: {args.package}\n"
        "# Install a future published actuator wheel here.\n",
        encoding="utf-8",
    )
    print(f"[+] Wrote placeholder {out}")
    return 0


def _cmd_test(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        schema_dict = TelosParser.load(path)
        schema = TelosSchema.model_validate(schema_dict)
        ok = LatentDebugger.simulate(schema, args.iters)
        return 0 if ok else 2
    except Exception as e:
        print(f"\n[Telos CLI] ERROR: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="telos",
        description="Telos OS - .telos manifests and MILP runtime",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen_p = sub.add_parser("generate", help="Generate a .telos file from natural language")
    gen_p.add_argument("prompt", type=str, help="Plain-English architecture / physics")
    gen_p.add_argument(
        "--out",
        type=str,
        default="generated.telos",
        help="Output path (default: generated.telos)",
    )
    gen_p.set_defaults(func=_cmd_generate)

    run_p = sub.add_parser("run", help="Run a .telos file headlessly (loop)")
    run_p.add_argument("file", type=str, help="Path to .telos")
    run_p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between ticks (default: 2)",
    )
    run_p.add_argument(
        "--matrix-key",
        type=str,
        default="main",
        help="Key passed to TelosRuntime.tick (default: main)",
    )
    run_p.add_argument(
        "--params",
        type=str,
        default="",
        help="JSON file of parameter floats for ontology.parameters",
    )
    run_p.add_argument(
        "--actuator",
        type=str,
        choices=("docker", "k8s", "fintech", "none"),
        default="docker",
        help="Side-effect backend (default: docker)",
    )
    run_p.add_argument(
        "--fintech-demo",
        action="store_true",
        help="After first healthy tick with fintech actuator, drop yield_tsla to 0.02",
    )
    run_p.add_argument(
        "--no-docker",
        action="store_true",
        help="Shortcut for --actuator none",
    )
    run_p.set_defaults(func=_cmd_run)

    hub_p = sub.add_parser(
        "install",
        help="Placeholder for future Actuator Hub packages (hub.telos.dev)",
    )
    hub_p.add_argument(
        "package",
        type=str,
        help="Package id e.g. vendor/name (stub only)",
    )
    hub_p.set_defaults(func=_cmd_install)

    test_p = sub.add_parser(
        "test",
        help="Monte Carlo parameter fuzzing; report infeasible witness constraints",
    )
    test_p.add_argument("file", type=str, help="Path to .telos manifest")
    test_p.add_argument(
        "--iters",
        type=int,
        default=1000,
        help="Number of random contexts (default: 1000)",
    )
    test_p.set_defaults(func=_cmd_test)

    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()

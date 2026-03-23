"""`python -m telos` — generate .telos from intent, or run a manifest headlessly."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

from .actuators.docker import DockerActuator
from .generator import TelosGenerator
from .parser import TelosParser
from .runtime import TelosRuntime


def _default_parameters(schema: Dict[str, Any]) -> Dict[str, float]:
    """Best-effort defaults for ontology.parameters when none are supplied."""
    names = (schema.get("ontology") or {}).get("parameters") or []
    params: Dict[str, float] = {}
    for name in names:
        lower = name.lower()
        if "cost" in lower:
            params[name] = 20.0
        elif "cap" in lower:
            params[name] = 1.0
        elif "price" in lower:
            params[name] = 10.0
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

    rt = TelosRuntime()
    if not args.no_docker:
        rt.attach_actuator(DockerActuator())

    tick_key = args.matrix_key
    interval = float(args.interval)

    print(f"[*] Running {path} (tick key={tick_key!r}, interval={interval}s)...")
    print(f"[*] Parameters: {telemetry}")
    print("    Ctrl+C to stop.\n")

    try:
        while True:
            result = rt.tick({tick_key: schema}, telemetry)
            if result["status"] == "HEALTHY":
                state = result["state"]
                parts = [f"{k}={float(v):.4g}" for k, v in sorted(state.items())]
                print(f"[MATH] {' | '.join(parts)}")
            else:
                detail = result.get("detail", "")
                print(f"[FATAL] {result['status']}" + (f" - {detail}" if detail else ""))
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[OS] Stopped.")
    return 0


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
        "--no-docker",
        action="store_true",
        help="Do not attach DockerActuator",
    )
    run_p.set_defaults(func=_cmd_run)

    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()

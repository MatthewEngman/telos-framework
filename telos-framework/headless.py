"""Headless daemon: .telos manifest + live parameters, no canvas UI."""

from __future__ import annotations

import time
from pathlib import Path

from telos import DockerActuator, TelosParser, TelosRuntime

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "infrastructure.telos"


def main() -> None:
    print("===========================================")
    print("    TELOS OS: HEADLESS INFRASTRUCTURE      ")
    print("===========================================\n")

    schema = TelosParser.load(MANIFEST)

    os_runtime = TelosRuntime()
    os_runtime.attach_actuator(DockerActuator())

    timeline = [
        {"us_cap": 1.0, "eu_cost": 20.0, "event": "Systems nominal."},
        {"us_cap": 1.0, "eu_cost": 20.0, "event": "Stable."},
        {
            "us_cap": 0.4,
            "eu_cost": 20.0,
            "event": "WARNING: US datacenter hot - capacity capped at 40%.",
        },
        {"us_cap": 0.4, "eu_cost": 20.0, "event": "Stable at 40%."},
        {
            "us_cap": 1.0,
            "eu_cost": 20.0,
            "event": "RECOVERY: US datacenter cooling restored.",
        },
    ]

    print("\nStarting biological clock...")
    print("-" * 70)

    for context in timeline:
        event = context.pop("event", "")
        print(f"\n[REALITY] {event}")

        result = os_runtime.tick({"main": schema}, context)

        if result["status"] == "HEALTHY":
            state = result["state"]
            mem = result.get("memory", {})
            print(
                f"  -> MATH: load_us={state['load_us']:.2f} | load_eu={state['load_eu']:.2f}"
            )
            print(
                f"  -> SHARDS: shards_us={state['shards_us']:.0f} | "
                f"shards_eu={state['shards_eu']:.0f}"
            )
            print(f"  -> HEAT: heat_us={mem.get('heat_us', 0):.2f}")
        else:
            detail = result.get("detail", "")
            print(f"  -> [FATAL] {result['status']}" + (f": {detail}" if detail else ""))

        time.sleep(3)

    print("\n" + "-" * 70)
    print("Timeline complete.\n")


if __name__ == "__main__":
    main()

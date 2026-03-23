"""Docker: reconcile shard counts with nginx:alpine containers."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List

from .base import BaseActuator

try:
    import docker as docker_sdk
except ImportError:
    docker_sdk = None  # type: ignore[misc, assignment]


class DockerActuator(BaseActuator):
    def __init__(self) -> None:
        self.active = False
        self.desired_state: Dict[str, int] = {}
        self.running_containers: Dict[str, List[Any]] = {}
        self.lock = threading.Lock()
        self.client: Any = None

        if docker_sdk is None:
            print("\n[DockerActuator] docker package not installed. Simulation-only mode.\n")
            return

        try:
            self.client = docker_sdk.from_env()
            self.client.ping()
            self.active = True
            print("\n[DockerActuator] Connected to Docker daemon.")
            print("[DockerActuator] Purging old Telos-labeled containers...")
            for c in self.client.containers.list(
                all=True, filters={"label": "telos_framework=true"}
            ):
                try:
                    c.remove(force=True)
                except Exception as e:
                    print(f"[DockerActuator] Purge skip: {e}")
        except Exception as e:
            print(f"\n[DockerActuator] Docker unavailable ({e}). Simulation-only mode.\n")
            self.client = None
            return

        threading.Thread(target=self._sync_loop, daemon=True).start()

    def on_update(self, optimal_state: Dict[str, Any]) -> None:
        if not self.active or not optimal_state:
            return
        with self.lock:
            self.desired_state = {
                k.replace("shards_", "", 1): int(round(float(v)))
                for k, v in optimal_state.items()
                if k.startswith("shards_") and v is not None
            }

    def _sync_loop(self) -> None:
        assert self.client is not None
        print("[DockerActuator] Sync loop running.")
        try:
            self.client.images.pull("nginx:alpine")
        except Exception as e:
            print(f"[DockerActuator] Image pull (nginx:alpine): {e}")

        max_shards = 15
        while True:
            time.sleep(0.5)
            with self.lock:
                target = dict(self.desired_state)

            for node_id in list(self.running_containers.keys()):
                if node_id not in target:
                    for c in self.running_containers[node_id]:
                        try:
                            c.remove(force=True)
                        except Exception:
                            pass
                    del self.running_containers[node_id]

            for node_id, desired_count in target.items():
                if node_id not in self.running_containers:
                    self.running_containers[node_id] = []

                desired_count = min(max(0, desired_count), max_shards)
                current_count = len(self.running_containers[node_id])

                if desired_count > current_count:
                    diff = desired_count - current_count
                    print(
                        f"\n[DockerActuator] MITOSIS: {desired_count} shard(s) for node "
                        f"{node_id}; booting {diff} container(s)..."
                    )
                    for _ in range(diff):
                        try:
                            c = self.client.containers.run(
                                "nginx:alpine",
                                detach=True,
                                labels={"telos_framework": "true", "node": str(node_id)},
                            )
                            self.running_containers[node_id].append(c)
                        except Exception as e:
                            print(f"[DockerActuator] run error: {e}")

                elif desired_count < current_count:
                    diff = current_count - desired_count
                    print(
                        f"\n[DockerActuator] APOPTOSIS: node {node_id}; "
                        f"removing {diff} container(s)..."
                    )
                    for _ in range(diff):
                        c = self.running_containers[node_id].pop()
                        try:
                            c.remove(force=True)
                        except Exception:
                            pass

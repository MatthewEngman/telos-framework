"""Scale Kubernetes Deployments from MILP variables named replicas_<deployment>."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict

from .base import BaseActuator

try:
    from kubernetes import client, config
except ImportError:
    client = None  # type: ignore[misc, assignment]
    config = None  # type: ignore[misc, assignment]


class KubernetesActuator(BaseActuator):
    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self.active = False
        self.desired_state: Dict[str, int] = {}
        self.lock = threading.Lock()
        self.apps_v1: Any = None

        if client is None or config is None:
            print("\n[KubernetesActuator] kubernetes package not installed. Simulation mode.\n")
            return

        try:
            config.load_kube_config()
            self.apps_v1 = client.AppsV1Api()
            self.active = True
            print(
                f"\n[KubernetesActuator] Connected. Namespace: {namespace!r}\n"
            )
        except Exception as e:
            print(f"\n[KubernetesActuator] No cluster / kubeconfig ({e}). Simulation mode.\n")
            self.apps_v1 = None

        if self.active:
            threading.Thread(target=self._reconciliation_loop, daemon=True).start()

    def on_update(self, optimal_state: Dict[str, Any]) -> None:
        if not self.active or not optimal_state:
            return
        with self.lock:
            self.desired_state = {
                k.replace("replicas_", "", 1): int(round(float(v)))
                for k, v in optimal_state.items()
                if k.startswith("replicas_") and v is not None
            }

    def _reconciliation_loop(self) -> None:
        assert self.apps_v1 is not None
        while True:
            time.sleep(2.0)
            with self.lock:
                target = dict(self.desired_state)

            for deployment_name, desired in target.items():
                try:
                    scale = self.apps_v1.read_namespaced_deployment_scale(
                        deployment_name, self.namespace
                    )
                    current = scale.spec.replicas
                    if current == desired:
                        continue
                    print(
                        f"[KubernetesActuator] Scale {deployment_name!r}: "
                        f"{current} -> {desired}"
                    )
                    scale.spec.replicas = desired
                    self.apps_v1.patch_namespaced_deployment_scale(
                        deployment_name,
                        self.namespace,
                        scale,
                    )
                except Exception as e:
                    print(f"[KubernetesActuator] {deployment_name!r}: {e}")

"""Optional LLM: natural language → draft ``.telos`` YAML, then ``TelosSchema`` validation."""

from __future__ import annotations

import os
import urllib.error
from pathlib import Path
from typing import Literal, Optional

from openai import OpenAI

from .agent import (
    _env_backend,
    _http_json,
    _ollama_base_url,
    _ollama_model,
    _ollama_model_installed,
    _ollama_reachable,
)
from .parser import TelosParser

BackendName = Literal["auto", "openai", "ollama"]


def _strip_yaml_fence(text: str) -> str:
    raw = text.strip()
    if raw.startswith("```yaml"):
        raw = raw[7:]
    elif raw.startswith("```yml"):
        raw = raw[6:]
    elif raw.startswith("```"):
        raw = raw[3:]
    raw = raw.strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()
    return raw


class TelosGenerator:
    """
    Translate English intent into a `.telos` file.
    Uses the same backend selection as `TelosAgent` (`TELOS_LLM_BACKEND`, Ollama env vars).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        backend: BackendName = "auto",
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        openai_model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.openai_model = (
            openai_model
            or os.getenv("TELOS_GENERATOR_MODEL")
            or os.getenv("TELOS_OPENAI_MODEL")
            or "gpt-4o"
        )
        self.ollama_base_url = (ollama_base_url or _ollama_base_url()).rstrip("/")
        self.ollama_model = ollama_model or _ollama_model()

        env_b = _env_backend()
        self.backend: BackendName = (
            env_b if env_b in ("openai", "ollama", "auto") else backend  # type: ignore[assignment]
        )
        if env_b == "mock":
            self.backend = backend

        self.system_prompt = """
You are the Core Architect for Telos OS (Infrastructure-as-Physics).
Your ONLY job is to translate human intent into a valid `.telos` YAML manifest.

RULES OF TELOS PHYSICS:
1. "ontology.variables": list of {name: str, type: "float" | "int", bounds: [min, max]}.
2. "ontology.parameters": symbols filled from live data each tick; list of strings (use [] if none).
3. "teleology": "direction" (minimize | maximize) and "objective" (single-line math string).
4. "invariants": list of {type: "eq" | "ineq", expression: str}.
   - "eq": expression == 0 (e.g. load_us + load_eu - 1.0 for 100% routing).
   - "ineq": expression >= 0 (e.g. "0.20 - load_eu" means load_eu <= 0.20).
5. "memory": optional list of {name, init, update}; "update" may use dt, min, max, and prior loads.

Output ONLY raw YAML. No markdown fences. No commentary.
""".strip()

    def _resolve_backend(self) -> BackendName:
        if self.backend != "auto":
            return self.backend
        if self.client:
            return "openai"
        if _ollama_reachable(self.ollama_base_url) and _ollama_model_installed(
            self.ollama_base_url, self.ollama_model
        ):
            return "ollama"
        raise ValueError(
            "[TelosGenerator] Set OPENAI_API_KEY, or run Ollama with "
            f"`ollama pull {self.ollama_model.split(':')[0]}` and TELOS_LLM_BACKEND=ollama."
        )

    def _generate_openai(self, intent: str) -> str:
        if not self.client:
            raise RuntimeError("OpenAI selected but OPENAI_API_KEY is missing.")
        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": intent},
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned empty content.")
        return _strip_yaml_fence(content)

    def _generate_ollama(self, intent: str) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": intent},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        try:
            data = _http_json(url, payload)
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Ollama HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.ollama_base_url}. Is `ollama serve` running?"
            ) from e

        message = data.get("message") or {}
        content = message.get("content")
        if not content or not isinstance(content, str):
            raise RuntimeError(f"Unexpected Ollama response: {data!r}")
        return _strip_yaml_fence(content)

    def generate(self, intent: str, output_path: str | Path) -> Path:
        out = Path(output_path)
        print(f"\n[TelosGenerator] Intent: {intent!r}")

        resolved = self._resolve_backend()
        if resolved == "openai":
            print(f"[TelosGenerator] Using OpenAI model {self.openai_model!r}.")
            raw_yaml = self._generate_openai(intent)
        else:
            print(
                f"[TelosGenerator] Using Ollama {self.ollama_model!r} @ {self.ollama_base_url}."
            )
            raw_yaml = self._generate_ollama(intent)

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw_yaml, encoding="utf-8")
        print(f"[TelosGenerator] Wrote -> {out.resolve()}")

        print("[TelosGenerator] Validating against TelosSchema...")
        try:
            TelosParser.loads(raw_yaml, silent=True)
        except ValueError as e:
            print(f"[TelosGenerator] WARNING: generated YAML failed validation:\n{e}")
            return out

        print("[TelosGenerator] Geometry is structurally valid.\n")
        return out

"""Load and validate ``.telos`` YAML into ``TelosSchema`` dicts (canonical MILP manifests)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

import yaml
from pydantic import ValidationError

from .models import TelosSchema

PathLike = Union[str, Path]


class TelosParser:
    @staticmethod
    def load(filepath: PathLike) -> Dict[str, Any]:
        """
        Read a `.telos` YAML file, validate as `TelosSchema`, return a dict
        suitable for `TelosRuntime.tick`. Optional root key ``template`` holds
        catalog metadata (see ``TelosTemplate``); the compiler ignores it.
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"[TelosParser] Manifest not found: {path}")

        raw_text = path.read_text(encoding="utf-8")
        try:
            raw_yaml = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ValueError(f"[TelosParser] Invalid YAML in {path}:\n{exc}") from exc

        if raw_yaml is None or not isinstance(raw_yaml, dict):
            raise ValueError(f"[TelosParser] Root of {path} must be a YAML mapping (object).")

        try:
            validated = TelosSchema.model_validate(raw_yaml)
        except ValidationError as exc:
            raise ValueError(
                f"[TelosParser] Schema validation failed for {path}:\n{exc}"
            ) from exc

        print(f"[TelosParser] Loaded physics manifest: {path}")
        return validated.model_dump()

    @staticmethod
    def loads(yaml_text: str, *, silent: bool = False) -> Dict[str, Any]:
        """Parse YAML from a string; validate as `TelosSchema` (no file I/O)."""
        try:
            raw = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            raise ValueError(f"[TelosParser] Invalid YAML string:\n{exc}") from exc

        if raw is None or not isinstance(raw, dict):
            raise ValueError("[TelosParser] Root must be a YAML mapping (object).")

        try:
            validated = TelosSchema.model_validate(raw)
        except ValidationError as exc:
            raise ValueError(f"[TelosParser] Schema validation failed:\n{exc}") from exc

        if not silent:
            print("[TelosParser] Validated in-memory manifest.")
        return validated.model_dump()

#!/usr/bin/env python3
"""Regenerate ``templates/index.json`` for static hub / Lovable consumption."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# telos-framework/
_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATES_DIR = _ROOT / "templates"
_INDEX_PATH = _TEMPLATES_DIR / "index.json"


def _build_payload() -> dict:
    templates_dir = _TEMPLATES_DIR
    if not templates_dir.is_dir():
        raise SystemExit(f"[generate_templates_index] Missing directory: {templates_dir}")

    entries: list[dict] = []
    for path in sorted(templates_dir.glob("*.telos")):
        raw = path.read_text(encoding="utf-8")
        # Import after sys.path is usable when run as script (requires editable install or PYTHONPATH).
        from telos.parser import TelosParser

        data = TelosParser.loads(raw, silent=True)
        meta = data.get("template") or {}
        stem = path.stem
        entries.append(
            {
                "id": stem,
                "file": f"templates/{path.name}",
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "name": meta.get("name") or stem,
                "category": meta.get("category"),
                "author": meta.get("author"),
                "description": meta.get("description"),
                "actuators": list(meta.get("actuators") or []),
            }
        )

    repo = os.environ.get("GITHUB_REPOSITORY")
    sha = os.environ.get("GITHUB_SHA")

    return {
        "schema": "telos-templates-index/v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {"repository": repo, "commit": sha},
        "templates": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON to stdout; do not write index.json",
    )
    args = parser.parse_args()

    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))

    payload = _build_payload()
    text = json.dumps(payload, indent=2, sort_keys=False) + "\n"

    if args.dry_run:
        sys.stdout.write(text)
        return 0

    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    _INDEX_PATH.write_text(text, encoding="utf-8")
    print(f"[generate_templates_index] Wrote {_INDEX_PATH} ({len(payload['templates'])} template(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

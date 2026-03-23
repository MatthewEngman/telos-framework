"""CLI entrypoint smoke (subprocess)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cli_help_exits_zero() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "telos", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0
    assert "generate" in r.stdout


def test_cli_test_vulnerable_finds_paradox() -> None:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "telos",
            "test",
            str(ROOT / "vulnerable.telos"),
            "--iters",
            "80",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 2

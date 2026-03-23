"""CLI entrypoint smoke (subprocess)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

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
    out = r.stdout + r.stderr
    assert "generate" in out
    assert "validate" in out


def test_cli_validate_example_router_minimal() -> None:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "telos",
            "validate",
            str(ROOT / "examples" / "router_minimal.telos"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0
    assert "validate: OK" in r.stdout


@pytest.mark.parametrize(
    "rel",
    sorted(p.name for p in (ROOT / "examples").glob("*.telos")),
)
def test_cli_validate_all_example_manifests(rel: str) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "telos", "validate", str(ROOT / "examples" / rel)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, (rel, r.stdout, r.stderr)


def test_cli_validate_strict_router_minimal() -> None:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "telos",
            "validate",
            str(ROOT / "examples" / "router_minimal.telos"),
            "--strict",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0
    assert "strict probe solve optimal" in r.stdout


@pytest.mark.parametrize(
    "rel",
    sorted(p.name for p in (ROOT / "examples").glob("*.telos")),
)
def test_cli_validate_strict_all_example_manifests(rel: str) -> None:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "telos",
            "validate",
            str(ROOT / "examples" / rel),
            "--strict",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, (rel, r.stdout, r.stderr)


def test_cli_validate_strict_infeasible_probe_returns_four(tmp_path: Path) -> None:
    inf = tmp_path / "infeasible.telos"
    inf.write_text(
        """
ontology:
  variables:
    - name: x
      type: float
      bounds: [0.0, 1.0]
  parameters: []
teleology:
  direction: minimize
  objective: "x"
invariants:
  - type: ineq
    expression: "x - 0.9"
  - type: ineq
    expression: "0.1 - x"
""".strip(),
        encoding="utf-8",
    )
    r = subprocess.run(
        [sys.executable, "-m", "telos", "validate", str(inf), "--strict"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 4


def test_cli_validate_invalid_manifest_exits_nonzero(tmp_path: Path) -> None:
    bad = tmp_path / "bad.telos"
    bad.write_text("- 1\n- 2\n", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "-m", "telos", "validate", str(bad)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 1
    assert "FAILED" in r.stderr or "FAILED" in r.stdout


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

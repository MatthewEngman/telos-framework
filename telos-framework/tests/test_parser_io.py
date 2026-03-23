"""TelosParser file I/O."""

from __future__ import annotations

from pathlib import Path

from telos.parser import TelosParser

ROOT = Path(__file__).resolve().parents[1]


def test_load_vulnerable_telos_file(tmp_path: Path) -> None:
    src = ROOT / "vulnerable.telos"
    dst = tmp_path / "copy.telos"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    d = TelosParser.load(dst)
    assert "load_us" in str(d["ontology"]["variables"])


def test_loads_rejects_bad_root() -> None:
    try:
        TelosParser.loads("[]", silent=True)
    except ValueError as e:
        assert "mapping" in str(e).lower() or "object" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")

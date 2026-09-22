"""Smoke tests for the CLI's non-bootstrap-heavy paths."""
from __future__ import annotations

import pytest

from holographic_codes.paths import DATA_ROOT

pytestmark = pytest.mark.skipif(
    not (DATA_ROOT / "manifests" / "selected_circuits.csv").exists(),
    reason="staged data/ not present in this checkout",
)


def test_validate_inputs_reports_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLOGRAPHIC_CODES_RESULT_ROOT", str(tmp_path))
    from holographic_codes.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["validate-inputs"])
    rc = args.func(args)
    assert rc == 0


def test_simulate_quick_sc8_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLOGRAPHIC_CODES_RESULT_ROOT", str(tmp_path))
    from holographic_codes.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["simulate", "--experiment", "sc8", "--mode", "quick"])
    rc = args.func(args)
    assert rc == 0
    assert (tmp_path / "simulations" / "sc8_quick_simulation.json").exists()

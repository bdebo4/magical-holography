"""End-to-end hardware-analysis regression against the staged reference
summaries (04_ACCEPTANCE_CRITERIA.md C.8/D.6/E.6).

No bootstrap here (bootstrap_repeats=0) purely for test runtime; the
bootstrap machinery itself is exercised by
test_hardware_analysis_bootstrap_determinism below. Mean entropy values are
computed exactly the same way whether or not bootstrap is requested.
"""
from __future__ import annotations

import json

import pytest

from holographic_codes.data.manifests import load_selected_circuits
from holographic_codes.paths import DATA_ROOT

pytestmark = pytest.mark.skipif(
    not (DATA_ROOT / "manifests" / "selected_circuits.csv").exists(),
    reason="staged data/ not present in this checkout",
)

TOL = 1e-9


def _theta_key(t):
    return format(float(t), ".16g")


def test_sc8_hardware_analysis_matches_reference():
    from holographic_codes.analysis.sc8 import analyze_condition

    all_circuits = load_selected_circuits("SC8")
    from holographic_codes.data.manifests import load_selected_jobs
    all_jobs = load_selected_jobs("SC8")
    ref = json.load(open(DATA_ROOT / "reference_summaries" / "SC8_entropy_summary.json"))["SC"]

    theta_codes = ["0000", "0196", "0393", "0589", "0785"]
    theta_vals = [0.0, 0.19634954084936207, 0.39269908169872414, 0.5890486225480862, 0.7853981633974483]
    mu_codes = ["000", "010", "020"]
    magic_vals = [0.0, 0.5, 1.0]

    for tcode, tval in zip(theta_codes, theta_vals):
        for mi, (mcode, mval) in enumerate(zip(mu_codes, magic_vals)):
            r = analyze_condition(f"{tcode}_{mcode}", tcode, mcode, mval, all_jobs, all_circuits, bootstrap_repeats=0, bootstrap_seed=1)
            ref_entry = ref[_theta_key(tval)]
            assert abs(r.boundary_entropy - ref_entry["boundary"]["mean"][mi]) < TOL
            assert abs(r.bulk_entropy - ref_entry["bulk"]["mean"][mi]) < TOL


def test_wh10_hardware_analysis_matches_reference():
    from holographic_codes.analysis.wh10 import analyze_condition
    from holographic_codes.data.manifests import load_selected_jobs

    all_circuits = load_selected_circuits("WH10")
    all_jobs = load_selected_jobs("WH10")
    ref = json.load(open(DATA_ROOT / "reference_summaries" / "WH10_entropy_summary.json"))["WH10"]

    theta_codes = ["0000", "0393", "0785"]
    theta_vals = [0.0, 0.39269908169872414, 0.7853981633974483]
    mu_codes = ["000", "013", "027"]
    magic_vals = [0.0, 0.5, 1.0]

    for tcode, tval in zip(theta_codes, theta_vals):
        for mi, (mcode, mval) in enumerate(zip(mu_codes, magic_vals)):
            r = analyze_condition(f"{tcode}_{mcode}", tcode, mcode, mval, all_jobs, all_circuits, bootstrap_repeats=0, bootstrap_seed=1)
            ref_entry = ref[_theta_key(tval)]
            assert abs(r.boundary_entropy - ref_entry["boundary"]["mean"][mi]) < TOL
            assert abs(r.bulk_entropy - ref_entry["bulk"]["mean"][mi]) < TOL


def test_wh16_hardware_analysis_matches_reference():
    from holographic_codes.analysis.wh16 import analyze_condition
    from holographic_codes.data.manifests import load_selected_jobs

    all_circuits = load_selected_circuits("WH16")
    all_jobs = load_selected_jobs("WH16")
    ref = json.load(open(DATA_ROOT / "reference_summaries" / "WH16_entropy_summary.json"))["WH16"]

    theta_codes = ["0000", "0785"]
    theta_vals = [0.0, 0.7853981633974483]
    mu_codes = ["000", "010"]
    magic_vals = [0.0, 1.0]

    for tcode, tval in zip(theta_codes, theta_vals):
        for mi, (mcode, mval) in enumerate(zip(mu_codes, magic_vals)):
            r = analyze_condition(f"{tcode}_{mcode}", tcode, mcode, mval, all_jobs, all_circuits, bootstrap_repeats=0, bootstrap_seed=1)
            ref_entry = ref[_theta_key(tval)]
            assert abs(r.boundary_entropy - ref_entry["boundary"]["mean"][mi]) < TOL
            assert abs(r.bulk_entropy - ref_entry["bulk"]["mean"][mi]) < TOL


def test_bootstrap_is_deterministic_under_fixed_seed():
    from holographic_codes.analysis.sc8 import analyze_condition
    from holographic_codes.data.manifests import load_selected_jobs

    all_circuits = load_selected_circuits("SC8")
    all_jobs = load_selected_jobs("SC8")

    r1 = analyze_condition("0000_000", "0000", "000", 0.0, all_jobs, all_circuits, bootstrap_repeats=5, bootstrap_seed=999)
    r2 = analyze_condition("0000_000", "0000", "000", 0.0, all_jobs, all_circuits, bootstrap_repeats=5, bootstrap_seed=999)
    assert (r1.boundary_entropy_boot == r2.boundary_entropy_boot).all()
    assert (r1.bulk_entropy_boot == r2.bulk_entropy_boot).all()


def test_missing_pauli_setting_fails_loudly():
    from holographic_codes.data.counts import aggregate_circuit_counts
    import pytest as pt

    with pt.raises(ValueError):
        aggregate_circuit_counts("nonexistent_circuit.qpy", [], num_qubits=8)

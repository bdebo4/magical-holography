"""Remaining 04_ACCEPTANCE_CRITERIA.md section G coverage:
G.3 (logical/physical mapping), G.5 (density-matrix physicality),
G.8 (inconsistent mappings fail loudly), G.9 (summary schema shots+provenance).
"""
from __future__ import annotations

import numpy as np
import pytest

from holographic_codes.data.mappings import group_jobs_by_circuit, validate_consistent_mapping_width
from holographic_codes.data.manifests import SelectedJob
from holographic_codes.tomography.pauli import add_pauli_measures_to_dict
from holographic_codes.tomography.reconstruction import state_reconstruction_from_pauli_expectations


def _job(circuit_name: str, mapping: list[int]) -> SelectedJob:
    return SelectedJob(
        experiment="SC8", condition_id="0000_000", theta_code="0000", magic_value=0.0, mu_code="000",
        measurement_role="shared_post_recovery", pauli_string="XXX", circuit_index=0,
        circuit_name=circuit_name, job_id="job1", raw_json_relpath="x.json", shots=100, mapping=mapping,
    )


def test_group_jobs_by_circuit():
    jobs = [_job("a.qpy", [0, 1, 2]), _job("a.qpy", [0, 1, 2]), _job("b.qpy", [0, 1, 2])]
    grouped = group_jobs_by_circuit(jobs)
    assert set(grouped.keys()) == {"a.qpy", "b.qpy"}
    assert len(grouped["a.qpy"]) == 2
    assert len(grouped["b.qpy"]) == 1


def test_validate_consistent_mapping_width_passes_when_uniform():
    jobs = [_job("a.qpy", [0, 1, 2]), _job("a.qpy", [3, 4, 5])]
    validate_consistent_mapping_width(jobs, expected_width=3, context="test")  # no raise


def test_validate_consistent_mapping_width_fails_loudly_on_inconsistent_width():
    jobs = [_job("a.qpy", [0, 1, 2]), _job("a.qpy", [3, 4])]  # inconsistent width
    with pytest.raises(ValueError, match="mapping"):
        validate_consistent_mapping_width(jobs, expected_width=3, context="test")


def test_reconstructed_density_matrix_is_hermitian_trace_one_and_psd():
    measure = {}
    add_pauli_measures_to_dict("X", measure, {"0": 620.0, "1": 380.0})
    add_pauli_measures_to_dict("Y", measure, {"0": 550.0, "1": 450.0})
    add_pauli_measures_to_dict("Z", measure, {"0": 700.0, "1": 300.0})
    rho, entropy = state_reconstruction_from_pauli_expectations(measure, [0], use_mlm=True)

    assert np.allclose(rho, rho.conj().T), "rho must be Hermitian"
    assert abs(np.trace(rho).real - 1.0) < 1e-9, "rho must have unit trace"
    evals = np.linalg.eigvalsh(rho)
    assert np.all(evals >= -1e-9), "rho must be positive-semidefinite (physicality-projected)"
    assert 0.0 <= entropy <= 1.0 + 1e-9


def test_generated_summary_schema_includes_shots_and_provenance():
    from holographic_codes.io.summaries import build_summary

    class _R:
        def __init__(self, theta_code, magic_value, b, k):
            self.theta_code = theta_code
            self.magic_value = magic_value
            self.boundary_entropy = b
            self.bulk_entropy = k
            self.proto_area = b - k
            self.boundary_entropy_boot = None
            self.bulk_entropy_boot = None
            self.shots_used_boundary = 1000
            self.shots_used_bulk = 500

    results = [_R("0000", 0.0, 2.0, 0.5)]
    summary = build_summary(
        "SC", results, ["0000"], [0.0], [0.0],
        measurement_scheme="shared_post_recovery_equal_depth",
        num_executed_settings=27, bulk_from_same_tomography=True,
        extra_meta={"provenance": {"config_version": "test"}},
    )
    theta_key = "0"
    assert "shots_used" in summary["SC"][theta_key]
    assert summary["SC"][theta_key]["shots_used"]["boundary"] == [1000]
    assert "provenance" in summary["SC"]["_meta"]
    assert summary["SC"]["_meta"]["provenance"]["config_version"] == "test"

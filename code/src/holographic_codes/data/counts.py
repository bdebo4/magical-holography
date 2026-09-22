"""Aggregate raw hardware counts for one manifest-selected circuit.

Canonical source: ``data_functions.py::circuit_details_to_qubit_probs``,
reimplemented against the Phase-1 manifest instead of live job-status CSVs
(01_IMPLEMENTATION_SPEC.md section 6 / 04_ACCEPTANCE_CRITERIA.md B.5).
"""
from __future__ import annotations

import dataclasses

from .bit_order import remap_ion_probs_to_qubit_probs
from .ionq_json import load_raw_counts
from .manifests import SelectedJob, resolve_raw_json_path
from .mappings import validate_consistent_mapping_width


@dataclasses.dataclass
class AggregatedCircuitCounts:
    circuit_name: str
    qubit_counts: dict[str, float]  # logical-qubit bitstring -> summed count
    total_shots: int
    n_jobs: int


def aggregate_circuit_counts(circuit_name: str, jobs: list[SelectedJob], *, num_qubits: int) -> AggregatedCircuitCounts:
    """Sum raw-count contributions from every selected job for one circuit,
    remapped from physical ions to the circuit's own logical-qubit register.

    Fails loudly (01_IMPLEMENTATION_SPEC.md section 6) if ``jobs`` is empty
    (missing Pauli setting) or if any job's mapping width is inconsistent.
    """
    if not jobs:
        raise ValueError(f"No selected jobs for circuit {circuit_name!r}: missing Pauli setting.")

    validate_consistent_mapping_width(jobs, expected_width=num_qubits, context=f"circuit {circuit_name!r}")

    combined: dict[str, float] = {}
    total_shots = 0
    for job in jobs:
        raw = load_raw_counts(resolve_raw_json_path(job))
        qubit_counts = remap_ion_probs_to_qubit_probs(raw, job.mapping, renormalize=False, bit_order="right_to_left")
        for key, value in qubit_counts.items():
            combined[key] = combined.get(key, 0.0) + value
        total_shots += job.shots

    return AggregatedCircuitCounts(
        circuit_name=circuit_name,
        qubit_counts=combined,
        total_shots=total_shots,
        n_jobs=len(jobs),
    )

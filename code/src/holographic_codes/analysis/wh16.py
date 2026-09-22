"""WH16 hardware-analysis pipeline: separate boundary/bulk circuit families.

Refactored from ``WH16-D-C011`` (merged with ``WH16-D-C012`` only where that
cell adds analysis logic not already present here). Reads job/circuit
information from the staged manifests, never from live job-status data.

Both boundary (4-qubit, ``boundary_ind=[4,12,7,15]``) and bulk (4-qubit,
``bulk_indices=[1,9,5,13]``) circuits are literally named with a `_bound_`
substring on disk -- a naming quirk in the original export step, which the
manuscript authors' own code comments acknowledge and keep rather than
re-export. This module distinguishes the two families purely by the
manifest's semantic ``measurement_role`` field; staged filenames are never
renamed to "fix" the quirk, since the executed QPY files are the regression
oracle and must be traceable back to the hardware jobs that produced them
unmodified.
"""
from __future__ import annotations

import dataclasses
from itertools import product

import numpy as np

from ..config import ExperimentConfig
from ..data.bit_order import remap_ion_probs_to_qubit_probs, reverse_bitstring_keys
from ..data.counts import aggregate_circuit_counts
from ..data.manifests import load_selected_circuits, load_selected_jobs
from ..tomography.bootstrap import bootstrap_w_replacement, make_rng
from ..tomography.pauli import add_pauli_measures_to_dict
from ..tomography.reconstruction import state_reconstruction_from_pauli_expectations

BOUNDARY_IND = [4, 12, 7, 15]
BULK_INDICES = [1, 9, 5, 13]
BOUNDARY_BASIS_SET = list(product(["X", "Y", "Z"], repeat=4))
BULK_BASIS_SET = list(product(["X", "Y", "Z"], repeat=4))


@dataclasses.dataclass
class ConditionResult:
    condition_id: str
    theta_code: str
    mu_code: str
    magic_value: float
    boundary_entropy: float
    bulk_entropy: float
    proto_area: float
    boundary_entropy_boot: np.ndarray | None
    bulk_entropy_boot: np.ndarray | None
    shots_used_boundary: int
    shots_used_bulk: int
    n_settings: int


def _extract_register(full_qubit_counts: dict[str, float], mapping: list[int]) -> dict[str, float]:
    reduced = remap_ion_probs_to_qubit_probs(full_qubit_counts, mapping, renormalize=False, bit_order="right_to_left")
    return reverse_bitstring_keys(reduced)


def analyze_condition(
    condition_id: str,
    theta_code: str,
    mu_code: str,
    magic_value: float,
    all_jobs,
    all_circuits,
    *,
    bootstrap_repeats: int,
    bootstrap_seed: int,
) -> ConditionResult:
    circuits_this_condition = [c for c in all_circuits if c.condition_id == condition_id]
    jobs_this_condition = [j for j in all_jobs if j.condition_id == condition_id]

    jobs_by_circuit: dict[str, list] = {}
    for j in jobs_this_condition:
        jobs_by_circuit.setdefault(j.circuit_name, []).append(j)

    boundary_by_pauli = {c.pauli_string: c.circuit_name for c in circuits_this_condition if c.measurement_role == "boundary"}
    bulk_by_pauli = {c.pauli_string: c.circuit_name for c in circuits_this_condition if c.measurement_role == "bulk"}
    if len(boundary_by_pauli) != 81:
        raise ValueError(f"Condition {condition_id}: expected 81 boundary settings, found {len(boundary_by_pauli)}.")
    if len(bulk_by_pauli) != 81:
        raise ValueError(f"Condition {condition_id}: expected 81 bulk settings, found {len(bulk_by_pauli)}.")

    def full_counts_for(circuit_name: str) -> tuple[dict[str, float], int]:
        jobs = jobs_by_circuit.get(circuit_name, [])
        width = len(jobs[0].mapping) if jobs else 16
        agg = aggregate_circuit_counts(circuit_name, jobs, num_qubits=width)
        return agg.qubit_counts, agg.total_shots

    measure_boundary: dict = {}
    measure_bulk: dict = {}
    shots_b = shots_k = 0
    per_circuit_full_counts: dict[tuple[str, str], dict[str, float]] = {}

    for p_tuple in BOUNDARY_BASIS_SET:
        p_string = "".join(p_tuple)
        full, shots = full_counts_for(boundary_by_pauli[p_string])
        per_circuit_full_counts[("boundary", p_string)] = full
        add_pauli_measures_to_dict(p_tuple, measure_boundary, _extract_register(full, BOUNDARY_IND))
        shots_b += shots

    for p_tuple in BULK_BASIS_SET:
        p_string = "".join(p_tuple)
        full, shots = full_counts_for(bulk_by_pauli[p_string])
        per_circuit_full_counts[("bulk", p_string)] = full
        add_pauli_measures_to_dict(p_tuple, measure_bulk, _extract_register(full, BULK_INDICES))
        shots_k += shots

    _, s_boundary = state_reconstruction_from_pauli_expectations(measure_boundary, [0, 1, 2, 3], use_mlm=True)
    _, s_bulk = state_reconstruction_from_pauli_expectations(measure_bulk, [0, 1, 2, 3], use_mlm=True)

    boundary_boot = None
    bulk_boot = None
    if bootstrap_repeats > 0:
        rng = make_rng(bootstrap_seed)
        boundary_boot = np.zeros(bootstrap_repeats)
        bulk_boot = np.zeros(bootstrap_repeats)
        for r in range(bootstrap_repeats):
            mb: dict = {}
            mk: dict = {}
            for p_tuple in BOUNDARY_BASIS_SET:
                p_string = "".join(p_tuple)
                full = per_circuit_full_counts[("boundary", p_string)]
                extracted = _extract_register(full, BOUNDARY_IND)
                bs = bootstrap_w_replacement(extracted, rng, number_of_repeats=1) if sum(extracted.values()) >= 500 else extracted
                add_pauli_measures_to_dict(p_tuple, mb, bs)
            for p_tuple in BULK_BASIS_SET:
                p_string = "".join(p_tuple)
                full = per_circuit_full_counts[("bulk", p_string)]
                extracted = _extract_register(full, BULK_INDICES)
                bs = bootstrap_w_replacement(extracted, rng, number_of_repeats=1) if sum(extracted.values()) >= 500 else extracted
                add_pauli_measures_to_dict(p_tuple, mk, bs)
            _, boundary_boot[r] = state_reconstruction_from_pauli_expectations(mb, [0, 1, 2, 3], use_mlm=True)
            _, bulk_boot[r] = state_reconstruction_from_pauli_expectations(mk, [0, 1, 2, 3], use_mlm=True)

    return ConditionResult(
        condition_id=condition_id,
        theta_code=theta_code,
        mu_code=mu_code,
        magic_value=magic_value,
        boundary_entropy=s_boundary,
        bulk_entropy=s_bulk,
        proto_area=s_boundary - s_bulk,
        boundary_entropy_boot=boundary_boot,
        bulk_entropy_boot=bulk_boot,
        shots_used_boundary=shots_b,
        shots_used_bulk=shots_k,
        n_settings=162,
    )


def run_hardware_analysis(config: ExperimentConfig) -> list[ConditionResult]:
    all_circuits = load_selected_circuits("WH16")
    all_jobs = load_selected_jobs("WH16")
    conditions = sorted({c.condition_id for c in all_circuits})
    results = []
    for condition_id in conditions:
        theta_code, mu_code = condition_id.split("_")
        magic_value = next(j.magic_value for j in all_jobs if j.condition_id == condition_id)
        results.append(
            analyze_condition(
                condition_id, theta_code, mu_code, magic_value, all_jobs, all_circuits,
                bootstrap_repeats=config.bootstrap_repeats, bootstrap_seed=config.bootstrap_seed,
            )
        )
    return results

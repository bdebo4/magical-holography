"""SC8 hardware-analysis pipeline: shared post-recovery equal-depth scheme.

Refactored from ``SC8-D-C043`` (the manuscript's unmitigated hardware
extraction cell, which already implements the "reuse 3 of the 27 boundary
circuits for the bulk marginal" trick, see module docstring below) merged
with the still-relevant unmitigated logic of a later analysis variant,
``SC8-D-C054``. This module reads job/circuit/mapping information from the
staged manifests (``data/manifests/selected_circuits.csv`` and
``selected_hardware_jobs.csv``) rather than any live job-status data.

There are 27 executed circuits per condition, named
``bound_XXX`` .. ``bound_ZZZ``. All 27 are POST-RECOVERY equal-depth
circuits (see :func:`holographic_codes.circuits.construction_sc8.build_shared_post_recovery_base`). The
**boundary** (3-qubit) entropy is reconstructed from the full 27-setting
tomography of the 3-qubit register directly. The **bulk** (1-qubit) entropy
is NOT a separate circuit family: it reuses exactly 3 of the same 27
circuits -- the settings whose Pauli string is ``P Z Z`` for P in {X,Y,Z}
(local tomography-register positions 1 and 2 fixed to Z) -- and treats
``<P Z Z>`` as a marginal single-qubit Pauli expectation for register
position 0 via ``state_reconstruction_from_pauli_expectations(..., qoi=[0])``.
This reproduces SC8-D-C043's ``newcounter in {8, 17, 26}`` indexing (those
are exactly the ``XZZ``/``YZZ``/``ZZZ`` positions in the 27-setting
lexicographic ordering) without requiring a separate 3-circuit bulk dataset.
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

BOUNDARY_IND = [5, 0, 6]  # physical-circuit qubit indices of the 3-qubit tomography register
BULK_INDICES = [5]  # the one physical qubit whose bit is kept for the marginal bulk estimator
BOUNDARY_BASIS_SET = list(product(["X", "Y", "Z"], repeat=3))
BULK_BASIS_SET = list(product(["X", "Y", "Z"], repeat=1))  # reinterpreted, see module docstring


def _extract_register(full_qubit_counts: dict[str, float], mapping: list[int]) -> dict[str, float]:
    """Second remap step from SC8-D-C043: reduce the full 8-qubit
    circuit-level counts dict down to just the tomography register named by
    ``mapping`` (physical qubit indices), reusing
    ``remap_ion_probs_to_qubit_probs`` generically (its "ion index" here is
    simply "bit position in the full qubit string") plus a final bitstring
    reversal, exactly as the source cell does."""
    reduced = remap_ion_probs_to_qubit_probs(full_qubit_counts, mapping, renormalize=False, bit_order="right_to_left")
    return reverse_bitstring_keys(reduced)


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


def _measure_dict_for_condition(condition_id: str, jobs_by_circuit: dict, circuits_by_role_pauli: dict) -> tuple[dict, dict, int, int]:
    """Build (measure_boundary, measure_bulk, shots_boundary, shots_bulk)
    for one condition from the 27 shared post-recovery circuits."""
    measure_boundary: dict = {}
    measure_bulk: dict = {}
    shots_boundary = 0
    shots_bulk = 0

    for p_tuple in BOUNDARY_BASIS_SET:
        p_string = "".join(p_tuple)
        circuit_name = circuits_by_role_pauli[p_string]
        jobs = jobs_by_circuit.get(circuit_name, [])
        width = len(jobs[0].mapping) if jobs else 8
        agg = aggregate_circuit_counts(circuit_name, jobs, num_qubits=width)
        boundary_counts = _extract_register(agg.qubit_counts, BOUNDARY_IND)
        add_pauli_measures_to_dict(p_tuple, measure_boundary, boundary_counts)
        shots_boundary += agg.total_shots

    for p_tuple in BULK_BASIS_SET:
        # reinterpret as the shared XZZ/YZZ/ZZZ boundary settings (see docstring)
        shared_tuple = (p_tuple[0], "Z", "Z")
        p_string = "".join(shared_tuple)
        circuit_name = circuits_by_role_pauli[p_string]
        jobs = jobs_by_circuit.get(circuit_name, [])
        width = len(jobs[0].mapping) if jobs else 8
        agg = aggregate_circuit_counts(circuit_name, jobs, num_qubits=width)
        bulk_counts = _extract_register(agg.qubit_counts, BULK_INDICES)
        add_pauli_measures_to_dict(p_tuple, measure_bulk, bulk_counts)
        shots_bulk += agg.total_shots

    return measure_boundary, measure_bulk, shots_boundary, shots_bulk


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
    jobs_this_condition = [j for j in all_jobs if j.condition_id == condition_id]
    circuits_this_condition = [c for c in all_circuits if c.condition_id == condition_id]

    jobs_by_circuit: dict[str, list] = {}
    for j in jobs_this_condition:
        jobs_by_circuit.setdefault(j.circuit_name, []).append(j)

    circuits_by_pauli = {c.pauli_string: c.circuit_name for c in circuits_this_condition}
    if len(circuits_by_pauli) != 27:
        raise ValueError(f"Condition {condition_id}: expected 27 shared settings, found {len(circuits_by_pauli)}.")

    measure_boundary, measure_bulk, shots_b, shots_k = _measure_dict_for_condition(condition_id, jobs_by_circuit, circuits_by_pauli)

    _, s_boundary = state_reconstruction_from_pauli_expectations(measure_boundary, [0, 1, 2], use_mlm=True)
    _, s_bulk = state_reconstruction_from_pauli_expectations(measure_bulk, [0], use_mlm=True)

    boundary_boot = None
    bulk_boot = None
    if bootstrap_repeats > 0:
        rng = make_rng(bootstrap_seed)
        boundary_boot = np.zeros(bootstrap_repeats)
        bulk_boot = np.zeros(bootstrap_repeats)
        # Re-derive per-circuit counts once (not re-aggregated per repeat) for bootstrap resampling.
        per_circuit_counts = {}
        for p_string, circuit_name in circuits_by_pauli.items():
            jobs = jobs_by_circuit.get(circuit_name, [])
            width = len(jobs[0].mapping) if jobs else 8
            per_circuit_counts[p_string] = aggregate_circuit_counts(circuit_name, jobs, num_qubits=width).qubit_counts

        for r in range(bootstrap_repeats):
            mb: dict = {}
            mk: dict = {}
            for p_tuple in BOUNDARY_BASIS_SET:
                p_string = "".join(p_tuple)
                full_counts = per_circuit_counts[p_string]
                bs = bootstrap_w_replacement(full_counts, rng, number_of_repeats=1) if sum(full_counts.values()) >= 500 else full_counts
                add_pauli_measures_to_dict(p_tuple, mb, _extract_register(bs, BOUNDARY_IND))
            for p_tuple in BULK_BASIS_SET:
                shared_tuple = (p_tuple[0], "Z", "Z")
                p_string = "".join(shared_tuple)
                full_counts = per_circuit_counts[p_string]
                bs = bootstrap_w_replacement(full_counts, rng, number_of_repeats=1) if sum(full_counts.values()) >= 500 else full_counts
                add_pauli_measures_to_dict(p_tuple, mk, _extract_register(bs, BULK_INDICES))
            _, boundary_boot[r] = state_reconstruction_from_pauli_expectations(mb, [0, 1, 2], use_mlm=True)
            _, bulk_boot[r] = state_reconstruction_from_pauli_expectations(mk, [0], use_mlm=True)

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
        n_settings=27,
    )


def run_hardware_analysis(config: ExperimentConfig) -> list[ConditionResult]:
    all_circuits = load_selected_circuits("SC8")
    all_jobs = load_selected_jobs("SC8")

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

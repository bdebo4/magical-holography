"""SC8 simulation driver (quick and full modes).

Derived from source cells SC8-C-C053/SC8-C-C055 (K-trajectory QST simulation
route) and SC8-C-C057 (serialization). Reuses the same circuit-construction
(:mod:`holographic_codes.circuits.construction_sc8`) and tomography engine
(:mod:`holographic_codes.tomography`) as the hardware pipeline. Each Pauli
setting's K trajectories are a genuine Monte Carlo average over incoherent
native-gate noise (:func:`holographic_codes.circuits.ionq_native.
add_errors_to_ionq_circuit`), not just repeated multinomial shot-sampling of
one fixed statevector -- this matches the manuscript's own simulation design.

Quick mode uses drastically reduced K/shots/bootstrap (see
``code/configs/sc8_simulation_quick.yaml``) purely to prove the pipeline
executes; it is never compared against the production reference. Full mode
uses the exact production parameters recovered from the reference JSON's own
``_meta`` (see ``code/configs/sc8_simulation_full.yaml``), including the
magic-specific optimized recovery pickles (see
:func:`_recovery_for_magic` below). Because the incoherent-noise draws are
genuinely random (unlike the deterministic coherent "magic" injection), and
the production run's original per-trajectory RNG seed is not recoverable
from the audited source (only the aggregate
``qst_count_bootstrap_seed`` is), regenerated arrays are compared to the
staged reference using a statistical tolerance, not bitwise equality.
"""
from __future__ import annotations

import dataclasses
import pickle
from itertools import product

import numpy as np
from qiskit.quantum_info import Statevector

from ..circuits.construction_sc8 import build_shared_post_recovery_base
from ..circuits.ionq_native import cirq_to_qisk_ionq, reattach_ionq_gates
from ..circuits.tomography_rotations import append_Paulis
from ..config import ExperimentConfig
from ..paths import optimized_artifacts_dir
from ..tomography.pauli import add_pauli_measures_to_dict
from ..tomography.reconstruction import state_reconstruction_from_pauli_expectations
from .finite_shot import trajectory_batched_counts

BOUNDARY_IND = [5, 0, 6]
BULK_INDICES = [5]
INCOH_NOISE = (False, True)  # [coherent, incoherent] -- trajectory noise is incoherent-only
ERROR_RAND_SQ = 0.02
ERROR_RAND_ZZ = 0.135


@dataclasses.dataclass
class SimConditionResult:
    theta_code: str
    theta_value: float
    magic_value: float
    boundary_entropy: float
    bulk_entropy: float
    proto_area: float


def _recovery_for_magic(magic_value: float):
    """Source cells SC8-C-C078/SC8-C-C053 load a magic-specific *optimized*
    recovery circuit for magic>0 rather than the plain Clifford recovery,
    since the manuscript's coherent-error injection at magic>0 requires a
    correspondingly optimized decode step to recover the encoded state.
    Returns None for magic=0.0 (Clifford recovery, no optimization needed)."""
    if magic_value == 0.0:
        return None
    fname = "circ_optimized_reco_singlecopy_halfmagic.pkl" if magic_value == 0.5 else "circ_optimized_reco_singlecopy_withmagic.pkl"
    with open(optimized_artifacts_dir() / fname, "rb") as f:
        return pickle.load(f)


def simulate_condition(
    theta_code: str, theta_value: float, magic_value: float,
    *, trajectories_K: int, shots_per_setting: int, rng: np.random.Generator,
) -> SimConditionResult:
    base = build_shared_post_recovery_base(theta_value, magic_value, recovery_circuit=_recovery_for_magic(magic_value))

    noise_array_turns = np.array([
        0.15 * magic_value, ERROR_RAND_SQ, 0.20 * magic_value, ERROR_RAND_ZZ,
    ]) / (2 * np.pi)

    measure_boundary: dict = {}
    measure_bulk: dict = {}

    for p_tuple in product(["X", "Y", "Z"], repeat=3):
        circ = base + append_Paulis(BOUNDARY_IND, p_tuple, num_qubits=8)
        qisk, _ = cirq_to_qisk_ionq(circ, opt_level=3)
        counts = trajectory_batched_counts(
            qisk, BOUNDARY_IND, 8, shots_per_setting, trajectories_K, noise_array_turns, INCOH_NOISE, rng,
        )
        add_pauli_measures_to_dict(p_tuple, measure_boundary, counts)

        if p_tuple[1:] == ("Z", "Z"):
            circ_k = base + append_Paulis(BULK_INDICES, (p_tuple[0],), num_qubits=8)
            qisk_k, _ = cirq_to_qisk_ionq(circ_k, opt_level=3)
            counts_k = trajectory_batched_counts(
                qisk_k, BULK_INDICES, 8, shots_per_setting, trajectories_K, noise_array_turns, INCOH_NOISE, rng,
            )
            add_pauli_measures_to_dict((p_tuple[0],), measure_bulk, counts_k)

    _, s_boundary = state_reconstruction_from_pauli_expectations(measure_boundary, [0, 1, 2], use_mlm=True)
    _, s_bulk = state_reconstruction_from_pauli_expectations(measure_bulk, [0], use_mlm=True)

    return SimConditionResult(theta_code, theta_value, magic_value, s_boundary, s_bulk, s_boundary - s_bulk)


def run_simulation(config: ExperimentConfig) -> list[SimConditionResult]:
    rng = np.random.default_rng(config.simulation_seed or config.bootstrap_seed)
    K = config.noise_parameters.get("qst_trajectory_batch_K", 5)
    shots_by_magic = config.noise_parameters.get("shots_qst_by_magic", {})

    results = []
    for theta_code, theta_value in zip(config.theta_codes, config.theta_values):
        for magic_code, magic_value in zip(config.magic_codes, config.magic_values):
            shots = int(shots_by_magic.get(str(magic_value), config.expected_shots_per_setting.get(magic_code, 100)))
            results.append(
                simulate_condition(theta_code, theta_value, magic_value, trajectories_K=K, shots_per_setting=shots, rng=rng)
            )
    return results

"""WH10 simulation driver (quick and full modes). Derived from source cell
WH10-C-C057. See :mod:`holographic_codes.simulation.sc8` for the shared
K-trajectory Monte Carlo design used by all three experiments' simulation
drivers."""
from __future__ import annotations

import dataclasses
from itertools import product

import numpy as np

from ..circuits.construction_wh10 import build_boundary_and_bulk_base
from ..circuits.ionq_native import cirq_to_qisk_ionq
from ..circuits.tomography_rotations import append_Paulis
from ..config import ExperimentConfig
from ..tomography.pauli import add_pauli_measures_to_dict
from ..tomography.reconstruction import state_reconstruction_from_pauli_expectations
from .finite_shot import trajectory_batched_counts

BOUNDARY_IND = [3, 4, 8, 9]
BULK_INDICES = [0, 5]
INCOH_NOISE = (False, True)
ERROR_RAND_SQ = 0.02
ERROR_RAND_ZZ = 0.117


@dataclasses.dataclass
class SimConditionResult:
    theta_code: str
    theta_value: float
    magic_value: float
    boundary_entropy: float
    bulk_entropy: float
    proto_area: float


def simulate_condition(
    theta_code: str, theta_value: float, magic_value: float,
    *, trajectories_K: int, shots_per_setting: int, rng: np.random.Generator,
) -> SimConditionResult:
    boundary_base, bulk_base = build_boundary_and_bulk_base(theta_value, magic_value)

    noise_array_turns = np.array([
        0.1 * magic_value, ERROR_RAND_SQ, 0.27 * magic_value, ERROR_RAND_ZZ,
    ]) / (2 * np.pi)

    measure_boundary: dict = {}
    measure_bulk: dict = {}

    for p_tuple in product(["X", "Y", "Z"], repeat=4):
        circ = boundary_base + append_Paulis(BOUNDARY_IND, p_tuple, num_qubits=10)
        qisk, _ = cirq_to_qisk_ionq(circ, opt_level=3)
        counts = trajectory_batched_counts(qisk, BOUNDARY_IND, 10, shots_per_setting, trajectories_K, noise_array_turns, INCOH_NOISE, rng)
        add_pauli_measures_to_dict(p_tuple, measure_boundary, counts)

    for p_tuple in product(["X", "Y", "Z"], repeat=2):
        circ = bulk_base + append_Paulis(BULK_INDICES, p_tuple, num_qubits=10)
        qisk, _ = cirq_to_qisk_ionq(circ, opt_level=3)
        counts = trajectory_batched_counts(qisk, BULK_INDICES, 10, shots_per_setting, trajectories_K, noise_array_turns, INCOH_NOISE, rng)
        add_pauli_measures_to_dict(p_tuple, measure_bulk, counts)

    _, s_boundary = state_reconstruction_from_pauli_expectations(measure_boundary, [0, 1, 2, 3], use_mlm=True)
    _, s_bulk = state_reconstruction_from_pauli_expectations(measure_bulk, [0, 1], use_mlm=True)
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

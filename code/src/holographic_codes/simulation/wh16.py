"""WH16 simulation driver (quick and full modes). Derived from source cells
WH16-C-C071/WH16-C-C073. Loads the staged optimized-encoding/recovery
artifacts for magic=1.0, exactly as
:mod:`holographic_codes.circuits.construction_wh16` requires (including the
magic=0.0 boundary/bulk aliasing that module reproduces -- see its
docstring), and uses the same K-trajectory Monte Carlo design as SC8/WH10."""
from __future__ import annotations

import dataclasses
import pickle
from itertools import product

import numpy as np

from ..circuits.construction_wh16 import build_boundary_and_bulk_base
from ..circuits.ionq_native import cirq_to_qisk_ionq, load_overrotations
from ..circuits.tomography_rotations import append_Paulis
from ..config import ExperimentConfig
from ..paths import optimized_artifacts_dir
from ..tomography.pauli import add_pauli_measures_to_dict
from ..tomography.reconstruction import state_reconstruction_from_pauli_expectations
from .finite_shot import trajectory_batched_counts

BOUNDARY_IND = [4, 12, 7, 15]
BULK_INDICES = [1, 9, 5, 13]
INCOH_NOISE = (False, True)


@dataclasses.dataclass
class SimConditionResult:
    theta_code: str
    theta_value: float
    magic_value: float
    boundary_entropy: float
    bulk_entropy: float
    proto_area: float


def _load_optimized_artifacts():
    x_best = load_overrotations(str(optimized_artifacts_dir() / "x_best_010.npy"))
    with open(optimized_artifacts_dir() / "circ_opt_reco_opt_magic_params", "rb") as f:
        recovery = pickle.load(f)
    return x_best, recovery


def simulate_condition(
    theta_code: str, theta_value: float, magic_value: float,
    *, trajectories_K: int, shots_per_setting: int, rng: np.random.Generator,
    optimized_encoding_vector, optimized_recovery,
) -> SimConditionResult:
    boundary_base, bulk_base = build_boundary_and_bulk_base(
        theta_value, theta_value, magic_value,
        optimized_encoding_vector=optimized_encoding_vector, optimized_recovery=optimized_recovery,
    )
    # WH16-C-C071 has a more elaborate noise model than SC8/WH10 (an
    # additional *shared* per-trajectory coherent draw, `coherent_sigma_SQ`/
    # `coherent_sigma_ZZ`, layered on top of the same per-gate incoherent
    # noise). Both staged reference simulation filenames encode
    # coherent_sigma_SQ=coherent_sigma_ZZ=0.0 ("coherr_000_000") for the run
    # being reproduced, so the shared-coherent-draw mechanism contributes
    # nothing and is safely omitted; error_rand_ZZ=0.125 ("randerr_000_125",
    # not the cell's own unused 0.135 default) is used, matching the actual
    # staged run.
    noise_array_turns = np.array([0.0, 0.0, 0.0, 0.125]) / (2 * np.pi)

    measure_boundary: dict = {}
    measure_bulk: dict = {}

    for p_tuple in product(["X", "Y", "Z"], repeat=4):
        circ = boundary_base + append_Paulis(BOUNDARY_IND, p_tuple, num_qubits=16)
        qisk, _ = cirq_to_qisk_ionq(circ, opt_level=3)
        counts = trajectory_batched_counts(qisk, BOUNDARY_IND, 16, shots_per_setting, trajectories_K, noise_array_turns, INCOH_NOISE, rng)
        add_pauli_measures_to_dict(p_tuple, measure_boundary, counts)

    for p_tuple in product(["X", "Y", "Z"], repeat=4):
        circ = bulk_base + append_Paulis(BULK_INDICES, p_tuple, num_qubits=16)
        qisk, _ = cirq_to_qisk_ionq(circ, opt_level=3)
        counts = trajectory_batched_counts(qisk, BULK_INDICES, 16, shots_per_setting, trajectories_K, noise_array_turns, INCOH_NOISE, rng)
        add_pauli_measures_to_dict(p_tuple, measure_bulk, counts)

    _, s_boundary = state_reconstruction_from_pauli_expectations(measure_boundary, [0, 1, 2, 3], use_mlm=True)
    _, s_bulk = state_reconstruction_from_pauli_expectations(measure_bulk, [0, 1, 2, 3], use_mlm=True)
    return SimConditionResult(theta_code, theta_value, magic_value, s_boundary, s_bulk, s_boundary - s_bulk)


def run_simulation(config: ExperimentConfig) -> list[SimConditionResult]:
    rng = np.random.default_rng(config.simulation_seed or config.bootstrap_seed)
    K = config.noise_parameters.get("qst_trajectory_batch_K", 2)
    x_best, recovery = _load_optimized_artifacts()

    results = []
    for theta_code, theta_value in zip(config.theta_codes, config.theta_values):
        for magic_code, magic_value in zip(config.magic_codes, config.magic_values):
            shots = int(config.expected_shots_per_setting.get(magic_code, config.simulation_shots or 50))
            results.append(
                simulate_condition(
                    theta_code, theta_value, magic_value,
                    trajectories_K=K, shots_per_setting=shots, rng=rng,
                    optimized_encoding_vector=x_best, optimized_recovery=recovery,
                )
            )
    return results

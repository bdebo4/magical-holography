"""Finite-shot sampling and K-trajectory Monte Carlo noise averaging, for
the quick/full simulation drivers.

Canonical source: the "QST" (quantum state tomography) simulation cells
(SC8-C-C053/055, WH10-C-C057, WH16-C-C071) draw K independent noisy circuit
realizations per Pauli setting -- each trajectory re-injects incoherent
native-gate noise via
:func:`holographic_codes.circuits.ionq_native.add_errors_to_ionq_circuit`
and is allotted its own slice of the setting's total shots
(``split_shots_across_trajectories``) -- and pool the resulting counts into
one dict before tomography. This is a genuine Monte-Carlo average over the
incoherent-noise channel, not just multinomial shot noise on a single fixed
statevector.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from ..analysis.entropy import reduced_rho_from_statevector_numpy
from ..circuits.ionq_native import add_errors_to_ionq_circuit


def reduced_probs_from_statevector_numpy(psi: np.ndarray, keep_indices: list[int], n_qubits: int) -> np.ndarray:
    """Marginal computational-basis probabilities over ``keep_indices``
    (diagonal of the reduced density matrix)."""
    rho = reduced_rho_from_statevector_numpy(psi, keep_indices, n_qubits)
    probs = np.real(np.diag(rho))
    probs = np.clip(probs, 0.0, None)
    return probs / probs.sum()


def split_shots_across_trajectories(total_shots: int, n_trajectories: int) -> np.ndarray:
    """Canonical source: SC8-C-C053. Near-equal split of ``total_shots``
    across ``n_trajectories``, remainder distributed to the first few."""
    total_shots = int(total_shots)
    n_trajectories = min(int(n_trajectories), total_shots)
    if total_shots <= 0:
        raise ValueError("total_shots must be positive.")
    if n_trajectories <= 0:
        raise ValueError("n_trajectories must be positive.")
    base = total_shots // n_trajectories
    remainder = total_shots % n_trajectories
    chunks = np.full(n_trajectories, base, dtype=int)
    chunks[:remainder] += 1
    return chunks


def trajectory_batched_counts(
    qisk_circuit: QuantumCircuit,
    measured_indices: list[int],
    n_qubits: int,
    shots_total: int,
    n_trajectories: int,
    noise_array_turns: np.ndarray,
    incoh_noise: tuple[bool, bool],
    rng: np.random.Generator,
) -> dict[str, int]:
    """K-trajectory Monte Carlo: for each of ``n_trajectories`` shot chunks,
    inject fresh incoherent native-gate noise, recompute the statevector,
    and multinomial-sample that chunk's shots from the resulting marginal
    probability distribution on ``measured_indices``. Pools all trajectories'
    counts into one dict, keyed by the ``len(measured_indices)``-bit
    computational-basis bitstring (qubit order matching ``measured_indices``,
    little-endian within that sub-register -- the same convention
    :mod:`holographic_codes.tomography.pauli` expects)."""
    shot_chunks = split_shots_across_trajectories(shots_total, n_trajectories)
    counts_total: Counter[str] = Counter()

    for shots_this_trajectory in shot_chunks:
        noisy = add_errors_to_ionq_circuit(qisk_circuit, noise_array_turns, incoh_noise)
        psi = Statevector(noisy).data
        probs = reduced_probs_from_statevector_numpy(psi, measured_indices, n_qubits)
        k = len(measured_indices)
        draws = rng.multinomial(int(shots_this_trajectory), probs)
        for idx, c in enumerate(draws):
            if c > 0:
                key = format(idx, f"0{k}b")
                counts_total[key] += int(c)

    return dict(counts_total)

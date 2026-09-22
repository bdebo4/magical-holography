"""Von Neumann entropy utilities shared by hardware analysis and simulation.

Derived from ``von_neumann_entropy_from_rho`` (density-matrix form) and
``reduced_rho_from_statevector_numpy`` (statevector-partial-trace form) in
the manuscript authors' original analysis code, refactored here into one
tested definition used by both the hardware-analysis path and the
simulation-side entropy computation (source cells SC8-C-C068, WH16-C-C039).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np


def von_neumann_entropy_from_rho(rho: np.ndarray, base: int = 2, eps: float = 1e-12) -> float:
    rho = 0.5 * (rho + rho.conj().T)
    evals = np.linalg.eigvalsh(rho).real
    evals = np.clip(evals, eps, None)
    evals = evals / np.sum(evals)
    if base == 2:
        return float(-np.sum(evals * np.log2(evals)))
    return float(-np.sum(evals * np.log(evals)) / np.log(base))


def reduced_rho_from_statevector_numpy(psi: np.ndarray, keep_indices: Sequence[int], n_qubits: int) -> np.ndarray:
    """Partial trace of a pure statevector onto ``keep_indices`` (qubit index
    0 = least significant, matching Qiskit's ``Statevector`` convention).

    ``psi.reshape((2,)*n_qubits)`` is C-order, so its *last* axis varies
    fastest -- i.e. reshape axis ``n_qubits-1-i`` corresponds to qubit ``i``
    in Qiskit's LSB=qubit-0 convention, not axis ``i`` directly. The
    canonical source (``data_functions.py::reduced_rho_from_statevector_numpy``)
    is always called after an explicit ``reverse_qubit_order(psi)`` step to
    paper over this; this implementation instead maps ``keep_indices``
    straight to the correct axes, verified against a hand-computed 2-qubit
    example (|01> -> qubit-0 marginal is |1><1|) in
    ``code/tests/test_tomography.py``.
    """
    keep_indices = list(keep_indices)
    keep_axes = [n_qubits - 1 - i for i in keep_indices]
    keep_set = set(keep_axes)
    trace_axes = [a for a in range(n_qubits) if a not in keep_set]

    psi_t = psi.reshape((2,) * n_qubits)
    perm = keep_axes + trace_axes
    psi_perm = np.transpose(psi_t, axes=perm)

    dk = 2 ** len(keep_indices)
    dt = 2 ** (n_qubits - len(keep_indices))
    psi_mat = psi_perm.reshape(dk, dt)
    return psi_mat @ psi_mat.conj().T


def von_neumann_entropy_from_statevector(psi: np.ndarray, keep_indices: Sequence[int], n_qubits: int, base: int = 2) -> float:
    rho = reduced_rho_from_statevector_numpy(psi, keep_indices, n_qubits)
    return von_neumann_entropy_from_rho(rho, base=base)

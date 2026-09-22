"""Full linear-inversion + physicality-projection state reconstruction.

Derived from ``state_reconstruction_from_pauli_expectations`` in the
manuscript authors' shared analysis code -- the counts-dict variant used by
every canonical hardware-analysis cell (SC8-D-C043, SC8-D-C054, and the
WH10/WH16 equivalents, which all import from the same shared analysis
module in the original repositories).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from .pauli import expectation_of_pauli_string_from_probs, generate_pauli_basis
from .physicality import mlm_rho


def state_reconstruction_from_pauli_expectations(
    measure_data: dict,
    qoi: Sequence[int],
    eps: float = 1e-12,
    use_mlm: bool = True,
) -> tuple[np.ndarray, float]:
    """Reconstruct the reduced density matrix on ``qoi`` via linear Pauli
    inversion, optionally physicality-project it (``use_mlm``), and return
    ``(rho, von_neumann_entropy_bits)``."""
    n = len(qoi)
    dim = 2 ** n

    basis_strings, basis_matrices = generate_pauli_basis(qoi)

    mu = np.zeros((dim, dim), dtype=complex)
    for p_string, P in zip(basis_strings, basis_matrices):
        exp_val = expectation_of_pauli_string_from_probs(measure_data, p_string)
        mu += (exp_val / dim) * P
    mu += (1.0 / dim) * np.eye(dim, dtype=complex)

    mu = 0.5 * (mu + mu.conj().T)
    tr = np.trace(mu).real
    if tr != 0:
        mu /= tr

    rho = mlm_rho(mu) if use_mlm else mu

    evals = np.linalg.eigvalsh(rho).real
    evals = np.clip(evals, eps, None)
    evals /= np.sum(evals)
    entropy = float(-np.sum(evals * np.log2(evals)))

    return rho, entropy

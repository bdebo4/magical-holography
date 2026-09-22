"""Physicality projection (maximum-likelihood eigenvalue correction).

Derived from ``mlm_rho`` in the manuscript authors' shared analysis code.
This is the Smolin/Gambetta/Smith-style algorithm that removes negative
eigenvalues from a linear-inversion density-matrix estimate by truncating
and redistributing probability mass from the smallest eigenvalues upward --
the physicality/maximum-likelihood transform used throughout the paper's
tomographic reconstructions.
"""
from __future__ import annotations

import numpy as np


def mlm_rho(mu: np.ndarray) -> np.ndarray:
    """Project a Hermitian, unit-trace matrix ``mu`` (which may have small
    negative eigenvalues from finite-shot linear inversion) onto the nearest
    physical (positive-semidefinite, unit-trace) density matrix."""
    w, v = np.linalg.eigh(mu)
    idx = np.argsort(w)[::-1]
    w = w[idx]
    v = v[:, idx]

    i = len(w) - 1
    a = 0.0
    lambda_ = np.zeros_like(w)

    while i >= 0:
        if w[i] + a / (i + 1) >= 0:
            break
        lambda_[i] = 0.0
        a += w[i]
        i -= 1

    for j in range(i + 1):
        lambda_[j] = w[j] + a / (i + 1)

    rho = sum(lambda_[k] * np.outer(v[:, k], v[:, k].conj()) for k in range(len(lambda_)))
    return rho

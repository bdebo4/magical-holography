"""Pauli-basis bookkeeping for state tomography.

Derived from ``pauli_matrix_from_string``/``generate_pauli_basis`` and
``add_pauli_measures_to_dict``/``expectation_of_pauli_string_from_probs`` in
the manuscript authors' shared analysis code -- the counts-dict variant used
by every canonical hardware-analysis cell, as opposed to the raw-shot-list
``expectation_of_pauli_string`` used only by older simulation-side cells.
"""
from __future__ import annotations

from itertools import product
from typing import Sequence

import numpy as np

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SI = np.array([[1, 0], [0, 1]], dtype=complex)

_PAULI_MATS = {"I": SI, "X": SX, "Y": SY, "Z": SZ}


def pauli_matrix_from_string(p_string: Sequence[str]) -> np.ndarray:
    mat = np.array([[1]], dtype=complex)
    for p in p_string:
        mat = np.kron(mat, _PAULI_MATS[p])
    return mat


def generate_pauli_basis(qoi: Sequence[int]) -> tuple[list[tuple[str, ...]], list[np.ndarray]]:
    """All non-identity n-qubit Pauli strings (n=len(qoi)) and their matrices,
    in the same order every canonical cell iterates them."""
    n = len(qoi)
    basis_strings, basis_matrices = [], []
    for p_string in product(["I", "X", "Y", "Z"], repeat=n):
        if all(p == "I" for p in p_string):
            continue
        basis_strings.append(p_string)
        basis_matrices.append(pauli_matrix_from_string(p_string))
    return basis_strings, basis_matrices


def add_pauli_measures_to_dict(p_string: Sequence[str], measure_dict: dict, qubit_probs: dict[str, float]) -> None:
    """Record one Pauli setting's counts into the accumulating
    ``measure_dict[p_string][eigenvalue_tuple] = count`` structure.

    Bitstring convention: '0' -> eigenvalue +1, '1' -> eigenvalue -1.
    """
    p_string = tuple(p_string)
    if p_string in measure_dict:
        raise ValueError(f"p_string '{p_string}' already exists in measure_dict.")
    measure_dict[p_string] = {}
    for key, value in qubit_probs.items():
        mapped = tuple(1 if bit == "0" else -1 for bit in key)
        measure_dict[p_string][mapped] = measure_dict[p_string].get(mapped, 0.0) + value


def expectation_of_pauli_string_from_probs(measure_data: dict, p_string: Sequence[str]) -> float:
    """<P> from a dict of eigenvalue-tuple -> count, per Pauli setting,
    including the 'I' (identity) extension-and-average handling used by
    every canonical hardware-analysis cell."""
    p_string = tuple(p_string)

    if "I" not in p_string:
        if p_string not in measure_data:
            raise KeyError(f"No measurement data for Pauli string {p_string}")
        eig_counts = measure_data[p_string]
        total = sum(eig_counts.values())
        if total == 0:
            return 0.0
        num = sum(np.prod(eigvals) * count for eigvals, count in eig_counts.items())
        return float(num / total)

    indices = [i for i, x in enumerate(p_string) if x == "I"]
    k = len(indices)
    exp_vals = []
    for extend in product(["X", "Y", "Z"], repeat=k):
        extended = list(p_string)
        for idx, label in zip(indices, extend):
            extended[idx] = label
        extended = tuple(extended)
        if extended not in measure_data:
            raise KeyError(f"No measurement data for extended Pauli string {extended}")
        eig_counts_ext = measure_data[extended]
        total_ext = sum(eig_counts_ext.values())
        if total_ext == 0:
            exp_vals.append(0.0)
            continue
        num_ext = 0.0
        for eigvals, count in eig_counts_ext.items():
            reduced = [ev for i, ev in enumerate(eigvals) if i not in indices]
            num_ext += float(np.prod(reduced)) * count
        exp_vals.append(num_ext / total_ext)

    return float(sum(exp_vals) / len(exp_vals)) if exp_vals else 0.0

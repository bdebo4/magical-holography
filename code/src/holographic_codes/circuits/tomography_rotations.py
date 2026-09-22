"""Pauli-basis-change gates appended before measurement (QST).

Derived from ``append_Paulis`` in the manuscript authors' shared analysis
code (``analysis_functions.py``), which appeared as byte-identical logic in
both the construction/simulation and execution/analysis source repositories.
"""
from __future__ import annotations

from itertools import product
from typing import Sequence

import cirq
import numpy as np


def append_Paulis(qoi: Sequence[int], p_string: Sequence[str], num_qubits: int) -> cirq.Circuit:
    """Basis-change circuit: for each qubit in ``qoi`` measured in Pauli
    basis ``p_string[i]``, rotate X->Z via H or Y->Z via Rx(pi/2); Z needs no
    rotation. Operates on a fresh ``cirq.LineQubit.range(num_qubits)``
    register matching the convention used throughout construction.py."""
    qubits = cirq.LineQubit.range(num_qubits)
    gates = []
    for idx, qubit in enumerate(qoi):
        p = p_string[idx]
        if p == "X":
            gates.append(cirq.H(qubits[qubit]))
        elif p == "Y":
            gates.append(cirq.rx(np.pi / 2).on(qubits[qubit]))
        # 'Z' (or 'I') needs no basis-change gate.
    return cirq.Circuit(gates)


def pauli_basis_settings(num_local_qubits: int) -> list[tuple[str, ...]]:
    """All 3**n Pauli-string settings for an n-qubit tomography register, in
    the same lexicographic order as ``itertools.product`` used throughout the
    canonical exporters (X before Y before Z)."""
    return list(product(["X", "Y", "Z"], repeat=num_local_qubits))

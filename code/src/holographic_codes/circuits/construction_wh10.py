"""WH10 (10-qubit two-copy wormhole code) circuit construction.

Refactored from source cell WH10-C-C007 (construction notebook). Two
independent 5-qubit HaPPY tiles (qubits 0-4 and 5-9), entangled at their
bulk legs (qubits 0 and 5) via a CNOT-based Bell-pair-like preparation, then
optionally recovered on a 3-qubit boundary of each copy.
"""
from __future__ import annotations

import cirq
import numpy as np

from .primitives import happy3_decode_noisy_wh, happy4_encode_noisy_wh, happy5_encode_noisy_wh

N_QUBITS = 10
CENTER_LEGS_1 = [0, 1, 2, 3, 4]
CENTER_LEGS_2 = [5, 6, 7, 8, 9]
LOGICAL_QUBITS = [0, 5]


def qubits() -> list[cirq.LineQubit]:
    return cirq.LineQubit.range(N_QUBITS)


def base_circuit(noise_scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    qs = qubits()
    blue_qs1 = [qs[i] for i in CENTER_LEGS_1]
    blue_qs2 = [qs[i] for i in CENTER_LEGS_2]
    c = happy5_encode_noisy_wh(blue_qs1, noise_scale, mean)
    c.append(happy5_encode_noisy_wh(blue_qs2, noise_scale, mean))
    return c


def theta_rotation(theta: float) -> cirq.Circuit:
    qs = qubits()
    logical_qs = [qs[i] for i in LOGICAL_QUBITS]
    c = cirq.Circuit()
    c.append(cirq.ry(2 * theta).on(logical_qs[0]))
    return c


def logical_entanglement() -> cirq.Circuit:
    qs = qubits()
    logical_qs = [qs[i] for i in LOGICAL_QUBITS]
    c = cirq.Circuit()
    c.append(cirq.CNOT(logical_qs[0], logical_qs[1]))
    return c


def generate_ent(theta: float) -> cirq.Circuit:
    return theta_rotation(theta) + logical_entanglement()


def happy_reduced_wormhole(encode: cirq.Circuit, theta: float) -> cirq.Circuit:
    return generate_ent(theta) + encode


def happy_wormhole_reco_only(boundary1, boundary2) -> cirq.Circuit:
    qs = qubits()
    boundary_qubits1 = [qs[i] for i in boundary1]
    boundary_qubits2 = [qs[i] for i in boundary2]
    c = cirq.Circuit()
    c.append(happy3_decode_noisy_wh(boundary_qubits1, scale=0, mean=0))
    c.append(happy3_decode_noisy_wh(boundary_qubits2, scale=0, mean=0))
    return c


def happy_wormhole_reco(reduced_circuit: cirq.Circuit, boundary1, boundary2) -> cirq.Circuit:
    qs = qubits()
    boundary_qubits1 = [qs[i] for i in boundary1]
    boundary_qubits2 = [qs[i] for i in boundary2]
    reduced_circuit.append(happy3_decode_noisy_wh(boundary_qubits1, scale=0, mean=0))
    reduced_circuit.append(happy3_decode_noisy_wh(boundary_qubits2, scale=0, mean=0))
    return reduced_circuit


def build_boundary_and_bulk_base(
    theta: float,
    magic: float,
    *,
    boundary1=(0, 1, 2),
    boundary2=(5, 6, 7),
    incl_rz_error: bool = True,
) -> tuple[cirq.Circuit, cirq.Circuit]:
    """Build the (boundary_base, bulk_base) pair for one (theta, magic)
    condition, matching WH10-D-C016 exactly.

    Unlike SC8, WH10's boundary and bulk settings genuinely come from two
    different circuit families: the boundary base has no recovery segment
    (tomography happens directly on the 4-qubit boundary_ind=[3,4,8,9]);
    the bulk base appends the Clifford recovery on both 3-qubit boundaries
    before tomography on bulk_indices=[0,5].
    """
    from .ionq_native import add_errors_to_cirq_circuit

    error_syst_Rx = 0.1 * magic
    error_syst_Ry = 0.2 * magic
    error_syst_Rz = 0.0 * magic
    error_syst_ZZ = 0.27 * magic
    noise_array_rad = np.array([error_syst_Rx, error_syst_Ry, error_syst_Rz, 0.0, error_syst_ZZ, 0.0])
    coh_error = (True, False)

    prep = generate_ent(theta)
    encode = base_circuit(noise_scale=0.0, mean=0.0)

    if magic:
        encode = add_errors_to_cirq_circuit(encode, noise_array_rad, coh_error, include_rz_error=incl_rz_error)

    decode = happy_wormhole_reco_only(boundary1, boundary2)

    bulk_base = prep + encode + decode
    boundary_base = prep + encode
    return boundary_base, bulk_base

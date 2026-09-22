"""SC8 (8-qubit single-copy reduced HaPPY code) circuit construction.

Refactored from source cell SC8-C-C004 (construction) and SC8-C-C078 (the
manuscript's exporter lineage, reinterpreted here as an explicit,
independently-testable function rather than notebook-global state).

Qubit layout (``cirq.LineQubit.range(25)`` in the source cell, but only
indices 0-7 are ever used -- the source over-allocates a 25-qubit register
inherited from a larger notebook context; this module allocates exactly the
8 qubits SC8 uses):

    logical_legs = [0, 5]           # bulk qubit (0) and one boundary leg (5)
    blue_legs    = [0, 1, 2, 3, 4]  # 5-qubit HaPPY "blue" tile
    reds_legs    = [[5, 0, 6, 7]]   # 4-qubit HaPPY "red" tile (shares qubit 0)

so the full circuit spans physical qubits {0,...,7}.
"""
from __future__ import annotations

from typing import Sequence

import cirq
import numpy as np

from .primitives import custom_H, custom_S, custom_Z, custom_cnot, custom_cz

N_QUBITS = 8
BLUE_LEGS = [0, 1, 2, 3, 4]
REDS_LEGS = [5, 0, 6, 7]
LOGICAL_QUBITS = [0, 5]
NO_NOISE = (False, False)
COHERENT_NOISE = (True, False)


def qubits() -> list[cirq.LineQubit]:
    return cirq.LineQubit.range(N_QUBITS)


def happy5_encode_noisy(qs, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    c = cirq.Circuit()
    custom_H(c, qs[4], noise_array, noise_bool)
    custom_H(c, qs[3], noise_array, noise_bool)
    custom_H(c, qs[2], noise_array, noise_bool)
    custom_H(c, qs[1], noise_array, noise_bool)
    custom_Z(c, qs[0], noise_array, noise_bool)

    custom_cnot(c, qs[4], qs[0], noise_array, noise_bool)
    custom_cnot(c, qs[3], qs[0], noise_array, noise_bool)
    custom_cnot(c, qs[2], qs[0], noise_array, noise_bool)
    custom_cnot(c, qs[1], qs[0], noise_array, noise_bool)

    custom_cz(c, qs[4], qs[3], noise_array, noise_bool)
    custom_cz(c, qs[3], qs[2], noise_array, noise_bool)
    custom_cz(c, qs[4], qs[0], noise_array, noise_bool)
    custom_cz(c, qs[2], qs[1], noise_array, noise_bool)
    custom_cz(c, qs[1], qs[0], noise_array, noise_bool)
    return c


def happy3_encode_noisy(qs, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    c = cirq.Circuit()
    custom_H(c, qs[0], noise_array, noise_bool)
    custom_S(c, qs[0], noise_array, noise_bool)
    custom_S(c, qs[2], noise_array, noise_bool)
    custom_cnot(c, qs[0], qs[1], noise_array, noise_bool)
    custom_cnot(c, qs[0], qs[2], noise_array, noise_bool)
    custom_S(c, qs[2], noise_array, noise_bool)
    custom_H(c, qs[2], noise_array, noise_bool)
    custom_cnot(c, qs[1], qs[0], noise_array, noise_bool)
    custom_cnot(c, qs[2], qs[0], noise_array, noise_bool)
    custom_cnot(c, qs[2], qs[1], noise_array, noise_bool)
    custom_cnot(c, qs[1], qs[2], noise_array, noise_bool)
    custom_cnot(c, qs[2], qs[1], noise_array, noise_bool)
    custom_H(c, qs[1], noise_array, noise_bool)
    custom_S(c, qs[1], noise_array, noise_bool)
    custom_S(c, qs[2], noise_array, noise_bool)
    custom_cnot(c, qs[1], qs[2], noise_array, noise_bool)
    custom_S(c, qs[2], noise_array, noise_bool)
    custom_H(c, qs[2], noise_array, noise_bool)
    custom_S(c, qs[0], noise_array, noise_bool)
    custom_S(c, qs[0], noise_array, noise_bool)
    custom_S(c, qs[2], noise_array, noise_bool)
    custom_S(c, qs[2], noise_array, noise_bool)
    return c


def happy4_encode_noisy(qs, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    c = cirq.Circuit()
    custom_H(c, qs[2], noise_array, noise_bool)
    custom_cnot(c, qs[2], qs[3], noise_array, noise_bool)
    c.append(happy3_encode_noisy(qs[:3], noise_array, noise_bool))
    return c


def happy3_decode_noisy(qs, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    q0, q1, q2 = qs
    c = cirq.Circuit()
    custom_S(c, q0, noise_array, noise_bool)
    custom_H(c, q0, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)
    custom_cnot(c, q0, q1, noise_array, noise_bool)
    custom_cnot(c, q0, q2, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)
    custom_cnot(c, q1, q0, noise_array, noise_bool)
    custom_cnot(c, q2, q0, noise_array, noise_bool)
    custom_S(c, q1, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)
    custom_cnot(c, q2, q1, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    custom_S(c, q2, noise_array, noise_bool)
    return c


def base_circuit(noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    qs = qubits()
    blue_qs = [qs[i] for i in BLUE_LEGS]
    red_qs = [qs[i] for i in REDS_LEGS]
    c = happy5_encode_noisy(blue_qs, noise_array, noise_bool)
    c.append(happy4_encode_noisy(red_qs, noise_array, noise_bool))
    return c


def theta_rotation(theta: float, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    qs = qubits()
    logical_qs = [qs[i] for i in LOGICAL_QUBITS]
    from .primitives import generate_dtheta_SQ

    c = cirq.Circuit()
    theta_noise_bool = (False, noise_bool[1])  # no coherent error on theta itself
    c.append(cirq.ry(2 * theta + generate_dtheta_SQ(noise_array, theta_noise_bool)).on(logical_qs[0]))
    c.append(cirq.Ry(rads=np.pi / 2 + generate_dtheta_SQ(noise_array, (False, noise_bool[1])))(logical_qs[0]))
    return c


def logical_entanglement(noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    from .primitives import generate_dtheta_SQ, generate_dtheta_XX

    qs = qubits()
    logical_qs = [qs[i] for i in LOGICAL_QUBITS]
    c = cirq.Circuit()
    c.append(cirq.XXPowGate(exponent=1 / 2 + generate_dtheta_XX(noise_array, noise_bool) / np.pi)(logical_qs[0], logical_qs[1]))
    c.append(cirq.Rx(rads=-np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(logical_qs[0]))
    c.append(cirq.Rx(rads=-np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(logical_qs[1]))
    c.append(cirq.Ry(rads=-np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(logical_qs[0]))
    c.append(cirq.GlobalPhaseGate(-1j)())
    return c


def generate_ent(theta: float, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    return theta_rotation(theta, noise_array, noise_bool) + logical_entanglement(noise_array, noise_bool)


def happy_reduced(theta: float, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    return generate_ent(theta, noise_array, noise_bool) + base_circuit(noise_array, noise_bool)


def happy_recovery_only(boundary: Sequence[int], noise_array: np.ndarray, noise_bool: Sequence[bool]) -> cirq.Circuit:
    qs = qubits()
    boundary_qubits = [qs[i] for i in boundary]
    return happy3_decode_noisy(boundary_qubits, noise_array, noise_bool)


def build_shared_post_recovery_base(
    theta: float,
    magic: float,
    *,
    recovery_circuit: cirq.Circuit | None = None,
    boundary_ind: Sequence[int] = (5, 0, 6),
    incl_rz_error: bool = True,
) -> cirq.Circuit:
    """Build the pre-Pauli-tomography base circuit shared by all 27
    post-recovery settings for one (theta, magic) condition.

    This is the "cirq_base_bulk" object of SC8-C-C078: theta-rotation +
    logical-entanglement + noisy HaPPY-5/HaPPY-4 encoding (with the
    magic-scaled coherent-error injection applied to the encoding segments
    only, matching SC8-C-C078) + a recovery/decode segment. This SAME base
    circuit (not a boundary-only variant) is what every one of the 27 saved
    ``bound_*`` QPY files is built from: although their filenames use
    boundary-style labels, all 27 are equal-depth post-recovery tomography
    circuits, and there is no separate "cirq_base_bound" circuit family in
    the executed data.

    Parameters
    ----------
    recovery_circuit:
        If given, used verbatim as the decode/recovery segment (the
        optimized-recovery pickles staged under
        ``data/optimized_artifacts/``). Otherwise the un-optimized
        Clifford ``happy_recovery_only`` is used.
    """
    from .ionq_native import add_errors_to_cirq_circuit

    error_syst_Rx = 0.15 * magic
    error_syst_Ry = 0.25 * magic
    error_syst_Rz = 0.15 * magic
    error_syst_ZZ = 0.20 * magic
    noise_array_rad = np.array([error_syst_Rx, error_syst_Ry, error_syst_Rz, 0.0, error_syst_ZZ, 0.0])

    no_noise = (False, False)
    coh_noise = (True, False)

    qs = qubits()
    blue_qs = [qs[i] for i in BLUE_LEGS]
    red_qs = [qs[i] for i in REDS_LEGS]

    cirq_theta_rot = theta_rotation(theta, noise_array=np.zeros(4), noise_bool=no_noise)
    cirq_gen_ent = logical_entanglement(noise_array=np.zeros(4), noise_bool=no_noise)

    cirq_gen_H5 = happy5_encode_noisy(blue_qs, np.zeros(4), no_noise)
    cirq_gen_H5 = add_errors_to_cirq_circuit(cirq_gen_H5, noise_array_rad, coh_noise, include_rz_error=incl_rz_error)

    cirq_gen_H4 = happy4_encode_noisy(red_qs, np.zeros(4), no_noise)
    cirq_gen_H4 = add_errors_to_cirq_circuit(cirq_gen_H4, noise_array_rad, coh_noise, include_rz_error=incl_rz_error)

    if recovery_circuit is not None:
        decode = recovery_circuit
    else:
        decode = happy_recovery_only(boundary_ind, noise_array=np.zeros(4), noise_bool=no_noise)

    cirq_base_bound = cirq_theta_rot + cirq_gen_ent + cirq_gen_H5 + cirq_gen_H4
    return cirq_base_bound + decode

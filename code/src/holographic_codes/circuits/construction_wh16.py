"""WH16 (16-qubit two-copy wormhole code) circuit construction.

Refactored from source cell WH16-C-C005 (construction notebook). Two
independent 8-qubit HaPPY constructions (each a 5-qubit blue tile plus a
4-qubit red tile sharing one leg, identical to
:mod:`holographic_codes.circuits.construction_sc8`), placed on qubits 0-7 and
8-15, entangled at logical qubits {0,8} and {5,13}.
"""
from __future__ import annotations

import cirq
import numpy as np

from .primitives import happy3_encode_noisy_wh, happy4_encode_noisy_wh, happy5_encode_noisy_wh

N_QUBITS = 16
BLUE_LEGS_LOCAL = [0, 1, 2, 3, 4]
REDS_LEGS_LOCAL = [5, 0, 6, 7]
LOGICAL_QUBITS_1 = [0, 8]
LOGICAL_QUBITS_2 = [5, 13]


def qubits() -> list[cirq.LineQubit]:
    return cirq.LineQubit.range(N_QUBITS)


def base_circuit_onecopy(qubits8, noise_scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    blue_qs = [qubits8[i] for i in BLUE_LEGS_LOCAL]
    red_qs = [qubits8[i] for i in REDS_LEGS_LOCAL]
    c = cirq.Circuit()
    c += happy5_encode_noisy_wh(blue_qs, noise_scale, mean)
    c += happy4_encode_noisy_wh(red_qs, noise_scale, mean)
    return c


def base_circuit_16(noise_scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    qs = qubits()
    c = cirq.Circuit()
    c += base_circuit_onecopy(qs[0:8], noise_scale, mean)
    c += base_circuit_onecopy(qs[8:16], noise_scale, mean)
    return c


def generate_ent(theta1: float, theta2: float) -> cirq.Circuit:
    qs = qubits()
    logical_qs1 = [qs[i] for i in LOGICAL_QUBITS_1]
    logical_qs2 = [qs[i] for i in LOGICAL_QUBITS_2]
    c = cirq.Circuit()
    c.append(cirq.ry(2 * theta1).on(logical_qs1[0]))
    c.append(cirq.CNOT(logical_qs1[0], logical_qs1[1]))
    c.append(cirq.ry(2 * theta2).on(logical_qs2[0]))
    c.append(cirq.CNOT(logical_qs2[0], logical_qs2[1]))
    return c


def wormhole16(encode: cirq.Circuit, theta1: float, theta2: float) -> cirq.Circuit:
    return generate_ent(theta1, theta2) + encode


def wormhole_reco(
    wormhole_circuit: cirq.Circuit,
    boundary_blue1=(1, 2, 3),
    boundary_blue2=(9, 10, 11),
    boundary_red1=(5, 0, 6),
    boundary_red2=(13, 8, 14),
) -> cirq.Circuit:
    qs = qubits()
    bblue1 = [qs[i] for i in boundary_blue1]
    bblue2 = [qs[i] for i in boundary_blue2]
    bred1 = [qs[i] for i in boundary_red1]
    bred2 = [qs[i] for i in boundary_red2]

    wormhole_circuit.append(cirq.inverse(happy3_encode_noisy_wh(bblue1, scale=0, mean=0)))
    wormhole_circuit.append(cirq.inverse(happy3_encode_noisy_wh(bblue2, scale=0, mean=0)))
    wormhole_circuit.append(cirq.inverse(happy3_encode_noisy_wh(bred1, scale=0, mean=0)))
    wormhole_circuit.append(cirq.inverse(happy3_encode_noisy_wh(bred2, scale=0, mean=0)))
    return wormhole_circuit


def build_boundary_and_bulk_base(
    theta1: float,
    theta2: float,
    magic: float,
    *,
    optimized_recovery: cirq.Circuit | None = None,
    optimized_encoding_vector: np.ndarray | None = None,
    boundary_blue1=(1, 2, 3),
    boundary_blue2=(9, 10, 11),
    boundary_red1=(5, 0, 6),
    boundary_red2=(13, 8, 14),
    incl_rz_error: bool = True,
) -> tuple[cirq.Circuit, cirq.Circuit]:
    """Build the (boundary_base, bulk_base) pair for one (theta, magic)
    condition, matching WH16-C-C039 -- INCLUDING a confirmed historical
    aliasing bug for ``magic == 0.0`` that is preserved intentionally (see
    below) because it reflects what was actually executed on hardware.

    ``magic == 0.0``: WH16-C-C039 computes ``c_full = wormhole_reco(c_boundary,
    ...)``. ``wormhole_reco`` calls ``wormhole_circuit.append(...)`` on its
    argument and returns that SAME (now-mutated) object, so ``c_full`` and
    ``c_boundary`` become the identical, already-recovered circuit -- the
    subsequent "boundary" Pauli-tomography loop unintentionally measures the
    POST-RECOVERY state, not the pre-recovery encoded state. Verified against
    the staged executed QPYs: a plain (no-recovery) boundary construction
    disagrees with the executed "boundary"-labeled circuit's measurement
    probabilities (max|dp|~1e-3), while the SAME recovered circuit used for
    both boundary- and bulk-labeled tomography reproduces both exactly
    (max|dp|=0.0). This function reproduces that behavior for magic=0.0
    rather than the "intended" separate-circuits design: the executed QPY
    files are treated as the ground truth for what ran on hardware, and
    construction code is written to match them rather than to match the
    notebook author's original intent.

    ``magic == 1.0``: no aliasing occurs (``c_full = prep + encode +
    circ_opt_reloaded`` is a fresh expression, not an in-place mutation of
    ``c_boundary``), so boundary and bulk are genuinely different circuits:
    the manuscript's executed circuits use the *optimized* coherent-error
    vector (``x_best_010.npy``, applied via
    :func:`holographic_codes.circuits.ionq_native.add_coh_err_all_gates_cirq`)
    for encoding, and the pickled optimized recovery circuit
    (``circ_opt_reco_opt_magic_params``) instead of the Clifford recovery.
    """
    from .ionq_native import add_coh_err_all_gates_cirq

    prep = generate_ent(theta1, theta2)
    encode_noiseless = base_circuit_16(noise_scale=0.0, mean=0.0)

    if magic and optimized_encoding_vector is not None:
        encode = add_coh_err_all_gates_cirq(
            encode_noiseless,
            x0=optimized_encoding_vector * magic,
            include_rz_error=incl_rz_error,
            sanity_check_counts=True,
        )
    else:
        encode = encode_noiseless

    if magic and optimized_recovery is not None:
        # magic=1.0: genuinely separate circuits (no aliasing in the source).
        boundary_base = prep + encode
        bulk_base = prep + encode + optimized_recovery
    else:
        # magic=0.0: reproduce the source's aliasing bug -- both "boundary"
        # and "bulk" tomography settings share this SAME recovered circuit.
        recovered = wormhole_reco(
            (prep + encode).copy(),
            boundary_blue1, boundary_blue2, boundary_red1, boundary_red2,
        )
        boundary_base = recovered
        bulk_base = recovered

    return boundary_base, bulk_base

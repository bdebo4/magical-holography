"""Shared noisy-gate primitives used by every HaPPY-code construction.

Derived from source cell SC8-C-C004, whose ``custom_H/X/Y/Z/S/cnot/cz``
decomposition of Clifford gates into the native-gate-friendly Rx/Ry/Rz/XX
basis was duplicated byte-for-byte across the three construction notebooks
(SC8-C-C004, WH10-C-C007, WH16-C-C005). This module is the single tested
definition used by the IonQ converter in
:mod:`holographic_codes.circuits.ionq_native`, eliminating that duplication.

The SC8-C-C004 version additionally threads a ``noise_array``/``noise_bool``
pair through every primitive (used for injecting the SC8/WH10 "magic"
overrotations at construction time). The WH10-C/WH16-C copies use a simpler
``noise: bool, mean: float, scale: float`` signature with no distinct
per-gate-type noise channel. Both call conventions are preserved here as
``build_*`` functions parameterized explicitly (no notebook globals), rather
than picking one and silently dropping the other's historical behavior.
"""
from __future__ import annotations

from typing import Sequence

import cirq
import numpy as np


def generate_dtheta_SQ(noise_array: np.ndarray, noise_bool: Sequence[bool]) -> float:
    """Single-qubit coherent/incoherent angle jitter (SC8-C-C004)."""
    return float(
        np.random.normal(
            loc=noise_array[0] * noise_bool[0],
            scale=noise_array[1] * noise_bool[1],
        )
    )


def generate_dtheta_XX(noise_array: np.ndarray, noise_bool: Sequence[bool]) -> float:
    """Two-qubit (XX) coherent/incoherent angle jitter (SC8-C-C004)."""
    return float(
        np.random.normal(
            loc=noise_array[2] * noise_bool[0],
            scale=noise_array[3] * noise_bool[1],
        )
    )


# ---------------------------------------------------------------------------
# SC8-C-C004 call convention: noise_array (4-vector) + noise_bool (2-vector).
# ---------------------------------------------------------------------------

def custom_cnot(c: cirq.Circuit, q1, q2, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    c.append(cirq.Ry(rads=np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(q1))
    c.append(cirq.XXPowGate(exponent=1 / 2 + generate_dtheta_XX(noise_array, noise_bool) / np.pi)(q1, q2))
    c.append(cirq.Rx(rads=-np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(q1))
    c.append(cirq.Rx(rads=-np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(q2))
    c.append(cirq.Ry(rads=-np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(q1))
    c.append(cirq.GlobalPhaseGate(-1j)())


def custom_cz(c: cirq.Circuit, q1, q2, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    custom_H(c, q2, noise_array, noise_bool)
    custom_cnot(c, q1, q2, noise_array, noise_bool)
    custom_H(c, q2, noise_array, noise_bool)


def custom_H(c: cirq.Circuit, q, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    c.append(cirq.Ry(rads=np.pi / 2 + generate_dtheta_SQ(noise_array, noise_bool))(q))
    c.append(cirq.Rx(rads=-np.pi + generate_dtheta_SQ(noise_array, noise_bool))(q))
    c.append(cirq.GlobalPhaseGate(-1j)())


def custom_Z(c: cirq.Circuit, q, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    c.append(cirq.Rz(rads=np.pi)(q))
    c.append(cirq.GlobalPhaseGate(1j)())


def custom_X(c: cirq.Circuit, q, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    c.append(cirq.Rx(rads=np.pi)(q) + generate_dtheta_SQ(noise_array, noise_bool))


def custom_Y(c: cirq.Circuit, q, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    c.append(cirq.Ry(rads=np.pi + generate_dtheta_SQ(noise_array, noise_bool))(q))


def custom_S(c: cirq.Circuit, q, noise_array: np.ndarray, noise_bool: Sequence[bool]) -> None:
    c.append(cirq.Rz(rads=np.pi / 2)(q))
    c.append(cirq.GlobalPhaseGate(np.exp(1j * np.pi / 4))())


# ---------------------------------------------------------------------------
# WH10-C-C007 / WH16-C-C005 call convention: noise: bool, mean, scale.
# Byte-identical between the two notebooks; kept as a distinct, explicitly
# named variant (not merged into the SC8 primitives above) because its noise
# model is structurally different (single shared Gaussian per gate instance,
# vs. SC8's separate systematic/random channels) -- see
# 01_IMPLEMENTATION_SPEC.md section 5.6 on variant isolation.
# ---------------------------------------------------------------------------

def wh_custom_cnot(c: cirq.Circuit, q1, q2, noise: bool = False, mean: float = 0.0, scale: float = 0.0) -> None:
    thetas = np.random.normal(0, scale, 5) if noise else np.zeros(5)
    c.append(cirq.Ry(rads=np.pi / 2 + mean + thetas[0])(q1))
    c.append(cirq.XXPowGate(exponent=1 / 2 + (mean + thetas[1]) / np.pi)(q1, q2))
    c.append(cirq.Rx(rads=-np.pi / 2 + mean + thetas[2])(q1))
    c.append(cirq.Rx(rads=-np.pi / 2 + mean + thetas[3])(q2))
    c.append(cirq.Ry(rads=-np.pi / 2 + mean + thetas[4])(q1))
    c.append(cirq.GlobalPhaseGate(-1j)())


def wh_custom_cz(c: cirq.Circuit, q1, q2, noise: bool = False, mean: float = 0.0, scale: float = 0.0) -> None:
    wh_custom_H(c, q2, noise, mean, scale)
    wh_custom_cnot(c, q1, q2, noise, mean, scale)
    wh_custom_H(c, q2, noise, mean, scale)


def wh_custom_H(c: cirq.Circuit, q, noise: bool = False, mean: float = 0.0, scale: float = 0.0) -> None:
    thetas = np.random.normal(0, scale, 2) if noise else np.zeros(2)
    c.append(cirq.Ry(rads=np.pi / 2 + mean + thetas[0])(q))
    c.append(cirq.Rx(rads=-np.pi + mean + thetas[1])(q))
    c.append(cirq.GlobalPhaseGate(-1j)())


def wh_custom_Z(c: cirq.Circuit, q, noise: bool = False, mean: float = 0.0, scale: float = 0.0) -> None:
    theta = np.random.normal(0, scale) if noise else 0.0
    c.append(cirq.Rz(rads=np.pi + mean + theta)(q))
    c.append(cirq.GlobalPhaseGate(1j)())


def wh_custom_S(c: cirq.Circuit, q, noise: bool = False, mean: float = 0.0, scale: float = 0.0) -> None:
    theta = np.random.normal(0, scale) if noise else 0.0
    c.append(cirq.Rz(rads=np.pi / 2 + mean + theta)(q))
    c.append(cirq.GlobalPhaseGate(np.exp(1j * np.pi / 4))())


def happy3_encode_noisy_wh(qubits, scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    """The [[3,1,3]]-style 3-qubit encoder shared by WH10/WH16 (identical
    body in WH10-C-C007 and WH16-C-C005)."""
    c = cirq.Circuit()
    wh_custom_H(c, qubits[0], True, mean, scale)
    wh_custom_S(c, qubits[0], True, mean, scale)
    wh_custom_S(c, qubits[2], True, mean, scale)
    wh_custom_cnot(c, qubits[0], qubits[1], True, mean, scale)
    wh_custom_cnot(c, qubits[0], qubits[2], True, mean, scale)
    wh_custom_S(c, qubits[2], True, mean, scale)
    wh_custom_H(c, qubits[2], True, mean, scale)
    wh_custom_cnot(c, qubits[1], qubits[0], True, mean, scale)
    wh_custom_cnot(c, qubits[2], qubits[0], True, mean, scale)
    wh_custom_cnot(c, qubits[2], qubits[1], True, mean, scale)
    wh_custom_cnot(c, qubits[1], qubits[2], True, mean, scale)
    wh_custom_cnot(c, qubits[2], qubits[1], True, mean, scale)
    wh_custom_H(c, qubits[1], True, mean, scale)
    wh_custom_S(c, qubits[1], True, mean, scale)
    wh_custom_S(c, qubits[2], True, mean, scale)
    wh_custom_cnot(c, qubits[1], qubits[2], True, mean, scale)
    wh_custom_S(c, qubits[2], True, mean, scale)
    wh_custom_H(c, qubits[2], True, mean, scale)
    wh_custom_S(c, qubits[0], True, mean, scale)
    wh_custom_S(c, qubits[0], True, mean, scale)
    wh_custom_S(c, qubits[2], True, mean, scale)
    wh_custom_S(c, qubits[2], True, mean, scale)
    return c


def happy4_encode_noisy_wh(qubits, scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    c = cirq.Circuit()
    wh_custom_H(c, qubits[2], True, mean, scale)
    wh_custom_cnot(c, qubits[2], qubits[3], True, mean, scale)
    c.append(happy3_encode_noisy_wh(qubits[:3], scale=scale, mean=mean))
    return c


def happy5_encode_noisy_wh(qubits, scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    c = cirq.Circuit()
    wh_custom_H(c, qubits[4], True, mean, scale)
    wh_custom_H(c, qubits[3], True, mean, scale)
    wh_custom_H(c, qubits[2], True, mean, scale)
    wh_custom_H(c, qubits[1], True, mean, scale)
    wh_custom_Z(c, qubits[0], True, mean, scale)

    wh_custom_cnot(c, qubits[4], qubits[0], True, mean, scale)
    wh_custom_cnot(c, qubits[3], qubits[0], True, mean, scale)
    wh_custom_cnot(c, qubits[2], qubits[0], True, mean, scale)
    wh_custom_cnot(c, qubits[1], qubits[0], True, mean, scale)

    wh_custom_cz(c, qubits[4], qubits[3], True, mean, scale)
    wh_custom_cz(c, qubits[3], qubits[2], True, mean, scale)
    wh_custom_cz(c, qubits[4], qubits[0], True, mean, scale)
    wh_custom_cz(c, qubits[2], qubits[1], True, mean, scale)
    wh_custom_cz(c, qubits[1], qubits[0], True, mean, scale)
    return c


def happy3_decode_noisy_wh(qubits, scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    return cirq.inverse(happy3_encode_noisy_wh(qubits, scale=0, mean=0))


def happy4_decode_noisy_wh(qubits, scale: float = 0.0, mean: float = 0.0) -> cirq.Circuit:
    return cirq.inverse(happy4_encode_noisy_wh(qubits, scale=0, mean=0))

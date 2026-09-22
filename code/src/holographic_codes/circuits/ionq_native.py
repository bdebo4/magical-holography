"""Cirq -> IonQ-native (GPI/GPI2/ZZ) conversion, and coherent-error injection.

Derived from source cell SC8-C-C009 (``to_ionq_gpi``,
``_fold_zz_turns_into_range``, ``cirq_to_qisk_ionq``, ``reattach_ionq_gates``),
whose logic was also duplicated verbatim in the shared analysis code
(``analysis_functions.py``); this module is the single tested definition.
Also incorporates ``analysis_functions.py::add_errors_to_cirq_circuit``
(SC8/WH10 magic injection during construction) and the ``load_overrotations``
/ ``add_coh_err_all_gates_cirq`` helpers used by the WH16 construction
notebook (dependencies of canonical source cell WH16-C-C039) for WH16's
optimized-magic injection.

The moving global phase-frame convention (``phase_turns_global``, indexed by
*physical* qubit) is preserved exactly: RZ is never emitted as a physical
gate, it is absorbed into a virtual Z-frame that later Rx/Ry conversions and
RZZ/ZZ folding read from.
"""
from __future__ import annotations

from typing import Sequence

import cirq
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ionq import GPI2Gate, GPIGate, ZZGate

from .conversion import cirq_to_qiskit
from .primitives import generate_dtheta_SQ, generate_dtheta_XX

TAU = 2 * np.pi
PI = np.pi
TOL = 1e-9

IONQ_NATIVE_GATES = ("rx", "ry", "rz", "rzz")


def _mod_turns(x: float) -> float:
    y = x % 1.0
    return 0.0 if abs(y - 1.0) < 1e-12 else y


def _turns(radians: float) -> float:
    return float(radians) / TAU


def _near(x: float, target: float, tol: float = TOL) -> bool:
    return abs(x - target) <= tol


def _normalize_pi(theta: float) -> float:
    t = (theta + PI) % TAU - PI
    for v in (0.0, 0.5 * PI, -0.5 * PI, PI, -PI):
        if abs(t - v) <= 1e-12:
            return float(v)
    return float(t)


def _fold_zz_turns_into_range(turns: float, phase_turns_global: list[float], gq0: int, gq1: int) -> float:
    """Fold ZZ 'turns' into [-0.25, 0.25) using ZZ(t+0.5) ~ (Z x Z).ZZ(t)."""
    folded = ((turns + 0.25) % 0.5) - 0.25
    k = int(np.round((turns - folded) / 0.5))
    if (k % 2) != 0:
        phase_turns_global[gq0] = _mod_turns(phase_turns_global[gq0] - 0.5)
        phase_turns_global[gq1] = _mod_turns(phase_turns_global[gq1] - 0.5)
    return folded


def to_ionq_gpi(
    circ: QuantumCircuit,
    phase_turns_global: list[float] | None = None,
    global_qubits: list[int] | None = None,
) -> tuple[QuantumCircuit, list[float]]:
    """Convert a Qiskit circuit in {rx,ry,rz,rzz} basis to IonQ's
    {gpi,gpi2,zz} basis, tracking a moving Z-frame per physical qubit."""
    nq = circ.num_qubits
    new = QuantumCircuit(circ.num_qubits, circ.num_clbits)

    if global_qubits is None:
        global_qubits = list(range(nq))
    elif len(global_qubits) != nq:
        raise ValueError(f"global_qubits length {len(global_qubits)} does not match circuit.num_qubits={nq}")

    max_idx = max(global_qubits) if global_qubits else -1
    if phase_turns_global is None:
        phase_turns_global = [0.0] * (max_idx + 1)
    else:
        phase_turns_global = list(phase_turns_global)
        if len(phase_turns_global) <= max_idx:
            phase_turns_global.extend([0.0] * (max_idx + 1 - len(phase_turns_global)))

    def emit_gpi2(i_local, base_turns):
        gq = global_qubits[i_local]
        ph = _mod_turns(base_turns + phase_turns_global[gq])
        new.append(GPI2Gate(ph), [new.qubits[i_local]])

    def emit_gpi(i_local, base_turns):
        gq = global_qubits[i_local]
        ph = _mod_turns(base_turns + phase_turns_global[gq])
        new.append(GPIGate(ph), [new.qubits[i_local]])

    for instr in circ.data:
        inst, qargs, cargs = instr.operation, instr.qubits, instr.clbits
        name = inst.name.lower()
        qs_local = [circ.find_bit(qb).index for qb in qargs]

        if name == "rz":
            theta = float(inst.params[0])
            t = _turns(theta)
            for gq in [global_qubits[i] for i in qs_local]:
                phase_turns_global[gq] = _mod_turns(phase_turns_global[gq] - t)
            continue

        if name == "rx":
            i_local = qs_local[0]
            gq = global_qubits[i_local]
            theta = _normalize_pi(float(inst.params[0]))
            if _near(theta, 0.5 * PI):
                emit_gpi2(i_local, 0.0)
            elif _near(theta, -0.5 * PI):
                emit_gpi2(i_local, 0.5)
            elif _near(theta, PI):
                emit_gpi(i_local, 0.0)
            elif _near(theta, -PI):
                emit_gpi(i_local, 0.5)
            elif _near(theta, 0.0):
                pass
            else:
                emit_gpi2(i_local, 0.75)
                phase_turns_global[gq] = _mod_turns(phase_turns_global[gq] - _turns(theta))
                emit_gpi2(i_local, 0.25)
            continue

        if name == "ry":
            i_local = qs_local[0]
            gq = global_qubits[i_local]
            theta = _normalize_pi(float(inst.params[0]))
            if _near(theta, 0.5 * PI):
                emit_gpi2(i_local, 0.25)
            elif _near(theta, -0.5 * PI):
                emit_gpi2(i_local, 0.75)
            elif _near(theta, PI):
                emit_gpi(i_local, 0.25)
            elif _near(theta, -PI):
                emit_gpi(i_local, 0.75)
            elif _near(theta, 0.0):
                pass
            else:
                emit_gpi2(i_local, 0.0)
                phase_turns_global[gq] = _mod_turns(phase_turns_global[gq] - _turns(theta))
                emit_gpi2(i_local, 0.5)
            continue

        if name in ("rzz", "zz"):
            theta_or_turns = float(inst.params[0])
            turns = _turns(theta_or_turns) if name == "rzz" else theta_or_turns
            q0_local, q1_local = qs_local
            gq0, gq1 = global_qubits[q0_local], global_qubits[q1_local]
            turns = _fold_zz_turns_into_range(turns, phase_turns_global, gq0, gq1)
            new.append(ZZGate(turns), [new.qubits[q0_local], new.qubits[q1_local]])
            continue

        new_qargs = [new.qubits[i] for i in qs_local]
        if cargs:
            cs = [circ.find_bit(cb).index for cb in cargs]
            new_cargs = [new.clbits[i] for i in cs]
        else:
            new_cargs = []
        new.append(inst, new_qargs, new_cargs)

    return new, phase_turns_global


def cirq_to_qisk_ionq(
    cirq_circuit: cirq.Circuit,
    opt_level: int,
    phase_turns_global: list[float] | None = None,
) -> tuple[QuantumCircuit, list[float]]:
    """Cirq -> Qiskit(rx/ry/rz/rzz, transpiled) -> IonQ-native(gpi/gpi2/zz)."""
    cirq_qubits = sorted(cirq_circuit.all_qubits())
    global_qubits = [q.x for q in cirq_qubits]

    qiskit_circuit = cirq_to_qiskit(cirq_circuit)
    qiskit_circuit = transpile(qiskit_circuit, basis_gates=list(IONQ_NATIVE_GATES), optimization_level=opt_level)

    qiskit_ionq_native, phase_turns_global = to_ionq_gpi(
        qiskit_circuit, phase_turns_global=phase_turns_global, global_qubits=global_qubits,
    )
    return qiskit_ionq_native, phase_turns_global


def reattach_ionq_gates(circ: QuantumCircuit) -> QuantumCircuit:
    """After QPY/JSON load, IonQ-native gates may come back as generic
    Instructions named gpi/gpi2/zz without matrices; reattach the real
    qiskit_ionq gate classes so Statevector simulation works."""
    new = QuantumCircuit(circ.num_qubits, circ.num_clbits)
    new.metadata = getattr(circ, "metadata", None)
    new.name = circ.name

    qubit_map = {old_q: new.qubits[i] for i, old_q in enumerate(circ.qubits)}
    clbit_map = {old_c: new.clbits[i] for i, old_c in enumerate(circ.clbits)}

    for instr in circ.data:
        op = instr.operation
        qargs = instr.qubits
        cargs = instr.clbits

        if op.name == "gpi":
            op = GPIGate(float(op.params[0]))
        elif op.name == "gpi2":
            op = GPI2Gate(float(op.params[0]))
        elif op.name == "zz":
            op = ZZGate(float(op.params[0]))

        new.append(op, [qubit_map[q] for q in qargs], [clbit_map[c] for c in cargs])

    return new


def add_errors_to_cirq_circuit(
    noiseless_cirq_circuit: cirq.Circuit,
    noise_array: np.ndarray,
    noise_bool: Sequence[bool],
    include_rz_error: bool = False,
) -> cirq.Circuit:
    """Add gate-angle (coherent/incoherent) errors to a Cirq circuit.

    ``noise_array`` length 4: legacy single SQ distribution shared by
    Rx/Ry/Rz plus one XX distribution (SC8-C-C078's ``theta_rotation``/
    ``logical_entanglement`` calls). Length 6: distinct per-gate-type
    coherent means (SC8-C-C078/WH10-D-C016's encoding-segment calls).
    """
    noise_array = np.asarray(noise_array, dtype=float)
    n = noise_array.shape[0]

    if n == 4:
        sq_noise_rx = sq_noise_ry = sq_noise_rz = xx_noise = noise_array
    elif n == 6:
        error_syst_Rx, error_syst_Ry, error_syst_Rz, error_rand_SQ, error_syst_ZZ, error_rand_ZZ = noise_array
        sq_noise_rx = np.array([error_syst_Rx, error_rand_SQ, error_syst_ZZ, error_rand_ZZ])
        sq_noise_ry = np.array([error_syst_Ry, error_rand_SQ, error_syst_ZZ, error_rand_ZZ])
        sq_noise_rz = np.array([error_syst_Rz, error_rand_SQ, error_syst_ZZ, error_rand_ZZ])
        xx_noise = np.array([0.0, 0.0, error_syst_ZZ, error_rand_ZZ])
    else:
        raise ValueError(f"noise_array must have length 4 or 6, got {n}.")

    noisy_circuit = cirq.Circuit()
    for moment in noiseless_cirq_circuit.moments:
        new_ops = []
        for op in moment.operations:
            gate = op.gate
            qs = op.qubits
            if isinstance(gate, cirq.XPowGate) and gate.global_shift == -0.5 and len(qs) == 1:
                theta = gate.exponent * np.pi
                new_ops.append(cirq.rx(theta + generate_dtheta_SQ(sq_noise_rx, noise_bool)).on(qs[0]))
            elif isinstance(gate, cirq.YPowGate) and gate.global_shift == -0.5 and len(qs) == 1:
                theta = gate.exponent * np.pi
                new_ops.append(cirq.ry(theta + generate_dtheta_SQ(sq_noise_ry, noise_bool)).on(qs[0]))
            elif isinstance(gate, cirq.ZPowGate) and gate.global_shift == -0.5 and len(qs) == 1:
                theta = gate.exponent * np.pi
                if include_rz_error:
                    new_ops.append(cirq.rz(theta + generate_dtheta_SQ(sq_noise_rz, noise_bool)).on(qs[0]))
                else:
                    new_ops.append(op)
            elif isinstance(gate, cirq.XXPowGate) and len(qs) == 2:
                theta = gate.exponent * np.pi
                theta_noisy = theta - generate_dtheta_XX(xx_noise, noise_bool)
                new_ops.append(cirq.XXPowGate(exponent=theta_noisy / np.pi, global_shift=gate.global_shift).on(*qs))
            else:
                new_ops.append(op)
        noisy_circuit.append(new_ops)
    return noisy_circuit


def load_overrotations(path: str) -> np.ndarray:
    """Load an optimized coherent-overrotation vector (``x_best_010.npy``).

    Source: the 16-qubit wormhole construction notebook, cell 2 (a
    dependency of canonical cell WH16-C-C039).
    """
    return np.load(path)


def add_coh_err_all_gates_cirq(
    noiseless_cirq_circuit: cirq.Circuit,
    x0: np.ndarray,
    N_RX: int = 110,
    N_RY: int = 110,
    N_RZ: int = 22,
    N_XX: int = 36,
    include_rz_error: bool = True,
    sanity_check_counts: bool = True,
) -> cirq.Circuit:
    """Apply per-gate coherent over/under-rotations from a flat vector x0.

    Source: the 16-qubit wormhole construction notebook, cell 7, a
    dependency of canonical cell WH16-C-C039 (WH16's optimized magic
    injection, gate-position-indexed rather than random per call).

    Layout: x0[0:N_RX] -> Rx deltas, x0[N_RX:N_RX+N_RY] -> Ry deltas,
    x0[N_RX+N_RY:+N_RZ] -> Rz deltas, remainder -> XX deltas. Sign
    convention matches ``add_errors_to_cirq_circuit``: Rx/Ry/Rz get
    ``theta + delta``, XX gets ``theta - delta``.
    """
    x0 = np.asarray(x0, dtype=float)
    expected_len = N_RX + N_RY + N_RZ + N_XX
    if x0.shape[0] != expected_len:
        raise ValueError(f"x0 has length {x0.shape[0]}, expected {expected_len}.")

    off_rx, off_ry, off_rz = 0, N_RX, N_RX + N_RY
    off_xx = off_rz + N_RZ
    i_rx = i_ry = i_rz = i_xx = 0

    noisy_circuit = cirq.Circuit()
    for moment in noiseless_cirq_circuit.moments:
        new_ops = []
        for op in moment.operations:
            gate = op.gate
            qs = op.qubits
            if isinstance(gate, cirq.XPowGate) and gate.global_shift == -0.5 and len(qs) == 1:
                theta = float(gate.exponent) * np.pi
                delta = x0[off_rx + i_rx]
                i_rx += 1
                new_ops.append(cirq.rx(theta + delta).on(qs[0]))
            elif isinstance(gate, cirq.YPowGate) and gate.global_shift == -0.5 and len(qs) == 1:
                theta = float(gate.exponent) * np.pi
                delta = x0[off_ry + i_ry]
                i_ry += 1
                new_ops.append(cirq.ry(theta + delta).on(qs[0]))
            elif isinstance(gate, cirq.ZPowGate) and gate.global_shift == -0.5 and len(qs) == 1:
                if include_rz_error:
                    theta = float(gate.exponent) * np.pi
                    delta = x0[off_rz + i_rz]
                    i_rz += 1
                    new_ops.append(cirq.rz(theta + delta).on(qs[0]))
                else:
                    new_ops.append(op)
            elif isinstance(gate, cirq.XXPowGate) and len(qs) == 2:
                theta = float(gate.exponent) * np.pi
                delta = x0[off_xx + i_xx]
                i_xx += 1
                theta_new = theta - delta
                new_ops.append(cirq.XXPowGate(exponent=theta_new / np.pi, global_shift=gate.global_shift).on(*qs))
            else:
                new_ops.append(op)
        noisy_circuit.append(new_ops)

    if sanity_check_counts:
        if i_rx != N_RX:
            raise RuntimeError(f"Encountered {i_rx} Rx gates, expected {N_RX}.")
        if i_ry != N_RY:
            raise RuntimeError(f"Encountered {i_ry} Ry gates, expected {N_RY}.")
        if include_rz_error and (i_rz != N_RZ):
            raise RuntimeError(f"Encountered {i_rz} Rz gates, expected {N_RZ}.")
        if i_xx != N_XX:
            raise RuntimeError(f"Encountered {i_xx} XX gates, expected {N_XX}.")

    return noisy_circuit


def generate_dphi_SQ_turns(noise_array: np.ndarray, noise_bool: Sequence[bool]) -> float:
    """Single-qubit (GPI/GPI2) phase-axis error, in turns.
    ``noise_array = [error_syst_SQ, error_rand_SQ, error_syst_XX, error_rand_XX]``."""
    error_syst_SQ, error_rand_SQ, _, _ = noise_array
    coherent_error, incoherent_error = noise_bool
    loc = error_syst_SQ if coherent_error else 0.0
    scale = error_rand_SQ if incoherent_error else 0.0
    return float(np.random.normal(loc=loc, scale=scale))


def generate_dphi_ZZ_turns(noise_array: np.ndarray, noise_bool: Sequence[bool]) -> float:
    """Two-qubit ZZ over/under-rotation error, in turns."""
    _, _, error_syst_XX, error_rand_XX = noise_array
    coherent_error, incoherent_error = noise_bool
    loc = error_syst_XX if coherent_error else 0.0
    scale = error_rand_XX if incoherent_error else 0.0
    return float(np.random.normal(loc=loc, scale=scale))


def add_errors_to_ionq_circuit(
    noiseless_circuit: QuantumCircuit,
    noise_array: np.ndarray,
    noise_bool: Sequence[bool],
    coherent_errors: np.ndarray | None = None,
) -> QuantumCircuit:
    """Add small per-gate errors (in turns) to an already-native GPI/GPI2/ZZ
    circuit. Canonical source: ``analysis_functions.py::
    add_errors_to_ionq_circuit`` (line 816) -- the per-*simulation-trajectory*
    incoherent-noise injector used by SC8-C-C053/WH10-C-C057/WH16-C-C071's
    K-trajectory Monte Carlo, distinct from
    :func:`add_errors_to_cirq_circuit` (construction-time, pre-native-conversion
    coherent "magic" injection).
    """
    if coherent_errors is not None:
        coherent_errors = np.asarray(coherent_errors, dtype=float).ravel()

    noisy_circuit = QuantumCircuit(noiseless_circuit.num_qubits, noiseless_circuit.num_clbits)
    zz_count = 0

    for instruction in noiseless_circuit.data:
        instr, qargs, cargs = instruction.operation, instruction.qubits, instruction.clbits
        name = instr.name.lower()
        params = list(instr.params)

        if name in ("gpi", "gpi2"):
            phi = float(params[0])
            dphi = generate_dphi_SQ_turns(noise_array, noise_bool)
            phi_noisy = _mod_turns(phi + dphi)
            noisy_gate = GPIGate(phi_noisy) if name == "gpi" else GPI2Gate(phi_noisy)
            noisy_circuit.append(noisy_gate, qargs, cargs)
        elif name == "zz":
            zz_phase = float(params[0])
            dphi_zz = generate_dphi_ZZ_turns(noise_array, noise_bool)
            extra = 0.0
            if coherent_errors is not None:
                if zz_count >= len(coherent_errors):
                    raise ValueError(
                        f"coherent_errors has length {len(coherent_errors)} but circuit contains "
                        f"more than {len(coherent_errors)} ZZ gates (failed at ZZ index {zz_count})."
                    )
                extra = float(coherent_errors[zz_count])
            zz_phase_noisy = zz_phase - np.sign(zz_phase) * dphi_zz + extra
            noisy_circuit.append(ZZGate(zz_phase_noisy), qargs, cargs)
            zz_count += 1
        else:
            noisy_circuit.append(instr, qargs, cargs)

    return noisy_circuit

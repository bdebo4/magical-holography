"""Cirq -> Qiskit circuit conversion (RX/RY/RZ/RZZ + CNOT/CZ/H/S basis).

Derived from ``cirq_to_qiskit`` in the manuscript authors' shared analysis
code (``analysis_functions.py``), which appeared as a byte-identical copy in
both the construction/simulation and execution/analysis source repositories.
This module is the single tested definition used throughout the capsule.
"""
from __future__ import annotations

import cirq
import numpy as np
from qiskit import QuantumCircuit


def cirq_to_qiskit(cirq_circuit: cirq.Circuit) -> QuantumCircuit:
    """Convert a Cirq circuit to a Qiskit circuit, gate-for-gate."""
    cirq_qubits = sorted(cirq_circuit.all_qubits())
    n_qubits = len(cirq_qubits)
    qiskit_circuit = QuantumCircuit(n_qubits)
    qubit_map = {cirq_q: i for i, cirq_q in enumerate(cirq_qubits)}

    for moment in cirq_circuit.moments:
        for op in moment.operations:
            gate = op.gate
            qubits = [qubit_map[q] for q in op.qubits]

            if gate == cirq.H:
                qiskit_circuit.h(qubits[0])
            elif gate == cirq.X:
                qiskit_circuit.x(qubits[0])
            elif gate == cirq.Y:
                qiskit_circuit.y(qubits[0])
            elif gate == cirq.Z:
                qiskit_circuit.z(qubits[0])
            elif gate == cirq.S:
                qiskit_circuit.s(qubits[0])
            elif gate == cirq.CNOT:
                qiskit_circuit.cx(qubits[0], qubits[1])
            elif gate == cirq.CZ:
                qiskit_circuit.cz(qubits[0], qubits[1])
            elif isinstance(gate, cirq.rx(np.pi).__class__):  # XPowGate
                qiskit_circuit.rx(gate.exponent * np.pi, qubits[0])
            elif isinstance(gate, cirq.ry(np.pi).__class__):  # YPowGate
                qiskit_circuit.ry(gate.exponent * np.pi, qubits[0])
            elif isinstance(gate, cirq.rz(np.pi).__class__):  # ZPowGate
                qiskit_circuit.rz(gate.exponent * np.pi, qubits[0])
            elif isinstance(gate, cirq.XXPowGate):
                qiskit_circuit.rxx(gate.exponent * np.pi, qubits[0], qubits[1])
            elif isinstance(gate, cirq.YYPowGate):
                qiskit_circuit.ryy(gate.exponent * np.pi, qubits[0], qubits[1])
            elif isinstance(gate, cirq.ZZPowGate):
                qiskit_circuit.rzz(gate.exponent * np.pi, qubits[0], qubits[1])
            elif isinstance(gate, cirq.GlobalPhaseGate):
                qiskit_circuit.global_phase += np.angle(gate.coefficient)
            else:
                raise ValueError(f"Unsupported gate type {type(gate).__name__}: {gate}")
    return qiskit_circuit

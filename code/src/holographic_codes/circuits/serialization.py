"""QPY read/write helpers.

Canonical source: every exporter cell (SC8-C-C078, WH10-D-C016, WH16-C-C039)
calls ``qpy.dump(circuit, f)`` to save and downstream analysis notebooks call
``qpy.load(f)`` to read. This module centralizes both.
"""
from __future__ import annotations

from pathlib import Path

from qiskit import QuantumCircuit
from qiskit import qpy


def load_qpy(path: str | Path) -> QuantumCircuit:
    with open(path, "rb") as f:
        circuits = qpy.load(f)
    if len(circuits) != 1:
        raise ValueError(f"Expected exactly one circuit in {path}, found {len(circuits)}.")
    return circuits[0]


def dump_qpy(circuit: QuantumCircuit, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        qpy.dump(circuit, f)

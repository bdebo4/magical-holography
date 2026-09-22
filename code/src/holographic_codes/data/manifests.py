"""Typed readers for the deterministic hardware/circuit selection manifests.

No module under ``holographic_codes.analysis`` reads live job-status data
directly. All job/circuit/mapping/shot information for the published
analyses comes from two explicit, immutable manifests staged once ahead of
time: ``data/manifests/selected_circuits.csv`` and
``data/manifests/selected_hardware_jobs.csv``. This keeps dataset selection
(which jobs and circuits are part of the reported result) fully explicit and
independent of filesystem ordering or ad hoc filtering at analysis time.
"""
from __future__ import annotations

import csv
import dataclasses
import json
from pathlib import Path

from ..paths import PROJECT_ROOT, manifests_dir


@dataclasses.dataclass(frozen=True)
class SelectedCircuit:
    experiment: str
    condition_id: str
    measurement_role: str
    pauli_string: str
    circuit_index: int
    circuit_name: str
    qpy_relpath: str
    qpy_sha256: str
    expected_shots_aggregate: int
    actual_shots_aggregate: int


@dataclasses.dataclass(frozen=True)
class SelectedJob:
    experiment: str
    condition_id: str
    theta_code: str
    magic_value: float
    mu_code: str
    measurement_role: str
    pauli_string: str
    circuit_index: int
    circuit_name: str
    job_id: str
    raw_json_relpath: str
    shots: int
    mapping: list[int]


def _resolve_relpath(relpath: str) -> Path:
    """Manifest relpaths are recorded relative to the project root (they
    start with ``data/...``); resolve against PROJECT_ROOT, not DATA_ROOT,
    so a relocated ``HOLOGRAPHIC_CODES_DATA_ROOT`` doesn't silently break
    manifest resolution -- the manifests and the data they point at always
    move together."""
    return PROJECT_ROOT / relpath


def load_selected_circuits(experiment: str) -> list[SelectedCircuit]:
    path = manifests_dir() / "selected_circuits.csv"
    out = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["experiment"] != experiment.upper():
                continue
            out.append(
                SelectedCircuit(
                    experiment=row["experiment"],
                    condition_id=row["condition_id"],
                    measurement_role=row["measurement_role"],
                    pauli_string=row["pauli_string"],
                    circuit_index=int(row["circuit_index"]),
                    circuit_name=row["circuit_name"],
                    qpy_relpath=row["qpy_relpath"],
                    qpy_sha256=row["qpy_sha256"],
                    expected_shots_aggregate=int(row["expected_shots_aggregate"]) if row["expected_shots_aggregate"] else 0,
                    actual_shots_aggregate=int(row["actual_shots_aggregate"]) if row["actual_shots_aggregate"] else 0,
                )
            )
    if not out:
        raise ValueError(f"No selected_circuits.csv rows found for experiment={experiment!r}")
    return out


def load_selected_jobs(experiment: str) -> list[SelectedJob]:
    path = manifests_dir() / "selected_hardware_jobs.csv"
    out = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["experiment"] != experiment.upper():
                continue
            mapping = json.loads(row["mapping_json"]) if row["mapping_json"] else []
            out.append(
                SelectedJob(
                    experiment=row["experiment"],
                    condition_id=row["condition_id"],
                    theta_code=row["theta_code"],
                    magic_value=float(row["magic_value"]),
                    mu_code=row["mu_code"],
                    measurement_role=row["measurement_role"],
                    pauli_string=row["pauli_string"],
                    circuit_index=int(row["circuit_index"]),
                    circuit_name=row["circuit_name"],
                    job_id=row["job_id"],
                    raw_json_relpath=row["raw_json_relpath"],
                    shots=int(row["shots"]) if row["shots"] else 0,
                    mapping=[int(x) for x in mapping],
                )
            )
    if not out:
        raise ValueError(f"No selected_hardware_jobs.csv rows found for experiment={experiment!r}")
    return out


def resolve_qpy_path(circuit: SelectedCircuit) -> Path:
    return _resolve_relpath(circuit.qpy_relpath)


def resolve_raw_json_path(job: SelectedJob) -> Path:
    return _resolve_relpath(job.raw_json_relpath)

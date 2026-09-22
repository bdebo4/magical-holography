"""Physical-ion <-> logical-qubit mapping validation.

Each selected hardware job carries its own ion-to-qubit ``mapping`` (recorded
in the manifest, one list of ion indices per job -- IonQ re-maps logical
qubits onto different physical ions between jobs for calibration reasons).
This module enforces 01_IMPLEMENTATION_SPEC.md section 6's "fail loudly for
... incompatible mappings ... inconsistent bit widths."
"""
from __future__ import annotations

from .manifests import SelectedJob


def validate_consistent_mapping_width(jobs: list[SelectedJob], *, expected_width: int, context: str) -> None:
    """All jobs contributing to one circuit must map the same number of
    logical qubits (even though the physical ion indices they map to may
    differ from run to run)."""
    for job in jobs:
        if len(job.mapping) != expected_width:
            raise ValueError(
                f"{context}: job {job.job_id} (circuit {job.circuit_name!r}) has a "
                f"{len(job.mapping)}-qubit mapping {job.mapping}, expected width {expected_width}."
            )


def group_jobs_by_circuit(jobs: list[SelectedJob]) -> dict[str, list[SelectedJob]]:
    """Group a flat job list by circuit_name, preserving manifest order."""
    grouped: dict[str, list[SelectedJob]] = {}
    for job in jobs:
        grouped.setdefault(job.circuit_name, []).append(job)
    return grouped

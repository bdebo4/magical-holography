"""Typed configuration objects loaded from ``code/configs/*.yaml``.

Every historical parameter used anywhere in the analysis/simulation pipeline
comes from one of these dataclasses, populated from a reviewed YAML file,
rather than being inferred from a filename or hard-coded inline. This keeps
each experiment's parameterization (theta/magic grids, qubit indices, shot
expectations, bootstrap settings, ...) explicit and auditable in one place
instead of scattered across the code.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml

from .paths import CONFIG_ROOT


@dataclasses.dataclass(frozen=True)
class MeasurementScheme:
    scheme: str
    settings_per_condition: int
    boundary_qubits: list[int]
    bulk_qubits: list[int]
    separate_bulk_circuits: bool
    boundary_settings: int | None = None
    bulk_settings: int | None = None


@dataclasses.dataclass(frozen=True)
class ExperimentConfig:
    """One reviewed configuration preset for one experiment/mode.

    Populated verbatim from a YAML file under ``code/configs/``; see that
    file's own comments for the historical evidence behind each field.
    """

    name: str
    experiment: str  # "sc8" | "wh10" | "wh16"
    version: str  # e.g. "sc8_jan2026_equal_depth"
    mode: str  # "hardware" | "simulation_quick" | "simulation_full"

    theta_codes: list[str]
    theta_values: list[float]
    magic_codes: list[str]
    magic_values: list[float]

    measurement: MeasurementScheme

    n_qubits: int
    logical_qubits: list[int]

    executed_circuit_root: str  # relative to DATA_ROOT
    raw_count_root: str  # relative to DATA_ROOT
    selected_circuits_manifest: str  # relative to DATA_ROOT
    selected_jobs_manifest: str  # relative to DATA_ROOT

    expected_circuit_count_per_condition: int
    expected_shots_per_setting: dict[str, int]  # magic_code -> shots

    bootstrap_repeats: int
    bootstrap_seed: int

    simulation_runs: int | None
    simulation_seed: int | None
    simulation_shots: int | None
    optimizer_artifacts: list[str]
    noise_parameters: dict[str, Any]

    reference_summary: str  # relative to DATA_ROOT
    reference_simulation: str | None  # relative to DATA_ROOT

    quick_mode: bool
    extra: dict[str, Any] = dataclasses.field(default_factory=dict)

    @staticmethod
    def load(path: Path) -> "ExperimentConfig":
        raw = yaml.safe_load(path.read_text())
        measurement = MeasurementScheme(**raw.pop("measurement"))
        known = {f.name for f in dataclasses.fields(ExperimentConfig)} - {"measurement", "extra"}
        extra = {k: v for k, v in raw.items() if k not in known}
        kwargs = {k: v for k, v in raw.items() if k in known}
        return ExperimentConfig(measurement=measurement, extra=extra, **kwargs)


def load_config(name: str) -> ExperimentConfig:
    """Load a named config file, e.g. ``load_config("sc8_hardware")``."""
    path = CONFIG_ROOT / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"No such config: {path}")
    return ExperimentConfig.load(path)


@dataclasses.dataclass(frozen=True)
class PlottingConfig:
    design_settings_path: str
    dpi: int
    formats: list[str]

    @staticmethod
    def load() -> "PlottingConfig":
        path = CONFIG_ROOT / "plotting.yaml"
        raw = yaml.safe_load(path.read_text())
        return PlottingConfig(**raw)

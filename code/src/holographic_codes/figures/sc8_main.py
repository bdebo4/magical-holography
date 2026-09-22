"""SC8 main-paper figure. Canonical source: SC8-C-C070."""
from __future__ import annotations

import json

from ..config import ExperimentConfig
from ..paths import figures_dir, numerical_results_dir
from ._shared_plot import plot_boundary_bulk_qes


def make_figure(summary: dict, config: ExperimentConfig) -> dict:
    arrays = plot_boundary_bulk_qes(
        summary, "SC", config.magic_values, "SC8: single-copy holographic entropies",
        figures_dir() / "sc8_main.png",
    )
    with open(numerical_results_dir() / "sc8_main.json", "w") as f:
        json.dump(arrays, f, indent=2)
    return arrays

"""WH16 main-paper figure. Canonical source: WH16-C-C085."""
from __future__ import annotations

import json

from ..config import ExperimentConfig
from ..paths import figures_dir, numerical_results_dir
from ._shared_plot import plot_boundary_bulk_qes


def make_figure(summary: dict, config: ExperimentConfig) -> dict:
    arrays = plot_boundary_bulk_qes(
        summary, "WH16", config.magic_values, "WH16: 16-qubit wormhole entropies",
        figures_dir() / "wh16_main.png",
    )
    with open(numerical_results_dir() / "wh16_main.json", "w") as f:
        json.dump(arrays, f, indent=2)
    return arrays

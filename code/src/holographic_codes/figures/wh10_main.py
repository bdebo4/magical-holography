"""WH10 main-paper figure. Canonical source: WH10-C-C065."""
from __future__ import annotations

import json

from ..config import ExperimentConfig
from ..paths import figures_dir, numerical_results_dir
from ._shared_plot import plot_boundary_bulk_qes


def make_figure(summary: dict, config: ExperimentConfig) -> dict:
    arrays = plot_boundary_bulk_qes(
        summary, "WH10", config.magic_values, "WH10: two-copy wormhole entropies",
        figures_dir() / "wh10_main.png",
    )
    with open(numerical_results_dir() / "wh10_main.json", "w") as f:
        json.dump(arrays, f, indent=2)
    return arrays

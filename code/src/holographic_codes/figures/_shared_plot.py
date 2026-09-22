"""Shared 3-panel (boundary/bulk/QES vs theta) plot core.

All three experiments' "main paper plot" cells (SC8-C-C070, WH10-C-C065,
WH16-C-C085) share this layout; the per-experiment modules
(``sc8_main.py``/``wh10_main.py``/``wh16_main.py``) supply only their own
summary data and design/label lookups (01_IMPLEMENTATION_SPEC.md section
4.1: "one canonical implementation of duplicated helpers"). Plotting is kept
separate from computation (section 9): every array plotted here must already
exist in the summary dict produced by
:mod:`holographic_codes.io.summaries`.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .design import color_for_magic, label_for_magic, load_design_settings


def plot_boundary_bulk_qes(
    summary: dict,
    experiment_tag: str,
    magic_values: list[float],
    title: str,
    out_path: Path,
    dpi: int = 300,
) -> dict:
    """Render the 3-panel figure and return the exact numerical arrays used,
    for separate storage under /results/numerical/."""
    design = load_design_settings()
    data = summary[experiment_tag]
    theta_keys = [k for k in data if k != "_meta"]
    theta_keys.sort(key=lambda k: data[k]["theta_float"])
    theta_values = [data[k]["theta_float"] for k in theta_keys]

    arrays = {"theta_values": theta_values, "magic_values": magic_values, "boundary": {}, "bulk": {}, "qes": {}}
    for mi, magic in enumerate(magic_values):
        arrays["boundary"][magic] = [data[k]["boundary"]["mean"][mi] for k in theta_keys]
        arrays["bulk"][magic] = [data[k]["bulk"]["mean"][mi] for k in theta_keys]
        arrays["qes"][magic] = [data[k]["qes"]["mean"][mi] for k in theta_keys]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, kind in zip(axes, ["qes", "boundary", "bulk"]):
        for magic in magic_values:
            color = color_for_magic(design, magic)
            label = label_for_magic(design, magic)
            ax.plot(theta_values, arrays[kind][magic], "o--", color=color, label=label)
        ax.set_xlabel("theta")
        ax.set_title(kind)
        ax.grid(True, color="0.9")
    axes[0].legend()
    fig.suptitle(title)
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)

    return arrays

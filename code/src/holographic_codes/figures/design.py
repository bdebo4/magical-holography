"""Shared figure styling, loaded from the staged manuscript design settings.

Staged verbatim from the manuscript authors' own plotting-configuration file
at ``data/plot_design_settings.json`` and never re-typed by hand, so figure
styling (colors, markers, fonts) matches the manuscript exactly; see
``code/configs/plotting.yaml`` for how this file is referenced.
"""
from __future__ import annotations

import json

from ..config import PlottingConfig
from ..paths import DATA_ROOT


def load_design_settings() -> dict:
    cfg = PlottingConfig.load()
    with open(DATA_ROOT / cfg.design_settings_path) as f:
        return json.load(f)


def color_for_magic(design: dict, magic_value: float) -> str:
    key = str(float(magic_value))
    entry = design["colors"]["magic_values"].get(key)
    if entry is None:
        raise KeyError(f"No design color entry for magic={magic_value!r}")
    return entry["experiment"]


def label_for_magic(design: dict, magic_value: float) -> str:
    key = str(float(magic_value))
    return design["colors"]["magic_values"][key]["magic_text"]

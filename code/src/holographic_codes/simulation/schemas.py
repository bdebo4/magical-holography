"""Schema validation for staged production-simulation JSONs.

Validates the ``_meta`` block present in every staged reference-simulation
JSON under ``data/reference_simulations/``. This module checks *structure*,
not values: that the file has the keys this capsule's simulation/analysis
code depends on.
"""
from __future__ import annotations

REQUIRED_META_KEYS = (
    "experiment", "theta_values", "magic_values", "nq",
)


def validate_simulation_schema(sim_json: dict) -> list[str]:
    """Return a list of problems (empty = valid)."""
    problems = []
    if "_meta" not in sim_json:
        return ["missing top-level '_meta' key"]
    meta = sim_json["_meta"]
    for key in REQUIRED_META_KEYS:
        if key not in meta:
            problems.append(f"_meta missing required key {key!r}")
    for section in ("ideal", "noisy_QST"):
        if section not in sim_json:
            problems.append(f"missing top-level section {section!r}")
    return problems

"""Loading a single staged raw hardware-count JSON file.

Canonical source: ``data_functions.py::circuit_details_to_qubit_probs``
(the ``json.load`` half). Pure I/O, kept separate from
:mod:`holographic_codes.data.counts`'s aggregation-across-jobs logic per
01_IMPLEMENTATION_SPEC.md section 4.1 ("separate pure data parsing from
service access").
"""
from __future__ import annotations

import json
from pathlib import Path


def load_raw_counts(path: str | Path) -> dict[str, int]:
    """Load one raw hardware-count JSON: a dict of 36-bit ion bitstrings to
    integer shot counts. Never renormalized (see bit_order.py docstring)."""
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object of bitstring->count, got {type(data)}")
    return data

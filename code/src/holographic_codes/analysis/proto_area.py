"""Boundary-minus-bulk "proto-area" (QES) quantity.

Canonical source: ``SC8-D-C054``'s ``extract_mean_and_std`` (``qes_mean =
boundary_mean - bulk_mean``), the same convention used by the WH10/WH16
summary writers (``qes`` key in every reference summary JSON).
"""
from __future__ import annotations

import numpy as np


def proto_area(boundary_entropy: np.ndarray, bulk_entropy: np.ndarray) -> np.ndarray:
    return np.asarray(boundary_entropy) - np.asarray(bulk_entropy)


def proto_area_bootstrap_std(boundary_boot: np.ndarray, bulk_boot: np.ndarray, ddof: int = 1) -> np.ndarray:
    """Bootstrap standard deviation of boundary-bulk, given bootstrap arrays
    of shape (..., n_bootstrap)."""
    qes_boot = np.asarray(boundary_boot) - np.asarray(bulk_boot)
    return np.std(qes_boot, axis=-1, ddof=ddof)

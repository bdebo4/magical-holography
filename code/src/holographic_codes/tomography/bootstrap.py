"""Deterministic bootstrap resampling of measurement counts.

Derived from ``bootstrap_w_replacement`` in the manuscript authors' shared
analysis code. Made deterministic here by requiring an explicit
``numpy.random.Generator`` derived from a config-recorded seed, rather than
defaulting to ``np.random.default_rng()`` with no seed as the original code
sometimes does when ``rng`` is omitted -- so every bootstrap resampling in
this capsule is reproducible from its config alone.
"""
from __future__ import annotations

from collections import Counter

import numpy as np


def bootstrap_w_replacement(
    probs_dict: dict[str, float],
    rng: np.random.Generator,
    number_of_repeats: int = 100,
) -> dict[str, float]:
    """Combine ``number_of_repeats`` bootstrap resamples of ``probs_dict``
    (bitstring -> count) into one dict of the same keys with pooled counts.

    Raises if fewer than 500 total shots are available (matches the source
    cell's guard against unreliable bootstraps on tiny samples).
    """
    bitstrings = list(probs_dict.keys())
    counts = np.array(list(probs_dict.values()), dtype=float)

    total_shots = counts.sum()
    if total_shots < 500:
        raise ValueError("Too few shots for bootstrapping, minimum is 500.")

    p = counts / total_shots
    total_draws = int(total_shots * number_of_repeats)

    sampled = rng.choice(bitstrings, size=total_draws, replace=True, p=p)
    counter = Counter(sampled)

    return {bs: float(counter.get(bs, 0.0)) for bs in bitstrings}


def make_rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)

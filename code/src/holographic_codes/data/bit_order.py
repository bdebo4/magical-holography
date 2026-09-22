"""The 36-bit IonQ ion-to-qubit bit-order convention.

Derived from ``remap_ion_probs_to_qubit_probs`` and ``reverse_bitstring_keys``
in the manuscript authors' hardware-analysis code. Every raw hardware-count
JSON under ``data/hardware_counts/`` is a dict of 36-character ``'0'``/``'1'``
ion bitstrings -> integer counts (one bit per physical IonQ ion register
position, independent of how many logical qubits a given circuit actually
used).

Convention, made explicit and tested:

1. ``mapping[q]`` gives the *ion index* for logical qubit ``q``.
2. ``bit_order="right_to_left"``: ion bit ``i`` is read from the RIGHT end of
   the 36-character string, i.e. ``ion_bits[-1 - i]``.
3. The per-qubit string assembled in mapping order is then reversed again
   (``qubit_key = qubit_key[::-1]``) to land in Qiskit's little-endian
   convention (rightmost char = qubit 0).
4. Counts for raw JSON files are NEVER renormalized to probabilities before
   aggregation: shot totals are preserved exactly as recorded, and any
   normalization happens only downstream, after aggregation.

Every caller in this capsule uses ``bit_order="right_to_left"`` (the only
value ever passed by the canonical source cells); the function still accepts
"left_to_right" because the canonical source supports it, but no config in
this capsule selects it.
"""
from __future__ import annotations

from typing import Sequence


def remap_ion_probs_to_qubit_probs(
    ion_result: dict[str, float],
    mapping: Sequence[int],
    renormalize: bool = True,
    bit_order: str = "right_to_left",
) -> dict[str, float]:
    if not isinstance(mapping, (list, tuple)):
        raise TypeError(f"mapping must be a list/tuple of ints, got {type(mapping)}: {mapping}")
    if not ion_result:
        return {}

    example_key = next(iter(ion_result.keys()))
    n_ions = len(example_key)

    if any(len(k) != n_ions for k in ion_result.keys()):
        raise ValueError("All bitstring keys in ion_result must have the same length.")
    if max(mapping) >= n_ions or min(mapping) < 0:
        raise ValueError(f"Mapping indices must be between 0 and {n_ions - 1}; got {mapping}.")
    if bit_order not in ("left_to_right", "right_to_left"):
        raise ValueError("bit_order must be 'left_to_right' or 'right_to_left'.")

    qubit_result: dict[str, float] = {}
    for ion_bits, p in ion_result.items():
        qubit_bits = []
        for ion_idx in mapping:
            bit = ion_bits[ion_idx] if bit_order == "left_to_right" else ion_bits[-1 - ion_idx]
            qubit_bits.append(bit)
        qubit_key = "".join(qubit_bits)
        if bit_order == "right_to_left":
            qubit_key = qubit_key[::-1]
        qubit_result[qubit_key] = qubit_result.get(qubit_key, 0.0) + p

    if renormalize:
        total = sum(qubit_result.values())
        if total > 0:
            for k in qubit_result:
                qubit_result[k] /= total

    return qubit_result


def reverse_bitstring_keys(input_dict: dict[str, float]) -> dict[str, float]:
    """Reverse every bitstring key: '01234' -> '43210'."""
    return {key[::-1]: value for key, value in input_dict.items()}

"""Hardware-analysis summary JSON schema: write and compare.

Derived from source cell SC8-D-C048's ``save_entropy_summary_json``,
generalized for all three experiments. The schema written here never
asserts a separate ``N_CIRCS_BULK=3`` for SC8 -- since SC8's bulk entropy is
a marginal of the same 27 shared post-recovery circuits used for the
boundary entropy, not a distinct 3-circuit family, it records the true
shared-circuit metadata instead (``measurement_scheme:
shared_post_recovery_equal_depth``, ``num_executed_settings: 27``,
``bulk_from_same_tomography: true``).
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any


def _theta_key(t: float, sigfigs: int = 16) -> str:
    return format(float(t), f".{sigfigs}g")


def build_summary(
    experiment_tag: str,
    condition_results: list,
    theta_codes: list[str],
    theta_values: list[float],
    magic_values: list[float],
    *,
    measurement_scheme: str,
    num_executed_settings: int,
    bulk_from_same_tomography: bool,
    extra_meta: dict[str, Any] | None = None,
) -> dict:
    """Build the summary dict from a list of per-condition analysis results
    (each exposing .theta_code, .magic_value, .boundary_entropy,
    .bulk_entropy, .proto_area, .*_entropy_boot, .shots_used_boundary,
    .shots_used_bulk)."""
    by_theta: dict[str, dict[str, dict[str, list]]] = {}

    for tcode, tval in zip(theta_codes, theta_values):
        results_here = sorted(
            (r for r in condition_results if r.theta_code == tcode),
            key=lambda r: magic_values.index(r.magic_value) if r.magic_value in magic_values else 0,
        )
        if not results_here:
            continue

        def _std(attr_boot: str, mean_attr: str) -> list[float]:
            out = []
            for r in results_here:
                boot = getattr(r, attr_boot)
                out.append(float(boot.std(ddof=1)) if boot is not None and len(boot) > 1 else 0.0)
            return out

        def _qes_std() -> list[float]:
            out = []
            for r in results_here:
                bb, kb = r.boundary_entropy_boot, r.bulk_entropy_boot
                if bb is not None and kb is not None and len(bb) > 1:
                    out.append(float((bb - kb).std(ddof=1)))
                else:
                    out.append(0.0)
            return out

        by_theta[_theta_key(tval)] = {
            "theta_float": float(tval),
            "boundary": {
                "mean": [float(r.boundary_entropy) for r in results_here],
                "std": _std("boundary_entropy_boot", "boundary_entropy"),
            },
            "bulk": {
                "mean": [float(r.bulk_entropy) for r in results_here],
                "std": _std("bulk_entropy_boot", "bulk_entropy"),
            },
            "qes": {
                "mean": [float(r.proto_area) for r in results_here],
                "std": _qes_std(),
            },
            "shots_used": {
                "boundary": [int(r.shots_used_boundary) for r in results_here],
                "bulk": [int(r.shots_used_bulk) for r in results_here],
            },
        }

    meta = {
        "experiment_tag": experiment_tag,
        "theta_values": [float(t) for t in theta_values],
        "magic_values": [float(m) for m in magic_values],
        "kind_order": ["boundary", "bulk", "qes"],
        "stat_order": ["mean", "std"],
        "measurement_scheme": measurement_scheme,
        "num_executed_settings": num_executed_settings,
        "bulk_from_same_tomography": bulk_from_same_tomography,
        "generated_by": "holographic_codes.analysis (offline, from staged manifests)",
    }
    if extra_meta:
        meta.update(extra_meta)

    return {experiment_tag: {"_meta": meta, **by_theta}}


def write_summary(summary: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=False)


def load_summary(path: str | Path) -> dict:
    with open(path) as f:
        return json.load(f)


@dataclasses.dataclass
class SummaryComparisonResult:
    max_boundary_mean_diff: float
    max_bulk_mean_diff: float
    max_qes_mean_diff: float
    within_tolerance: bool
    per_theta_diffs: dict[str, dict[str, float]]


def compare_summaries(generated: dict, reference: dict, experiment_tag: str, tolerance: float = 1e-6) -> SummaryComparisonResult:
    gen = generated[experiment_tag]
    ref = reference[experiment_tag]
    theta_keys = [k for k in ref if k != "_meta"]

    max_b = max_k = max_q = 0.0
    per_theta: dict[str, dict[str, float]] = {}

    for tkey in theta_keys:
        if tkey not in gen:
            raise KeyError(f"Generated summary missing theta key {tkey!r} present in reference.")
        db = max(abs(g - r) for g, r in zip(gen[tkey]["boundary"]["mean"], ref[tkey]["boundary"]["mean"]))
        dk = max(abs(g - r) for g, r in zip(gen[tkey]["bulk"]["mean"], ref[tkey]["bulk"]["mean"]))
        dq = max(abs(g - r) for g, r in zip(gen[tkey]["qes"]["mean"], ref[tkey]["qes"]["mean"]))
        per_theta[tkey] = {"boundary": db, "bulk": dk, "qes": dq}
        max_b, max_k, max_q = max(max_b, db), max(max_k, dk), max(max_q, dq)

    within = max(max_b, max_k, max_q) <= tolerance
    return SummaryComparisonResult(max_b, max_k, max_q, within, per_theta)

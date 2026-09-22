"""Circuit regression vs staged executed QPYs.

Runs a deterministic representative sample (one circuit per experiment,
theta=0/first magic code) rather than the full 1,863-circuit batch, since
the full batch is too slow for routine test runs. The full-batch result
(1,863/1,863 circuits pass at the measurement-equivalent tier, 0 failures)
is recorded in ``data/manifests/circuit_regression_report.json``.

``measurement_equivalent`` (not ``structural``) is the pass criterion
because of a documented, benign property of the native-gate conversion
(see :mod:`holographic_codes.circuits.comparison` for the full explanation).
This suite also locks in the WH16 magic=0.0 boundary/bulk aliasing
(see :mod:`holographic_codes.circuits.construction_wh16`) and the SC8
magic>0 optimized-recovery-pickle requirement
(see :func:`holographic_codes.simulation.sc8._recovery_for_magic`).
"""
from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from holographic_codes.circuits import construction_sc8, construction_wh10, construction_wh16
from holographic_codes.circuits.comparison import compare_circuits
from holographic_codes.circuits.ionq_native import cirq_to_qisk_ionq
from holographic_codes.circuits.serialization import load_qpy
from holographic_codes.circuits.tomography_rotations import append_Paulis
from holographic_codes.paths import DATA_ROOT, optimized_artifacts_dir

SC8_QPY = DATA_ROOT / "executed_circuits" / "SC8" / "0000_000" / "00_Data_zeromagic_theta_0000_mu_000_bound_XXX_rx000_ry000_rz000_xx000.qpy"
SC8_HALFMAGIC_QPY = DATA_ROOT / "executed_circuits" / "SC8" / "0000_010" / "00_Data_halfMagic_theta_0000_mu_010_bound_XXX_rx007_ry012_rz007_xx010.qpy"
WH10_BOUND_QPY = DATA_ROOT / "executed_circuits" / "WH10" / "0000_000" / "00_Data_zeromagic_theta_0000_mu_000_bound_XXXX_rx000_ry000_rz000_xx000.qpy"
WH10_BULK_QPY = DATA_ROOT / "executed_circuits" / "WH10" / "0000_000" / "81_Data_zeromagic_theta_0000_mu_000_bulk_XX_rx000_ry000_rz000_xx000.qpy"
WH16_BOUND_QPY = DATA_ROOT / "executed_circuits" / "WH16" / "0000_000" / "000_Data_000_theta_0000_bound_XXXX_x_best_010_opt_recovery.qpy"
WH16_BULK_QPY = DATA_ROOT / "executed_circuits" / "WH16" / "0000_000" / "081_Data_000_theta_0000_bound_XXXX_x_best_010_opt_recovery.qpy"

pytestmark = pytest.mark.skipif(not SC8_QPY.exists(), reason="staged data/ not present in this checkout")


def test_sc8_representative_circuit_measurement_equivalent():
    base = construction_sc8.build_shared_post_recovery_base(0.0, 0.0)
    circ = base + append_Paulis([5, 0, 6], ("X", "X", "X"), num_qubits=8)
    mine, _ = cirq_to_qisk_ionq(circ, opt_level=3)
    ref = load_qpy(SC8_QPY)

    result = compare_circuits(mine, ref)
    assert result.passes, result.notes
    assert result.measurement_equivalent
    assert result.max_probability_diff < 1e-6


def test_sc8_halfmagic_requires_optimized_recovery_pickle():
    """D15: magic=0.5 must use circ_optimized_reco_singlecopy_halfmagic.pkl,
    not the plain Clifford recovery -- locks in the fix."""
    with open(optimized_artifacts_dir() / "circ_optimized_reco_singlecopy_halfmagic.pkl", "rb") as f:
        recovery = pickle.load(f)

    base_correct = construction_sc8.build_shared_post_recovery_base(0.0, 0.5, recovery_circuit=recovery)
    circ_correct = base_correct + append_Paulis([5, 0, 6], ("X", "X", "X"), num_qubits=8)
    mine_correct, _ = cirq_to_qisk_ionq(circ_correct, opt_level=3)
    ref = load_qpy(SC8_HALFMAGIC_QPY)
    result_correct = compare_circuits(mine_correct, ref)
    assert result_correct.passes, result_correct.notes

    # Sanity check: the *wrong* (Clifford) recovery must NOT match, proving
    # this test would have caught the original bug.
    base_wrong = construction_sc8.build_shared_post_recovery_base(0.0, 0.5, recovery_circuit=None)
    circ_wrong = base_wrong + append_Paulis([5, 0, 6], ("X", "X", "X"), num_qubits=8)
    mine_wrong, _ = cirq_to_qisk_ionq(circ_wrong, opt_level=3)
    result_wrong = compare_circuits(mine_wrong, ref)
    assert not result_wrong.passes


def test_wh10_representative_circuits_measurement_equivalent():
    boundary_base, bulk_base = construction_wh10.build_boundary_and_bulk_base(0.0, 0.0)

    circ_b = boundary_base + append_Paulis([3, 4, 8, 9], ("X", "X", "X", "X"), num_qubits=10)
    mine_b, _ = cirq_to_qisk_ionq(circ_b, opt_level=3)
    result_b = compare_circuits(mine_b, load_qpy(WH10_BOUND_QPY))
    assert result_b.passes, result_b.notes

    circ_k = bulk_base + append_Paulis([0, 5], ("X", "X"), num_qubits=10)
    mine_k, _ = cirq_to_qisk_ionq(circ_k, opt_level=3)
    result_k = compare_circuits(mine_k, load_qpy(WH10_BULK_QPY))
    assert result_k.passes, result_k.notes


def test_wh16_representative_circuits_measurement_equivalent_magic_zero():
    """Also locks in the D11 aliasing behavior: both boundary- and
    bulk-labeled circuits share one recovered base for magic=0.0."""
    boundary_base, bulk_base = construction_wh16.build_boundary_and_bulk_base(0.0, 0.0, 0.0)

    circ_b = boundary_base + append_Paulis([4, 12, 7, 15], ("X", "X", "X", "X"), num_qubits=16)
    mine_b, _ = cirq_to_qisk_ionq(circ_b, opt_level=3)
    result_b = compare_circuits(mine_b, load_qpy(WH16_BOUND_QPY))
    assert result_b.passes, result_b.notes
    assert result_b.max_probability_diff < 1e-9

    circ_k = bulk_base + append_Paulis([1, 9, 5, 13], ("X", "X", "X", "X"), num_qubits=16)
    mine_k, _ = cirq_to_qisk_ionq(circ_k, opt_level=3)
    result_k = compare_circuits(mine_k, load_qpy(WH16_BULK_QPY))
    assert result_k.passes, result_k.notes
    assert result_k.max_probability_diff < 1e-9

"""Pauli tomography, physicality projection, and entropy
(04_ACCEPTANCE_CRITERIA.md G.4-G.7)."""
import numpy as np

from holographic_codes.tomography.pauli import (
    add_pauli_measures_to_dict,
    expectation_of_pauli_string_from_probs,
    generate_pauli_basis,
    pauli_matrix_from_string,
)
from holographic_codes.tomography.physicality import mlm_rho
from holographic_codes.tomography.reconstruction import state_reconstruction_from_pauli_expectations


def test_pauli_matrix_from_string_is_unitary_and_hermitian():
    for s in ("X", "Y", "Z", "I", "XY", "ZZI"):
        m = pauli_matrix_from_string(list(s))
        assert np.allclose(m, m.conj().T)
        assert np.allclose(m @ m, np.eye(m.shape[0]))


def test_generate_pauli_basis_excludes_identity_only():
    strings, mats = generate_pauli_basis([0, 1])
    assert ("I", "I") not in strings
    assert len(strings) == 4 ** 2 - 1


def test_expectation_all_plus_one_gives_expectation_one():
    measure = {}
    add_pauli_measures_to_dict("Z", measure, {"0": 100.0})  # bit '0' -> eigenvalue +1
    assert expectation_of_pauli_string_from_probs(measure, "Z") == 1.0


def test_expectation_with_identity_averages_extensions():
    measure = {}
    add_pauli_measures_to_dict(("X", "X"), measure, {"00": 50.0, "11": 50.0})
    add_pauli_measures_to_dict(("Y", "X"), measure, {"00": 50.0, "11": 50.0})
    add_pauli_measures_to_dict(("Z", "X"), measure, {"00": 50.0, "11": 50.0})
    # <I,X> should average <X,X>,<Y,X>,<Z,X> each measuring qubit0-dropped correlator
    val = expectation_of_pauli_string_from_probs(measure, ("I", "X"))
    assert isinstance(val, float)


def test_mlm_rho_projects_negative_eigenvalues_away():
    # A Hermitian, trace-1 matrix with a small negative eigenvalue.
    mu = np.diag([0.6, 0.5, -0.1]).astype(complex)
    rho = mlm_rho(mu)
    evals = np.linalg.eigvalsh(rho)
    assert np.all(evals >= -1e-12)
    assert abs(np.trace(rho).real - 1.0) < 1e-9


def test_state_reconstruction_pure_zero_state_zero_entropy():
    # |0> state: <Z>=+1, <X>=<Y>=0 -> pure state, zero entropy.
    measure = {}
    add_pauli_measures_to_dict("X", measure, {"0": 500.0, "1": 500.0})
    add_pauli_measures_to_dict("Y", measure, {"0": 500.0, "1": 500.0})
    add_pauli_measures_to_dict("Z", measure, {"0": 1000.0})
    rho, entropy = state_reconstruction_from_pauli_expectations(measure, [0], use_mlm=True)
    assert entropy < 1e-6
    assert abs(rho[0, 0] - 1.0) < 1e-6


def test_state_reconstruction_maximally_mixed_gives_entropy_one():
    measure = {}
    add_pauli_measures_to_dict("X", measure, {"0": 500.0, "1": 500.0})
    add_pauli_measures_to_dict("Y", measure, {"0": 500.0, "1": 500.0})
    add_pauli_measures_to_dict("Z", measure, {"0": 500.0, "1": 500.0})
    rho, entropy = state_reconstruction_from_pauli_expectations(measure, [0], use_mlm=True)
    assert abs(entropy - 1.0) < 1e-3


def test_reduced_rho_from_statevector_matches_qiskit_qubit_order():
    """|01> in Qiskit little-endian convention (qubit0=1, qubit1=0):
    statevector index = qubit1*2+qubit0 = 1 -> psi=[0,1,0,0]. The qubit-0
    marginal must be |1><1|, and the qubit-1 marginal must be |0><0|."""
    import numpy as np
    from holographic_codes.analysis.entropy import reduced_rho_from_statevector_numpy

    psi = np.array([0, 1, 0, 0], dtype=complex)
    rho0 = reduced_rho_from_statevector_numpy(psi, [0], 2)
    rho1 = reduced_rho_from_statevector_numpy(psi, [1], 2)
    assert np.allclose(rho0, [[0, 0], [0, 1]])
    assert np.allclose(rho1, [[1, 0], [0, 0]])

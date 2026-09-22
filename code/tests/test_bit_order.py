"""36-bit IonQ bit-order convention, covered by known examples
(04_ACCEPTANCE_CRITERIA.md G.2)."""
from holographic_codes.data.bit_order import remap_ion_probs_to_qubit_probs, reverse_bitstring_keys


def test_remap_identity_mapping_right_to_left():
    # 4-ion register, mapping = identity, all bits distinct.
    ion_result = {"1000": 5.0, "0100": 3.0}
    out = remap_ion_probs_to_qubit_probs(ion_result, mapping=[0, 1, 2, 3], renormalize=False, bit_order="right_to_left")
    # ion_bits[-1-0]=ion_bits[3], etc.; for "1000": positions -1,-2,-3,-4 = '0','0','0','1' -> "0001" -> reversed "1000"
    assert out == {"1000": 5.0, "0100": 3.0}


def test_remap_extracts_subset_and_reorders():
    ion_result = {"101100": 10.0}  # 6-bit ion register
    # mapping picks ion indices [5, 0, 2] (right_to_left: ion i is ion_bits[-1-i])
    out = remap_ion_probs_to_qubit_probs(ion_result, mapping=[5, 0, 2], renormalize=False, bit_order="right_to_left")
    # ion_bits[-1-5]=bit0='1', ion_bits[-1-0]=bit-1='0', ion_bits[-1-2]=bit-3='1' -> "101" -> reversed "101"
    assert out == {"101": 10.0}


def test_remap_renormalizes_when_requested():
    ion_result = {"00": 1.0, "01": 3.0}
    out = remap_ion_probs_to_qubit_probs(ion_result, mapping=[0], renormalize=True, bit_order="right_to_left")
    assert abs(sum(out.values()) - 1.0) < 1e-12


def test_remap_rejects_inconsistent_key_lengths():
    import pytest
    with pytest.raises(ValueError):
        remap_ion_probs_to_qubit_probs({"01": 1.0, "1": 2.0}, mapping=[0], renormalize=False)


def test_remap_rejects_out_of_range_mapping():
    import pytest
    with pytest.raises(ValueError):
        remap_ion_probs_to_qubit_probs({"01": 1.0}, mapping=[5], renormalize=False)


def test_reverse_bitstring_keys():
    assert reverse_bitstring_keys({"01234": 1.0}) == {"43210": 1.0}
